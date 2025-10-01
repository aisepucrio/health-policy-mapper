from typing import Optional
from application.use_cases.job_lifecycle import JobLifecycle

_lifecycle: Optional[JobLifecycle] = None

def set_lifecycle(lc: JobLifecycle) -> None:
    global _lifecycle
    _lifecycle = lc

def get_lifecycle() -> JobLifecycle:
    if _lifecycle is None:
        raise RuntimeError("JobLifecycle dependency not set")
    return _lifecycle
