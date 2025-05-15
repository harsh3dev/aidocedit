from fastapi import WebSocket
from typing import Dict

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, doc_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[doc_id] = websocket

    def disconnect(self, doc_id: str):
        self.active_connections.pop(doc_id, None)

    async def send_to_client(self, doc_id: str, data: str):
        if doc_id in self.active_connections:
            await self.active_connections[doc_id].send_text(data)

ws_manager = ConnectionManager()
