from fastapi import FastAPI
from pydantic import BaseModel
from server.server import start_server, stop_server, is_server_running
from server.client_handler import clients_with_names


app = FastAPI()



# API Models
class ServerStatus(BaseModel):
    state: str
    text: str
    clients: dict

# Endpoint to get server status
@app.get("/server/status", response_model=ServerStatus)
async def get_server_status():

    state = "Online" if is_server_running() else "Offline"
    text = "Server is running" if state == "Online" else "Server is offline"
    clients = clients_with_names
    return ServerStatus(state=state, text=text, clients=clients)

# Endpoint to start the server
@app.post("/server/start")
async def start_server_api():
    await start_server()  # Start the server
    return {"message": "Server started successfully."}

# Endpoint to stop the server
@app.post("/server/stop")
async def stop_server_api():
    await stop_server()  # Stop the server
    return {"message": "Server stopped successfully."}

