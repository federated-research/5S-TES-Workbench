from typing import TypedDict, Required


class ConfigValidationParams(TypedDict, total=False):
    """
    TypedDict for validation parameters to 
    be passed as keyword arguments to
    `Workbench.validate()`.

    The parameters are divided into two categories:
        1. Config parameters: Required parameters
           for validation.

        2. Auth parameters: Optional parameters
           for authentication.
    """
    # --- Config parameters ---

    project: Required[str]
    tes_base_url: Required[str]
    minio_sts_endpoint: Required[str]
    minio_endpoint: Required[str]
    minio_output_bucket: Required[str]
    tres: Required[list[str]]

    # --- Auth parameters ---

    access_token: str
    client_id: str
    client_secret: str
    keycloak_url: str
    username: str
    password: str


def split_config_params(params: ConfigValidationParams) -> tuple[dict[str, object], dict[str, object]]:
    """Splits the input parameters into config and auth
    parameters based on predefined keys.

    Attributes:
    -----------
        params: A dictionary of input parameters.

    Returns:
    ---------
        A tuple containing two dictionaries: (config_params,
          auth_params).
    """
    config = {k: v for k, v in params.items() if k in _CONFIG_KEYS}
    auth = {k: v for k, v in params.items() if k in _AUTH_KEYS}
    return config, auth

_CONFIG_KEYS = {
    "project", "tes_base_url", "minio_sts_endpoint",
    "minio_endpoint", "minio_output_bucket", "tres",
}

_AUTH_KEYS = {
    "access_token", "client_id", "client_secret",
    "keycloak_url", "username", "password",
}