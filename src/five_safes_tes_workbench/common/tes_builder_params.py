from typing import TypedDict, Required, NotRequired


class TESTaskParams(TypedDict):
    """
    Parameters for building a TES task.

    Required:
        - image: Container image to run.
        - command: Command to execute in the container.

    Optional:
        - name: Task name.
        - description: Task description.
        - output_url: S3 output URL.
        - output_path: Output path inside the container.
    """

    image: Required[str]
    command: Required[list[str]]
    name: Required[str]
    description: NotRequired[str]
    output_url: NotRequired[str]
    output_path: NotRequired[str]