import os
import logging
from dotenv import load_dotenv
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


class Settings:
    def __init__(self, log_level: int = logging.DEBUG):
        self.LOG_LEVEL = log_level
        self.CORS_ORIGINS: List[str] = [
            "https://d42d28ed-8111-4d52-a322-32ec5886beca.lovableproject.com",
            "http://localhost:8080", "http://127.0.0.1:8080",
            "http://localhost:3000", "http://127.0.0.1:3000",
            "https://health-policy-mapper.lovable.app"
        ]
        self.GOOGLE_API_KEY: str | None = None
        self.MODEL_NAME: str = "gemini-2.5-flash-lite"

    def load_env(self):
        load_dotenv()
        self.GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        if not self.GOOGLE_API_KEY:
            raise RuntimeError("Missing GOOGLE_API_KEY")

    def configure_logging(self):
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpcore.http11").setLevel(logging.WARNING)
        logging.getLogger("httpcore.connection").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("watchfiles.main").setLevel(logging.WARNING)
        logging.getLogger("python_multipart.multipart").setLevel(logging.WARNING)
        # logging.getLogger("google_genai.models").setLevel(logging.WARNING)

        logging.basicConfig(
            level=self.LOG_LEVEL,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def apply_cors(self, app: FastAPI):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )
