import asyncio
import secrets
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Header, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict
from server.server import start_server, stop_server, is_server_running
from server.client_handler import clients_with_names, get_communication_messages
from setting.config import get_api_token
from typing import List, Dict, Any, Optional
import datetime


# Background monitor to broadcast changes
async def monitor_changes():
    last_state = None
    last_clients = None
    last_message_count = 0
    
    while True:
        try:
            state = "Online" if is_server_running() else "Offline"
            clients = clients_with_names.copy()
            if len(clients) > 0:
                from log.logger import log_info
                log_info(f"[API] Monitor sees clients: {list(clients.keys())}")
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
                
        except asyncio.CancelledError:
            break
        except Exception as e:
            from log.logger import log_error
            log_error(f"[API] Error in monitor_changes: {e}")
            
        await asyncio.sleep(1) # Poll internal state once per second


@asynccontextmanager
async def lifespan(app: FastAPI):
    monitor_task = asyncio.create_task(monitor_changes())
    try:
        yield
    finally:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="HealthMesh LIS API", lifespan=lifespan)

# CORS Middleware with explicit trusted origins (Fetch / W3C compliant)
ALLOWED_ORIGINS = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


def verify_token(
    x_internal_token: Optional[str] = Header(None, alias="X-Internal-Token"),
    authorization: Optional[str] = Header(None),
):
    """Verifies that requests to sensitive clinical / control endpoints carry valid auth."""
    expected_token = get_api_token()
    token = x_internal_token
    if not token and authorization:
        if authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
        else:
            token = authorization.strip()

    if not token or not secrets.compare_digest(str(token), str(expected_token)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True


# API Models
class ServerStatus(BaseModel):
    state: str
    text: str
    clients: dict


class CommunicationMessage(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2024-01-01T12:00:00",
                "client_name": "Device1",
                "client_address": "Device_ip",
                "message": "Hello server",
                "direction": "device"
            }
        }
    )
    timestamp: str
    client_name: str = Field(..., description="Client identifier or name")
    client_address: str = Field(..., description="Client identifier or name")
    message: str = Field(..., description="Message content")
    direction: str = Field(..., description="Message direction (server/device/info/error)")


class SendOutFinancialsUpdate(BaseModel):
    patient_id: str
    test_name: str
    price: float
    amount_paid: float
    destination_lab: str = ""
    status: str = "Pending"
    edit_date: Optional[str] = None


class SendOutMarkSent(BaseModel):
    patient_id: str
    test_name: str
    sent_date: Optional[str] = None


# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for dead_conn in disconnected:
            if dead_conn in self.active_connections:
                self.active_connections.remove(dead_conn)


manager = ConnectionManager()


# Endpoint to get server status
@app.get("/server/status", response_model=ServerStatus)
async def get_server_status():
    state = "Online" if is_server_running() else "Offline"
    text = "Server is running" if state == "Online" else "Server is offline"
    clients = clients_with_names
    return ServerStatus(state=state, text=text, clients=clients)


# Endpoint to get communication messages (Protected)
@app.get("/server/messages", response_model=List[CommunicationMessage], dependencies=[Depends(verify_token)])
async def get_messages():
    messages = get_communication_messages()
    # Ensure all messages have valid client names
    for msg in messages:
        if msg["client_address"] is None:
            msg["client_address"] = "Unknown Client"
    return messages


# WebSocket endpoint (Protected via query param or header)
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
):
    expected_token = get_api_token()
    header_token = websocket.headers.get("x-internal-token")
    auth_token = token or header_token
    if not auth_token or not secrets.compare_digest(str(auth_token), str(expected_token)):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket)
    try:
        # Send initial status
        status_data = await get_server_status()
        await websocket.send_json({"type": "status", "data": status_data.model_dump()})
        
        while True:
            # Keep connection alive, can receive heartbeats here if needed
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Endpoint to start the server (Protected)
@app.post("/server/start", dependencies=[Depends(verify_token)])
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


