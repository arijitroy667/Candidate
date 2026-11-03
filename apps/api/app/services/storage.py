from __future__ import annotations

from pathlib import Path

from app.core.config import get_settings


_LOCAL_STORAGE_ROOT = Path(__file__).resolve().parents[2] / "local-storage"


class StorageUnavailableError(RuntimeError):
    """A resume could not be read from or written to the configured store."""


def _local_path(storage_key: str) -> Path:
    root = _LOCAL_STORAGE_ROOT.resolve()
    path = (root / storage_key).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Invalid local storage key")
    return path


def _use_local_storage() -> bool:
    return get_settings().app_env.lower() in {"local", "development"}


def uses_local_storage() -> bool:
    return _use_local_storage()


def _client():
    settings = get_settings()
    if not settings.supabase_url:
        raise StorageUnavailableError("SUPABASE_URL is missing from the API environment")
    if not settings.supabase_service_role_key:
        raise StorageUnavailableError("SUPABASE_SERVICE_ROLE_KEY is missing from the API environment")
    if settings.supabase_service_role_key.startswith("sb_secret_"):
        raise StorageUnavailableError(
            "The API has a new-format Supabase secret key (sb_secret_...) in "
            "SUPABASE_SERVICE_ROLE_KEY. This Python Storage integration also needs a JWT-format "
            "legacy service_role key. In Supabase, copy the service_role key from Settings → API Keys → "
            "Legacy API keys, set it as SUPABASE_SERVICE_ROLE_KEY in Render, then redeploy."
        )

    from app.db.supabase import get_supabase_client

    client = get_supabase_client()
    if client is None:
        raise StorageUnavailableError("Supabase service-role storage is not configured")
    return client.storage.from_(settings.supabase_storage_bucket)


def upload_bytes(storage_key: str, content: bytes, content_type: str) -> None:
    if _use_local_storage():
        try:
            path = _local_path(storage_key)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        except OSError as error:
            raise StorageUnavailableError(
                f"Local resume storage could not write the file ({error}). Check that the project folder is writable."
            ) from error
        return
    try:
        _client().upload(storage_key, content, {"content-type": content_type, "upsert": "true"})
    except StorageUnavailableError:
        raise
    except Exception as error:
        bucket = get_settings().supabase_storage_bucket
        raise StorageUnavailableError(
            f"Supabase Storage could not save the resume in bucket '{bucket}'. Check that this bucket exists "
            "in the same Supabase project as SUPABASE_URL and that the Render service-role key is valid."
        ) from error


def create_download_url(storage_key: str, expires_in: int = 600) -> str:
    try:
        result = _client().create_signed_url(storage_key, expires_in)
    except StorageUnavailableError:
        raise
    except Exception as error:
        bucket = get_settings().supabase_storage_bucket
        raise StorageUnavailableError(
            f"Supabase Storage could not create a download link for bucket '{bucket}'. Check the bucket and service-role key."
        ) from error
    if isinstance(result, dict):
        return result.get("signedURL") or result.get("signedUrl") or ""
    return getattr(result, "signedURL", None) or getattr(result, "signedUrl", "")


def download_bytes(storage_key: str) -> bytes:
    if _use_local_storage():
        try:
            return _local_path(storage_key).read_bytes()
        except OSError as error:
            raise StorageUnavailableError("The locally stored resume file could not be read") from error
    try:
        return _client().download(storage_key)
    except StorageUnavailableError:
        raise
    except Exception as error:
        bucket = get_settings().supabase_storage_bucket
        raise StorageUnavailableError(
            f"Supabase Storage could not read the resume from bucket '{bucket}'. Check the bucket and service-role key."
        ) from error
