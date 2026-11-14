import httpx
from setting.config import get_config, get_api_token
from log.logger import log_info, log_error

api_base_url = None
_client = None

def get_api_base_url():
    cfg = get_config()
    api_port = cfg["API_PORT"]
    api_ip = cfg["API_IP"]
    url = f"http://{api_ip}:{api_port}"
    return url

def get_ws_base_url():
    cfg = get_config()
    api_port = cfg["API_PORT"]
    api_ip = cfg["API_IP"]
    token = get_api_token()
    url = f"ws://{api_ip}:{api_port}/ws?token={token}"
    return url

def test_db_connection_api(db_params: dict = None) -> bool:
    """
    Validates database connection parameters through the service/persistence boundary.
    """
    from database.sqlconnection import test_db_connection
    if db_params is None:
        cfg = get_config()
        db_params = cfg
    try:
        return test_db_connection(db_params)
    except Exception:
        return False

def get_client():
    global _client
    token = get_api_token()
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(headers={"X-Internal-Token": token})
    return _client


async def fetch_server_status():
    """
    Fetch server status from the FastAPI API.
    """
    url = f"{get_api_base_url()}/server/status"
    try:
        client = get_client()
        response = await client.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "state": "Error",
                "text": "Failed to fetch server status",
                "clients": {},
            }
    except Exception as e:
        log_error(f"[API_METHODS] Exception in fetch_server_status: {e}")
        return {"state": "Error", "text": str(e), "clients": {}}


async def fetch_communication_messages():
    """
    Fetch communication messages from the FastAPI API.
    """
    url = f"{get_api_base_url()}/server/messages"
    try:
        client = get_client()
        response = await client.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return []
    except Exception as e:
        log_error(f"[API_METHODS] Exception in fetch_communication_messages: {e}")
        return []


async def toggle_server_state(current_state):
    """
    Start or stop the server using the FastAPI API.
    """
    endpoint = "/server/start" if current_state == "Offline" else "/server/stop"
    url = f"{get_api_base_url()}{endpoint}"
    log_info(f"[API_METHODS] POST {url}")
    try:
        client = get_client()
        response = await client.post(url)
        log_info(
            f"[API_METHODS] Response: status={response.status_code}, body={response.text}"
        )
        return response.json()
    except Exception as e:
        log_error(f"[API_METHODS] Exception in toggle_server_state: {e}")
        return {"message": str(e)}


async def stop_server():
    """
    Stop the server using the FastAPI API.
    """
    endpoint = "/server/stop"
    url = f"{get_api_base_url()}{endpoint}"
    log_info(f"[API_METHODS] POST {url}")
    try:
        client = get_client()
        response = await client.post(url)
        log_info(
            f"[API_METHODS] Response: status={response.status_code}, body={response.text}"
        )
        return response.json()

    except Exception as e:
        log_error(f"[API_METHODS] Exception in stop_server: {e}")
        return {"message": str(e)}


from log.logger import log_info, log_error


async def start_server():
    """
    Start the CBC server using the FastAPI API.
    """
    endpoint = "/server/start"
    url = f"{get_api_base_url()}{endpoint}"
    log_info(f"[API_METHODS] POST {url} to start CBC server...")
    try:
        client = get_client()
        response = await client.post(url)
        log_info(
            f"[API_METHODS] CBC server /server/start response: status={response.status_code}, body={response.text}"
        )
        return response.json()

    except Exception as e:
        log_error(f"[API_METHODS] Exception in start_server: {e}")
        return {"message": str(e)}

async def fetch_patients_api(
    patient_id=None,
    patient_name=None,
    start_date=None,
    end_date=None,
    result_finished=None,
):
    """
    Fetch patients list through the API layer with database fallback.
    """
    url = f"{get_api_base_url()}/api/v1/patients"
    params = {}
    if patient_id:
        params["id"] = patient_id
    if patient_name:
        params["name"] = patient_name
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if result_finished is not None:
        params["result_finished"] = result_finished

    try:
        client = get_client()
        response = await client.get(url, params=params, timeout=5.0)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        log_info(f"[API_METHODS] API unavailable ({e}), falling back to direct service execution.")

    # Graceful fallback to direct DB execution
    from database.sqlqueries import exec_procedure_for
    from database.sqldbdictionary import PATIENT_SEARCH_SQL

    db_params = {
        "PATIENT_ID": patient_id or None,
        "PATIENT_NAME": patient_name or None,
        "START_DATE": start_date or None,
        "END_DATE": end_date or None,
        "RESULT_FINISHED": result_finished,
    }
    return await exec_procedure_for(PATIENT_SEARCH_SQL, db_params) or []


async def fetch_patient_cbc_api(patient_id: str):
    """
    Fetch patient CBC result through the API layer with database fallback.
    """
    url = f"{get_api_base_url()}/api/v1/patients/{patient_id}/cbc"
    try:
        client = get_client()
        response = await client.get(url, timeout=5.0)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        log_info(f"[API_METHODS] API unavailable ({e}), falling back to direct service execution.")

    from database.sqlqueries import exec_procedure_for
    from database.sqldbdictionary import PATIENT_CBC_RESULT_SQL

    db_params = {"PATIENT_ID": patient_id or None}
    return await exec_procedure_for(PATIENT_CBC_RESULT_SQL, db_params) or []


