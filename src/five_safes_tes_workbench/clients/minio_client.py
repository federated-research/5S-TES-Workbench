import os
import time
from urllib.parse import urlparse
import json
from typing import Dict, List, Optional, Union, Any
import minio
from dotenv import load_dotenv
from minio import Minio
import xml.etree.ElementTree as ET
import csv
from io import StringIO

from five_safes_tes_workbench.auth.submission_api_session import SubmissionAPISession


# Load environment variables from .env file
load_dotenv()


class TokenExpiredError(Exception):
    """Exception raised when the provided token has expired."""

    pass


class MinIOClient:
    """
    Handles MinIO operations including token exchange and object retrieval.
    """

    def __init__(
        self,
        token_session: SubmissionAPISession = None,
        sts_endpoint: str = None,
        minio_endpoint: str = None,
    ):
        """
        Initialize the MinIO client.

        Args:
            token (str): OIDC token for authentication
            sts_endpoint (str): STS endpoint URL
            minio_endpoint (str): MinIO endpoint URL
        """
        self.token_session = token_session
        # Use environment variables - required
        self.sts_endpoint = sts_endpoint or os.getenv("MINIO_STS_ENDPOINT")
        if not self.sts_endpoint:
            raise ValueError("MINIO_STS_ENDPOINT environment variable is required")

        self.minio_endpoint = minio_endpoint or os.getenv("MINIO_ENDPOINT")
        if not self.minio_endpoint:
            raise ValueError("MINIO_ENDPOINT environment variable is required")

        self._client = None
        self._credentials = None

    def _exchange_token_for_credentials(self) -> Dict[str, str]:
        """
        Exchange OIDC token for temporary AWS credentials.

        Returns:
            Dict[str, str]: Dictionary containing access_key, secret_key, and session_token

        Raises:
            TokenExpiredError: If the token has expired
            Exception: If token exchange fails
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        data = {
            "Action": "AssumeRoleWithWebIdentity",
            "Version": "2011-06-15",
            "DurationSeconds": "3600",
        }

        print("Exchanging token for credentials...")

        response = self.token_session.request(
            method="POST",
            url=self.sts_endpoint,
            token_in="body",
            token_field="WebIdentityToken",
            headers=headers,
            data=data,
        )

        if response.status_code != 200:
            raise Exception(
                f"Failed to exchange token for MinIO credentials: "
                f"{response.status_code} - {response.text}"
            )

        # Parse the STS response
        root = ET.fromstring(response.text)
        ns = {"sts": "https://sts.amazonaws.com/doc/2011-06-15/"}

        credentials = root.find(".//sts:Credentials", ns)
        if credentials is None:
            raise Exception("No credentials found in STS response")

        access_key = credentials.find("sts:AccessKeyId", ns).text
        secret_key = credentials.find("sts:SecretAccessKey", ns).text
        session_token = credentials.find("sts:SessionToken", ns).text

        return {
            "access_key": access_key,
            "secret_key": secret_key,
            "session_token": session_token,
        }

    def _get_client(self) -> Minio:
        """
        Get or create MinIO client with valid credentials.

        Returns:
            Minio: MinIO client instance
        """
        if self._client is None or self._credentials is None:
            self._credentials = self._exchange_token_for_credentials()

            self._client = Minio(
                self.minio_endpoint,
                access_key=self._credentials["access_key"],
                secret_key=self._credentials["secret_key"],
                session_token=self._credentials["session_token"],
                secure=self._is_https(),
            )

        return self._client

    def _is_https(self):
        """
        Determine whether MinIO uses encrypted communication.
        """
        endpoint = os.environ.get("MINIO_STS_ENDPOINT")
        if not endpoint:
            raise ValueError("MINIO_STS_ENDPOINT is not set")

        parsed = urlparse(endpoint)

        if parsed.scheme == "https":
            return True
        elif parsed.scheme == "http":
            return False
        else:
            raise ValueError("MINIO_STS_ENDPOINT must start with http:// or https://")

    def refresh_credentials(self):
        """Force refresh of credentials."""
        self._credentials = None
        self._client = None

    def get_object(self, bucket: str, object_path: str) -> Optional[str]:
        """
        Get object content from MinIO.

        Args:
            bucket (str): Name of the MinIO bucket
            object_path (str): Path to the object within the bucket

        Returns:
            Optional[str]: Contents of the file as a string, or None if not found
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                client = self._get_client()

                print(f"Getting object '{object_path}' from bucket '{bucket}'...")
                response = client.get_object(bucket, object_path)

                # Read and decode the content
                content = response.read().decode("utf-8")
                response.close()
                response.release_conn()

                return content

            except minio.error.S3Error as e:
                if e.code == "NoSuchKey":
                    print(f"Object not found: {object_path} in bucket {bucket}")
                    return None
                elif e.code == "ExpiredTokenException":
                    print("Token expired, refreshing credentials...")
                    self.refresh_credentials()
                    retry_count += 1
                    continue
                else:
                    print(f"MinIO error: {e}")
                    retry_count += 1
                    continue

            except Exception as e:
                print(f"Error accessing MinIO: {str(e)}")
                print(f"Error type: {type(e).__name__}")

                if retry_count < max_retries - 1:
                    retry_count += 1
                    print(f"\nRetrying... (Attempt {retry_count + 1} of {max_retries})")
                    time.sleep(2**retry_count)  # Exponential backoff
                    continue
                else:
                    print(f"Failed after {max_retries} attempts")
                    return None

        return None

    def combine_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combine data from multiple sources.

        Args:
            data (List[Dict[str, Any]]): List of dictionaries containing data from multiple sources

        Returns:
            Dict[str, Any]: Combined data as a dictionary
        """
        combined_data = {}
        for item in data:
            if isinstance(item, dict):
                for key, value in item.items():
                    if key not in combined_data:
                        combined_data[key] = []
                    combined_data[key].append(value)
        return combined_data

    def list_objects(self, bucket: str, prefix: str = "") -> List[str]:
        """
        List objects in a bucket.

        Args:
            bucket (str): Name of the MinIO bucket
            prefix (str): Prefix to filter objects

        Returns:
            List[str]: List of object names
        """
        try:
            client = self._get_client()
            objects = client.list_objects(bucket, prefix=prefix)
            return [obj.object_name for obj in objects]
        except Exception as e:
            print(f"Error listing objects: {str(e)}")
            return []

    def list_buckets(self) -> List[str]:
        """
        List available buckets.

        Returns:
            List[str]: List of bucket names
        """
        try:
            client = self._get_client()
            buckets = client.list_buckets()
            return [bucket.name for bucket in buckets]
        except Exception as e:
            print(f"Error listing buckets: {str(e)}")
            return []

    def bucket_exists(self, bucket: str) -> bool:
        """
        Check if a bucket exists.

        Args:
            bucket (str): Name of the bucket

        Returns:
            bool: True if bucket exists, False otherwise
        """
        try:
            client = self._get_client()
            return client.bucket_exists(bucket)
        except Exception as e:
            print(f"Error checking bucket existence: {str(e)}")
            return False

    def object_exists(self, bucket: str, object_path: str) -> bool:
        """
        Check if an object exists.

        Args:
            bucket (str): Name of the bucket
            object_path (str): Path to the object

        Returns:
            bool: True if object exists, False otherwise
        """
        try:
            client = self._get_client()
            client.stat_object(bucket, object_path)
            return True
        except minio.error.S3Error as e:
            if e.code == "NoSuchKey":
                return False
            else:
                print(f"Error checking object existence: {e}")
                return False
        except Exception as e:
            print(f"Error checking object existence: {str(e)}")
            return False

    def get_object_info(self, bucket: str, object_path: str) -> Optional[Dict]:
        """
        Get information about an object.

        Args:
            bucket (str): Name of the bucket
            object_path (str): Path to the object

        Returns:
            Optional[Dict]: Object information or None if not found
        """
        try:
            client = self._get_client()
            stat = client.stat_object(bucket, object_path)
            return {
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "content_type": stat.content_type,
            }
        except minio.error.S3Error as e:
            if e.code == "NoSuchKey":
                return None
            else:
                print(f"Error getting object info: {e}")
                return None
        except Exception as e:
            print(f"Error getting object info: {str(e)}")
            return None

    def wait_for_object(
        self,
        bucket: str,
        object_path: str,
        timeout: int = 300,
        check_interval: int = 10,
    ) -> Optional[str]:
        """
        Wait for an object to appear and return its content.

        Args:
            bucket (str): Name of the bucket
            object_path (str): Path to the object
            timeout (int): Maximum time to wait in seconds
            check_interval (int): Time between checks in seconds

        Returns:
            Optional[str]: Object content or None if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            content = self.get_object(bucket, object_path)
            if content is not None:
                return content

            print(
                f"Object {object_path} not found, waiting {check_interval} seconds..."
            )
            time.sleep(check_interval)

        print(f"Timeout waiting for object {object_path}")
        return None

    def get_object_as_json(self, bucket: str, object_path: str) -> Optional[Dict]:
        """
        Get object content from MinIO and parse it as JSON.

        Args:
            bucket (str): Name of the MinIO bucket
            object_path (str): Path to the object within the bucket

        Returns:
            Optional[Dict]: Parsed JSON object, or None if not found or not JSON
        """
        content = self.get_object(bucket, object_path)
        if content is None:
            return None

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            print(f"Failed to decode JSON from object {object_path} in bucket {bucket}")
            return None

    def get_object_smart(
        self, bucket: str, object_path: str
    ) -> Optional[Union[str, Dict, List]]:
        """
        Get object content from MinIO and automatically detect format.

        Args:
            bucket (str): Name of the MinIO bucket
            object_path (str): Path to the object within the bucket

        Returns:
            Optional[Union[str, Dict, List]]: Parsed JSON object, list, or string content, or None if not found
        """
        content = self.get_object(bucket, object_path)
        if content is None:
            return None

        # Try JSON first
        try:
            json_data = json.loads(content)
            # Return JSON data as-is (could be dict, list, or other valid JSON)
            return json_data
        except json.JSONDecodeError:
            # Try CSV parsing
            try:
                reader = csv.DictReader(StringIO(content))
                data = next(reader)
                return data
            except:
                # Fall back to raw string
                return content
