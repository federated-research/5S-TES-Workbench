from typing import Required, TypedDict

from ..enums.validator_enums import AuthParamEnums, ConfigParamEnums


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
    ConfigParamEnums.PROJECT.value,
    ConfigParamEnums.TES_BASE_URL.value,
    ConfigParamEnums.MINIO_STS_ENDPOINT.value,
    ConfigParamEnums.MINIO_ENDPOINT.value,
    ConfigParamEnums.MINIO_OUTPUT_BUCKET.value,
    ConfigParamEnums.TRES.value,
}

_AUTH_KEYS = {
    AuthParamEnums.ACCESS_TOKEN.value,
    AuthParamEnums.CLIENT_ID.value,
    AuthParamEnums.CLIENT_SECRET.value,
    AuthParamEnums.KEYCLOAK_URL.value,
    AuthParamEnums.USERNAME.value,
    AuthParamEnums.PASSWORD.value,
}