# Endpoint to stop the server (Protected)
@app.post("/server/stop", dependencies=[Depends(verify_token)])
async def stop_server_api():
    await stop_server()  # Stop the server
    return {"message": "Server stopped successfully."}


# --- Domain Endpoints (Protected) ---

@app.get("/api/v1/patients", dependencies=[Depends(verify_token)])
async def get_patients(
    id: Optional[str] = None,
    name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    result_finished: Optional[int] = None,
):
    from database.sqlqueries import exec_procedure_for
    from database.sqldbdictionary import PATIENT_SEARCH_SQL

    if result_finished is None and status is not None:
        result_finished = {"Pending": 0, "Completed": 1}.get(status, None)

    params = {
        "PATIENT_ID": id.strip() if id else None,
        "PATIENT_NAME": name.strip() if name else None,
        "START_DATE": start_date or None,
        "END_DATE": end_date or None,
        "RESULT_FINISHED": result_finished,
    }
    results = await exec_procedure_for(PATIENT_SEARCH_SQL, params)
    return results or []


@app.get("/api/v1/patients/{patient_id}/cbc", dependencies=[Depends(verify_token)])
async def get_patient_cbc(patient_id: str):
    from database.sqlqueries import exec_procedure_for
    from database.sqldbdictionary import PATIENT_CBC_RESULT_SQL

    params = {"PATIENT_ID": patient_id or None}
    results = await exec_procedure_for(PATIENT_CBC_RESULT_SQL, params)
    return results or []


@app.get("/api/v1/send-out", dependencies=[Depends(verify_token)])
async def get_send_outs(
    patient_id: Optional[str] = None,
    patient_name: Optional[str] = None,
    destination_lab: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
):
    from database.sqlqueries import exec_procedure_for
    from database.sqldbdictionary import SEND_OUT_SEARCH_SQL

    params = {
        "PatientID": patient_id or None,
        "PatientName": patient_name or None,
        "DestinationLab": destination_lab or None,
        "StartDate": start_date or None,
        "EndDate": end_date or None,
        "Status": status or None,
    }
    results = await exec_procedure_for(SEND_OUT_SEARCH_SQL, params)
    return results or []


@app.get("/api/v1/send-out/destinations", dependencies=[Depends(verify_token)])
async def get_send_out_destinations():
    from database.sqlqueries import exec_procedure_for
    from database.sqldbdictionary import GET_DESTINATION_LABS_SQL

    results = await exec_procedure_for(GET_DESTINATION_LABS_SQL, {})
    return results or []


@app.post("/api/v1/send-out/financials", dependencies=[Depends(verify_token)])
async def update_send_out_financials(payload: SendOutFinancialsUpdate):
    from database.sqlqueries import exec_procedure_no_return
    from database.sqldbdictionary import UPDATE_SEND_OUT_FINANCIALS_SQL

    edit_date = payload.edit_date or datetime.datetime.now().strftime("%d-%b-%Y %I:%M %p")
    params = {
        "PatientID": payload.patient_id,
        "TestName": payload.test_name,
        "Price": payload.price,
        "AmountPaid": payload.amount_paid,
        "DestinationLab": payload.destination_lab,
        "EditDate": edit_date,
        "Status": payload.status,
    }
    await exec_procedure_no_return(UPDATE_SEND_OUT_FINANCIALS_SQL, params)
    return {"status": "success", "message": "Financials updated successfully"}


@app.post("/api/v1/send-out/sent", dependencies=[Depends(verify_token)])
async def mark_send_out_sent(payload: SendOutMarkSent):
    from database.sqlqueries import exec_procedure_no_return
    from database.sqldbdictionary import INSERT_SEND_OUT_LOG_SQL

    sent_date = payload.sent_date or datetime.datetime.now()
    params = {
        "PatientID": payload.patient_id,
        "TestName": payload.test_name,
        "SentDate": sent_date,
    }
    await exec_procedure_no_return(INSERT_SEND_OUT_LOG_SQL, params)
    return {"status": "success", "message": "Sample marked as sent successfully"}


