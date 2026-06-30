from typing import Any

from fastapi import WebSocket


class RealtimeConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        message = {"type": event_type, "payload": payload or {}}
        stale: list[WebSocket] = []
        for connection in list(self._connections):
            try:
                await connection.send_json(message)
            except RuntimeError:
                stale.append(connection)
        for connection in stale:
            self.disconnect(connection)


realtime_manager = RealtimeConnectionManager()
