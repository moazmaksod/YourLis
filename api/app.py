from fastapi import FastAPI
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

