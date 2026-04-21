import copy
import os
from typing import Dict, List, Optional

from five_safes_tes_workbench.auth.auth import keycloak_token, resolve_token
from five_safes_tes_workbench.helpers.build_tags import default_tags
from five_safes_tes_workbench.helpers.submit import submit_request


class TESTask:
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
        """
        Submit this task to the TES Submission API.

        Parameters
        ----------
        token : str, optional
            Bearer token override. When omitted the method resolves a token
            automatically (static .env value → Keycloak fallback).

        Returns
        -------
        dict
            JSON response from the server (typically contains the task ID).

        Raises
        ------
        requests.HTTPError
            If the server returns a non-2xx status after exhausting retries.
        """
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

    # ------------------------------------------------------------------
    # Factory: shell / arbitrary command
    # ------------------------------------------------------------------

    @classmethod
    def shell(
        cls,
        name: str,
        image: str,
        command: List[str],
        *,
        workdir: str = "/outputs",
        stdout: str = "/outputs/stdout",
        tags: Optional[Dict[str, str]] = None,
    ) -> "TESTask":
        """
        Build a task that runs an arbitrary shell command inside a container.

        Parameters
        ----------
        name : str
            Human-readable task name.
        image : str
            Docker image (e.g. ``"ubuntu"``).
        command : list[str]
            Command + arguments (e.g. ``["echo", "Hello World"]``).
        workdir : str
            Working directory inside the container. Defaults to ``"/outputs"``.
        stdout : str
            Path inside the container where stdout is written.
        tags : dict, optional
            Extra tags to merge with the defaults from .env.

        Example
        -------
        >>> task = TESTask.shell(
        ...     name="Hello World",
        ...     image="ubuntu",
        ...     command=["echo", "Hello World"],
        ... )
        """
        merged_tags = {**default_tags(), **(tags or {})}
        payload = {
            "state": 0,
            "name": name,
            "inputs": [],
            "outputs": [
                {
                    "name": "Stdout",
                    "description": "Stdout results",
                    "url": "s3://",
                    "path": workdir,
                    "type": "DIRECTORY",
                }
            ],
            "executors": [
                {
                    "image": image,
                    "command": command,
                    "workdir": workdir,
                    "stdout": stdout,
                }
            ],
            "volumes": None,
            "tags": merged_tags,
            "logs": None,
            "creation_time": None,
        }
        return cls(payload)

    # ------------------------------------------------------------------
    # Factory: SQL analytics
    # ------------------------------------------------------------------

    @classmethod
    def simple_sql(
        cls,
        name: str,
        query: str,
        *,
        output_path: str = "/outputs",
        workdir: str = "/app",
        image: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> "TESTask":
        """
        Build a task that runs a SQL analytics query via the 5S analytics container.

        Parameters
        ----------
        name : str
            Human-readable task name.
        query : str
            SQL SELECT statement to execute.
        analysis_type : str
            Analysis to perform on the result set (e.g. ``"mean"``, ``"count"``).
        output_format : str
            Format for the output file — ``"json"`` (default) or ``"csv"``.
        output_path : str
            Directory path inside the container for outputs.
        workdir : str
            Working directory inside the container. Defaults to ``"/app"``.
        image : str, optional
            Override the Docker image. Defaults to ``TES_DOCKER_IMAGE`` in .env.
        tags : dict, optional
            Extra tags to merge with the defaults from .env.
        """
        resolved_image = image or os.environ.get("TES_DOCKER_IMAGE", "")
        if not resolved_image:
            raise ValueError(
                "No Docker image specified. Set TES_DOCKER_IMAGE in .env "
                "or pass image= explicitly."
            )

        merged_tags = {**default_tags(), **(tags or {})}

        command = [
            f"--Query={query}",
            f"--Output={output_path}/output.csv",
        ]

        payload = {
            "state": 0,
            "name": name,
            "inputs": [],
            "outputs": [
                {
                    "name": "Results",
                    "description": "Simple SQL analysis output",
                    "url": "s3://",
                    "path": output_path,
                    "type": "DIRECTORY",
                }
            ],
            "executors": [
                {
                    "image": resolved_image,
                    "command": command,
                    "workdir": workdir,
                }
            ],
            "volumes": None,
            "tags": merged_tags,
            "logs": None,
            "creation_time": None,
        }
        return cls(payload)
