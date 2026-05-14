"""Schemas for unified parent notification feed (HTTP + WebSocket)."""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class ParentNotificationItem(BaseModel):
    id: str
    type: str
    title: str
    body: str
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    read: bool


class ParentNotificationListResponse(BaseModel):
    notifications: List[ParentNotificationItem]
    total_count: int
    unread_count: int


class MarkParentNotificationReadRequest(BaseModel):
    notification_id: str
