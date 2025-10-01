import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import Settings
from presentation.controllers.job_controller import router as job_router
from presentation.controllers.eval_controller import router as eval_router
from presentation.dependencies import set_lifecycle
from application.interfaces.job_repository import JobRepository
from infrastructure.repository.job_repo_inmemory import InMemoryJobRepository
from application.use_cases.llm_processor import LLMProcessor
from application.use_cases.aggregator import Aggregator
from application.use_cases.job_lifecycle import JobLifecycle
from infrastructure.llm_clients.gemini_client import GeminiClient

settings = Settings()
settings.load_env()
settings.configure_logging()

logger = logging.getLogger(__name__)

# load dependencies
llm_client = GeminiClient(api_key=settings.GOOGLE_API_KEY, model_name=settings.MODEL_NAME)
llm_processor = LLMProcessor(llm_client)
aggregator     = Aggregator()
repo: JobRepository = InMemoryJobRepository()

# initialize the job lifecycle
lifecycle = JobLifecycle(repo=repo, llm_processor=llm_processor, aggregator=aggregator)

# create FastAPI app
app = FastAPI(title="Health Policy Mapper")

settings.apply_cors(app)

@app.get("/")
def root():
    return {
        "message": "Health Policy Mapper API",
        "docs": "/docs",
        "jobs": "/jobs"
    }


set_lifecycle(lifecycle)

# include the job router
app.include_router(
    job_router,
    prefix="/jobs",
    tags=["jobs"],
)

# include the evaluation router
app.include_router(
    eval_router,
    prefix="/eval",
    tags=["evaluation"],
)

logger.info("Health Policy Mapper API started successfully")
