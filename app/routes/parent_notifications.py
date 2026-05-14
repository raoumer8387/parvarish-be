"""Unified parent notification feed (lacking, games, check-in reminders)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user
from app.db.models.user import User
from app.schemas.parent_notifications import (
    MarkParentNotificationReadRequest,
    ParentNotificationListResponse,
)
from app.services.parent_realtime import (
    get_parent_notifications,
    mark_parent_notification_read,
)

router = APIRouter(prefix="/parent", tags=["parent-notifications"])


def _assert_parent(user: User) -> None:
    if user.user_type != "parent":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only parents can access notifications",
        )


@router.get("/notifications", response_model=ParentNotificationListResponse)
def list_all_notifications(
    unread_only: bool = False,
    limit: int = 10,
    user: User = Depends(get_current_user),
):
    """Latest notifications for the logged-in parent (newest first; default 10).

    Includes lacking alerts, child game completions, and daily check-in reminders.
    Same events as the WebSocket stream, with stable ``id`` for mark-read.
    Use ``limit`` (max 500) to fetch more.
    """
    _assert_parent(user)
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=422, detail="limit must be between 1 and 500")
    data = get_parent_notifications(
        user.id, unread_only=unread_only, limit=limit
    )
    for item in data["notifications"]:
        item.pop("parent_user_id", None)
    return data


@router.post("/notifications/mark-read")
def mark_notification_read(
    request: MarkParentNotificationReadRequest,
    user: User = Depends(get_current_user),
):
    _assert_parent(user)
    if mark_parent_notification_read(user.id, request.notification_id):
        return {"success": True, "message": "Notification marked as read"}
    raise HTTPException(status_code=404, detail="Notification not found")
