"""Real-time notifications for parents via WebSocket (browser tab / Notification API).

Events are JSON messages pushed when the parent has an open WebSocket connection.
The frontend should request Notification permission and call ``new Notification(...)``
when the tab is in the background, similar to WhatsApp Web.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.db.models.child import Child

logger = logging.getLogger(__name__)

_main_loop: Optional[asyncio.AbstractEventLoop] = None

# In-memory feed for GET /parent/notifications (production: use a DB table)
_feed_lock = threading.Lock()
_parent_notification_feed: List[Dict[str, Any]] = []
_MAX_FEED_LEN = 2000

GAME_LABELS = {
    "mood": "Mood game",
    "scenario": "Scenario game",
    "islamic_quiz": "Islamic quiz",
    "memory": "Memory game",
}


def set_parent_realtime_loop(loop: Optional[asyncio.AbstractEventLoop]) -> None:
    """Register the ASGI event loop (call from application lifespan)."""
    global _main_loop
    _main_loop = loop


class ParentRealtimeHub:
    """One or more browser tabs per parent user id."""

    def __init__(self) -> None:
        self._connections: Dict[int, List[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, parent_user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(parent_user_id, []).append(websocket)

    async def disconnect(self, parent_user_id: int, websocket: WebSocket) -> None:
        async with self._lock:
            conns = self._connections.get(parent_user_id)
            if not conns:
                return
            if websocket in conns:
                conns.remove(websocket)
            if not conns:
                del self._connections[parent_user_id]

    async def send_json_to_parent(self, parent_user_id: int, message: Dict[str, Any]) -> None:
        async with self._lock:
            sockets = list(self._connections.get(parent_user_id, ()))
        if not sockets:
            return
        text = json.dumps(message, default=str)
        stale: List[WebSocket] = []
        for ws in sockets:
            try:
                await ws.send_text(text)
            except Exception as exc:  # pragma: no cover - network
                logger.debug("Dropping stale parent websocket: %s", exc)
                stale.append(ws)
        if stale:
            async with self._lock:
                conns = self._connections.get(parent_user_id)
                if conns:
                    for ws in stale:
                        if ws in conns:
                            conns.remove(ws)
                    if not conns:
                        del self._connections[parent_user_id]


parent_realtime_hub = ParentRealtimeHub()


def _append_parent_notification_feed(
    parent_user_id: int,
    message: Dict[str, Any],
    record_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Persist one row for HTTP list + include id on WebSocket payload."""
    rid = record_id or str(uuid.uuid4())
    entry: Dict[str, Any] = {
        "id": rid,
        "parent_user_id": parent_user_id,
        "type": message["type"],
        "title": message["title"],
        "body": message["body"],
        "data": message.get("data") or {},
        "created_at": message.get("created_at") or datetime.utcnow().isoformat(),
        "read": False,
    }
    with _feed_lock:
        _parent_notification_feed.append(entry)
        if len(_parent_notification_feed) > _MAX_FEED_LEN:
            del _parent_notification_feed[: len(_parent_notification_feed) - _MAX_FEED_LEN]
    return entry


def get_parent_notifications(
    parent_user_id: int,
    *,
    unread_only: bool = False,
    limit: int = 10,
) -> Dict[str, Any]:
    """Return notifications newest first."""
    with _feed_lock:
        mine = [dict(r) for r in _parent_notification_feed if r["parent_user_id"] == parent_user_id]
    total_count = len(mine)
    unread_count = sum(1 for r in mine if not r.get("read"))
    if unread_only:
        mine = [r for r in mine if not r.get("read")]
    mine.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    if limit > 0:
        mine = mine[:limit]
    return {
        "notifications": mine,
        "total_count": total_count,
        "unread_count": unread_count,
    }


def mark_parent_notification_read(parent_user_id: int, notification_id: str) -> bool:
    with _feed_lock:
        for row in _parent_notification_feed:
            if row["id"] == notification_id and row["parent_user_id"] == parent_user_id:
                row["read"] = True
                return True
    return False


def schedule_parent_realtime_message(
    parent_user_id: int,
    message: Dict[str, Any],
    *,
    record_id: Optional[str] = None,
) -> None:
    """Record for GET /parent/notifications and push to any open WebSockets."""
    entry = _append_parent_notification_feed(parent_user_id, message, record_id=record_id)
    outbound = {
        "id": entry["id"],
        "type": entry["type"],
        "title": entry["title"],
        "body": entry["body"],
        "data": entry["data"],
        "created_at": entry["created_at"],
    }
    if _main_loop is None:
        logger.debug("Parent realtime loop not configured; skipping WebSocket push")
        return

    def _log_err(fut: asyncio.Future) -> None:
        try:
            exc = fut.exception()
            if exc:
                logger.warning("Parent realtime delivery failed: %s", exc)
        except asyncio.CancelledError:
            pass

    fut = asyncio.run_coroutine_threadsafe(
        parent_realtime_hub.send_json_to_parent(parent_user_id, outbound),
        _main_loop,
    )
    fut.add_done_callback(_log_err)


def schedule_lacking_alert_realtime(child: Child, notification: Dict[str, Any]) -> None:
    """Push lacking-analyzer ticker to the child's parent."""
    message = {
        "type": "lacking_alert",
        "title": f"Parvarish — {child.name}",
        "body": notification.get("message") or "A new area may need your attention.",
        "data": notification,
        "created_at": datetime.utcnow().isoformat(),
    }
    schedule_parent_realtime_message(
        child.parent_id, message, record_id=notification.get("id")
    )


def notify_parent_child_game_completed(
    db: Session,
    child_id: int,
    game_type: str,
    score_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Notify parent when a child finishes a full game session (or memory submit)."""
    child = db.query(Child).filter(Child.id == child_id).first()
    if not child:
        return
    label = GAME_LABELS.get(game_type, game_type.replace("_", " ").title())
    pct: Optional[float] = None
    if score_data and isinstance(score_data.get("percentage"), (int, float)):
        pct = float(score_data["percentage"])
    if pct is not None:
        body = f"{child.name} finished {label} ({pct:.0f}%)."
    else:
        body = f"{child.name} finished {label}."
    message = {
        "type": "child_game_completed",
        "title": f"{child.name} played a game",
        "body": body,
        "data": {
            "child_id": child_id,
            "child_name": child.name,
            "game_type": game_type,
            "score": score_data,
        },
        "created_at": datetime.utcnow().isoformat(),
    }
    schedule_parent_realtime_message(child.parent_id, message)


def schedule_daily_checkin_reminder_realtime(
    parent_user_id: int,
    parent_name: Optional[str],
    children: List[Dict[str, Any]],
) -> None:
    """Web push companion to logged/email reminders."""
    names = ", ".join(c.get("child_name") or "child" for c in children)
    greeting = (parent_name or "Parent").strip() or "Parent"
    message = {
        "type": "daily_checkin_reminder",
        "title": "Daily behavior check-in",
        "body": f"{greeting}, please complete check-in for: {names}.",
        "data": {"children": children},
        "created_at": datetime.utcnow().isoformat(),
    }
    schedule_parent_realtime_message(parent_user_id, message)
