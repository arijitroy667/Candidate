from __future__ import annotations

from app.core.config import get_settings


def _client():
    settings = get_settings()
    from app.db.supabase import get_supabase_client

    client = get_supabase_client()
    if client is None:
        raise RuntimeError("Supabase service-role storage is not configured")
    return client.storage.from_(settings.supabase_storage_bucket)


def upload_bytes(storage_key: str, content: bytes, content_type: str) -> None:
    _client().upload(storage_key, content, {"content-type": content_type, "upsert": "true"})


def create_download_url(storage_key: str, expires_in: int = 600) -> str:
    result = _client().create_signed_url(storage_key, expires_in)
    if isinstance(result, dict):
        return result.get("signedURL") or result.get("signedUrl") or ""
    return getattr(result, "signedURL", None) or getattr(result, "signedUrl", "")


def download_bytes(storage_key: str) -> bytes:
    return _client().download(storage_key)
