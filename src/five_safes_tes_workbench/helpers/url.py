from urllib.parse import urlparse


def is_https(url: str) -> bool:
    """
    Check if a URL is HTTPS.

    Parameters:
    -----------
    - url: The URL to check.

    Returns:
    """
    parsed = urlparse(url)
    if parsed.scheme == "https":
        return True
    if parsed.scheme == "http":
        return False
    raise ValueError(f"URL must start with http:// or https://, got: {url}")
