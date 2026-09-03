from app.db.session import SessionLocal
from app.db.supabase import get_supabase_auth_client, get_supabase_client
from app.models.domain import User


def create_test_user(email: str, password: str, full_name: str, role: str) -> dict:
    admin = get_supabase_client()
    auth = get_supabase_auth_client()
    if admin is None or auth is None:
        raise RuntimeError("Supabase clients are not configured")
    try:
        created = admin.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"full_name": full_name, "role": role},
        })
        auth_user = created.user
    except Exception:
        existing = auth.auth.sign_in_with_password({"email": email, "password": password})
        auth_user = existing.user
    with SessionLocal() as db:
        user = db.get(User, str(auth_user.id))
        if not user:
            db.add(User(id=str(auth_user.id), email=email, full_name=full_name, role=role))
            db.commit()
    session = auth.auth.sign_in_with_password({"email": email, "password": password})
    return {"user": {"id": str(auth_user.id)}, "access_token": session.session.access_token}
