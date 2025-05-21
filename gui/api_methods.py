import httpx
from setting.config import get_config

cfg = get_config() # Load configuration from file
api_port = cfg['API_PORT']
api_ip = cfg['API_IP']
api_base_url = f"http://{api_ip}:{api_port}"


async def fetch_server_status():
    """
    Fetch server status from the FastAPI API.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_base_url}/server/status")
            if response.status_code == 200:
                return response.json()
            else:
                return {"state": "Error", "text": "Failed to fetch server status", "clients": {}}
    except Exception as e:
        return {"state": "Error", "text": str(e), "clients": {}}



async def toggle_server_state(current_state):
    """
    Start or stop the server using the FastAPI API.
    """
    try:
        endpoint = "/server/start" if current_state == "Offline" else "/server/stop"
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{api_base_url}{endpoint}")
            return response.json()
    except Exception as e:
        return {"message": str(e)}


async def stop_server():
    """
    Start or stop the server using the FastAPI API.
    """
    try:
        endpoint = "/server/stop"
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{api_base_url}{endpoint}")
            return response.json()
        
    except Exception as e:
        return {"message": str(e)}
    
async def start_server():
    """
    Start or stop the server using the FastAPI API.
    """
    try:
        endpoint = "/server/start"
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{api_base_url}{endpoint}")
            return response.json()
        
    except Exception as e:
        return {"message": str(e)}