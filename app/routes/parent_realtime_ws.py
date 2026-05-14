"""Authenticated WebSocket for parent real-time notifications.

Connect from the browser (parent session only)::

    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${proto}//${host}/api/v1/ws/parent-notifications?token=${accessToken}`);

After ``Notification.requestPermission()`` is ``granted``, on each message::

    const msg = JSON.parse(event.data);
    if (document.hidden && Notification.permission === 'granted') {
      new Notification(msg.title, { body: msg.body, data: msg.data });
    }

Message ``type`` values: ``lacking_alert``, ``child_game_completed``, ``daily_checkin_reminder``.
"""

import logging

from fastapi import APIRouter, Query, WebSocket
from jose import JWTError, jwt
from starlette.websockets import WebSocketDisconnect

from app.core.config import settings
from app.db.models.user import User
from app.db.session import SessionLocal
from app.services.parent_realtime import parent_realtime_hub

router = APIRouter(tags=["parent-realtime"])
logger = logging.getLogger(__name__)


@router.websocket("/ws/parent-notifications")
async def parent_notifications_ws(
    websocket: WebSocket,
    token: str | None = Query(None),
):
    if not token:
        await websocket.close(code=1008)
        return
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        raw_sub = payload.get("sub")
        if raw_sub is None:
            raise JWTError("missing sub")
        user_id = int(raw_sub)
    except (JWTError, ValueError, TypeError):
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None or user.user_type != "parent":
            await websocket.close(code=1008)
            return
    finally:
        db.close()

    await parent_realtime_hub.connect(user_id, websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            if msg.strip().lower() in ("ping", '{"type":"ping"}'):
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.debug("Parent websocket disconnected user_id=%s", user_id)
    finally:
        await parent_realtime_hub.disconnect(user_id, websocket)
