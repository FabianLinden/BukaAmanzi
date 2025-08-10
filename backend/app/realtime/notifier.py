from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, Set

from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect
import redis.asyncio as redis


class DataChangeNotifier:
    """Manages real-time notifications for data changes"""

    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, connection_id: str) -> None:
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        self.subscriptions[connection_id] = set()
        await self.redis_client.sadd("websocket_connections", connection_id)

    async def disconnect(self, connection_id: str) -> None:
        self.active_connections.pop(connection_id, None)
        self.subscriptions.pop(connection_id, None)
        await self.redis_client.srem("websocket_connections", connection_id)

    async def subscribe_to_entity(self, connection_id: str, entity_type: str, entity_id: str | None) -> None:
        if connection_id in self.subscriptions:
            if entity_type == "all":
                self.subscriptions[connection_id].add("all")
            elif entity_id:
                subscription_key = f"{entity_type}:{entity_id}"
                self.subscriptions[connection_id].add(subscription_key)

    async def notify_change(self, change: dict) -> None:
        notification = {
            "type": "data_update",
            "timestamp": change.get("timestamp", datetime.utcnow()).isoformat(),
            "data": change,
        }
        await self.redis_client.publish("project_changes", json.dumps(notification, default=str))
        await self.broadcast_to_subscribers(notification, change)

    async def broadcast_to_subscribers(self, notification: dict, change: dict) -> None:
        entity_key = f"{change.get('entity_type', 'project')}:{change.get('entity_id')}"
        disconnected: list[str] = []
        for connection_id, subscriptions in self.subscriptions.items():
            if entity_key in subscriptions or "all" in subscriptions:
                websocket = self.active_connections.get(connection_id)
                if websocket:
                    try:
                        await websocket.send_text(json.dumps(notification, default=str))
                    except WebSocketDisconnect:
                        disconnected.append(connection_id)
                    except Exception:
                        disconnected.append(connection_id)
        for connection_id in disconnected:
            await self.disconnect(connection_id)

    async def notify_system_error(self, error_type: str, message: str) -> None:
        notification = {
            "type": "system_error",
            "error_type": error_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(notification, default=str))
            except Exception:
                await self.disconnect(connection_id)
    
    async def notify_system_event(self, event_type: str, data: dict) -> None:
        """Notify about system events (scheduler start/stop, config changes, etc.)"""
        notification = {
            "type": "system_event",
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.redis_client.publish("system_notifications", json.dumps(notification, default=str))
        
        # Also send to all connected clients
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(notification, default=str))
            except Exception:
                await self.disconnect(connection_id)


class RedisPubSubListener:
    """Listens to Redis pub/sub for cross-instance notifications"""

    def __init__(self, redis_client: redis.Redis, notifier: DataChangeNotifier):
        self.redis_client = redis_client
        self.notifier = notifier

    async def start_listening(self) -> None:
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe("project_changes", "system_notifications")
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])  # type: ignore[arg-type]
                    await self.notifier.broadcast_to_subscribers(data, data.get("data", {}))
                except Exception:
                    # swallow errors to keep listener alive
                    pass

