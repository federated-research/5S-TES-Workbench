import requests

from ..common.enums.validator_enums import AuthMode
from ..schema.auth_schema import AuthValidationModel
from ..utils.logger import get_logger

logger = get_logger(__name__)

_KEYCLOAK_TOKEN_SCOPES = "openid"


def fetch_keycloak_tokens(auth: AuthValidationModel) -> tuple[str, str | None]:
    """
    Fetch access and ID tokens from Keycloak using the provided credentials.

    The ID token is required for STS AssumeRoleWithWebIdentity when retrieving
    results from object storage. Keycloak only returns an id_token when the
    openid scope is requested.

    Returns
    -------
    A tuple of (access_token, id_token). id_token may be None if Keycloak
    did not return one.
    """
    url = (
        f"{auth.keycloak_url.rstrip('/')}"  # type: ignore[union-attr]
        f"/realms/Dare-Control/protocol/openid-connect/token"
    )

    logger.info("Requesting Keycloak tokens from %s", url)

    response = requests.post(
        url,
        data={
            "client_id": auth.client_id,
            "client_secret": auth.client_secret,
            "username": auth.username,
            "password": auth.password,
            "grant_type": "password",
            "scope": _KEYCLOAK_TOKEN_SCOPES,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )

    response.raise_for_status()

    body = response.json()
    logger.info("Keycloak tokens fetched successfully")
    return body["access_token"], body.get("id_token")


def fetch_keycloak_token(auth: AuthValidationModel) -> str:
    """
    Fetch an access token from Keycloak for TES submission and API calls.
    """
    access_token, _ = fetch_keycloak_tokens(auth)
    return access_token


def resolve_bearer(auth: AuthValidationModel) -> str:
    """
    Resolve the bearer access token for TES submission and API calls.

    - ACCESS_TOKEN mode: uses the configured access_token.
    - CREDENTIALS mode: fetches a fresh access token from Keycloak.
    """
    if auth.auth_mode == AuthMode.ACCESS_TOKEN:
        if auth.access_token is None:
            raise ValueError("access_token is required when auth_mode is ACCESS_TOKEN")

        logger.info("Using provided access token")
        return auth.access_token

    logger.info("Fetching access token from Keycloak...")
    return fetch_keycloak_token(auth)


def resolve_web_identity_token(auth: AuthValidationModel) -> str:
    """
    Resolve the token for STS AssumeRoleWithWebIdentity when fetching
    results from object storage.

    Preference order:
    1. Configured id_token
    2. Keycloak-fetched id_token (CREDENTIALS mode)
    3. access_token fallback (ACCESS_TOKEN mode without id_token)
    """
    if auth.id_token:
        logger.info("Using provided ID token for STS")
        return auth.id_token

    if auth.auth_mode == AuthMode.ACCESS_TOKEN:
        if auth.access_token is None:
            raise ValueError("access_token is required when auth_mode is ACCESS_TOKEN")
        logger.info("No id_token provided; falling back to access_token for STS")
        return auth.access_token

    logger.info("Fetching ID token from Keycloak for STS...")
    _, id_token = fetch_keycloak_tokens(auth)
    if not id_token:
        raise ValueError(
            "Keycloak did not return an id_token. Provide id_token in config "
            "or ensure the client allows the openid scope."
        )
    return id_token
