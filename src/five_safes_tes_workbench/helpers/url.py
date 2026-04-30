from urllib.parse import urlparse


def is_https(url: str) -> bool:
    """
    Check if a URL is HTTPS.

    Parameters:
    -----------
    - url: The URL to check.

    Returns:
    --------
    True if HTTPS, False if HTTP.
    """
    parsed = urlparse(url)
    if parsed.scheme == "https":
        return True
    if parsed.scheme == "http":
        return False
    raise ValueError(f"URL must start with http:// or https://, got: {url}")


def strip_scheme(url: str) -> str:
    """
    Remove the ``http://`` or ``https://`` scheme from a URL, returning
    only the ``host:port`` (and any path) portion.

    The MinIO Python client constructor does not accept a scheme prefix;
    this helper normalises user-supplied endpoints so both
    ``"localhost:9000"`` and ``"http://localhost:9000"`` are accepted.

    Parameters:
    -----------
    - url: URL with or without a scheme prefix.

    Returns:
    --------
    The URL with the scheme stripped (e.g. ``"localhost:9000"``).
    """
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https"):
        # netloc contains host:port; path covers anything after
        return parsed.netloc + parsed.path.rstrip("/")
    return url
