from typing import NotRequired, Required, TypedDict


class SimpleSQLUserParams(TypedDict):
    """
    User-facing parameters for the Simple SQL template.

    Required (must be provided by the caller):
        - name: Task name.
        - description: Task description.
        - query: SQL query to execute.

    Internal (fixed by the template, not user-configurable):
        - image: Custom 5STES SQL Analysis Tool image
        from Harbor.
        - output_url: "s3://simple-sql-output"
        - output_path: "/outputs"
    """

    name: Required[str]
    query: Required[str]
    description: NotRequired[str]
    output_url: NotRequired[str]
    output_path: NotRequired[str]
