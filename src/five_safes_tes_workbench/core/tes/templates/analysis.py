from ....common.params.analysis_params import AnalysisUserParams
from ....common.params.tes_builder_params import (
    ExecutorTESParams,
    OutputTESParams,
    TESTaskParams,
)
from ...base.tes_template_abc import BaseTESTemplate


class AnalysisTemplate(BaseTESTemplate[AnalysisUserParams]):
    """
    Analysis template for TES tasks.

    Executes the analytics container with a user query and analysis mode.

    Method Usage:
    - `build_tes.analysis(name=..., query=..., analysis_type=...)`
    """

    @property
    def name(self) -> str:
        """
        Unique name for this template.
        """
        return "analysis"

    def resolve(self, overrides: AnalysisUserParams) -> TESTaskParams:
        """
        Merges user-provided params with internal defaults.
        """

        # ---- Fixed parameters for this template ----

        _IMAGE = "ghcr.io/health-informatics-uon/five-safes-tes-analytics-dev:sha-dbf029b"
        _DESCRIPTION = overrides.get("description", "Analysis Task")
        _OUTPUT_PATH = overrides.get("output_path", "/outputs")
        _OUTPUT_URL = overrides.get("output_url", "s3://")
        _OUTPUT_FILENAME = overrides.get(
            "output_filename", f"{_OUTPUT_PATH}/output"
        )
        _OUTPUT_FORMAT = overrides.get("output_format", "json")
        _WORKDIR = "/app"

        _COMMAND = [
            f"--user-query={overrides['query']}",
            f"--analysis={overrides['analysis_type']}",
            f"--output-filename={_OUTPUT_FILENAME}",
            f"--output-format={_OUTPUT_FORMAT}",
        ]

        return TESTaskParams(
            name=overrides["name"],
            executors=[
                ExecutorTESParams(
                    image=_IMAGE,
                    command=_COMMAND,
                    workdir=_WORKDIR,
                    env={},
                )
            ],
            outputs=[
                OutputTESParams(
                    name=overrides["name"],
                    description=_DESCRIPTION,
                    url=_OUTPUT_URL,
                    path=_OUTPUT_PATH,
                )
            ],
            volumes=[],
        )
