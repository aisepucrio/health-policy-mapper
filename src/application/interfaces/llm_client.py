from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List
from domain.value_objects.column import Column

class BaseLLMClient(ABC):
    """
    Abstract base class for LLM clients.
    """
    def __init__(self, api_key: str | None, model_name: str):
        """
        Initialize the LLM client with the provided API key.

        :param api_key: The API key for authenticating with the LLM service.
        """
        if not api_key:
            raise ValueError("API key must be provided.")

        if not model_name:
            raise ValueError("Model name must be provided.")

        self.api_key = api_key
        self.model_name = model_name

    @abstractmethod
    async def process(
        self,
        document_path: Path,
        prompt: str,
    ) -> List[Dict[str, Any]]:
        """
        Process the document with the LLM and return structured data.

        :param document: The document to process as bytes.
        :param prompt: The prompt to use for processing.
        :return: List of dictionaries containing the processed data.
        """
        pass
