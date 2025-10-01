from threading import Lock
from uuid import UUID
from domain.entities.job import Job
from application.interfaces.job_repository import JobRepository

class InMemoryJobRepository(JobRepository):
    def __init__(self):
        self._store = {} # Stores all the jobs in a dict {UUID: Job}
        self._lock = Lock() # Ensures thread safety for concurrent access

    def new_job(self, job: Job) -> UUID:
        with self._lock:
            self._store[job.id] = job
        return job.id

    def get_job(self, job_id: UUID) -> Job:
        with self._lock:
            job = self._store.get(job_id)

        if not job:
            raise ValueError(f"Job not found: {job_id}")
        return job

    def update_job(self, job: Job) -> None:
        with self._lock:
            if job.id not in self._store:
                raise ValueError(f"Job not found: {job.id}")
            self._store[job.id] = job
