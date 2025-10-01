from abc import ABC, abstractmethod
from uuid import UUID
from domain.entities.job import Job

class JobRepository(ABC):
    """
    Abstract base class for job repositories.
    """

    @abstractmethod
    def new_job(self, job: Job) -> UUID:
        """
        Persists a new job and return its ID.
        """
        pass

    @abstractmethod
    def get_job(self, job_id: UUID) -> Job:
        """
        Retrieves a job by its ID or raise an error if not found.
        """
        pass

    @abstractmethod
    def update_job(self, job: Job) -> None:
        """
        Updates an existing job.
        """
        pass
