import httpx
from setting.config import get_config
from log.logger import log_info, log_error

def get_api_base_url():
    cfg = get_config()
    api_port = cfg['API_PORT']
    api_ip = cfg['API_IP']
    url = f"http://{api_ip}:{api_port}"
    log_info(f"[API_METHODS] Using api_base_url: {url}")
    return url


async def fetch_server_status():
    """
    Fetch server status from the FastAPI API.
    """
    url = f"{get_api_base_url()}/server/status"
    log_info(f"[API_METHODS] GET {url}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            log_info(f"[API_METHODS] Response: status={response.status_code}, body={response.text}")
            if response.status_code == 200:
                return response.json()
            else:
                return {"state": "Error", "text": "Failed to fetch server status", "clients": {}}
    except Exception as e:
        log_error(f"[API_METHODS] Exception in fetch_server_status: {e}")
        return {"state": "Error", "text": str(e), "clients": {}}


async def fetch_communication_messages():
    """
    Fetch communication messages from the FastAPI API.
    """
    url = f"{get_api_base_url()}/server/messages"
    log_info(f"[API_METHODS] GET {url}")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            log_info(f"[API_METHODS] Response: status={response.status_code}, body={response.text}")
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
        async with httpx.AsyncClient() as client:
            response = await client.post(url)
            log_info(f"[API_METHODS] Response: status={response.status_code}, body={response.text}")
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
        async with httpx.AsyncClient() as client:
            response = await client.post(url)
            log_info(f"[API_METHODS] Response: status={response.status_code}, body={response.text}")
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
        async with httpx.AsyncClient() as client:
            response = await client.post(url)
            log_info(f"[API_METHODS] CBC server /server/start response: status={response.status_code}, body={response.text}")
            return response.json()
        
    except Exception as e:
        log_error(f"[API_METHODS] Exception in start_server: {e}")
        return {"message": str(e)}