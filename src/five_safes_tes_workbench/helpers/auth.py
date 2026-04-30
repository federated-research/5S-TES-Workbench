import requests

from ..common.enums.validator_enums import AuthMode
from ..schema.auth_schema import AuthValidationModel
from ..utils.logger import get_logger

logger = get_logger(__name__)


def fetch_keycloak_token(auth: AuthValidationModel) -> str:
    """
    Helper method to fetch a new access token from
    Keycloak using the provided credentials.

    Attributes:
            - `auth`: The authentication details containing
        Keycloak credentials.

    Returns:
            - The access token fetched from Keycloak.
    """
    url = (
        f"{auth.keycloak_url.rstrip('/')}"  # type: ignore[union-attr]
        f"/realms/Dare-Control/protocol/openid-connect/token"
    )

    logger.info("Requesting keycloak token from %s", url)

    response = requests.post(
        url,
        data={
            "client_id": auth.client_id,
            "client_secret": auth.client_secret,
            "username": auth.username,
            "password": auth.password,
            "grant_type": "password",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )

    response.raise_for_status()

    logger.info("Keycloak token fetched successfully")
    return response.json()["access_token"]


def resolve_bearer(auth: AuthValidationModel) -> str:
    """
    Helper for resolving the bearer token based on
    the authentication mode.

    - If the mode is ACCESS_TOKEN, it uses the provided token.

    - If the mode is CREDENTIALS, it fetches a new token from Keycloak.

    Attributes:
            - `auth`: The authentication details containing
            mode and credentials.
    """
    if auth.auth_mode == AuthMode.ACCESS_TOKEN:
        if auth.access_token is None:
            raise ValueError("access_token is required when auth_mode is ACCESS_TOKEN")

        logger.info("Using provided access token")
        return auth.access_token

    logger.info("Fetching token from keycloak...")
    return fetch_keycloak_token(auth)
