from typing import NotRequired, Required, TypedDict


class AnalysisUserParams(TypedDict):
    """
    User-facing parameters for the analysis template.

    Required:
        - name: Task name.
        - query: SQL query to execute.
        - analysis_type: Analysis mode to run.

    Optional (Solved internally):
        - description: TES task description.
        - output_url: Output storage URL.
        - output_path: Output directory path.
        - output_filename: Output file path written by the container.
        - output_format: Output serialization format.
    """

    name: Required[str]
    query: Required[str]
    analysis_type: Required[str]
    description: NotRequired[str]
    output_url: NotRequired[str]
    output_path: NotRequired[str]
    output_filename: NotRequired[str]
    output_format: NotRequired[str]
