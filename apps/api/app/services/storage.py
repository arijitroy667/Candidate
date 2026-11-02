from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings


_LOCAL_STORAGE_ROOT = Path(__file__).resolve().parents[2] / "local-storage"


def _local_path(storage_key: str) -> Path:
    root = _LOCAL_STORAGE_ROOT.resolve()
    path = (root / storage_key).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Invalid local storage key")
    return path


def _use_local_storage() -> bool:
    return get_settings().app_env.lower() in {"local", "development"}


def _client():
    settings = get_settings()
    from app.db.supabase import get_supabase_client

    client = get_supabase_client()
    if client is None:
        raise RuntimeError("Supabase service-role storage is not configured")
    return client.storage.from_(settings.supabase_storage_bucket)


def upload_bytes(storage_key: str, content: bytes, content_type: str) -> None:
    if _use_local_storage():
        path = _local_path(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return
    _client().upload(storage_key, content, {"content-type": content_type, "upsert": "true"})


def create_download_url(storage_key: str, expires_in: int = 600) -> str:
    result = _client().create_signed_url(storage_key, expires_in)
    if isinstance(result, dict):
        return result.get("signedURL") or result.get("signedUrl") or ""
    return getattr(result, "signedURL", None) or getattr(result, "signedUrl", "")


def download_bytes(storage_key: str) -> bytes:
    if _use_local_storage():
        return _local_path(storage_key).read_bytes()
    return _client().download(storage_key)
