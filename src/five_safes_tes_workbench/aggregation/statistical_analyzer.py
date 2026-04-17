"""
These classes are for the aggregation of data, and the analysis of data, i.e., to be run on the aggregator, NOT the client.
"""

import numpy as np
from typing import Dict, Any, Union, List
from abc import ABC, abstractmethod
from tdigest import TDigest  # type: ignore
import json

from five_safes_tes_workbench.aggregation.data_processor import (
    dict_to_array,
    combine_contingency_tables,
)


class AnalysisBase(ABC):
    """Abstract base class for statistical analysis."""

    @property
    @abstractmethod
    def return_format(self) -> dict:
        """Return format specification."""
        pass

    @abstractmethod
    def aggregate_data(
        self, input_data: Union[np.ndarray, List[np.ndarray], Dict[str, List[float]]]
    ) -> Union[np.ndarray, Dict[str, List[float]]]:
        """Aggregate data for analysis."""
        pass

    @abstractmethod
    def analyze(
        self, aggregated_data: Union[np.ndarray, Dict[str, List[float]]]
    ) -> Union[float, Dict[str, Any]]:
        """Analyze aggregated data."""
        pass


class MeanAnalysis(AnalysisBase):
    """Analysis class for calculating mean values."""

    def __init__(self):
        self.aggregated_data = {}

    @property
    def return_format(self) -> dict:
        return {"n": None, "total": None}

    def aggregate_data(
        self, input_data: Union[np.ndarray, List[np.ndarray], Dict[str, List[float]]]
    ) -> Union[np.ndarray, Dict[str, List[float]]]:
        """Aggregate data for mean calculation."""
        if isinstance(input_data, dict):
            n = np.sum(np.array(input_data["n"]))
            total = np.sum(np.array(input_data["total"]))

        elif isinstance(input_data, list) or isinstance(input_data, np.ndarray):
            n, total = np.sum(np.vstack(input_data), axis=0)
        self.aggregated_data.update({"n": n, "total": total})
        return self.aggregated_data

    def analyze(self) -> float:
        """Calculate mean from aggregated values."""

        return self.aggregated_data["total"] / self.aggregated_data["n"]


class VarianceAnalysis(AnalysisBase):
    """Analysis class for calculating variance."""

    def __init__(self):
        self.aggregated_data = {}

    @property
    def return_format(self) -> dict:
        return {"n": None, "sum_x2": None, "total": None}

    def aggregate_data(
        self, input_data: Union[np.ndarray, List[np.ndarray], Dict[str, List[float]]]
    ) -> Union[np.ndarray, Dict[str, List[float]]]:
        """Aggregate data for variance calculation."""
        if isinstance(input_data, dict):
            # Already aggregated by key, just pass through
            n = np.sum(np.array(input_data["n"]))
            sum_x2 = np.sum(np.array(input_data["sum_x2"]))
            total = np.sum(np.array(input_data["total"]))

        elif isinstance(input_data, list) or isinstance(input_data, np.ndarray):
            n, sum_x2, total = np.sum(np.vstack(input_data), axis=0)

        self.aggregated_data.update({"n": n, "sum_x2": sum_x2, "total": total})
        return self.aggregated_data

    def analyze(self) -> float:
        """Calculate variance from aggregated values."""

        return (
            self.aggregated_data["sum_x2"]
            - (self.aggregated_data["total"] * self.aggregated_data["total"])
            / self.aggregated_data["n"]
        ) / (self.aggregated_data["n"] - 1)


class PMCCAnalysis(AnalysisBase):
    """Analysis class for calculating Pearson's correlation coefficient."""

    def __init__(self):
        self.aggregated_data = {}

    @property
    def return_format(self) -> dict:
        return {
            "n": None,
            "sum_x": None,
            "sum_y": None,
            "sum_xy": None,
            "sum_x2": None,
            "sum_y2": None,
        }

    def aggregate_data(
        self, input_data: Union[np.ndarray, List[np.ndarray], Dict[str, List[float]]]
    ) -> Union[np.ndarray, Dict[str, List[float]]]:
        """Aggregate data for PMCC calculation."""
        if isinstance(input_data, dict):
            n = np.sum(np.array(input_data["n"]))
            sum_x = np.sum(np.array(input_data["sum_x"]))
            sum_y = np.sum(np.array(input_data["sum_y"]))
            sum_xy = np.sum(np.array(input_data["sum_xy"]))
            sum_x2 = np.sum(np.array(input_data["sum_x2"]))
            sum_y2 = np.sum(np.array(input_data["sum_y2"]))

        elif isinstance(input_data, list) or isinstance(input_data, np.ndarray):
            n, sum_x, sum_y, sum_xy, sum_x2, sum_y2 = np.sum(
                np.vstack(input_data), axis=0
            )

        self.aggregated_data.update(
            {
                "n": n,
                "sum_x": sum_x,
                "sum_y": sum_y,
                "sum_xy": sum_xy,
                "sum_x2": sum_x2,
                "sum_y2": sum_y2,
            }
        )
        return self.aggregated_data

    def analyze(self) -> float:
        """Calculate Pearson's correlation coefficient from aggregated values."""

        # Calculate means
        mean_x = self.aggregated_data["sum_x"] / self.aggregated_data["n"]
        mean_y = self.aggregated_data["sum_y"] / self.aggregated_data["n"]

        # Calculate standard deviations
        std_x = np.sqrt(
            self.aggregated_data["sum_x2"]
            - (self.aggregated_data["sum_x"] ** 2) / self.aggregated_data["n"]
        )
        std_y = np.sqrt(
            self.aggregated_data["sum_y2"]
            - (self.aggregated_data["sum_y"] ** 2) / self.aggregated_data["n"]
        )

        # Calculate covariance
        cov = (
            self.aggregated_data["sum_xy"]
            - (self.aggregated_data["sum_x"] * self.aggregated_data["sum_y"])
            / self.aggregated_data["n"]
        ) / (self.aggregated_data["n"] - 1)

        # Calculate correlation coefficient
        return cov / (std_x * std_y)


