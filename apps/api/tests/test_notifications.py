import json
from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.notifications import mark_read, notification_payload


def test_notification_payload_decodes_event_data_and_mark_read() -> None:
    notification = SimpleNamespace(
        id="notification-1",
        user_id="user-1",
        event_type="CANDIDATE_APPLIED",
        channel="IN_APP",
        title="New candidate application",
        body="A candidate applied.",
        payload=json.dumps({"application_id": "application-1"}),
        is_read=False,
        read_at=None,
        created_at=datetime.now(timezone.utc),
    )

    mark_read(notification)
    result = notification_payload(notification)

    assert result["payload"] == {"application_id": "application-1"}
    assert result["is_read"] is True
    assert result["read_at"] is not None