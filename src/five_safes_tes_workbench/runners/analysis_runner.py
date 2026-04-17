from typing import List, Dict, Any, Optional, Union
import numpy as np
import os
from string import Template

from five_safes_tes_workbench.clients.base_tes_client import BaseTESClient
from five_safes_tes_workbench.clients.analytics_tes_client import AnalyticsTES
from five_safes_tes_workbench.aggregation.data_processor import DataProcessor
from five_safes_tes_workbench.aggregation.statistical_analyzer import (
    StatisticalAnalyzer,
)
from five_safes_tes_workbench.auth.submission_api_session import SubmissionAPISession
from five_safes_tes_workbench.runners.analysis_orchestrator import AnalysisOrchestrator


class AnalysisRunner:
    def __init__(self, tes_client: BaseTESClient = None, project: str = None):
        if tes_client is None:
            tes_client = AnalyticsTES()

        self.analysis_orchestrator = None
        self.tes_client = tes_client
        self.project = project
        # Own instances for aggregation and analysis
        self.data_processor = DataProcessor()
        self.statistical_analyzer = StatisticalAnalyzer()
        # Storage for aggregated values
        self.aggregated_data = {}

    def run_analysis(
        self,
        analysis_type: str,
        user_query: str = None,
        tres: List[str] = None,
        task_name: str = None,
        task_description: str = None,
        bucket: str = None,
    ) -> Dict[str, Any]:
        """
        Run a complete federated analysis workflow.

        Args:
            analysis_type (str): Type of analysis to perform
            user_query (str, optional): User's data selection query (without analysis calculations)
            tres (List[str], optional): List of TREs to run analysis on
            task_name (str, optional): Name for the TES task (defaults to "analysis {analysis_type}")
            task_description (str, optional): Description for the TES task / output
            bucket (str, optional): MinIO bucket for outputs (defaults to MINIO_OUTPUT_BUCKET env var)

        Returns:
            Dict[str, Any]: Analysis results
        """
        with SubmissionAPISession() as token_session:
            self.analysis_orchestrator = AnalysisOrchestrator(
                self.tes_client, token_session=token_session, project=self.project
            )

            task_name, task_description, bucket, tres = (
                self.analysis_orchestrator.setup_analysis(
                    analysis_type, task_name, task_description, bucket, tres
                )
            )

            # Check if we should run on existing data (returns early if so)
            existing_data_result = self.check_analysis_on_existing_data(
                analysis_type, user_query, tres
            )
            if existing_data_result is not None:
                return existing_data_result

            ### create the TES message for the analysis

            self.tes_client.set_tes_messages(
                query=user_query,
                analysis_type=analysis_type,
                task_name=task_name,
                task_description=task_description,
                output_format="json",
            )
            self.tes_client.set_tags(tres=self.analysis_orchestrator.tres)
            five_Safes_TES_message = self.tes_client.create_FiveSAFES_TES_message()

            # Submit task and collect results (common workflow)
            try:
                task_id, data = self.analysis_orchestrator._submit_and_collect_results(
                    five_Safes_TES_message,
                    bucket,
                    output_format="json",
                    submit_message=f"Submitting {analysis_type} analysis to {len(self.analysis_orchestrator.tres)} TREs...",
                )

                # Process and analyze data (aggregation moved to this class)
                print("Processing and analyzing data...")
                raw_aggregated_data = self.data_processor.aggregate_data(
                    data, analysis_type
                )

                analysis_result = self.statistical_analyzer.analyze_data(
                    raw_aggregated_data, analysis_type
                )

                # Store the aggregated values in the centralized dict
                self._store_aggregated_values(analysis_type)

                return {
                    "analysis_type": analysis_type,
                    "result": analysis_result,
                    "task_id": task_id,
                    "tres_used": tres,
                    "data_sources": len(data),
                    "complete_query": user_query,
                }

            except Exception as e:
                print(f"Analysis failed: {str(e)}")
                raise

    def _store_aggregated_values(self, analysis_type: str):
        """
        Store the aggregated values in the centralized dict.

        Args:
            analysis_type (str): Type of analysis to store
        """
        analysis_class = self.statistical_analyzer.analysis_classes[analysis_type]

        # Store the aggregated values from the analysis class
        self.aggregated_data.update(analysis_class.aggregated_data)

    def check_analysis_on_existing_data(
        self, analysis_type: str, user_query: str = None, tres: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Check if analysis should run on existing data, and run it if so.

        Args:
            analysis_type (str): Type of analysis to perform
            user_query (str, optional): User's data selection query
            tres (List[str], optional): List of TREs to run analysis on

        Returns:
            Optional[Dict[str, Any]]: Analysis results if running on existing data, None otherwise
        """
        # Check if user is trying to run analysis on existing data
        if user_query is None and tres is None:
            # User wants to run analysis on existing aggregated data
            compatible_analyses = self.get_compatible_analyses()
            if analysis_type in compatible_analyses:
                print(f"Running {analysis_type} analysis on existing data...")
                result = self.run_additional_analysis(analysis_type)
                return {
                    "analysis_type": analysis_type,
                    "result": result,
                    "data_source": "existing_aggregated_data",
                    "compatible_analyses": compatible_analyses,
                }
            else:
                raise ValueError(
                    f"Analysis type '{analysis_type}' not compatible with existing data. "
                    f"Available analyses: {compatible_analyses}"
                )
        return None

    def get_runnable_analysis_types(self) -> List[str]:
        """
        Get list of analyses that can be run on the currently stored data.

        Returns:
            List[str]: List of compatible analysis types
        """
        compatible = []

        # Check each analysis type to see if we have the required data
        for analysis_type in self.statistical_analyzer.get_supported_analysis_types():
            if self._has_required_data(analysis_type):
                compatible.append(analysis_type)

        return compatible

    def run_additional_analysis(
        self, analysis_type: str
    ) -> Union[float, Dict[str, Any]]:
        """
        Run an additional analysis on stored aggregated data.

        Args:
            analysis_type (str): Type of analysis to run

        Returns:
            Union[float, Dict[str, Any]]: Analysis result

        Raises:
            ValueError: If no data is stored or analysis is incompatible
        """
        if analysis_type not in self.statistical_analyzer.analysis_classes:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")

        analysis_class = self.statistical_analyzer.analysis_classes[analysis_type]

        # Check if we have the required data for this analysis
        if not self._has_required_data(analysis_type):
            raise ValueError(
                f"Stored data is not compatible with {analysis_type} analysis"
            )

        # Convert stored data to the format expected by the analyzer
        raw_data = self._convert_stored_data_to_raw(analysis_type)

        return self.statistical_analyzer.analyze_data(raw_data, analysis_type)

    def _has_required_data(self, analysis_type: str) -> bool:
        """
        Check if we have the required data for a given analysis type.

        Args:
            analysis_type (str): Type of analysis to check

        Returns:
            bool: True if we have the required data
        """
        if analysis_type not in self.statistical_analyzer.analysis_classes:
            return False

        # Get the return format keys from the analysis class
        analysis_class = self.statistical_analyzer.analysis_classes[analysis_type]
        keys = analysis_class.return_format.keys()

        # Check if we have all the required keys
        return all(key in self.aggregated_data for key in keys)

    def _convert_stored_data_to_raw(self, analysis_type: str) -> np.ndarray:
        """
        Convert stored data from the centralized dict to raw numpy array for analysis.

        Args:
            analysis_type (str): Type of analysis to run

        Returns:
            np.ndarray: Raw data array
        """
        analysis_class = self.statistical_analyzer.analysis_classes[analysis_type]
        keys = list(analysis_class.return_format.keys())

        # Check if this analysis expects a contingency table
        if "contingency_table" in analysis_class.return_format:
            if "contingency_table" in self.aggregated_data:
                return self.aggregated_data["contingency_table"]
        else:
            # For other analyses, get values in the order of return_format keys
            if all(key in self.aggregated_data for key in keys):
                values = [self.aggregated_data[key] for key in keys]
                return np.array([values])

        raise ValueError(
            f"No compatible stored data found for {analysis_type} analysis"
        )

    def get_analysis_requirements(self, analysis_type: str) -> dict:
        """
        Get the requirements for a specific analysis type.

        Args:
            analysis_type (str): Type of analysis

        Returns:
            dict: Requirements including expected columns and format
        """
        return self.statistical_analyzer.get_analysis_config(analysis_type)

    def get_supported_analysis_types(self) -> List[str]:
        """
        Get list of supported analysis types.

        Returns:
            List[str]: List of supported analysis types
        """
        return self.statistical_analyzer.get_supported_analysis_types()


# Example usage
if __name__ == "__main__":
    from string import Template

    # Will use 5STES_PROJECT from environment and 5STES_TOKEN from environment
    # analytics_tes = AnalyticsTES()
    # orchestrator = AnalysisOrchestrator(tes_client=analytics_tes)
    # analysis_runner = AnalysisRunner(engine)
    analysis_runner = AnalysisRunner()

    ## need this to populate the query template
    sql_schema = os.getenv("postgresSchema", "public")

    # Example: Run variance analysis first, then mean analysis on the same data
    query_template = Template("""SELECT value_as_number FROM $sql_schema.measurement 
WHERE measurement_concept_id = 43055141
AND value_as_number IS NOT NULL""")

    user_query = query_template.safe_substitute(sql_schema=sql_schema)

    print("Running mean analysis...")
    mean_result = analysis_runner.run_analysis(
        analysis_type="mean",
        task_name="DEMO: mean analysis test",
        user_query=user_query,
    )

    # Show what aggregated data we have stored
    print(f"Mean analysis result: {mean_result['result']}")
    print(f"Stored aggregated data: {analysis_runner.aggregated_data}")
