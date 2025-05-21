import uvicorn
import socket
from setting.config import get_config, save_config
import multiprocessing
from gui.main_flet import main as flet_main
from log.logger import log_info, log_error
import flet as ft

cfg = get_config()  # Load configuration from file
api_ip = cfg["API_IP"]


def generate_dynamic_port():
    """
    Generate a dynamic port and save it in the config.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((api_ip, 0))  # Bind to an available port
        _, port = s.getsockname()  # Get the dynamically assigned port

    return port


def run_fastapi(port):
    """
    Run FastAPI server on the dynamically generated port.
    """

    # Start the FastAPI server on the assigned port
    uvicorn.run("api.app:app", host=api_ip, port=port)


def run_flet():
    """
    Run Flet application.
    """
    

    ft.app(target=flet_main, assets_dir="assets")


def main():

    port = generate_dynamic_port()  # Generate a dynamic port

    # Create separate processes for Flet
    flet_process = multiprocessing.Process(target=run_flet)
    # Start Flet process
    flet_process.start()

    # Create separate processes for FastAPI
    fastapi_process = multiprocessing.Process(target=run_fastapi, args=(port,))
    # # Start FastAPI process
    fastapi_process.start()

    # Wait for FastAPI process to finish
    save_config({"API_PORT": port})  # Save the port in the configuration file

    try:
        # Wait for Flet process to finish
        flet_process.join()
    except KeyboardInterrupt:
        log_info("Shutting down...")

    # Terminate FastAPI process on exit
    fastapi_process.terminate()
    fastapi_process.join()


if __name__ == "__main__":

    main()
