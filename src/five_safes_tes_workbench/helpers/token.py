import xml.etree.ElementTree as ET
from urllib.parse import urlsplit, urlunsplit

import requests

from ..constants.minio import (
    STS_DURATION_SECONDS,
    STS_NAMESPACE,
    STS_TOKEN_EXCHANGE_TIMEOUT,
)
from ..helpers.minio import MinioCredentials
from ..utils.logger import get_logger

logger = get_logger(__name__)

STS_ACTION = "AssumeRoleWithWebIdentity"
STS_VERSION = "2011-06-15"


def _parse_sts_response(response: requests.Response) -> MinioCredentials:
    """
    Parse and validate the STS response and return the credentials.

    Parameters
    ----------
    - response: The response from the STS endpoint.

    Returns
    -------
    A MinioCredentials object.
    """
    try:
        root = ET.fromstring(response.text)
    except ET.ParseError as exc:
        raise RuntimeError(
            f"STS response is not valid XML (status {response.status_code}). "
            f"Raw response:\n{response.text!r}"
        ) from exc

    credentials = root.find(".//sts:Credentials", STS_NAMESPACE)
    if credentials is None:
        credentials = next(
            (element for element in root.iter() if _local_name(element.tag) == "Credentials"),
            None,
        )

    if credentials is None:
        raise RuntimeError("STS response contained no Credentials element")

    access_key = _find_child_text(credentials, "AccessKeyId")
    secret_key = _find_child_text(credentials, "SecretAccessKey")
    session_token = _find_child_text(credentials, "SessionToken")

    if access_key is None or secret_key is None or session_token is None:
        raise RuntimeError("STS response did not contain all required credentials")

    return MinioCredentials(
        access_key=access_key, secret_key=secret_key, session_token=session_token
    )


def _local_name(tag: str) -> str:
    """Return an XML tag name without its optional namespace."""
    return tag.rsplit("}", 1)[-1]


def _find_child_text(element: ET.Element, child_name: str) -> str | None:
    child = next(
        (child for child in element if _local_name(child.tag) == child_name),
        None,
    )
    return child.text if child is not None else None


def _sts_endpoint_candidates(sts_endpoint: str) -> list[str]:
    """
    Return STS endpoints to try.

    MinIO commonly exposes STS at ``/sts``. RustFS routes
    ``AssumeRoleWithWebIdentity`` at the service root.
    """
    parsed = urlsplit(sts_endpoint)
    candidates = [sts_endpoint]
    if parsed.path.rstrip("/") == "/sts":
        root_endpoint = urlunsplit(
            (parsed.scheme, parsed.netloc, "", parsed.query, parsed.fragment)
        )
        candidates.append(root_endpoint)
    return candidates


def _should_try_next_sts_endpoint(response: requests.Response) -> bool:
    return (
        response.status_code == 501
        and "NotImplemented" in response.text
        and "Unknown operation" in response.text
    )


def exchange_s3_token(bearer: str, sts_endpoint: str) -> MinioCredentials:
    """
    Call the STS AssumeRoleWithWebIdentity action and return temporary
    AWS-style credentials.
    """
    logger.info("Exchanging bearer token for MinIO credentials via STS (%s)", sts_endpoint)

    response = None
    candidates = _sts_endpoint_candidates(sts_endpoint)

    for endpoint in candidates:
        response = requests.post(
            endpoint,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "Action": STS_ACTION,
                "Version": STS_VERSION,
                "DurationSeconds": STS_DURATION_SECONDS,
                "WebIdentityToken": bearer,
            },
            timeout=STS_TOKEN_EXCHANGE_TIMEOUT,
        )

        if response.status_code == 200:
            return _parse_sts_response(response)

        if endpoint != candidates[-1] and _should_try_next_sts_endpoint(response):
            logger.warning(
                "STS endpoint %s did not recognize %s; retrying service root",
                endpoint,
                STS_ACTION,
            )
            continue

        raise RuntimeError(f"STS token exchange failed ({response.status_code}): {response.text}")

    if response is None:
        raise RuntimeError("STS token exchange failed: no endpoint candidates")

    return _parse_sts_response(response)
