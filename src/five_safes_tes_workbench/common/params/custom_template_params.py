from typing import Required, TypedDict


class CustomUserParams(TypedDict):
    """
    User-facing parameters for the Custom template.
    All fields are required — no defaults are provided.

    - name: Task name.
    - description: Task description.
    - image: Container image to run.
    - command: Command to execute in the container.
    - output_url: S3 output URL.
    - output_path: Output path inside the container.
    """

    name: Required[str]
    description: Required[str]
    image: Required[str]
    command: Required[list[str]]
    output_url: Required[str]
    output_path: Required[str]
