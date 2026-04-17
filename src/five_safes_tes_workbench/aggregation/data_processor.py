import numpy as np
from typing import List, Dict, Any, Union


class DataProcessor:
    """
    Handles data processing, aggregation, and file operations for federated analysis.
    """

    def __init__(self):
        """Initialize the data processor."""
        pass

    def convert_csv_to_dict(
        self, csv_inputs: List[str], analysis_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert CSV strings to dict format matching the analysis return_format.

        Args:
            csv_inputs: List of CSV strings from multiple TREs
            analysis_config: Analysis configuration with return_format

        Returns:
            Dict in the format expected by the analysis (dict of lists for single-row,
            or dict with row_data_key for row-based analyses)
        """
        return_format_keys = list(analysis_config["return_format"].keys())
        is_row_based = len(return_format_keys) == 1

        if is_row_based:
            # For row-based analyses: convert CSV to list of dicts, then wrap in return_format key
            # Use combine_contingency_tables to parse and aggregate CSV
            combined_table = combine_contingency_tables(csv_inputs)
            # Convert back to list of dicts format
            list_of_dicts = []
            header = combined_table.get("header", "").split(",")
            for key, value in combined_table.items():
                if key != "header":
                    row_dict = {}
                    parts = key.split(",")
                    for i, part in enumerate(parts):
                        if i < len(header) - 1:  # Exclude 'n' column
                            row_dict[header[i]] = part
                    row_dict["n"] = value
                    list_of_dicts.append(row_dict)
            row_data_key = return_format_keys[0]
            return {row_data_key: list_of_dicts}
        else:
            # For single-row analyses: convert CSV to dict of lists
            # CSV format: "n,total\n65,117.0" -> {"n": [65], "total": [117.0]}
            result_dict = {}
            for csv_str in csv_inputs:
                lines = csv_str.strip().split("\n")
                if len(lines) < 2:
                    continue
                header = lines[0].split(",")
                values = lines[1].split(",")
                for i, key in enumerate(header):
                    if key not in result_dict:
                        result_dict[key] = []
                    try:
                        result_dict[key].append(float(values[i]))
                    except (ValueError, IndexError):
                        continue
            return result_dict

    def aggregate_data(
        self,
        inputs: Union[List[str], Dict[str, List[float]], List[Dict[str, Any]]],
        analysis_type: str,
    ) -> Union[np.ndarray, List[np.ndarray]]:
        """
        Aggregate data based on analysis type.

        Args:
            inputs: Either List[str] (CSV strings), Dict[str, List[float]] (pre-aggregated JSON dict),
                    or List[Dict[str, Any]] (list of JSON results from multiple TREs)
            analysis_type (str): Type of analysis to perform

        Returns:
            Union[np.ndarray, List[np.ndarray]]: Aggregated data
        """
        # TODO: lazy import to avoid circular dependency with statistical_analyzer;
        # resolve by extracting shared config/utilities in a later refactor.
        from five_safes_tes_analytics.aggregation.statistical_analyzer import StatisticalAnalyzer
    
        analyzer = StatisticalAnalyzer()
        analysis_config = analyzer.get_analysis_config(analysis_type)

        # Convert CSV strings to dict format if needed (before other processing)
        if isinstance(inputs, list) and inputs and isinstance(inputs[0], str):
            # CSV format detected - convert to dict format matching return_format
            inputs = self.convert_csv_to_dict(inputs, analysis_config)

        # Check if inputs is a list of results from multiple TREs
        if isinstance(inputs, list) and inputs:
            # Check if first element is a dict (for mean, variance, PMCC - single row results)
            if isinstance(inputs[0], dict):
                # Handle list of dicts: [{"n": 65, "total": 117.0}, {"n": 42, "total": 89.0}, ...]
                # Convert to dict of lists: {"n": [65, 42, ...], "total": [117.0, 89.0, ...]}
                combined = {}
                for item in inputs:
                    if isinstance(item, dict):
                        for key, value in item.items():
                            if key not in combined:
                                combined[key] = []
                            combined[key].append(value)
                inputs = combined
            # Check if first element is a list (for row-based analyses like contingency tables)
            elif isinstance(inputs[0], list):
                # Handle list of lists: [[{"category": "A", "n": 10}, ...], [{"category": "B", "n": 20}, ...]]
                # Flatten all rows from all TREs into a single list
                # The statistical analyzer will handle the aggregation
                flattened = []
                for table_list in inputs:
                    if isinstance(table_list, list):
                        flattened.extend(table_list)

                # Use the key from return_format instead of hardcoding "contingency_table"
                # This makes it general for any row-based analysis
                row_data_key = list(analysis_config["return_format"].keys())[0]
                inputs = {row_data_key: flattened}

        # All paths now result in dict format - just return it
        # CSV conversion would happen earlier if needed (convert CSV to dict first)
        return inputs


def combine_contingency_tables(
    contingency_tables: List[str] | Dict[str, Any],
) -> Dict[str, Any]:
    """
    Combine multiple contingency tables.

    Args:
        contingency_tables (List[str]): List of CSV strings containing contingency tables

    Returns:
        Dict[str, Any]: Combined contingency table as dictionary
    """

    if isinstance(contingency_tables, dict):
        ### it's already a dict of lists of the data, so we just need to sum the values in each list
        for key, value in contingency_tables.items():
            contingency_tables[key] = sum(value)
        return contingency_tables

    labels = {}

    for table in contingency_tables:
        rows = [row.strip() for row in table.split("\n") if row.strip()]
        if not rows:  # Skip empty tables
            continue

        labels["header"] = rows[0]  # Column order is guaranteed to be the same

        data_rows = rows[1:]
        for row in data_rows:
            try:
                parts = row.split(",")
                if len(parts) < 2:  # Skip rows without enough parts
                    continue
                count = int(parts[-1])  # Get count from last column
                row_without_count = ",".join(
                    parts[:-1]
                )  # Get rest of row without count
                if row_without_count in labels:
                    labels[row_without_count] += count
                else:
                    labels[row_without_count] = count
            except (ValueError, IndexError) as e:
                print(f"Warning: Skipping malformed row: {row}")
                continue

    return labels


def dict_to_array(contingency_dict: Dict[str, Any]) -> np.ndarray:
    """
    Convert contingency table dictionary to numpy array.

    Args:
        contingency_dict (Dict[str, Any]): Contingency table as dictionary

    Returns:
        np.ndarray: Contingency table as 2D array
    """
    # Get unique values for each dimension from the keys
    keys = [k for k in contingency_dict.keys() if k != "header"]
    first_values = set(k.split(",")[0] for k in keys)
    second_values = set(k.split(",")[1] for k in keys)

    # Create empty array
    row_labels = list(first_values)
    col_labels = list(second_values)
    result = np.zeros((len(row_labels), len(col_labels)))

    labels = {
        "row_labels": row_labels,
        "col_labels": col_labels,
        "header": contingency_dict.get("header", ""),
    }

    # Fill array using the keys to determine position
    for key, value in contingency_dict.items():
        if key != "header":
            first_part, second_part = key.split(",")
            row_idx = row_labels.index(first_part)  # First part as rows
            col_idx = col_labels.index(second_part)  # Second part as columns
            result[row_idx, col_idx] = value

    return result, labels
