import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import CompanyMember, Notification


def create_notification(
    db: Session,
    user_id: str,
    event_type: str,
    title: str,
    body: str,
    payload: dict[str, Any] | None = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        event_type=event_type,
        title=title,
        body=body,
        payload=json.dumps(payload or {}),
    )
    db.add(notification)
    return notification


def notify_company(
    db: Session,
    company_id: str,
    event_type: str,
    title: str,
    body: str,
    payload: dict[str, Any] | None = None,
) -> None:
    member_ids = db.scalars(select(CompanyMember.user_id).where(CompanyMember.company_id == company_id)).all()
    for user_id in member_ids:
        create_notification(db, user_id, event_type, title, body, payload)


def notification_payload(notification: Notification) -> dict[str, Any]:
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "event_type": notification.event_type,
        "channel": notification.channel,
        "title": notification.title,
        "body": notification.body,
        "payload": json.loads(notification.payload),
        "is_read": notification.is_read,
        "read_at": notification.read_at,
        "created_at": notification.created_at,
    }


def mark_read(notification: Notification) -> None:
    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)