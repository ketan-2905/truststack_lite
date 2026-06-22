"""Object storage client (MinIO locally, S3-compatible in the cloud).

This is real object storage. There is no in-memory fallback: if the bucket is
unreachable the health check fails and upload endpoints (MD 05) will error.
"""

from __future__ import annotations

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from app.config import settings

_client = None


def get_s3():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path" if settings.s3_use_path_style else "auto"},
            ),
        )
    return _client


def ensure_bucket() -> None:
    """Create the configured bucket if it does not already exist."""
    s3 = get_s3()
    try:
        s3.head_bucket(Bucket=settings.s3_bucket)
    except ClientError:
        s3.create_bucket(Bucket=settings.s3_bucket)


def check_storage() -> None:
    """Raise if object storage is not reachable. Used by the health endpoint."""
    get_s3().list_buckets()


def put_object(key: str, data: bytes, content_type: str | None = None) -> None:
    """Store bytes at ``key`` in the configured bucket (real object storage)."""
    ensure_bucket()
    extra = {"ContentType": content_type} if content_type else {}
    get_s3().put_object(Bucket=settings.s3_bucket, Key=key, Body=data, **extra)


def get_object(key: str) -> bytes:
    """Fetch object bytes at ``key``. Raises if the object does not exist."""
    resp = get_s3().get_object(Bucket=settings.s3_bucket, Key=key)
    return resp["Body"].read()


def delete_object(key: str) -> None:
    get_s3().delete_object(Bucket=settings.s3_bucket, Key=key)


def object_exists(key: str) -> bool:
    try:
        get_s3().head_object(Bucket=settings.s3_bucket, Key=key)
        return True
    except ClientError:
        return False
