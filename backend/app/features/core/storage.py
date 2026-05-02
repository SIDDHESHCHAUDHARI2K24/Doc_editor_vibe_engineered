"""S3-compatible object storage helpers using aioboto3."""

from contextlib import asynccontextmanager
from typing import Any

import aioboto3

from app.features.core.settings import get_settings

settings = get_settings()


def _build_client_kwargs() -> dict[str, Any]:
    return {
        "service_name": "s3",
        "endpoint_url": settings.s3_endpoint_url,
        "aws_access_key_id": settings.s3_access_key,
        "aws_secret_access_key": settings.s3_secret_key.get_secret_value(),
        "region_name": settings.s3_region,
        "config": None,
    }


@asynccontextmanager
async def get_s3_client():
    """Async context manager that yields an S3-compatible client."""
    kwargs = _build_client_kwargs()
    session = aioboto3.Session()
    async with session.client(**kwargs) as client:
        yield client


async def put_object(bucket: str, key: str, body: bytes, content_type: str = "application/octet-stream") -> None:
    """Upload an object to the configured S3 storage."""
    async with get_s3_client() as client:
        if settings.s3_addressing_style == "path":
            await client.put_object(Bucket=bucket, Key=key, Body=body, ContentType=content_type)
        else:
            await client.put_object(Bucket=bucket, Key=key, Body=body, ContentType=content_type)


async def get_object(bucket: str, key: str) -> bytes:
    """Download an object from S3 storage."""
    async with get_s3_client() as client:
        response = await client.get_object(Bucket=bucket, Key=key)
        body = await response["Body"].read()
        return body


async def generate_presigned_put(bucket: str, key: str, content_type: str, expires_in: int = 3600) -> str:
    """Generate a presigned URL for uploading an object."""
    async with get_s3_client() as client:
        url = await client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires_in,
        )
        return url


async def generate_presigned_get(bucket: str, key: str, expires_in: int = 3600) -> str:
    """Generate a presigned URL for downloading an object."""
    async with get_s3_client() as client:
        url = await client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": bucket,
                "Key": key,
            },
            ExpiresIn=expires_in,
        )
        return url
