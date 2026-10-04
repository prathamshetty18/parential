from typing import Dict
import uuid
from fastapi import WebSocket


class DeviceWebSocketManager:
    def __init__(self):
        self.active_connections: Dict[uuid.UUID, WebSocket] = {}

    async def connect(self, device_id: uuid.UUID, websocket: WebSocket):
        self.active_connections[device_id] = websocket

    def disconnect(self, device_id: uuid.UUID):
        if device_id in self.active_connections:
            del self.active_connections[device_id]

    async def send_controls(self, device_id: uuid.UUID, payload: dict):
        websocket = self.active_connections.get(device_id)
        if websocket:
            try:
                await websocket.send_json(payload)
            except Exception:
                self.disconnect(device_id)


device_ws_manager = DeviceWebSocketManager()
