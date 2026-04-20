from enum import Enum

class AuthMode(str, Enum):
    ACCESS_TOKEN = "token"  # nosec B105
    CREDENTIALS = "credentials"