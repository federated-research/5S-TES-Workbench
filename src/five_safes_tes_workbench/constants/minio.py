"""Constants for S3 and STS operations."""

STS_NAMESPACE = {"sts": "https://sts.amazonaws.com/doc/2011-06-15/"}
STS_DURATION_SECONDS = "3600"
STS_TOKEN_EXCHANGE_TIMEOUT = 60

# SigV4 requires a region. S3-compatible stores such as MinIO and RustFS
# accept this placeholder when they do not enforce a real region.
S3_REGION = "us-east-1"
