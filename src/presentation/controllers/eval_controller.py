from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from enum import Enum
from typing import Optional
import tempfile
import logging
from pathlib import Path

from application.use_cases.eval.prep_sti_evaluator import PrepSTIEvaluator
from application.interfaces.eval import EvalResult
from config import Settings

settings = Settings()
logger = logging.getLogger(__name__)

router = APIRouter()

class EvalContext(str, Enum):
    """Supported evaluation contexts."""
    STI_90_PREP = "90_prep_sti"

@router.post("/", status_code=200)
async def evaluate_csv(
    file: UploadFile = File(..., description="CSV file to evaluate"),
    context: EvalContext = Form(..., description="Evaluation context")
):
    """
    Evaluate an uploaded CSV file against a reference dataset.

    Args:
        file: CSV file to evaluate
        context: Evaluation context (currently only 90_prep_sti supported)

    Returns:
        JSON response with evaluation metrics and file paths
    """
    model_name = settings.MODEL_NAME
    logger.info(f"Evaluation request received for context: {context.value}, model: {model_name}")

    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    # Create evaluator
    evaluator = PrepSTIEvaluator()

    # Validate context
    if context.value not in evaluator.get_supported_contexts():
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported context: {context.value}. Supported: {evaluator.get_supported_contexts()}"
        )

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        temp_path = Path(tmp_file.name)

    try:
        # Perform evaluation
        result: EvalResult = evaluator.evaluate(
            input_csv_path=temp_path,
            context=context.value,
            model_name=model_name
        )

        # Prepare response
        response_data = {
            "status": "success",
            "context": context.value,
            "model_name": model_name,
            "metrics": {
                "accuracy": result.accuracy,
                "precision": result.precision,
                "recall": result.recall,
                "f1_score": result.f1,
                "total_matches": result.total_matches,
                "total_cells": result.total_cells,
                "per_column_accuracy": result.per_column_accuracy
            },
            "dataset_info": {
                "common_countries": result.common_countries,
                "ref_countries": result.ref_countries,
                "generated_countries": result.generated_countries,
                "missing_in_generated": result.missing_in_generated,
                "extra_in_generated": result.extra_in_generated
            },
            "output_files": {
                "output_directory": str(result.output_dir),
                "highlighted_errors_csv": str(result.highlighted_errors_path),
                "metrics_txt": str(result.metrics_txt_path)
            }
        }

        logger.info(f"Evaluation completed successfully. Accuracy: {result.accuracy:.2%}")
        return response_data

    except ValueError as e:
        logger.error(f"Validation error during evaluation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        logger.error(f"File not found during evaluation: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during evaluation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
    finally:
        # Cleanup temporary file
        try:
            temp_path.unlink()
        except Exception:
            logger.warning(f"Failed to cleanup temporary file: {temp_path}")


@router.get("/contexts", status_code=200)
def get_supported_contexts():
    """
    Get list of supported evaluation contexts.

    Returns:
        List of supported evaluation contexts
    """
    evaluator = PrepSTIEvaluator()
    return {
        "supported_contexts": evaluator.get_supported_contexts(),
        "descriptions": {
            "90_prep_sti": "Evaluation for 90 countries STI/PrEP policy analysis"
        }
    }
