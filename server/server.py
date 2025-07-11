import asyncio
from server.client_handler import handle_client_connection
from log.logger import log_info, log_error
from setting.config import get_config
import socket
from threading import Lock

# Define the source for logging purposes
SOURCE = "Server"






# Server state variables
server_running = False
server_tasks = []  # Track client tasks
stop_event = None  # Event to stop the server
status_lock = Lock()  # Thread-safe lock for server_running


def is_valid_ip(ip):
    """
    Validate if the provided IP address is valid.
    """
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


def is_server_running():
    """
    Safely check if the server is running.
    """
    with status_lock:
        return server_running


async def set_server_running(state):
    """
    Safely set the server running state.
    """
    global server_running
    with status_lock:
        server_running = state


async def run_server():
    """
    Starts the TCP server and manages incoming client connections.
    """
    cfg = get_config()  # Load configuration from file
    SERVER_HOST = cfg['SERVER_HOST']
    SERVER_PORT = cfg['SERVER_PORT']
    
    global stop_event, server_tasks

    if is_server_running():
        log_info("Server is already running", source=SOURCE)
        return

    # Create a new stop_event for the current event loop
    stop_event = asyncio.Event()

    # Validate the IP address and port
    if not is_valid_ip(SERVER_HOST):
        log_error(f"Invalid IP address: {SERVER_HOST}", source=SOURCE)
        return
    if not (1 <= SERVER_PORT <= 65535):
        log_error(f"Invalid port: {SERVER_PORT}. Port must be in the range 1–65535.", source=SOURCE)
        return


    await set_server_running(True)


    try:
        server = await asyncio.start_server(client_connected, SERVER_HOST, SERVER_PORT)
        log_info(f"Server started at {SERVER_HOST}:{SERVER_PORT}", source=SOURCE)

        async with server:
            await stop_event.wait()  # Wait for the stop event
            log_info("Server is shutting down...", source=SOURCE)

            # Cancel all client tasks
            for task in server_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            server.close()
            await server.wait_closed()
            log_info("Server has shut down gracefully.", source=SOURCE)



    except OSError as e:
        if e.errno == 98:  # Address already in use
            log_error(f"Port {SERVER_PORT} is busy.", source=SOURCE)
        elif e.errno == 99:  # Cannot assign requested address
            log_error(f"Invalid address or unavailable network: {SERVER_HOST}:{SERVER_PORT}", source=SOURCE)
        else:
            log_error(f"Unexpected error: {e}", source=SOURCE)
    except Exception as e:
        log_error(f"Unhandled error: {e}", source=SOURCE)
    finally:
        await set_server_running(False)



    await set_server_running(False)


async def client_connected(reader, writer):
    """
    Handles a new client connection and adds it to the server task list.
    """
    global server_tasks
    task = asyncio.create_task(handle_client_connection(reader, writer))
    server_tasks.append(task)

    try:
        await task
    except asyncio.CancelledError:
        log_info("Client connection forcibly closed.", source=SOURCE)
        writer.close()
        await writer.wait_closed()
    finally:
        server_tasks.remove(task)


async def start_server():
    # Start the server asynchronously in the background so the API endpoint can return immediately
    asyncio.create_task(run_server())


async def stop_server():
    global stop_event

    if stop_event:
        log_info("Stopping server...", source=SOURCE)
        stop_event.set()  # Set the stop event to signal shutdown
