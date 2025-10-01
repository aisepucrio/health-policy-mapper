import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from application.interfaces.eval import BaseEvaluator, EvalResult

logger = logging.getLogger(__name__)


class PrepSTIEvaluator(BaseEvaluator):
    """Evaluator for PrEP/STI policy evaluation contexts."""

    # Global constant for supported contexts
    SUPPORTED_CONTEXTS = ["90_prep_sti"]

    # Context configuration
    CONTEXT_CONFIG = {
        "90_prep_sti": {
            "reference_file": "reference_90_prep_sti_cleaned.csv",
            "key_column": "country_alpha_3_code",
            "columns_to_compare": [
                'partner_management',
                'hbv_screening_for_hbsag',
                'vaccination_for_hbv',
                'vaccination_for_hpv',
                'syphilis_screening',
                'ng_screening',
                'ct_screening'
            ]
        }
    }

    def __init__(self, reference_data_dir: Optional[Path] = None):
        """Initialize evaluator with reference data directory."""
        if reference_data_dir is None:
            reference_data_dir = Path("data/reference")
        self.reference_data_dir = reference_data_dir

    def get_supported_contexts(self) -> List[str]:
        """Return list of supported evaluation contexts."""
        return self.SUPPORTED_CONTEXTS.copy()

    def evaluate(
        self,
        input_csv_path: Path,
        context: str,
        model_name: str = "unknown"
    ) -> EvalResult:
        """Evaluate input CSV against reference CSV for given context."""

        # Validate context
        if context not in self.SUPPORTED_CONTEXTS:
            raise ValueError(f"Unsupported context: {context}. Supported: {self.SUPPORTED_CONTEXTS}")

        # Get context configuration
        config = self.CONTEXT_CONFIG[context]
        reference_file = self.reference_data_dir / config["reference_file"]

        if not reference_file.exists():
            raise FileNotFoundError(f"Reference file not found: {reference_file}")

        # Create output directory structure
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = f"{model_name}_{timestamp}"
        output_dir = Path("data/output") / context / folder_name
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Starting evaluation for context {context}, model {model_name}")

        # Load datasets
        df_ref_original = self._load_dataset(reference_file)
        df_generated_original = self._load_dataset(input_csv_path)

        # Copy input CSV to output directory with original name
        input_filename = input_csv_path.name
        input_copy_path = output_dir / input_filename
        import shutil
        shutil.copy2(input_csv_path, input_copy_path)

        # Standardize and preprocess
        df_ref = self._preprocess_dataframe(df_ref_original, config)
        df_generated = self._preprocess_dataframe(df_generated_original, config)

        # Find common countries
        common_countries_info = self._find_common_countries(
            df_ref, df_generated, config["key_column"]
        )

        # Filter to common countries
        df_ref_filtered = df_ref[df_ref[config["key_column"]].isin(common_countries_info["common"])].copy()
        df_generated_filtered = df_generated[df_generated[config["key_column"]].isin(common_countries_info["common"])].copy()

        # Perform evaluation
        merged = self._match_rows_and_compare(
            df_ref_filtered,
            df_generated_filtered,
            [config["key_column"]],
            config["columns_to_compare"]
        )

        # Compute metrics
        metrics = self._compute_all_metrics(merged, config["columns_to_compare"])

        # Generate output files (without detailed comparison)
        output_files = self._generate_output_files(
            merged, config, output_dir, context, model_name, timestamp, common_countries_info
        )

        # Create and return result (no detailed_comparison_path)
        result = EvalResult(
            accuracy=float(metrics["accuracy"]),
            precision=float(metrics["precision"]),
            recall=float(metrics["recall"]),
            f1=float(metrics["f1"]),
            total_matches=int(metrics["total_matches"]),
            total_cells=int(metrics["total_cells"]),
            common_countries=int(len(common_countries_info["common"])),
            ref_countries=int(len(common_countries_info["ref"])),
            generated_countries=int(len(common_countries_info["generated"])),
            missing_in_generated=sorted(list(common_countries_info["missing_in_generated"])),
            extra_in_generated=sorted(list(common_countries_info["extra_in_generated"])),
            per_column_accuracy={k: float(v) for k, v in metrics["per_column_accuracy"].items()},
            output_dir=output_dir,
            highlighted_errors_path=output_files["highlighted_errors"],
            detailed_comparison_path=output_files["highlighted_errors"],  # Use same file for both
            metrics_txt_path=output_files["metrics_txt"]
        )

        logger.info(f"Evaluation completed. Accuracy: {metrics['accuracy']:.2%}")
        return result

    def _load_dataset(self, path: Path) -> pd.DataFrame:
        """Load CSV file into pandas DataFrame."""
        return pd.read_csv(path)

    def _preprocess_dataframe(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Standardize and preprocess dataframe."""
        df = df.copy()

        # Standardize column names
        df.columns = [col.strip().lower().replace(' ', '_').replace('-', '_') for col in df.columns]

        # Ensure key column exists
        key_column = config["key_column"]
        if key_column not in df.columns:
            raise ValueError(f"Key column '{key_column}' not found in dataset")

        # Convert key column to string
        df[key_column] = df[key_column].astype(str).str.strip()

        # Normalize yes/no values
        for col in df.columns:
            if col in [key_column, 'country'] or col.endswith('_justification'):
                continue
            df[col] = df[col].apply(lambda v: v if pd.isna(v) else str(v).strip().lower())
            df[col] = df[col].replace({'not specified': 'no'})

        return df

    def _find_common_countries(self, df_ref: pd.DataFrame, df_generated: pd.DataFrame, key_column: str) -> Dict[str, Any]:
        """Find common countries between reference and generated datasets."""
        ref_countries = set(df_ref[key_column].unique())
        generated_countries = set(df_generated[key_column].unique())
        common_countries = ref_countries.intersection(generated_countries)

        return {
            "ref": ref_countries,
            "generated": generated_countries,
            "common": common_countries,
            "missing_in_generated": ref_countries - common_countries,
            "extra_in_generated": generated_countries - common_countries
        }

    def _match_rows_and_compare(
        self,
        df_ref: pd.DataFrame,
        df_generated: pd.DataFrame,
        join_on: List[str],
        columns_to_compare: List[str]
    ) -> pd.DataFrame:
        """Match rows and compare values between reference and generated data."""

        # Merge datasets
        merged = pd.merge(
            df_ref,
            df_generated,
            how="left",
            on=join_on,
            suffixes=("_ref", "_generated"),
            indicator=True
        )

        # Create match columns
        for col in columns_to_compare:
            col_ref = col + "_ref"
            col_generated = col + "_generated"
            check_col = col + "_match"

            # Skip if columns don't exist in the merged data
            if col_ref not in merged.columns or col_generated not in merged.columns:
                continue

            def compare_func(row):
                val_ref = row[col_ref]
                val_generated = row[col_generated]

                if pd.isna(val_generated):
                    return 0

                # String comparison (case insensitive)
                if isinstance(val_ref, str) and isinstance(val_generated, str):
                    return 1 if val_ref.strip().lower() == val_generated.strip().lower() else 0

                # Fallback string compare
                return 1 if str(val_ref).strip().lower() == str(val_generated).strip().lower() else 0

            merged[check_col] = merged.apply(compare_func, axis=1)

        return merged

    def _compute_all_metrics(self, merged_df: pd.DataFrame, columns_to_compare: List[str]) -> Dict[str, Any]:
        """Compute all evaluation metrics."""

        # Overall accuracy - only include columns that exist
        match_cols = [c + "_match" for c in columns_to_compare if c + "_match" in merged_df.columns]
        total_matches = int(merged_df[match_cols].sum().sum()) if match_cols else 0
        total_cells = int(len(merged_df) * len(match_cols)) if match_cols else 0
        accuracy = float(total_matches / total_cells) if total_cells > 0 else 0.0

        # Per-column accuracy
        per_column_accuracy = {}
        for c in columns_to_compare:
            match_col = c + "_match"
            if match_col in merged_df.columns:
                per_column_accuracy[c] = float(merged_df[match_col].mean())

        # Precision, recall, F1
        tp = fp = fn = 0

        for col in columns_to_compare:
            col_ref = col + "_ref"
            col_generated = col + "_generated"

            # Skip if columns don't exist
            if col_ref not in merged_df.columns or col_generated not in merged_df.columns:
                continue

            ref_series = merged_df[col_ref].astype(str).str.strip().str.lower()
            gen_series = merged_df[col_generated].astype(str).str.strip().str.lower()

            tp += int(((ref_series == "yes") & (gen_series == "yes")).sum())
            fp += int(((ref_series == "no") & (gen_series == "yes")).sum())
            fn += int(((ref_series == "yes") & (gen_series == "no")).sum())

        precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = float(2 * (precision * recall) / (precision + recall)) if (precision + recall) > 0 else 0.0

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "total_matches": total_matches,
            "total_cells": total_cells,
            "per_column_accuracy": per_column_accuracy
        }

    def _generate_output_files(
        self,
        merged: pd.DataFrame,
        config: Dict[str, Any],
        output_dir: Path,
        context: str,
        model_name: str,
        timestamp: str,
        common_countries_info: Dict[str, Any]
    ) -> Dict[str, Path]:
        """Generate output files (only highlighted errors and metrics, no detailed comparison)."""

        key_column = config["key_column"]
        columns_to_compare = config["columns_to_compare"]

        # Highlighted errors report
        df_report = pd.DataFrame({key_column: merged[key_column]})

        # Add country column if available
        if 'country_generated' in merged.columns:
            df_report['country'] = merged['country_generated']
        elif 'country' in merged.columns:
            df_report['country'] = merged['country']

        # Add policy columns with error highlighting
        for col in columns_to_compare:
            col_ref = col + "_ref"
            col_generated = col + "_generated"
            col_match = col + "_match"

            # Skip if columns don't exist
            if col_ref not in merged.columns or col_generated not in merged.columns or col_match not in merged.columns:
                continue

            # Create policy values column with error highlighting using vectorized operations
            match_series = merged[col_match]
            generated_series = merged[col_generated].astype(str)
            ref_series = merged[col_ref].astype(str)

            # Use where to create error highlighting
            policy_values = generated_series.where(
                match_series == 1,
                "ERR: " + generated_series + " (REF: " + ref_series + ")"
            )
            df_report[col] = policy_values

            # Add justification column
            just_col_base = f"{col}_justification"
            if f"{just_col_base}_generated" in merged.columns:
                df_report[just_col_base] = merged[f"{just_col_base}_generated"].fillna('')
            elif just_col_base in merged.columns:
                df_report[just_col_base] = merged[just_col_base].fillna('')
            else:
                df_report[just_col_base] = "Justification N/A"

        highlighted_path = output_dir / f"highlighted_errors.csv"
        df_report.to_csv(highlighted_path, index=False)

        # Metrics text file
        metrics = self._compute_all_metrics(merged, columns_to_compare)
        metrics_path = output_dir / f"evaluation_metrics.txt"

        with open(metrics_path, 'w') as f:
            f.write(f"Evaluation Results for {context}\n")
            f.write(f"Model: {model_name}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write("=" * 50 + "\n\n")

            f.write("Dataset Overview:\n")
            f.write(f"  Reference countries: {len(common_countries_info['ref'])}\n")
            f.write(f"  Generated countries: {len(common_countries_info['generated'])}\n")
            f.write(f"  Common countries: {len(common_countries_info['common'])}\n")

            # Show missing and extra countries if they exist
            if common_countries_info['missing_in_generated']:
                f.write(f"  Missing in generated: {', '.join(sorted(common_countries_info['missing_in_generated']))}\n")
            if common_countries_info['extra_in_generated']:
                f.write(f"  Extra in generated: {', '.join(sorted(common_countries_info['extra_in_generated']))}\n")
            f.write("\n")

            f.write("Overall Metrics:\n")
            f.write(f"  Accuracy: {metrics['accuracy']:.2%} ({metrics['total_matches']}/{metrics['total_cells']})\n")
            f.write(f"  Precision: {metrics['precision']:.2%}\n")
            f.write(f"  Recall: {metrics['recall']:.2%}\n")
            f.write(f"  F1 Score: {metrics['f1']:.2%}\n\n")

            f.write("Per-Column Accuracy:\n")
            for col, acc in metrics['per_column_accuracy'].items():
                f.write(f"  {col}: {acc:.2%}\n")

        return {
            "highlighted_errors": highlighted_path,
            "metrics_txt": metrics_path
        }
