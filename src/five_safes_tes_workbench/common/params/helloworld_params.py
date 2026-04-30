from typing import NotRequired, Required, TypedDict


class HelloWorldUserParams(TypedDict):
    """
    User-facing parameters for the Hello World template.

    Required (must be provided by the caller):
        - name: Task name.
        - command: ["echo", "hello"]
        - image: Container image to run.

    Internal (fixed by the template, not user-configurable):
        - Description default: "Hello World Task"
        - output_url: "s3://hello-world-output"
        - output_path: "/outputs"
    """

    image: Required[str]
    command: Required[list[str]]
    name: Required[str]
    description: NotRequired[str]
    output_url: NotRequired[str]
    output_path: NotRequired[str]
