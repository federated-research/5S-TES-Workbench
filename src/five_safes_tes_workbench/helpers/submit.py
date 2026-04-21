import os
import requests
from dotenv import load_dotenv

load_dotenv()


def submit_request(payload: dict, token: str) -> requests.Response:
    base_url = os.environ["TES_BASE_URL"].rstrip("/")
    url = f"{base_url}/v1/tasks"
    return requests.post(
        url,
        json=payload,
        headers={
            "accept": "text/plain",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        timeout=60,
    )
