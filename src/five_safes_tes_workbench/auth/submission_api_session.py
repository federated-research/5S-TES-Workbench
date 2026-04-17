import os 
from urllib.parse import urlparse

from dotenv import load_dotenv
import requests 


load_dotenv()


class SubmissionAPISession(): 
    """
    Context-managed OAuth2 session for the Submission API (Keycloak).

    Handles login, automatic token refresh (on 401), and logout, 
    and provides a unified `request()` method that injects the access token transparently.

    Designed for explicit session scoping via `with` and to replace static
    token strings in consumers (e.g., MinioClient, AnalysisOrchestrator).

    Example:
        with SubmissionAPISession() as session:
            response = session.request("GET", some_url)
            response.raise_for_status()
    """
    TOKEN_ERROR_INDICATORS = (
        'expired',
        'token expired',
        'invalid token',
        'invalid number of segments',
        'malformed',
        'invalidparametervalue',
        'unauthorized',
        'invalid_token'
    )
    TOKEN_ERROR_STATUS_CODES = (400, 401)

    def __init__(
        self, 
        client_id: str = None,
        client_secret: str = None, 
        username: str = None, 
        password: str = None, 
        base_keycloak_url: str = None 
    ):
        """
        Initialise a SubmissionAPISession.

        Parameters
        ----------
        client_id : str, optional
            OAuth2 client ID issued by Keycloak. If not provided, the value is
            loaded from the ``SubmissionAPIKeyCloakClientId`` environment variable.

        client_secret : str, optional
            OAuth2 client secret associated with the client ID. If omitted,
            ``SubmissionAPIKeyCloakSecret`` from the environment is used.

        username : str, optional
            Username used for the password grant login flow. Defaults to the
            ``SubmissionAPIKeyCloakUsername`` environment variable.

        password : str, optional
            Password used for the password grant login flow. Defaults to the
            ``SubmissionAPIKeyCloakPassword`` environment variable.

        base_keycloak_url : str, optional
            Base URL of the Keycloak realm endpoint (for example:
            ``https://auth.example.com/realms/myrealm``). If not supplied,
            the value is read from ``SubmissionAPIBaseKeyCloakUrl``.

        Raises
        ------
        ValueError
            If any required configuration value is missing or if the
            Keycloak base URL is not a valid URL.
        """
        self.client_id = client_id or os.getenv("SubmissionAPIKeyCloakClientId")
        self.client_secret = client_secret or os.getenv("SubmissionAPIKeyCloakSecret")
        self.username = username or os.getenv("SubmissionAPIKeyCloakUsername")
        self.password = password or os.getenv("SubmissionAPIKeyCloakPassword")
        self.base_keycloak_url = base_keycloak_url or os.getenv("SubmissionAPIBaseKeyCloakUrl")

        self._validate_input()

        self.token_url = os.path.join(self.base_keycloak_url, "protocol", "openid-connect", "token")
        self.logout_url = os.path.join(self.base_keycloak_url, "protocol", "openid-connect", "logout")

        self._access_token = None
        self._refresh_token = None

    def __enter__(self):
        self._login()
        return self

    def __exit__(self, exc_type, exc, tb):
        self._logout()

    @property
    def access_token(self): 
        """
        Returns the current access token string.

        This value is automatically updated when a token refresh occurs.
        """
        return self._access_token
    
    @property
    def refresh_token(self): 
        """
        Returns the current refresh token string.

        This value is rotated when a new token pair is issued.
        """
        return self._refresh_token 
    
    def request(self, method, url, token_in="header", token_field="Authorization", **kwargs):
        """
        Perform an HTTP request authenticated with the current access token.

        The token is automatically injected either into the request headers
        or request body, depending on the `token_in` parameter.

        If the request returns HTTP 401 (Unauthorised), the session will:
            1. Attempt to refresh the access token.
            2. Retry the request once with the new token.

        Parameters
        ----------
        method: str 
            HTTP method (e.g. "GET", "POST", "PUT", "DELETE")
        
        url: str
            Target request URL. 
        
        token_in: str
            Where to inject the access token:
                - "header" (default): adds "Authorization: Bearer <token>"
                - "body": injects token into request payload
        
        token_field: str
            Header or body field name used for token injection.

        **kwargs:
            Additional keyword arguments passed directly to `requests.request()`.

        Returns 
        -------
        requests.Response:
            The final HTTP response object. 
        """
        response = self._send(method, url, token_in, token_field, **kwargs)
        if self._is_token_error(response):
            self._refresh()
            response = self._send(method, url, token_in, token_field, **kwargs)
        return response
    
    def _validate_input(self): 
        required = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": self.username,
            "password": self.password,
            "base_keycloak_url": self.base_keycloak_url
        }

        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(
                f"Missing required Submission API configuration: {', '.join(missing)}"
                "Please make sure these are present in the .env file!"
            )
        missing = [k for k, v in required.items() if not v]

        parsed_base_url = urlparse(self.base_keycloak_url)
        if not all([parsed_base_url.scheme, parsed_base_url.netloc]): 
            raise ValueError("base_keycloak_url must be a valid URL!")

    def _login(self):
        payload = {
            "client_id": self.client_id, 
            "client_secret": self.client_secret, 
            "username": self.username, 
            "password": self.password, 
            "grant_type": "password"
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(
            self.token_url,
            data=payload,  
            headers=headers
        )

        response.raise_for_status()
        response_json = response.json()
        self._access_token = response_json["access_token"]
        self._refresh_token = response_json["refresh_token"]

    def _refresh(self):
        response = requests.post(
            self.token_url,
            data={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
            },
        )
        response.raise_for_status()
        response_json = response.json()
        self._access_token = response_json["access_token"]
        self._refresh_token = response_json["refresh_token"]

    def _logout(self):
        requests.post(
            self.logout_url,
            data={
                "client_id": self.client_id,
                "refresh_token": self.refresh_token,
            }
        )
        self._access_token = None
        self._refresh_token = None

    def _send(self, method, url, token_in="header", token_field="Authorization", **kwargs): 
        kwargs = kwargs.copy()
        headers = dict(kwargs.pop("headers", {}))
        data = dict(kwargs.pop("data", {}))

        if token_in == "header":
            headers[token_field] = f"Bearer {self.access_token}"
        elif token_in == "body":
            data[token_field] = self.access_token
        else:
            raise ValueError(f"Unknown token_in value: {token_in}")

        kwargs["headers"] = headers
        kwargs["data"] = data

        return requests.request(method, url, **kwargs)

    def _is_token_error(self, response: requests.Response): 
        if response.status_code in self.TOKEN_ERROR_STATUS_CODES:
            if response.status_code == 401:
                return True
            elif response.status_code == 400:
                error_content = response.text.lower()
                return any(
                    indicator in error_content 
                    for indicator in self.TOKEN_ERROR_INDICATORS
                )
        return False 