class ContingencyTableAnalysis(AnalysisBase):
    """Analysis class for chi-squared test using scipy."""

    def __init__(self):
        self.aggregated_data = {}

    @property
    def return_format(self) -> dict:
        return {"contingency_table": None}

    def aggregate_data(
        self, input_data: Union[np.ndarray, List[np.ndarray], Dict[str, List[float]]]
    ) -> Union[np.ndarray, Dict[str, List[float]]]:
        """Aggregate contingency tables."""
        if isinstance(input_data, dict):
            # Already aggregated by key, just pass through
            data = input_data["contingency_table"]  ## should be a list of dicts.
            ## to compare two dicts, we can do len(dict1 - dict2)<=1, and then check that the remaining key is 'n'.
            # Use categorical values as composite key
            # Get all keys except 'n' for header
            categorical_keys = [k for k in data[0].keys() if k != "n"]
            header = ",".join(categorical_keys) + ",n"
            aggregated = {"header": header}

            for row in data:
                # Create string key from all categorical values (excluding 'n')
                categorical_values = [str(row[k]) for k in categorical_keys]
                str_key = ",".join(categorical_values)

                count = row["n"]

                if str_key in aggregated:
                    aggregated[str_key] += count  # Direct lookup and sum
                else:
                    aggregated[str_key] = count

            ## now we need to convert the aggregated dict into a numpy array
            ## the keys are the categorical values, and the values are the counts.
            contingency_array, labels = dict_to_array(aggregated)

            self.aggregated_data.update(
                {
                    "contingency_table": contingency_array,
                    "contingency_table_headers": labels,
                }
            )
            return self.aggregated_data

        elif isinstance(input_data, list):
            # For contingency tables, we need to combine them
            if len(input_data) == 1:
                if isinstance(input_data[0], dict):
                    ## if a list of dicts, then it's a list containing a single contingency table as a dict.
                    contingency_array, labels = dict_to_array(input_data[0])
                    self.aggregated_data.update(
                        {
                            "contingency_table": contingency_array,
                            "contingency_table_headers": labels,
                        }
                    )
                    return self.aggregated_data
                elif isinstance(input_data[0], str):
                    ## if it's a string, then it's csv data as a string.
                    # data = input_data[0].spit('\n')
                    data = combine_contingency_tables(input_data)
                    contingency_array, labels = dict_to_array(data)

                    self.aggregated_data.update(
                        {
                            "contingency_table": contingency_array,
                            "contingency_table_headers": labels,
                        }
                    )
                    return self.aggregated_data
                return contingency_array
            else:
                # Combine multiple contingency tables
                combined = []
                for table in input_data:
                    combined += table["contingency_table"]

                ## run recursively on the combined data, now it's in a format to be combined.
                self.aggregate_data({"contingency_table": combined})
                # self.aggregated_data.update({"contingency_table": combined})
                return self.aggregated_data

        elif isinstance(input_data, np.ndarray):
            ## should only be used for testing purposes.
            # Create empty labels for numpy array case
            labels = {"row_labels": [], "col_labels": [], "header": ""}
            self.aggregated_data.update(
                {"contingency_table": input_data, "contingency_table_headers": labels}
            )
            return self.aggregated_data
        return None

    def analyze(self) -> tuple:
        """Calculate contingency table."""
        # Return contingency table and headers
        return self.aggregated_data["contingency_table"], self.aggregated_data[
            "contingency_table_headers"
        ]


