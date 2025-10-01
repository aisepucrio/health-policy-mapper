import logging
import pandas as pd
from typing import List, Dict, Any, cast

# Set up logger
logger = logging.getLogger(__name__)

class Aggregator:
    """
    Aggregates results from multiple documents in a single DataFrame, grouping by 'country_alpha_3_code'
    Applying the binary rule: if ANY == yes -> yes, else preserve original values.
    Concatenates justifications for "yes" answers.
    """

    def __init__(self):
        self.grouping_key = "country_alpha_3_code"

    def aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info(f"Aggregator starting with {len(df)} raw records")

        self._validate_input(df)

        # Expand rows that contain multiple countries in the same line
        df = self._safe_explode_countries(df)

        unique_countries = df[self.grouping_key].nunique()
        logger.info(f"Found {unique_countries} unique countries to aggregate")

        # Separate column types
        regular_columns, justification_columns = self._categorize_columns(df)


        # Perform initial aggregation on regular columns
        result = self._aggregate_regular_columns(df, regular_columns)
        logger.info(f"Initial aggregation completed: {len(result)} countries aggregated")

        # Add justification columns
        result = self._add_justification_columns(df, result, regular_columns)

        # Reorder columns for better readability
        result = self._reorder_columns(result, regular_columns)

        logger.info(f"Aggregation completed successfully: {len(result)} final records with {len(result.columns)} columns")
        return result

    def _safe_explode_countries(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Safely explode rows where country_alpha_3_code and country contain comma-separated
        lists, ensuring both columns have matching lengths before exploding.
        """
        codes_col = self.grouping_key  # "country_alpha_3_code"
        name_col = "country"

        if codes_col not in df.columns or name_col not in df.columns:
            return df

        work = df.copy()
        # Split on commas with optional spaces
        work[codes_col] = work[codes_col].astype(str).str.split(r",\s*")
        work[name_col] = work[name_col].astype(str).str.split(r",\s*")

        # Keep only rows where both lists have the same length
        lengths_match = work[codes_col].map(lambda x: len(x) if isinstance(x, list) else 1) == \
                        work[name_col].map(lambda x: len(x) if isinstance(x, list) else 1)
        work = work[lengths_match].copy()

        # Explode both columns together
        work = work.explode([codes_col, name_col])

        # Trim whitespace after explosion
        work[codes_col] = work[codes_col].astype(str).str.strip()
        work[name_col] = work[name_col].astype(str).str.strip()
        return work

    def _validate_input(self, df: pd.DataFrame) -> None:
        """Validate that required columns exist in the DataFrame"""
        if self.grouping_key not in df.columns:
            available_columns = list(df.columns)
            logger.error(f"Required column '{self.grouping_key}' not found. Available: {available_columns}")
            raise KeyError(f"Required column '{self.grouping_key}' not found in DataFrame")

    def _categorize_columns(self, df: pd.DataFrame) -> tuple[List[str], List[str]]:
        """Separate regular columns from justification columns"""
        all_columns = [col for col in df.columns if col != self.grouping_key]

        justification_columns = [col for col in all_columns if col.endswith('_justification')]
        regular_columns = [
            col for col in all_columns
            if not col.endswith('_justification') and col not in ("source_file", "error")
        ]

        return regular_columns, justification_columns

    def _aggregate_regular_columns(self, df: pd.DataFrame, regular_columns: List[str]) -> pd.DataFrame:
        """Aggregate regular columns using appropriate functions"""
        agg_dict = {}

        for col in regular_columns:
            if col == "country":
                agg_dict[col] = self._get_first_value
            else:
                agg_dict[col] = self._apply_yes_wins_rule

        return df.groupby(self.grouping_key, as_index=False).agg(agg_dict)

    def _add_justification_columns(self, original_df: pd.DataFrame, result: pd.DataFrame, regular_columns: List[str]) -> pd.DataFrame:
        """Add justification columns to the aggregated result"""
        policy_columns = [col for col in regular_columns if col != "country"]

        # Initialize all justification columns
        for col in policy_columns:
            just_col = f"{col}_justification"
            result[just_col] = ""

        # Populate justification columns
        for _, row in result.iterrows():
            country_code = row[self.grouping_key]

            for col in policy_columns:
                just_col = f"{col}_justification"
                # Compute selection according to rules:
                # - If any 'yes' for this country/column: include justifications from 'yes' rows only
                # - Else, if all rows are 'no' or 'not specified' (treat 'not specified' as 'no'):
                #   include justifications from rows with 'no' or 'not specified'
                # - Else: leave justification empty

                country_mask = (original_df[self.grouping_key] == country_code)
                series_raw = cast(pd.Series, original_df.loc[country_mask, col])
                series_vals = series_raw.astype(str).str.lower().str.strip()
                any_yes = series_vals.eq('yes').any()
                allowed_no_like = {'no', 'not specified', '' , 'nan'}
                all_no_or_not_spec = series_vals.isin(allowed_no_like).all() and (not any_yes)

                include_mask = None
                if any_yes:
                    include_mask = series_vals.eq('yes')
                elif all_no_or_not_spec:
                    include_mask = series_vals.isin({'no', 'not specified'})

                if include_mask is not None:
                    matching_docs = original_df.loc[country_mask & include_mask]

                    if not matching_docs.empty and (f"{col}_justification" in original_df.columns):
                        formatted_justifications = []
                        jcol = f"{col}_justification"
                        for _, src_row in matching_docs.iterrows():
                            justification = str(src_row.get(jcol, "")) if pd.notna(src_row.get(jcol)) else ""
                            source_file = str(src_row.get("source_file", "Unknown_File"))
                            if self._is_valid_justification(justification):
                                formatted_justifications.append(f"{source_file}: {justification}")

                        unique_justifications = sorted(list(set(formatted_justifications)))
                        justification_text = " | ".join(unique_justifications)
                    else:
                        justification_text = ""

                    result.loc[result[self.grouping_key] == country_code, just_col] = (
                        justification_text if justification_text else "Justification not provided"
                    )

        return result

    def _get_justifications_for_policy(self, df: pd.DataFrame, policy_col: str, country_code: str) -> str:
        """Get concatenated justifications for a specific policy and country where policy is 'yes'"""
        just_col = f"{policy_col}_justification"

        if just_col not in df.columns:
            return ""

        # Consider only documents for this country where the policy value is exactly 'yes'
        matching_docs = df[
            (df[self.grouping_key] == country_code) &
            (df[policy_col].astype(str).str.lower().str.strip() == 'yes')
        ]

        if matching_docs.empty:
            return ""

        # Extract and format justifications
        formatted_justifications = []
        for _, row in matching_docs.iterrows():
            justification = str(row[just_col]) if pd.notna(row[just_col]) else ""
            source_file = str(row.get("source_file", "Unknown_File"))

            if self._is_valid_justification(justification):
                formatted_justifications.append(f"{source_file}: {justification}")

        # Remove duplicates and join
        unique_justifications = sorted(list(set(formatted_justifications)))
        return " | ".join(unique_justifications)

    def _reorder_columns(self, result: pd.DataFrame, regular_columns: List[str]) -> pd.DataFrame:
        """Reorder columns for better readability"""
        final_column_order = []

        # Add country information first
        if "country" in result.columns:
            final_column_order.append("country")
        final_column_order.append(self.grouping_key)

        # Add policy columns paired with their justifications
        policy_columns = [col for col in regular_columns if col != "country"]
        for col in policy_columns:
            final_column_order.append(col)
            just_col = f"{col}_justification"
            if just_col in result.columns:
                final_column_order.append(just_col)

        # Filter to ensure all columns exist and reorder
        existing_columns = [col for col in final_column_order if col in result.columns]
        return result[existing_columns]

    @staticmethod
    def _get_first_value(series: pd.Series) -> str:
        """Get the first non-null value from a series"""
        non_null_series = series.dropna()
        return str(non_null_series.iloc[0]) if len(non_null_series) > 0 else ""

    @staticmethod
    def _apply_yes_wins_rule(series: pd.Series) -> str:
        """Apply the 'yes wins' aggregation rule"""
        non_null_series = series.dropna()

        if len(non_null_series) == 0:
            return "Not specified"

        # Check if any value is "yes" (case insensitive)
        if non_null_series.astype(str).str.lower().eq('yes').any():
            return "yes"

        # Otherwise return the first non-null value
        return str(non_null_series.iloc[0])

    @staticmethod
    def _is_yes_value(value: str) -> bool:
        """Check if a value represents 'yes'"""
        return str(value).lower() == "yes"

    @staticmethod
    def _is_valid_justification(justification: str) -> bool:
        """Check if a justification text is valid and not empty"""
        if not justification.strip():
            return False

        invalid_values = {'not specified', 'not found', 'nan', 'none', ''}
        return justification.lower().strip() not in invalid_values


    @staticmethod
    def _should_include_justification(value: str) -> bool:
        """Include justification only when aggregated value is 'yes'"""
        return str(value).lower().strip() == 'yes'
