from pathlib import Path
import tempfile

tmp_root = Path(tempfile.gettempdir()) / "hpm_jobs"

def get_job_temp_dir(job_id: str) -> Path: # bacalhau
    """
    Returns the temporary directory for a given job ID.
    Creates the directory if it does not exist.
    """
    job_dir = tmp_root / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir
