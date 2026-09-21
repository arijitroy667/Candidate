from __future__ import annotations

from io import BytesIO

from app.core.config import get_settings


def _client():
    import boto3

    settings = get_settings()
    if not settings.s3_bucket or not settings.aws_region:
        raise RuntimeError("S3_BUCKET and AWS_REGION must be configured")
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        endpoint_url=settings.s3_endpoint_url or None,
        aws_access_key_id=settings.aws_access_key_id or None,
        aws_secret_access_key=settings.aws_secret_access_key or None,
    )


def upload_bytes(storage_key: str, content: bytes, content_type: str) -> None:
    settings = get_settings()
    _client().upload_fileobj(BytesIO(content), settings.s3_bucket, storage_key, ExtraArgs={"ContentType": content_type, "ServerSideEncryption": "AES256"})


def create_download_url(storage_key: str, expires_in: int = 600) -> str:
    settings = get_settings()
    return _client().generate_presigned_url("get_object", Params={"Bucket": settings.s3_bucket, "Key": storage_key}, ExpiresIn=expires_in)


def download_bytes(storage_key: str) -> bytes:
    settings = get_settings()
    response = _client().get_object(Bucket=settings.s3_bucket, Key=storage_key)
    return response["Body"].read()
