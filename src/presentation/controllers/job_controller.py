from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, Depends, HTTPException, Response
from typing import List, Optional
import uuid
import shutil
import logging

import pandas as pd

from application.use_cases.job_lifecycle import JobLifecycle
from application.use_cases.aggregator import Aggregator
from application.utils.temp_file_handler import get_job_temp_dir
from presentation.schema import (
    JobCreatedResponse,
    JobStatusResponse,
    RawIncrementalResponse,
    ResumeResponse,
)
from presentation.dependencies import get_lifecycle
from presentation.parsers.column_parser import parse_columns_payload

# Set up logger
logger = logging.getLogger(__name__)


router = APIRouter()
aggregator = Aggregator()



@router.post("/", status_code=202, response_model=JobCreatedResponse)
async def create_job(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="One or more PDF files to process"),
    context: str = Form(..., description="Research context for the extraction"),
    columns: str = Form(..., description="List of fields (name + description) as a JSON string"),
    lifecycle: JobLifecycle = Depends(get_lifecycle),
):
    """
    Start a new extraction job
    Returns a job_id immediately and processes in background.
    """
    logger.info(f"New job request received with {len(files)} files")

    domain_columns = parse_columns_payload(columns)

    # Create job first to get the actual job ID
    temp_job_id = uuid.uuid4()
    tmp_dir = get_job_temp_dir(str(temp_job_id))

    paths = []

    for upload in files:

        if upload.filename is None:
            raise HTTPException(status_code=400, detail="Filename missing")
        dest = tmp_dir / upload.filename
        with dest.open("wb") as out_file:
            shutil.copyfileobj(upload.file, out_file)
        paths.append(dest)

    # Create job with the same UUID used for temp directory
    job_id = lifecycle.create_job(
        files=paths,
        context=context,
        columns=domain_columns,
        job_id=temp_job_id  # Pass the same UUID
    )

    background_tasks.add_task(
        lifecycle.process_job,
        job_id
    )

    logger.info(f"Job {job_id} created and queued for processing")
    return JobCreatedResponse(job_id=str(job_id))


@router.get("/{job_id}/status", response_model=JobStatusResponse)
def get_job_status(job_id: str, lifecycle: JobLifecycle = Depends(get_lifecycle)) -> JobStatusResponse:
    """
    Get the status of a job
    """
    # transform job_id from string to UUID
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    try:
        progress_info = lifecycle.get_job_progress(job_uuid)
        logger.debug(
            "Job %s status: %s (%d/%d)",
            job_id,
            progress_info['status'],
            progress_info['files_processed'],
            progress_info['total_files']
        )
        return JobStatusResponse(**progress_info)
    except ValueError:
        logger.warning(f"Job status requested for non-existent job: {job_id}")
        raise HTTPException(status_code=404, detail="Job not found")



@router.get("/{job_id}/result")
def get_job_result(job_id: str, lifecycle: JobLifecycle = Depends(get_lifecycle)):
    """
    Get the result of a job as CSV
    """
    logger.info(f"CSV download requested for job: {job_id}")

    # transform job_id from string to UUID
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    try:
        csv_text = lifecycle.get_job_result(job_uuid)
        logger.info(f"CSV download successful for job: {job_id}")
    except RuntimeError as e:
        logger.error(f"CSV download failed for job {job_id}: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=job_{job_id}.csv"}
    )


@router.get("/{job_id}/raw", response_model=RawIncrementalResponse)
def get_raw_data(
    job_id: str,
    format: str = "csv",
    since: Optional[int] = None,
    lifecycle: JobLifecycle = Depends(get_lifecycle)
):
    """Return raw (non-aggregated) data for a job.
    format=csv|json ; since=N (1-based row index) returns only new rows in JSON.
    """
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    job = lifecycle.get_job(job_uuid)
    if job.status not in ("running", "done", "failed") and job.files_processed == 0:
        raise HTTPException(404, "Job not started or no data yet")

    # Raw CSV path
    raw_path = get_job_temp_dir(job_id) / f"raw_data_{job_id}.csv"
    if not raw_path.exists():
        raise HTTPException(404, "Raw data not available yet")

    if format == "csv" and since is None:
        return Response(
            content=raw_path.read_text(encoding='utf-8'),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=raw_{job_id}.csv"}
        )

    # JSON / incremental
    try:
        df = pd.read_csv(raw_path, keep_default_na=False)
        # Ensure 'error' exists even for legacy CSVs
        if 'error' not in df.columns:
            df['error'] = ''
        else:
            df['error'] = df['error'].astype('string').fillna('')
    except Exception as e:
        raise HTTPException(500, f"Failed reading raw CSV: {e}")

    if since is not None:
        # since is 1-based, convert to 0-based slice
        start = max(since, 1) - 1
        if start >= len(df):
            subset = df.iloc[0:0]
        else:
            subset = df.iloc[start:]
    else:
        subset = df
    rows_instances = []
    for d in subset.to_dict(orient="records"):
        d['source_file'] = '' if d.get('source_file') in (None, float('nan')) else str(d.get('source_file', ''))
        err = d.get('error', '')
        # force string and remove NaN
        d['error'] = '' if err is None else ('' if str(err).lower() == 'nan' else str(err))
        rows_instances.append(d)
    return RawIncrementalResponse(
        total_rows=int(len(df)),
        rows_returned=int(len(rows_instances)),
        since=since,
        rows=rows_instances
    )


@router.post("/{job_id}/retry-failed-records", status_code=200)
async def retry_failed_records(job_id: str, lifecycle: JobLifecycle = Depends(get_lifecycle)):
    """Retry processing of a job that completed with errors by removing error records and reprocessing."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    # Verify that the job has done_with_errors status
    try:
        job = lifecycle.get_job(job_uuid)
        if job.status != "done_with_errors":
            raise HTTPException(
                status_code=400,
                detail="Only jobs with done_with_errors status can be retried"
            )
    except ValueError:
        raise HTTPException(status_code=404, detail="Job not found")

    # Clean the CSV immediately and get the cleaned content
    try:
        cleaned_csv_content = lifecycle.prepare_retry_and_get_cleaned_csv(job_uuid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to prepare retry: {str(e)}")

    # Start background processing
    background = BackgroundTasks()
    background.add_task(lifecycle.retry_failed_records, job_uuid)

    # Return the cleaned CSV immediately
    return Response(
        content=cleaned_csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=raw_{job_id}_cleaned.csv"},
        background=background
    )
@router.post("/{job_id}/resume", status_code=202, response_model=ResumeResponse)
async def resume_job(job_id: str, lifecycle: JobLifecycle = Depends(get_lifecycle)) -> ResumeResponse:
    """Resume a failed/incomplete job; continues processing remaining files."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format")

    background = BackgroundTasks()
    background.add_task(lifecycle.process_job, job_uuid, True)
    return ResumeResponse(job_id=job_id, status="resuming")


@router.post("/aggregate", status_code=200)
def aggregate_csv(upload: UploadFile = File(..., description="Raw CSV produced by extraction")):
    """Aggregate an uploaded raw CSV (stateless)."""
    import io
    if not upload.filename or not upload.filename.lower().endswith('.csv'):
        raise HTTPException(400, "A .csv file is required")
    try:
        content = upload.file.read()
        df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(400, f"Failed to read CSV: {e}")
    try:
        agg_df = aggregator.aggregate(df)
    except Exception as e:
        raise HTTPException(400, f"Aggregation failed: {e}")
    return Response(
        content=agg_df.to_csv(index=False),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=aggregated.csv"}
    )
