from typing import List, Dict, Any

from five_safes_tes_workbench.runners.analysis_orchestrator import AnalysisOrchestrator
from five_safes_tes_workbench.clients.bunny_tes_client import BunnyTES
from five_safes_tes_workbench.clients.base_tes_client import BaseTESClient
from five_safes_tes_workbench.aggregation.data_processor import DataProcessor
from five_safes_tes_workbench.auth.submission_api_session import SubmissionAPISession


class MetadataRunner:
    def __init__(self, tes_client: BaseTESClient = None, project: str = None):
        if tes_client is None:
            tes_client = BunnyTES()
        self.analysis_orchestrator = None
        self.tes_client = tes_client
        self.project = project
        ## don't know whether to use the same processor, or create a new one.
        self.data_processor = DataProcessor()

        ## There will be significant differences in the metadata processing, so will need something new. But I'm leaving this here as a placeholder.
        # self.statistical_analyzer = StatisticalAnalyzer()

        # Storage for aggregated values
        self.aggregated_data = {}

    def get_metadata(
        self,
        tres: List[str] = None,
        task_name: str = None,
        task_description: str = None,
        bucket: str = None,
    ) -> Dict[str, Any]:

        analysis_type = "metadata"

        with SubmissionAPISession() as token_session:
            self.analysis_orchestrator = AnalysisOrchestrator(
                self.tes_client, token_session, self.project
            )
            task_name, task_description, bucket, tres = (
                self.analysis_orchestrator.setup_analysis(
                    analysis_type, task_name, task_description, bucket, tres
                )
            )

            ### create the TES message for the metadata
            metadata_tes = self.tes_client
            metadata_tes.set_tes_messages(
                task_name=task_name, task_description=task_description
            )
            metadata_tes.set_tags(tres=self.analysis_orchestrator.tres)
            metadata_tes.create_FiveSAFES_TES_message()

            if self.analysis_orchestrator.tres is None:
                self.analysis_orchestrator.tres = tres
            try:
                task_id, data = self.analysis_orchestrator._submit_and_collect_results(
                    metadata_tes.task,
                    bucket,
                    output_format="json",
                    submit_message=f"Submitting {analysis_type} analysis to {len(self.analysis_orchestrator.tres)} TREs...",
                )

                # Process and analyze data
                print("Processing and analyzing data...")

                # TODO: Implement proper metadata aggregation
                # For now, just pass through the raw data as a placeholder
                # The aggregation logic for metadata is different from analytics
                # and needs to be implemented separately
                raw_aggregated_data = data  # Placeholder: no aggregation yet

                ## placeholder for now, this is where the postprocessing will go.
                # analysis_result = self.statistical_analyzer.analyze_data(raw_aggregated_data, analysis_type)
                metadata_result = self.postprocess_metadata(raw_aggregated_data)

                # Store the aggregated values in the centralized dict
                # Note: Metadata storage may differ from analysis results
                if isinstance(raw_aggregated_data, dict):
                    self.aggregated_data.update(raw_aggregated_data)
                else:
                    self.aggregated_data["raw_data"] = raw_aggregated_data

                return {
                    "analysis_type": "metadata",
                    "result": metadata_result,
                    "task_id": task_id,
                    "tres_used": tres,
                    "data_sources": len(data),
                }

            except Exception as e:
                print(f"Metadata analysis failed: {str(e)}")
                raise

    def postprocess_metadata(self, raw_data: Any) -> Any:
        """
        Postprocess the metadata.

        TODO: Implement proper metadata postprocessing logic.
        For now, this is a placeholder that just returns the raw data unchanged.

        Args:
            raw_data: Raw data from TREs (could be dict, list, etc.)

        Returns:
            Any: Postprocessed metadata (currently just passes through)
        """
        # Placeholder: just return the raw data unchanged
        return raw_data


if __name__ == "__main__":
    # orchestrator = AnalysisOrchestrator(tes_client=BunnyTES())
    # metadata_runner = MetadataRunner(engine)
    metadata_runner = MetadataRunner()

    print("Running metadata analysis...")
    metadata_result = metadata_runner.get_metadata(
        task_name="DEMO: metadata test",
        task_description="This is a test description for the metadata analysis",
    )

    print(f"Metadata analysis result: {metadata_result['result']}")
    print(f"Stored aggregated data: {metadata_runner.aggregated_data}")
