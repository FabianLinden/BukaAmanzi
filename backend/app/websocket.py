from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, WebSocket


def create_websocket_router() -> APIRouter:
    router = APIRouter()

    @router.websocket("/ws/projects")
    async def websocket_projects(websocket: WebSocket):
        # get notifier from app state created during startup
        notification_manager = websocket.app.state.notifier  # type: ignore[attr-defined]
        connection_id = str(uuid.uuid4())
        try:
            await notification_manager.connect(websocket, connection_id)
            while True:
                data = await websocket.receive_json()
                if data.get("action") == "subscribe":
                    entity_type = data.get("entity_type", "all")
                    entity_id = data.get("entity_id")
                    await notification_manager.subscribe_to_entity(connection_id, entity_type, entity_id)
                    await websocket.send_json(
                        {
                            "type": "subscription_confirmed",
                            "entity_type": entity_type,
                            "entity_id": entity_id,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
        except Exception:
            await notification_manager.disconnect(connection_id)

    @router.websocket("/ws/municipalities/{municipality_id}")
    async def websocket_municipality(websocket: WebSocket, municipality_id: str):
        notification_manager = websocket.app.state.notifier  # type: ignore[attr-defined]
        connection_id = str(uuid.uuid4())
        try:
            await notification_manager.connect(websocket, connection_id)
            await notification_manager.subscribe_to_entity(connection_id, "municipality", municipality_id)
            while True:
                await websocket.receive_text()
        except Exception:
            await notification_manager.disconnect(connection_id)

    return router

