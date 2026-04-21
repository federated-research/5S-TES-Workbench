import os
import requests
from five_safes_tes_workbench.auth.auth import keycloak_token
from five_safes_tes_workbench.helpers.build_tags import default_tags
import tes  # type: ignore


class TESTaskV2:
    @classmethod
    def example_generic(cls) -> None:
        # Define task
        base_url = os.environ["TES_BASE_URL"].rstrip("/")
        tasks_url = f"{base_url}"
        task = tes.Task(
            name="Hello World",
            description="Hello World",
            inputs=[],
            outputs=[
                tes.Output(
                    name="Stdout",
                    description="Stdout results",
                    url="s3://",
                    path="/outputs",
                    type="DIRECTORY",
                )
            ],
            executors=[tes.Executor(image="alpine", command=["echo", "hello"])],
            volumes=None,
            tags=default_tags(),
            logs=None,
            creation_time=None,
        )
        bearer = keycloak_token()
        # Inspect the task payload before submitting
        print("task_dict for inspection", task.as_json(indent=3))

        # Create task manually to avoid UnmarshalError caused by the server
        # returning a '$id' field that py-tes cannot unpack as a keyword argument.
        create_response = requests.post(
            f"{tasks_url}/v1/tasks",
            data=task.as_json(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {bearer}",
            },
            timeout=60,
        )
        create_response.raise_for_status()
        task_id = create_response.json()["id"]

        return task_id
