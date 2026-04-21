import os
from typing import Optional

import requests

# ---------------------------------------------------------------------------
# Internal auth helpers
# ---------------------------------------------------------------------------


def static_token() -> Optional[str]:
    """Return the static AccessToken from .env, or None if absent."""
    return os.getenv("AccessToken") or None


def keycloak_token() -> str:
    """Fetch a fresh access token from Keycloak using password-grant credentials."""
    base = os.environ["SubmissionAPIBaseKeyCloakUrl"].rstrip("/")
    url = f"{base}/realms/Dare-Control/protocol/openid-connect/token"
    resp = requests.post(
        url,
        data={
            "client_id": os.environ["SubmissionAPIKeyCloakClientId"],
            "client_secret": os.environ["SubmissionAPIKeyCloakSecret"],
            "username": os.environ["SubmissionAPIKeyCloakUsername"],
            "password": os.environ["SubmissionAPIKeyCloakPassword"],
            "grant_type": "password",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def resolve_token(token: Optional[str]) -> str:
    """
    Return a bearer token, using the priority order:
      1. Explicitly passed ``token`` argument
      2. Static ``AccessToken`` in .env
      3. Fresh token from Keycloak credentials in .env
    """
    return token or static_token() or keycloak_token()
