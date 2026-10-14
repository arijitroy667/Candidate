from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.db.supabase import get_supabase_auth_client
from app.models.domain import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    token = credentials.credentials
    payload: dict[str, Any] = {}
    try:
        if not settings.supabase_jwt_secret:
            raise JWTError("local JWT verification is disabled")
        payload = jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], audience="authenticated")
        user_id = payload.get("sub")
    except JWTError:
        auth = get_supabase_auth_client()
        try:
            verified = auth.auth.get_user(token) if auth else None
            auth_user = verified.user if verified and verified.user else None
            user_id = str(auth_user.id) if auth_user else None
            if auth_user:
                payload = {
                    "email": getattr(auth_user, "email", None),
                    "user_metadata": getattr(auth_user, "user_metadata", {}) or {},
                }
        except Exception as error:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from error
    user = db.get(User, user_id) if user_id else None
    if not user and user_id:
        # Supabase Auth is the source of truth for identity. Provision the
        # application profile on first authenticated use so the frontend can
        # use Supabase Auth directly without a second registration flow.
        auth = get_supabase_auth_client()
        try:
            verified = auth.auth.get_user(token) if auth else None
            auth_user = verified.user if verified and verified.user else None
            if auth_user:
                payload["email"] = getattr(auth_user, "email", payload.get("email"))
                payload["user_metadata"] = getattr(auth_user, "user_metadata", {}) or payload.get("user_metadata", {})
        except Exception as error:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token") from error
        metadata = payload.get("user_metadata") or {}
        role = metadata.get("role", "CANDIDATE")
        if role not in {"COMPANY_ADMIN", "RECRUITER", "HIRING_MANAGER", "CANDIDATE"}:
            role = "CANDIDATE"
        user = User(
            id=str(user_id),
            email=str(payload.get("email") or "unknown@example.invalid"),
            full_name=str(metadata.get("full_name") or "Candidex user"),
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive or missing")
    return user


def require_roles(*roles: str):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return dependency
