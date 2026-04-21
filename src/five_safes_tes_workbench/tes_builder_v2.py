import copy
import os
from typing import Dict, List, Optional
import json

from five_safes_tes_workbench.auth.auth import keycloak_token, resolve_token
from five_safes_tes_workbench.helpers.build_tags import default_tags
from five_safes_tes_workbench.helpers.submit import submit_request
import tes  # type: ignore


class TESTaskV2:
    """
    A simple, immutable-ish container for a TES task payload.

    Do not instantiate directly — use the factory class methods:
      - ``TESTask.shell(...)``  for arbitrary shell / container commands
      - ``TESTask.sql(...)``    for SQL analytics tasks
    """

    def __init__(self, payload: dict) -> None:
        self._payload = payload

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def as_dict(self) -> dict:
        """Return a deep copy of the raw task payload dict."""
        return copy.deepcopy(self._payload)

    def __repr__(self) -> str:  # pragma: no cover
        return f"TESTask(name={self._payload.get('name')!r})"

    # ------------------------------------------------------------------
    # Submission
    # ------------------------------------------------------------------

    def submit(self, token: Optional[str] = None) -> dict:
        bearer = resolve_token(token)
        response = submit_request(self._payload, bearer)

        # Transparently retry once with a fresh Keycloak token on 401
        if response.status_code == 401:
            print("Token rejected (401) — fetching fresh token from Keycloak…")
            bearer = keycloak_token()
            response = submit_request(self._payload, bearer)

        if not response.ok:
            print(f"Submission failed [{response.status_code}]: {response.text}")

        response.raise_for_status()
        return response.json()

    @classmethod
    def example_generic(cls) -> None:
        # Define task
        base_url = os.environ["TES_BASE_URL"].rstrip("/")
        tasks_url = f"{base_url}"
        task = tes.Task(
            executors=[tes.Executor(image="alpine", command=["echo", "hello"])]
        )
        bearer = keycloak_token()
        # Create client
        cli = tes.HTTPClient(tasks_url, timeout=60, token=bearer)

        print("task_dict", task.as_json(indent=3))
        # Create and run task
        task_id = cli.create_task(task)
        cli.wait(task_id, timeout=60)

        # Fetch task info
        task_info = cli.get_task(task_id, view="BASIC")
        j = json.loads(task_info.as_json())

        # Pretty print task info
        print(json.dumps(j, indent=2))
