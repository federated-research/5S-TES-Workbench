from ....common.params.simple_sql_params import SimpleSQLUserParams
from ....common.params.tes_builder_params import (
    ExecutorTESParams,
    OutputTESParams,
    TESTaskParams,
)
from ...base.tes_template_abc import BaseTESTemplate


class SimpleSQLTemplate(BaseTESTemplate[SimpleSQLUserParams]):
    """
    Simple SQL template for TES tasks.

    Executes a SQL query using the TRE SQL PostgreSQL analysis tool.

    Method Usage:
    - `build_tes.simple_sql(name=..., description=..., query=...)`
    """

    @property
    def name(self) -> str:
        """
        Unique name for this template.
        """
        return "simple_sql"

    def resolve(self, overrides: SimpleSQLUserParams) -> TESTaskParams:
        """
        Merges user-provided params with internal defaults.
        The user's SQL query is injected into the command list.
        """

        # ---- Available Docker images for this template ----

        _DEFAULT_IMAGE = "harbor.federated-analytics.ac.uk/5s-tes-analysis-tools/5s-tes-analysis-tools-tre-sqlpg:1.0.0"  # noqa: E501
        _UON_ANALYSIS_IMAGE = "ghcr.io/health-informatics-uon/five-safes-tes-analytics-dev:sha-dbf029b" # noqa: E501

        # ---- Fixed parameters for this template ----

        _DESCRIPTION = overrides.get("description", "Simple SQL Task")
        _OUTPUT_PATH = overrides.get("output_path", "/outputs")
        _OUTPUT_URL = overrides.get("output_url", "s3://")
        _OUTPUT_FORMAT = overrides.get("output_format")
        _ANALYSIS = overrides.get("analysis")
        _COMMAND = [
            f"--Output={_OUTPUT_PATH}/output.csv",
            f"--Query={overrides['query']}",
        ]

        if _OUTPUT_FORMAT:
            _COMMAND.append(f"--output-format={_OUTPUT_FORMAT}")
        if _ANALYSIS:
            _COMMAND.append(f"--analysis={_ANALYSIS}")


        _IMAGE = _DEFAULT_IMAGE if not _ANALYSIS else _UON_ANALYSIS_IMAGE

        return TESTaskParams(
            name=overrides["name"],
            executors=[ExecutorTESParams(image=_IMAGE, command=_COMMAND)],
            description=_DESCRIPTION,
            inputs=[],
            outputs=[
                OutputTESParams(
                    name="Output",
                    description="Output results",
                    url=_OUTPUT_URL,
                    path=_OUTPUT_PATH,
                )
            ],
            volumes=[],
        )
