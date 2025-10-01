from typing import Any, Dict, List
from google import genai
from google.genai import types
from pathlib import Path
import json
import re
import logging
import asyncio

from application.interfaces.llm_client import BaseLLMClient

# Set up logger
logger = logging.getLogger(__name__)

class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str | None, model_name: str):
        """
        Initialize the Gemini client with the provided API key.

        :param api_key: The API key for authenticating with the Gemini service.
        """
        super().__init__(api_key, model_name)
        self._client = genai.Client(api_key=self.api_key)
        self._model = model_name
        self._seed = 44

    async def process(
        self,
        document_path: Path,
        prompt: str,
    ) -> List[Dict[str, Any]]:
        """
        Async wrapper: executes the blocking logic in a thread to avoid blocking the event loop.
        """
        return await asyncio.to_thread(self._send_gemini_request, document_path, prompt)

    def _send_gemini_request(
        self,
        document_path: Path,
        prompt: str,
    ) -> List[Dict[str, Any]]:
        file_size = document_path.stat().st_size

        if file_size > 20 * 1024 * 1024:  # 20 MB limit
            sample_file = self._client.files.upload(file=str(document_path))
            response = self._client.models.generate_content(
                model=self._model,
                contents=[sample_file, prompt],
                config=types.GenerateContentConfig(
                    seed=self._seed,
                )
            )
        else:
            response = self._client.models.generate_content(
                model=self._model,
                contents=[
                    types.Part.from_bytes(
                        data=document_path.read_bytes(),
                        mime_type="application/pdf"
                    ),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    seed=self._seed,
                )
            )

        raw_text = getattr(response, "text", "")
        logger.debug(f"*********Raw response text: {raw_text}")
        parsed = self._parse_response(raw_text)

        if not isinstance(parsed, dict):
            raise ValueError("Parsed response is not a JSON object.")

        normalized_record = self._normalize(parsed)
        return [normalized_record]


    def _parse_response(self, text: str) -> Dict[str, Any]:
        """
        Try to load the response text as JSON. If that fails, extract a markdown
        ```json ...``` block and parse that. Raises ValueError if no valid JSON found.
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            match = re.search(pattern, text, re.DOTALL)
            if not match:
                raise ValueError("Response does not contain valid JSON or a JSON markdown block.")
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse JSON from markdown block: {e}")

    def _normalize(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Given one raw record from the parsed LLM output, ensure every key maps to:
          - "<field>": the 'value' or "Not specified"
          - "<field>_justification": the 'justification' or "Not found"
        """
        normalized: Dict[str, Any] = {}
        for field, info in record.items():
            if isinstance(info, dict):
                value = info.get("value", "Not specified")
                just = info.get("justification", "Not found")
            elif field in ("country", "country_alpha_3_code"):
                value = str(info) if info is not None else "Not specified"
                just = ""
            else:
                raise ValueError(f"Field '{field}' has unexpected structure: {info!r}")

            normalized[field] = value or "Not specified"
            normalized[f"{field}_justification"] = just

        return normalized
