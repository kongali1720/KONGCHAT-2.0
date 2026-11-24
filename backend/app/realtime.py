from collections import defaultdict

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: dict[int, set[WebSocket]] = defaultdict(set)

    def connect(self, conversation_id: int, websocket: WebSocket):
        self.connections[conversation_id].add(websocket)

    def disconnect(self, conversation_id: int, websocket: WebSocket):
        room = self.connections.get(conversation_id)

        if room is None:
            return

        room.discard(websocket)

        if not room:
            self.connections.pop(conversation_id, None)

    async def broadcast(self, conversation_id: int, payload: dict):
        room = self.connections.get(conversation_id, set())
        dead_connections = []

        for websocket in list(room):
            try:
                await websocket.send_json(payload)
            except Exception:
                dead_connections.append(websocket)

        for websocket in dead_connections:
            self.disconnect(conversation_id, websocket)


manager = ConnectionManager()