class PercentileSketchAnalysis(AnalysisBase):
    def __init__(self):
        self.aggregated_data = {}

    @property
    def return_format(self) -> dict:
        return {"percentile_sketch": None}

    def aggregate_data(
        self, input_data: Union[np.ndarray, List[np.ndarray], Dict[str, List[float]]]
    ) -> Union[np.ndarray, Dict[str, List[float]]]:
        """Aggregate percentile sketches."""

        digest = TDigest()
        if isinstance(input_data, dict):
            # Already aggregated by key, just pass through
            ## example: input_data = {
            #    "percentile_sketch": [
            #        {"centroids": [...], "count": 100},
            #        {"centroids": [...], "count": 150}
            #    ]
            # }
            if "percentile_sketch" in input_data:
                data = input_data["percentile_sketch"]
                ## this should be a list of digests (digests expressed as dicts)

                for datum in data:
                    temp_digest = TDigest()
                    temp_digest.update_from_dict(datum)
                    digest += temp_digest

                self.aggregated_data.update({"percentile_sketch": digest})
                return digest
            else:
                return input_data

            return input_data
        elif isinstance(input_data, list):
            ## example:
            # input_data = [
            #    '{"centroids": [...], "count": 100}',
            #    '{"centroids": [...], "count": 150}'
            # ]

            ## get the digests from the list of strings
            for data_string in input_data:
                temp_digest = TDigest()
                temp_digest.update_from_dict(json.loads(data_string))
                digest += temp_digest
            self.aggregated_data.update({"percentile_sketch": digest})
            return digest
        return None

    def analyze(self, aggregated_data: np.ndarray, percentile: float) -> float:
        return self.aggregated_data["percentile_sketch"].percentile(percentile)


class MetadataAnalysis(AnalysisBase):
    ## placeholder for now, this is where the metadata analysis will go.

    """Analysis class for calculating metadata values."""

    def __init__(self):
        self.aggregated_data = {}

    @property
    def return_format(self) -> dict:
        return {"n": None, "total": None}

    def aggregate_data(
        self, input_data: Union[np.ndarray, List[np.ndarray], Dict[str, List[float]]]
    ) -> Union[np.ndarray, Dict[str, List[float]]]:
        """Aggregate data for mean calculation."""
        if isinstance(input_data, dict):
            n = np.sum(np.array(input_data["n"]))
            total = np.sum(np.array(input_data["total"]))

        elif isinstance(input_data, list) or isinstance(input_data, np.ndarray):
            n, total = np.sum(np.vstack(input_data), axis=0)
        self.aggregated_data.update({"n": n, "total": total})
        return self.aggregated_data

    def analyze(self) -> float:
        """Calculate mean from aggregated values."""

        return self.aggregated_data["total"] / self.aggregated_data["n"]


def get_statistical_analysis_registry():
    """Get registry of all statistical analysis classes."""
    registry = {}
    for cls in AnalysisBase.__subclasses__():
        # Convert class name to analysis type (e.g., MeanAnalysis -> mean)
        analysis_type = cls.__name__.replace("Analysis", "").lower()
        registry[analysis_type] = cls
    return registry


STATISTICAL_ANALYSIS_CLASSES = get_statistical_analysis_registry()


class StatisticalAnalyzer:
    """
    Handles statistical calculations and analysis for federated data.
    Uses individual analysis classes that inherit from AnalysisBase.
    """

    def __init__(self):
        """Initialize the statistical analyzer with analysis classes."""
        self.analysis_classes = {
            analysis_type: cls()
            for analysis_type, cls in STATISTICAL_ANALYSIS_CLASSES.items()
        }

    def get_analysis_config(
        self,
        analysis_type: str,
    ) -> Dict[str, Any]:
        """
        Get configuration for a specific analysis type.

        Args:
            analysis_type (str): Type of analysis

        Returns:
            Dict[str, Any]: Analysis configuration

        Raises:
            ValueError: If analysis type is not supported
        """
        if analysis_type not in self.analysis_classes:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")

        analysis_class = self.analysis_classes[analysis_type]
        return {
            "return_format": analysis_class.return_format,
            "aggregation_function": analysis_class.aggregate_data,
            "analysis_function": analysis_class.analyze,
        }

    def get_supported_analysis_types(self) -> List[str]:
        """
        Get list of supported analysis types.

        Returns:
            List[str]: List of supported analysis types
        """
        return list(self.analysis_classes.keys())

    def analyze_data(
        self,
        input_data: Union[np.ndarray, List[np.ndarray], Dict[str, List[float]]],
        analysis_type: str,
    ) -> Union[float, Dict[str, Any]]:
        """
        Analyze data using the specified analysis type.

        Args:
            input_data: Input data (numpy array, list of arrays, or dict of lists)
            analysis_type (str): Type of analysis to perform

        Returns:
            Union[float, Dict[str, Any]]: Analysis result

        Raises:
            ValueError: If analysis type is not supported
        """
        if analysis_type not in self.analysis_classes:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")

        analysis_class = self.analysis_classes[analysis_type]

        # Aggregate data
        aggregated_data = analysis_class.aggregate_data(input_data)

        # Perform analysis
        ##don't pass in the aggregated data, just call the analyze method. Data is stored in the class.
        result = analysis_class.analyze()
        return result
