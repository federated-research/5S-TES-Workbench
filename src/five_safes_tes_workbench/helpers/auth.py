import requests

from ..common.enums.validator_enums import AuthMode
from ..schema.auth_schema import AuthValidationModel
from ..utils.logger import get_logger

logger = get_logger(__name__)


def _fetch_keycloak_token_response(auth: AuthValidationModel) -> dict[str, str]:
    """
    Fetch a token JSON response from Keycloak using the provided credentials.

    Attributes:
    - auth: The authentication details containing
      Keycloak credentials.

    Returns:
    - A dictionary containing the access token and id token.
    """
    url = (
        f"{auth.keycloak_url.rstrip('/')}"  # type: ignore[union-attr]
        f"/realms/Dare-Control/protocol/openid-connect/token"
    )

    logger.info("Requesting Keycloak token from %s", url)

    response = requests.post(
        url,
        data={
            "client_id": auth.client_id,
            "client_secret": auth.client_secret,
            "username": auth.username,
            "password": auth.password,
            "grant_type": "password",
            "scope": "openid",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )

    response.raise_for_status()

    logger.info("Keycloak token fetched successfully")
    return response.json()


def fetch_keycloak_access_token(auth: AuthValidationModel) -> str:
    """
    Helper method to fetch a new access token from
    Keycloak using the provided credentials.

    Attributes:
            - `auth`: The authentication details containing
        Keycloak credentials.

    Returns:
            - The access token fetched from Keycloak.
    """
    return _fetch_keycloak_token_response(auth)["access_token"]


def fetch_keycloak_id_token(auth: AuthValidationModel) -> str:
    """
    Fetch an OIDC ID token from Keycloak for STS web identity exchange.

    RustFS validates ``AssumeRoleWithWebIdentity`` tokens as OIDC identity
    tokens.
    """
    token_response = _fetch_keycloak_token_response(auth)
    id_token = token_response.get("id_token")
    if not id_token:
        raise RuntimeError(
            "Keycloak did not return an id_token. Ensure the client supports "
            "OpenID Connect and that the 'openid' scope is allowed."
        )
    return id_token


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

    logger.info("Fetching token from Keycloak...")
    return fetch_keycloak_access_token(auth)


def resolve_sts_bearer(auth: AuthValidationModel) -> str:
    """
    Resolve the bearer token used for S3 STS web identity exchange.

    For username/password credentials this uses the Keycloak ID token. If the
    caller provides a token directly, they must provide a token RustFS trusts
    for ``AssumeRoleWithWebIdentity``.
    """
    if auth.auth_mode == AuthMode.ACCESS_TOKEN:
        if auth.access_token is None:
            raise ValueError("access_token is required when auth_mode is ACCESS_TOKEN")

        logger.info("Using provided token for STS exchange")
        return auth.access_token

    logger.info("Fetching Keycloak ID token for STS exchange...")
    return fetch_keycloak_id_token(auth)
