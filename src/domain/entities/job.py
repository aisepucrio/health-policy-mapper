from uuid import UUID, uuid4
from typing import List, Optional, Any, Dict
from domain.value_objects.column import Column

import pandas as pd


class JobStatus:
    PENDING = "pending"
    RUNNING = "running"
    FAILED = "failed"
    DONE = "done"
    DONE_WITH_ERRORS = "done_with_errors"

class Job:
    """
    Entity representing a job for processing documents with an LLM.
    """

    def __init__(
        self,
        files: List[Any],
        context: str,
        columns: List[Column],
        job_id: Optional[UUID] = None,
    ):
        self.id = job_id or uuid4()
        self.files = files
        self.context = context
        self.columns = columns
        self.status = JobStatus.PENDING
        self.result = None
        self.error_message = None
        self.total_files = len(files)
        self.files_processed = 0
        self.error_count = 0

    def start(self) -> None:
        """
        Start the job processing.
        """
        if self.status != JobStatus.PENDING:
            raise ValueError("Job can only be started if it is in pending state.")
        self.status = JobStatus.RUNNING

    def update_progress(self, files_processed: int, error_count: Optional[int] = None) -> None:
        """
        Update the progress of the job.
        """
        self.files_processed = files_processed
        if error_count is not None:
            self.error_count = error_count

    def complete(self, result: pd.DataFrame) -> None:
        """
        Mark the job as completed with the result.
        """
        if self.status != JobStatus.RUNNING:
            raise ValueError("Job can only be completed if it is running.")

        # Check if the result has any errors
        if self._has_errors(result):
            self.status = JobStatus.DONE_WITH_ERRORS
        else:
            self.status = JobStatus.DONE
        self.result = result

    def complete_with_errors(self, result: pd.DataFrame) -> None:
        """
        Mark the job as completed with errors.
        """
        if self.status != JobStatus.RUNNING:
            raise ValueError("Job can only be completed if it is running.")
        self.status = JobStatus.DONE_WITH_ERRORS
        self.result = result

    def _has_errors(self, result: pd.DataFrame) -> bool:
        """
        Check if the DataFrame has any rows with errors.
        """
        if result is None or result.empty:
            return False

        # Check if error column exists and has any non-empty, non-null values
        if 'error' in result.columns:
            error_column = result['error']
            # Consider an error if the error column has any non-null, non-empty values
            has_errors = error_column.notna() & (error_column != '') & (error_column.astype(str).str.strip() != '')
            return bool(has_errors.any())

        return False

    def fail(self, message: str) -> None:
        """
        Mark the job as failed with an error message.
        """
        if self.status != JobStatus.RUNNING:
            raise ValueError("Job can only be failed if it is running.")
        self.status = JobStatus.FAILED
        self.error_message = message

    def restart_for_retry(self, new_files_processed: int) -> None:
        """
        Restart a job with done_with_errors status for retry processing.
        Updates the files_processed count and changes status to running.
        """
        if self.status != JobStatus.DONE_WITH_ERRORS:
            raise ValueError("Job can only be restarted if it has done_with_errors status.")
        self.status = JobStatus.RUNNING
        self.files_processed = new_files_processed

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the Job object to a dict representation
        """
        return {
            "id": str(self.id),
            "files": self.files,
            "context": self.context,
            "columns": [col.to_dict() for col in self.columns],
            "status": self.status,
            "total_files": self.total_files,
            "files_processed": self.files_processed,
            "error_count": self.error_count,
            "result": self.result.to_dict() if isinstance(self.result, pd.DataFrame) else self.result,
            "error_message": self.error_message
        }
