import os
from typing import Dict
from dotenv import load_dotenv

load_dotenv()


def default_tags() -> Dict[str, str]:
    return {
        "project": os.getenv("5STES_PROJECT", ""),
        "tres": os.getenv("5STES_TRES", ""),
    }
