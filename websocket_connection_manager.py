from collections import defaultdict
from fastapi import WebSocket
class WSConnectionManager:
    instance = None
    def __init__(self):
        self.active_connections = defaultdict(list)

    async def connect(self, websocket: WebSocket, channel_id: str):
        await websocket.accept()
        self.active_connections[channel_id].append(websocket)

    def disconnect(self, websocket, channel_id: str):
        self.active_connections[channel_id].remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: str, channel_id: str, exclude: list[WebSocket] = []):
        for connection in self.active_connections[channel_id]:
            if connection in exclude: continue
            await connection.send_json(message)
    
    @staticmethod
    def get_instance():
        if WSConnectionManager.instance is None:
            WSConnectionManager.instance = WSConnectionManager()
        return WSConnectionManager.instance