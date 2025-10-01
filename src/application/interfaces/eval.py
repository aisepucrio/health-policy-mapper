from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd
from typing import Dict, Any, List, Optional


class EvalResult:
    """Result object containing evaluation metrics and file paths."""

    def __init__(
        self,
        accuracy: float,
        precision: float,
        recall: float,
        f1: float,
        total_matches: int,
        total_cells: int,
        common_countries: int,
        ref_countries: int,
        generated_countries: int,
        missing_in_generated: List[str],
        extra_in_generated: List[str],
        per_column_accuracy: Dict[str, float],
        output_dir: Path,
        highlighted_errors_path: Path,
        detailed_comparison_path: Optional[Path],
        metrics_txt_path: Path
    ):
        self.accuracy = accuracy
        self.precision = precision
        self.recall = recall
        self.f1 = f1
        self.total_matches = total_matches
        self.total_cells = total_cells
        self.common_countries = common_countries
        self.ref_countries = ref_countries
        self.generated_countries = generated_countries
        self.missing_in_generated = missing_in_generated
        self.extra_in_generated = extra_in_generated
        self.per_column_accuracy = per_column_accuracy
        self.output_dir = output_dir
        self.highlighted_errors_path = highlighted_errors_path
        self.detailed_comparison_path = detailed_comparison_path
        self.metrics_txt_path = metrics_txt_path


class BaseEvaluator(ABC):
    """Abstract base class for evaluation implementations."""

    @abstractmethod
    def evaluate(
        self,
        input_csv_path: Path,
        context: str,
        model_name: str = "unknown"
    ) -> EvalResult:
        """
        Evaluate input CSV against reference CSV for given context.

        Args:
            input_csv_path: Path to the input CSV file to evaluate
            context: Context name (e.g., "90_prep_sti")
            model_name: Name of the model being evaluated

        Returns:
            EvalResult containing metrics and output file paths

        Raises:
            ValueError: If context is not supported
            FileNotFoundError: If reference CSV not found
        """
        pass

    @abstractmethod
    def get_supported_contexts(self) -> List[str]:
        """Return list of supported evaluation contexts."""
        pass
