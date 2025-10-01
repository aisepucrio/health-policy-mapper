import logging
import pandas as pd
from pathlib import Path
from typing import List, Callable, Optional, Dict, Any

from application.interfaces.llm_client import BaseLLMClient
from application.utils.prompt_builder import build_prompt
from domain.value_objects.column import Column

# Set up logger
logger = logging.getLogger(__name__)

class LLMProcessor:
    """
    Use case for processing documents with an LLM client.
    """
    def __init__(self, llm_client: BaseLLMClient):
        self.client = llm_client

    async def run(
        self,
        documents: List[Path],
        context: str,
        columns: List[Column],
        progress_callback: Optional[Callable[[int], None]] = None,
        row_callback: Optional[Callable[[Dict[str, Any], int, int], None]] = None,
    ) -> pd.DataFrame:
        """
        Process a list of documents with the LLM client in a given context and return results as a DataFrame.

        :param documents: List of document paths to process.
        :param context: Context for processing the documents.
        :param columns: Names of the columns for the structured output.
        :param progress_callback: Optional callback to report progress of the job.
        :param row_callback: Optional callback for each processed row.
        :return: DataFrame containing the processed results.
        """
        logger.info(f"LLM processor starting with {len(documents)} documents")
        records: List[Dict[str, Any]] = []

        total = len(documents)
        for i, document in enumerate(documents, 1):
                logger.info(f"Processing document {i}/{len(documents)}: {document.name}")

                if not document.exists():
                    logger.error(f"Document {document} does not exist")
                    raise FileNotFoundError(f"Document {document} does not exist.")

                file_name = document.name
                prompt = build_prompt(context, columns, file_name)

                try:
                    results = await self.client.process(
                        document_path=document,
                        prompt=prompt,
                    )

                    if not results:
                        logger.error(f"No results returned for document {document}")
                        raise ValueError(f"No results returned for document {document}.")

                    item = results[0]
                    record = {"source_file": file_name, **item, "error": ""}
                    records.append(record)
                    logger.info(f"Successfully processed document {i}/{len(documents)}: {document.name}")

                    # tracks the progress
                    if progress_callback:
                        progress_callback(i)
                    # incremental row callback
                    if row_callback:
                        try:
                            row_callback(record, i, total)
                        except Exception as cb_err:
                            logger.warning(f"row_callback failed for document {i}: {cb_err}")

                except Exception as e:
                    # Store error message
                    err_msg = str(e)
                    logger.error(f"Failed to process document {i}/{len(documents)} ({document.name}): {err_msg}")
                    record = {"source_file": file_name, "error": err_msg[:1000]}
                    for col in columns:
                        record.setdefault(col.name, '')
                        record.setdefault(f"{col.name}_justification", '')
                    records.append(record)

                    # Call row_callback for error records too
                    if row_callback:
                        try:
                            row_callback(record, i, len(documents))
                        except Exception as cb_err:
                            logger.warning(f"row_callback failed for error record {i}: {cb_err}")

        df = pd.DataFrame(records)
        logger.info(f"LLM processing completed. Generated DataFrame with {len(df)} records and {len(df.columns)} columns")
        return df
