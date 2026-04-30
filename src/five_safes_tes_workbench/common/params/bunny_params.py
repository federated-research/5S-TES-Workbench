from typing import NotRequired, Required, TypedDict


class BunnyUserParams(TypedDict):
    """
    User-facing params for the Bunny template.

    Required:
    - name: Task name.
    - command: Command args passed to the Bunny CLI executor.

    Optional:
    - description: Task description.
    - image: Override the default Bunny CLI image.
    - output_url: S3 destination for outputs.
    - output_path: Output path inside the container.
    """

    name: Required[str]
    command: Required[list[str]]
    description: NotRequired[str]
    image: NotRequired[str]
    output_url: NotRequired[str]
    output_path: NotRequired[str]
