import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from server.server import start_server, stop_server, is_server_running
from server.client_handler import clients_with_names, get_communication_messages
from typing import List, Dict


app = FastAPI()


# API Models
class ServerStatus(BaseModel):
    state: str
    text: str
    clients: dict

class CommunicationMessage(BaseModel):
    timestamp: str
    client_name: str = Field(..., description="Client identifier or name")
    client_address: str = Field(..., description="Client identifier or name")
    message: str = Field(..., description="Message content")
    direction: str = Field(..., description="Message direction (server/device/info/error)")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-01T12:00:00",
                "client_name": "Device1",
                "client_address": "Device_ip",
                "message": "Hello server",
                "direction": "device"
            }
        }

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection might be dead
                pass

manager = ConnectionManager()

# Endpoint to get server status
@app.get("/server/status", response_model=ServerStatus)
async def get_server_status():
    state = "Online" if is_server_running() else "Offline"
    text = "Server is running" if state == "Online" else "Server is offline"
    clients = clients_with_names
    return ServerStatus(state=state, text=text, clients=clients)

# Endpoint to get communication messages
@app.get("/server/messages", response_model=List[CommunicationMessage])
async def get_messages():
    messages = get_communication_messages()
    # Ensure all messages have valid client names
    for msg in messages:
        if msg["client_address"] is None:
            msg["client_address"] = "Unknown Client"
    return messages

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send initial status
        status = await get_server_status()
        await websocket.send_json({"type": "status", "data": status.model_dump()})
        
        while True:
            # Keep connection alive, can receive heartbeats here if needed
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background monitor to broadcast changes
async def monitor_changes():
    last_state = None
    last_clients = None
    last_message_count = 0
    
    while True:
        try:
            state = "Online" if is_server_running() else "Offline"
            clients = clients_with_names.copy()
            messages = get_communication_messages()
            message_count = len(messages)
            
            # Detect changes
            state_changed = state != last_state or clients != last_clients
            messages_changed = message_count > last_message_count
            
            if state_changed:
                text = "Server is running" if state == "Online" else "Server is offline"
                status_data = {"state": state, "text": text, "clients": clients}
                await manager.broadcast({"type": "status", "data": status_data})
                last_state = state
                last_clients = clients
                
            if messages_changed:
                # Send only new messages
                new_messages = messages[last_message_count:]
                for msg in new_messages:
                    if msg["client_address"] is None:
                        msg["client_address"] = "Unknown Client"
                await manager.broadcast({"type": "messages", "data": new_messages})
                last_message_count = message_count
                
        except Exception as e:
            from log.logger import log_error
            log_error(f"[API] Error in monitor_changes: {e}")
            
        await asyncio.sleep(1) # Poll internal state once per second

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(monitor_changes())

# Endpoint to start the server
@app.post("/server/start")
async def start_server_api():
    from log.logger import log_info, log_error
    try:
        log_info("[API] /server/start endpoint called. Attempting to start CBC server...")
        await start_server()  # Start the server
        log_info("[API] CBC server started successfully.")
        return {"message": "Server started successfully."}
    except Exception as e:
        log_error(f"[API] Exception in /server/start: {e}")
        return {"message": f"Failed to start server: {e}"}

# Endpoint to stop the server
@app.post("/server/stop")
async def stop_server_api():
    await stop_server()  # Stop the server
    return {"message": "Server stopped successfully."}

