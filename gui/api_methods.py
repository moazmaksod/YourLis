import httpx
from setting.config import get_config
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
    url = f"ws://{api_ip}:{api_port}/ws"
    return url

def get_client():
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient()
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

async def listen_to_updates(on_status_update, on_message_update):
    """
    Listen to real-time updates from the FastAPI server via WebSocket.
    """
    import websockets
    import json
    import asyncio

    ws_url = get_ws_base_url()
    log_info(f"[API_METHODS] Connecting to WebSocket: {ws_url}")
    
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
                        await on_status_update(msg_data)
                    elif msg_type == "messages":
                        await on_message_update(msg_data)
        except Exception as e:
            log_error(f"[API_METHODS] WebSocket error: {e}. Retrying in 5s...")
            await asyncio.sleep(5)
