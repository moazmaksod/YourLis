import multiprocessing
import asyncio
import time
import httpx
from setting.config import get_config, save_config, pre_startup_check
from gui.main_flet import main as flet_main
from gui.api_methods import start_server as cbc_start_server
from log.logger import log_info, log_error
import flet as ft


def generate_dynamic_port(api_ip):
    """
    Bind to an available port and return it for FastAPI server use.
    """
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((api_ip, 0))
        _, port = s.getsockname()
    return port


def run_fastapi(api_ip, port):
    """
    Start the FastAPI server on the given IP and port.
    """
    import uvicorn
    from api.app import app

    uvicorn.run(app, host=api_ip, port=port, log_config=None)


def run_flet():
    """
    Start the Flet GUI application.
    """
    ft.app(target=flet_main, assets_dir="assets")


def wait_for_fastapi_server(api_ip, port, timeout=15, interval=0.5):
    """
    Wait until the FastAPI server is available at /server/status.
    Returns True if available, False if timeout is reached.
    """
    status_url = f"http://{api_ip}:{port}/server/status"
    log_info(f"Waiting for FastAPI server at {status_url} to become available...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            resp = httpx.get(status_url)
            if resp.status_code == 200:
                log_info(f"FastAPI server is available at {status_url}.")
                return True
        except Exception as e:
            log_info(f"FastAPI server not available yet: {e}")
        time.sleep(interval)
    log_error(
        f"FastAPI server did not become available at {status_url} within {timeout} seconds."
    )
    return False


def patch_api_methods_base_url(api_ip, port):
    """
    Patch gui.api_methods.api_base_url to use the correct dynamic port.
    """
    import gui.api_methods as api_methods

    api_methods.api_base_url = f"http://{api_ip}:{port}"
    return api_methods.start_server


from setting.user_manager import ensure_initial_user

def main():
    # Ensure required folders exist
    import os

    # Ensure user setup on first run
    ensure_initial_user()

    for folder in ["assets", "setting"]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Load config and pre-startup checks
    cfg = get_config()
    api_ip = cfg["API_IP"]
    pre_startup_check()

    # Dynamically assign a port for FastAPI
    port = generate_dynamic_port(api_ip)

    # Save the dynamic port to config for reference BEFORE any API calls
    save_config({"API_PORT": port})

    # Start Flet GUI in a separate process
    flet_process = multiprocessing.Process(target=run_flet)
    flet_process.start()

    # Start FastAPI server in a separate process
    fastapi_process = multiprocessing.Process(target=run_fastapi, args=(api_ip, port))
    fastapi_process.start()

    # Wait for FastAPI server to be ready, then start CBC server if enabled
    if cfg.get("AUTO_START_CBC_SERVER", True):
        if wait_for_fastapi_server(api_ip, port):
            try:
                log_info(
                    "Attempting to auto start CBC server (calling start_server)..."
                )
                cbc_start_server_dynamic = patch_api_methods_base_url(api_ip, port)
                result = asyncio.run(cbc_start_server_dynamic())
                log_info(f"CBC server start_server() result: {result}")
            except Exception as e:
                log_error(f"Failed to auto start CBC server: {e}")
        else:
            log_error(
                "CBC server not started because FastAPI server was not available."
            )

    # Wait for the Flet GUI process to finish
    try:
        flet_process.join()
    except KeyboardInterrupt:
        log_info("Shutting down...")

    # Terminate FastAPI process on exit
    fastapi_process.terminate()
    fastapi_process.join()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    multiprocessing.set_start_method("spawn")
    main()
