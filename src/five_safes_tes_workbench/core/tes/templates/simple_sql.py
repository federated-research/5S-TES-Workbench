from ....common.params.simple_sql_params import SimpleSQLUserParams
from ....common.params.tes_builder_params import TESTaskParams
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

        # ---- Fixed parameters for this template ----

        _IMAGE = "harbor.federated-analytics.ac.uk/5s-tes-analysis-tools/5s-tes-analysis-tools-tre-sqlpg:1.0.0" # noqa: E501
        _DESCRIPTION = overrides.get("description", "Simple SQL Task")
        _OUTPUT_PATH = overrides.get("output_path", "/outputs")
        _OUTPUT_URL = overrides.get("output_url", "s3://simple-sql-output")
        _OUTPUT_FILE = f"{_OUTPUT_PATH}/output.csv"

        return TESTaskParams(
            # --- Required params from user ---
            name=overrides["name"],

            # --- Fixed by this template ---
            description=_DESCRIPTION,
            image=_IMAGE,
            command=[
                f"--Output={_OUTPUT_FILE}",
                f"--Query={overrides['query']}",
            ],

            # --- Optional params with template defaults ---
            output_url=_OUTPUT_URL,
            output_path=_OUTPUT_PATH,
        )
