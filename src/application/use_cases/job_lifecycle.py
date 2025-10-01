import logging
from uuid import UUID
from typing import List, Optional, Set
from pathlib import Path

import pandas as pd

from application.use_cases.aggregator import Aggregator
from application.interfaces.job_repository import JobRepository
from application.use_cases.llm_processor import LLMProcessor
from application.utils.temp_file_handler import get_job_temp_dir
from domain.value_objects.column import Column
from domain.entities.job import Job, JobStatus

# Set up logger
logger = logging.getLogger(__name__)


class JobLifecycle:
    """
    Orchestrates the full job workflow:
    1. create_job     -> register a new job
    2. process_job    -> run LLMProcessor in background
    3. get_job_status -> retrieve job status
    4. get_job_result -> retrieve job result as CSV
    """

    def __init__(
            self,
            repo: JobRepository,
            llm_processor: LLMProcessor,
            aggregator: Aggregator
    ):
        self.repo = repo
        self.llm_processor = llm_processor
        self.aggregator = aggregator


    def create_job(
            self,
            files: List[Path],
            context: str,
            columns: List[Column],
            job_id: Optional[UUID] = None,
            ) -> UUID:
        """
        Register a new job in PENDING state.
        :returns: the new job's UUID
        """
        job = Job(
            files=files,
            context=context,
            columns=columns,
            job_id=job_id,
        )
        final_job_id = self.repo.new_job(job)
        logger.info(f"Job {final_job_id} created with {len(files)} files and {len(columns)} columns")
        return final_job_id

    async def process_job(self, job_id: UUID, resume: bool = False) -> None:
        """
        Fetches the job, marks it RUNNING, then:
        1. runs LLMProcessor to get a DataFrame of raw rows
        2. runs Aggregator to collapse to one row per country
        3. stores the aggregated DataFrame in job.result
        4. marks job as DONE or FAILED

        Note: This method no longer handles failed jobs - use retry_failed_records for that.
        """
        logger.info(f"Starting job processing for {job_id}")

        job = self.repo.get_job(job_id)

        # Only process pending or running jobs
        if job.status == JobStatus.PENDING:
            job.start()
            self.repo.update_job(job)
            logger.info(f"Job {job_id} marked as RUNNING")
        elif job.status == JobStatus.RUNNING:
            logger.info(f"Job {job_id} already RUNNING; continuing")
        elif job.status in [JobStatus.DONE, JobStatus.DONE_WITH_ERRORS]:
            logger.info(f"Job {job_id} already {job.status}; skipping processing")
            return
        elif job.status == JobStatus.FAILED:
            logger.info(f"Job {job_id} is FAILED; use retry_failed_records if retry is needed")
            return
        else:
            logger.error(f"Job {job_id} in unexpected status {job.status}")
            return

        # Determine raw CSV path (incremental output of LLM processing)
        job_temp_dir = get_job_temp_dir(str(job_id))
        raw_csv_path = job_temp_dir / f"raw_data_{job_id}.csv"

        # Load already processed source_file names if resuming
        processed_sources: Set[str] = set()
        if raw_csv_path.exists() and resume:
            processed_files_list = self._get_processed_files(raw_csv_path)
            processed_sources = set(processed_files_list)
            job.update_progress(len(processed_sources))
            logger.info(f"Resume detected for job {job_id}: {len(processed_sources)} files already processed")

        try:
            await self._process_remaining_files(job, processed_sources, raw_csv_path)
            logger.info(f"Job {job_id} completed processing successfully")

        except Exception as e:
            logger.error(f"Job {job_id} failed: {str(e)}")
            job.fail(str(e))

        finally:
            self.repo.update_job(job)

    def prepare_retry_and_get_cleaned_csv(self, job_id: UUID) -> str:
        """
        Prepare a job for retry by cleaning the CSV and updating job state.
        Returns the cleaned CSV content as string.
        """
        logger.info(f"Preparing retry for job {job_id}")

        job = self.repo.get_job(job_id)

        # Validate job status
        if job.status != JobStatus.DONE_WITH_ERRORS:
            raise ValueError("Only jobs with done_with_errors status can be retried")

        # Get raw CSV path
        job_temp_dir = get_job_temp_dir(str(job_id))
        raw_csv_path = job_temp_dir / f"raw_data_{job_id}.csv"

        if not raw_csv_path.exists():
            raise RuntimeError(f"Raw CSV not found for job {job_id}")

        try:
            # Calculate current total files processed and errors before cleaning
            df = pd.read_csv(raw_csv_path)
            total_processed_before = len(df)
            error_count_before = 0
            if 'error' in df.columns:
                error_mask = df['error'].notna() & (df['error'] != '') & (df['error'].astype(str).str.strip() != '')
                error_count_before = error_mask.sum()

            # Clean errors from raw CSV
            self._clean_raw_csv_errors(raw_csv_path)

            # Get successfully processed files count after cleaning
            processed_files = self._get_processed_files(raw_csv_path)

            # Update job for retry: files_processed should be count of remaining records (after cleaning)
            job.restart_for_retry(len(processed_files))
            job.error_count = 0  # Reset error count since we cleaned the CSV
            self.repo.update_job(job)

            # Read and return the cleaned CSV content
            cleaned_csv_content = raw_csv_path.read_text(encoding='utf-8')

            logger.info(f"Job {job_id} prepared for retry with {len(processed_files)} successful records, {error_count_before} errors removed")
            return cleaned_csv_content

        except Exception as e:
            logger.error(f"Failed to prepare retry for job {job_id}: {str(e)}")
            raise

    async def retry_failed_records(self, job_id: UUID) -> None:
        """
        Retry processing of a job that completed with errors.
        This method assumes the CSV has already been cleaned and job status updated.
        """
        logger.info(f"Starting retry processing for job {job_id}")

        job = self.repo.get_job(job_id)

        # Job should already be in RUNNING status from prepare_retry_and_get_cleaned_csv
        if job.status != JobStatus.RUNNING:
            logger.warning(f"Job {job_id} not in running status for retry, current status: {job.status}")
            return

        # Get raw CSV path
        job_temp_dir = get_job_temp_dir(str(job_id))
        raw_csv_path = job_temp_dir / f"raw_data_{job_id}.csv"

        if not raw_csv_path.exists():
            logger.error(f"Raw CSV not found for job {job_id}")
            job.fail("Raw CSV not found")
            self.repo.update_job(job)
            return

        try:
            # Get successfully processed files (CSV should already be cleaned)
            processed_files = self._get_processed_files(raw_csv_path)

            # Identify files that need processing
            files_to_process = self._get_unprocessed_files(job, processed_files, set())

            if not files_to_process:
                logger.info(f"No files to reprocess for job {job_id}")
                # Re-evaluate the CSV to update job status
                df_raw = pd.read_csv(raw_csv_path)
                job.complete(result=df_raw)
                self.repo.update_job(job)
                return

            logger.info(f"Job {job_id} retry will process {len(files_to_process)} files")

            # Process the remaining files using existing processed files as starting point
            processed_sources = set(processed_files)
            await self._process_remaining_files(job, processed_sources, raw_csv_path, files_to_process)
            logger.info(f"Job {job_id} retry completed successfully")

        except Exception as e:
            logger.error(f"Job {job_id} retry failed: {str(e)}")
            job.fail(str(e))

        finally:
            self.repo.update_job(job)

    def _clean_raw_csv_errors(self, raw_csv_path: Path) -> Set[str]:
        """
        Remove rows with errors from the raw CSV and return set of error files removed.
        """
        try:
            df = pd.read_csv(raw_csv_path)

            if 'error' not in df.columns:
                logger.warning("No error column found in raw CSV")
                return set()

            # Identify error records
            error_mask = df['error'].notna() & (df['error'] != '') & (df['error'].astype(str).str.strip() != '')
            error_files = set(df.loc[error_mask, 'source_file'].astype(str).tolist())

            # Keep only successful records
            clean_df = df[~error_mask]
            clean_df.to_csv(raw_csv_path, index=False)

            logger.info(f"Cleaned {len(error_files)} error records from raw CSV")
            return error_files

        except Exception as e:
            logger.error(f"Failed to clean raw CSV errors: {e}")
            return set()

    def _get_processed_files(self, raw_csv_path: Path) -> List[str]:
        """
        Get list of successfully processed files from raw CSV.
        """
        try:
            if not raw_csv_path.exists():
                return []

            df = pd.read_csv(raw_csv_path)
            if 'source_file' not in df.columns:
                return []

            return df['source_file'].astype(str).tolist()

        except Exception as e:
            logger.warning(f"Failed reading processed files from CSV: {e}")
            return []

    def _get_unprocessed_files(self, job: Job, processed_files: List[str], error_files: Set[str]) -> List[Path]:
        """
        Identify files that need to be processed: unprocessed files + files that had errors.
        """
        processed_set = set(processed_files)
        unprocessed_files = []

        for file_path in job.files:
            file_name = file_path.name
            # Include if never processed or had errors
            if file_name not in processed_set or file_name in error_files:
                unprocessed_files.append(file_path)

        return unprocessed_files

    def _update_job_for_retry(self, job: Job, files_processed_count: int) -> None:
        """
        Update job state for retry processing.
        """
        job.restart_for_retry(files_processed_count)
        self.repo.update_job(job)

    async def _process_remaining_files(self, job: Job, processed_sources: Set[str], raw_csv_path: Path, files_to_process: Optional[List[Path]] = None) -> None:
        """
        Process remaining files for a job.
        """
        import csv

        # If no specific files provided, calculate remaining files
        if files_to_process is None:
            files_to_process = [p for p in job.files if p.name not in processed_sources]

        if not files_to_process:
            logger.info(f"No files to process for job {job.id}")
            # Load existing raw data
            if raw_csv_path.exists():
                df_raw = pd.read_csv(raw_csv_path)
                job.complete(result=df_raw)
            return

        logger.info(f"Processing {len(files_to_process)} files for job {job.id}")

        # Define fieldnames for CSV
        all_fieldnames = ['source_file']
        for col in job.columns:
            all_fieldnames.append(col.name)
            all_fieldnames.append(f"{col.name}_justification")
        all_fieldnames.append('error')

        # Track processed files and errors separately
        total_processed_files = set()  # All files (success + error) - start fresh for this processing session
        error_files = set()

        # Get baseline from existing job progress
        baseline_files_processed = job.files_processed
        baseline_error_count = job.error_count

        def row_callback(record, index, total):
            src = str(record.get('source_file'))

            # Skip if this file was already successfully processed (in processed_sources)
            if src in processed_sources:
                return

            # Skip if we already processed this file in current session
            if src in total_processed_files:
                return

            mode = 'a' if raw_csv_path.exists() else 'w'
            with open(raw_csv_path, mode, newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=all_fieldnames)
                if mode == 'w':
                    writer.writeheader()
                writer.writerow(record)

            # Always add to processed files regardless of error status
            total_processed_files.add(src)

            # Track errors separately
            if record.get('error'):
                error_files.add(src)

            # Update job progress with both counts (add to baseline)
            new_files_processed = baseline_files_processed + len(total_processed_files)
            new_error_count = baseline_error_count + len(error_files)
            self._update_job_progress(job.id, new_files_processed, new_error_count)

        # Process files with LLM
        df_new: pd.DataFrame = await self.llm_processor.run(
            documents=files_to_process,
            context=job.context,
            columns=job.columns,
            progress_callback=lambda processed: None,
            row_callback=row_callback,
        )

        # Load final result
        if raw_csv_path.exists():
            try:
                df_raw = pd.read_csv(raw_csv_path)
            except Exception:
                df_raw = df_new
        else:
            df_raw = df_new

        logger.info(f"LLM processing completed for job {job.id}. Generated {len(df_raw)} raw records")
        job.complete(result=df_raw)


    def _update_job_progress(self, job_id: UUID, files_processed: int, error_count: Optional[int] = None) -> None:
        """
        Update the progress of a job.
        """
        try:
            job = self.repo.get_job(job_id)
            job.update_progress(files_processed, error_count)
            self.repo.update_job(job)
            error_info = f", {error_count} errors" if error_count is not None else ""
            logger.debug(f"Job {job_id} progress updated: {files_processed}/{job.total_files} files processed{error_info}")
        except Exception as e:
            logger.error(f"Failed to update progress for job {job_id}: {str(e)}")


    def get_job_progress(self, job_id: UUID) -> dict:
        """
        Get the progress information for a job.
        """
        job = self.repo.get_job(job_id)
        return {
            "job_id": str(job.id),
            "status": job.status,
            "files_processed": job.files_processed,
            "total_files": job.total_files,
            "error_count": job.error_count,
            "error_message": job.error_message
        }


    def get_job(self, job_id: UUID) -> Job:
        """
        return the full job object
        """
        return self.repo.get_job(job_id)


    def get_job_result(self, job_id: UUID) -> str:
        """
        Once the job is DONE or DONE_WITH_ERRORS, return the result as a CSV file.
        """
        job = self.repo.get_job(job_id)

        if job.status not in [JobStatus.DONE, JobStatus.DONE_WITH_ERRORS] or not hasattr(job, 'result') or job.result is None:
            raise RuntimeError(f"Job {job_id} is not done or has no result.")

        logger.info(f"Returning CSV result for job {job_id}")
        return job.result.to_csv(index=False)
