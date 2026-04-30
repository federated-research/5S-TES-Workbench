from typing import Required, TypedDict


class TESTaskParams(TypedDict):
    """
    Parameters for building a TES task and
    all fields are required.

    - image: Container image to run.
    - command: Command to execute in the container.
    - name: Task name.
    - description: Task description.
    - output_url: S3 output URL.
    - output_path: Output path inside the container.
    """

    image: Required[str]
    command: Required[list[str]]
    name: Required[str]
    description: Required[str]
    output_url: Required[str]
    output_path: Required[str]