async def fetch_send_out_api(
    patient_id=None,
    patient_name=None,
    destination_lab=None,
    start_date=None,
    end_date=None,
    status=None,
):
    """
    Fetch send-out samples through the API layer with database fallback.
    """
    url = f"{get_api_base_url()}/api/v1/send-out"
    params = {}
    if patient_id:
        params["patient_id"] = patient_id
    if patient_name:
        params["patient_name"] = patient_name
    if destination_lab:
        params["destination_lab"] = destination_lab
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if status:
        params["status"] = status

    try:
        client = get_client()
        response = await client.get(url, params=params, timeout=5.0)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        log_info(f"[API_METHODS] API unavailable ({e}), falling back to direct service execution.")

    from database.sqlqueries import exec_procedure_for
    from database.sqldbdictionary import SEND_OUT_SEARCH_SQL

    db_params = {
        "PatientID": patient_id or None,
        "PatientName": patient_name or None,
        "DestinationLab": destination_lab or None,
        "StartDate": start_date or None,
        "EndDate": end_date or None,
        "Status": status or None,
    }
    return await exec_procedure_for(SEND_OUT_SEARCH_SQL, db_params) or []


async def fetch_destination_labs_api():
    """
    Fetch destination labs list through the API layer with database fallback.
    """
    url = f"{get_api_base_url()}/api/v1/send-out/destinations"
    try:
        client = get_client()
        response = await client.get(url, timeout=5.0)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        log_info(f"[API_METHODS] API unavailable ({e}), falling back to direct service execution.")

    from database.sqlqueries import exec_procedure_for
    from database.sqldbdictionary import GET_DESTINATION_LABS_SQL

    return await exec_procedure_for(GET_DESTINATION_LABS_SQL, {}) or []


async def update_send_out_financials_api(
    patient_id: str,
    test_name: str,
    price: float,
    amount_paid: float,
    destination_lab: str = "",
    status: str = "Pending",
    edit_date: str = None,
):
    """
    Update send-out sample financials through the API layer with database fallback.
    """
    url = f"{get_api_base_url()}/api/v1/send-out/financials"
    payload = {
        "patient_id": str(patient_id),
        "test_name": str(test_name),
        "price": float(price),
        "amount_paid": float(amount_paid),
        "destination_lab": str(destination_lab or ""),
        "status": str(status or "Pending"),
        "edit_date": edit_date,
    }
    try:
        client = get_client()
        response = await client.post(url, json=payload, timeout=5.0)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        log_info(f"[API_METHODS] API unavailable ({e}), falling back to direct service execution.")

    import datetime
    from database.sqlqueries import exec_procedure_no_return
    from database.sqldbdictionary import UPDATE_SEND_OUT_FINANCIALS_SQL

    params = {
        "PatientID": patient_id,
        "TestName": test_name,
        "Price": price,
        "AmountPaid": amount_paid,
        "DestinationLab": destination_lab,
        "EditDate": edit_date or datetime.datetime.now().strftime("%d-%b-%Y %I:%M %p"),
        "Status": status,
    }
    await exec_procedure_no_return(UPDATE_SEND_OUT_FINANCIALS_SQL, params)
    return {"status": "success", "message": "Financials updated"}


async def mark_send_out_sent_api(patient_id: str, test_name: str, sent_date=None):
    """
    Mark send-out sample as sent through the API layer with database fallback.
    """
    url = f"{get_api_base_url()}/api/v1/send-out/sent"
    payload = {
        "patient_id": str(patient_id),
        "test_name": str(test_name),
        "sent_date": str(sent_date) if sent_date else None,
    }
    try:
        client = get_client()
        response = await client.post(url, json=payload, timeout=5.0)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        log_info(f"[API_METHODS] API unavailable ({e}), falling back to direct service execution.")

    import datetime
    from database.sqlqueries import exec_procedure_no_return
    from database.sqldbdictionary import INSERT_SEND_OUT_LOG_SQL

    params = {
        "PatientID": patient_id,
        "TestName": test_name,
        "SentDate": sent_date or datetime.datetime.now(),
    }
    await exec_procedure_no_return(INSERT_SEND_OUT_LOG_SQL, params)
    return {"status": "success", "message": "Marked as sent"}


async def listen_to_updates(on_status_update, on_message_update):
    """
    Listen to real-time updates from the FastAPI server via WebSocket.
    """
    import websockets
    import json
    import asyncio

    import re

    ws_url = get_ws_base_url()
    sanitized_ws_url = re.sub(r'(token=)[^&]+', r'\1********', ws_url)
    log_info(f"[API_METHODS] Connecting to WebSocket: {sanitized_ws_url}")
    
    while True:
        try:
            async with websockets.connect(ws_url) as websocket:
                log_info("[API_METHODS] WebSocket connected.")
                while True:
                    message_raw = await websocket.recv()
                    data = json.loads(message_raw)
                    msg_type = data.get("type")
                    msg_data = data.get("data")
                    
                    
                    if msg_type == "status":
                        log_info(f"[WebSocket] Received status update: {msg_data.get('clients', 'No Clients Key')}")
                        await on_status_update(msg_data)
                    elif msg_type == "messages":
                        log_info(f"[WebSocket] Received message update: {len(msg_data)} messages")
                        await on_message_update(msg_data)
        except Exception as e:
            log_error(f"[API_METHODS] WebSocket error: {e}. Retrying in 5s...")
            await asyncio.sleep(5)
