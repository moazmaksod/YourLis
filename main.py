import multiprocessing
import asyncio
import time
import httpx
import socket
from setting.config import get_config, save_config, pre_startup_check, get_available_sql_drivers, validate_binding
from gui.main_flet import main as flet_main
from log.logger import log_info, log_error
import flet as ft
from database.db_schema import setup_database_schema


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


def database_startup_check():
    """
    Check DB connection and ensure required tables and stored procedures exist, creating them if missing.
    """
    try:
        setup_database_schema()
        return True
    except Exception as e:
        log_error(f"Database startup check failed: {e}")
        return False


def show_db_config_window():
    """
    Shows a Flet window to update database configuration.
    Returns 'retry' if the user saved new settings, or 'exit' if they cancelled.
    """
    result = {"action": "exit"}

    def config_app(page: ft.Page):
        page.title = "Database Configuration"
        page.window_width = 500
        page.window_height = 650
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.theme_mode = ft.ThemeMode.DARK

        cfg = get_config()
        
        # UI Elements
        host_input = ft.TextField(label="Database Host", value=cfg.get("DB_HOST", ""), width=400)
        port_input = ft.TextField(label="Database Port", value=str(cfg.get("DB_PORT", "")), width=400)
        name_input = ft.TextField(label="Database Name", value=cfg.get("DB_NAME", ""), width=400)
        user_input = ft.TextField(label="Database User", value=cfg.get("DB_USER", ""), width=400)
        pass_input = ft.TextField(label="Database Password", value=cfg.get("DB_PASSWORD", ""), password=True, can_reveal_password=True, width=400)
        
        drivers = get_available_sql_drivers()
        driver_dropdown = ft.Dropdown(
            label="SQL Driver",
            options=[ft.dropdown.Option(d) for d in drivers],
            value=cfg.get("DB_DRIVE", drivers[0] if drivers else ""),
            width=400
        )
        
        type_dropdown = ft.Dropdown(
            label="Connection Type",
            options=[ft.dropdown.Option("local"), ft.dropdown.Option("online")],
            value=cfg.get("DB_TYPE", "local"),
            width=400
        )

        def save_click(e):
            try:
                new_cfg = {
                    "DB_HOST": host_input.value,
                    "DB_PORT": int(port_input.value) if port_input.value else 1433,
                    "DB_NAME": name_input.value,
                    "DB_USER": user_input.value,
                    "DB_PASSWORD": pass_input.value,
                    "DB_DRIVE": driver_dropdown.value,
                    "DB_TYPE": type_dropdown.value,
                }
                save_config(new_cfg)
                result["action"] = "retry"
                page.window_close()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Error saving: {ex}"))
                page.snack_bar.open = True
                page.update()

        def cancel_click(e):
            result["action"] = "exit"
            page.window_close()

        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.icons.STORAGE, size=50, color=ft.colors.AMBER),
                        ft.Text("Database Connection Failed", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("Please verify and update your connection settings:", size=14),
                        host_input,
                        port_input,
                        name_input,
                        user_input,
                        pass_input,
                        driver_dropdown,
                        type_dropdown,
                        ft.Row(
                            [
                                ft.ElevatedButton("Save & Retry", on_click=save_click, icon=ft.icons.SAVE),
                                ft.TextButton("Cancel / Exit", on_click=cancel_click),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=20,
            )
        )
        page.update()

    ft.app(target=config_app)
    return result["action"]


def show_network_config_window(failed_ip=None):
    """
    Shows a Flet window to check/update network configuration (API_IP, SERVER_HOST).
    """
    result = {"action": "exit"}

    def config_app(page: ft.Page):
        page.title = "Network Configuration"
        page.window_width = 500
        page.window_height = 450
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        page.theme_mode = ft.ThemeMode.DARK

        cfg = get_config()
        
        # We focus on API_IP and SERVER_HOST
        api_ip_input = ft.TextField(label="API IP (FastAPI)", value=cfg.get("API_IP", "127.0.0.1"), width=400)
        server_host_input = ft.TextField(label="Server Host (CBC)", value=cfg.get("SERVER_HOST", "127.0.0.1"), width=400)
        
        # Helper to get local IPs
        hostname = socket.gethostname()
        local_ips = socket.gethostbyname_ex(hostname)[2]
        # Always include localhost
        if "127.0.0.1" not in local_ips:
            local_ips.insert(0, "127.0.0.1")
            
        ip_suggestions = ft.Text(f"Available Local IPs: {', '.join(local_ips)}", size=12, color=ft.colors.GREY_400)

        error_msg = ft.Text(f"Failed to bind to: {failed_ip}" if failed_ip else "", color=ft.colors.RED, size=14)

        def save_click(e):
            try:
                # Basic validation
                new_api_ip = api_ip_input.value.strip()
                new_server_host = server_host_input.value.strip()
                
                # Try validation immediately? 
                # Or just save and let the main loop re-check.
                # Let's save.
                new_cfg = {
                    "API_IP": new_api_ip,
                    "SERVER_HOST": new_server_host
                }
                save_config(new_cfg)
                result["action"] = "retry"
                page.window_close()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Error saving: {ex}"))
                page.snack_bar.open = True
                page.update()

        def cancel_click(e):
            result["action"] = "exit"
            page.window_close()

        page.add(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.icons.WIFI_OFF, size=50, color=ft.colors.RED),
                        ft.Text("Network Configuration Error", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text("The server cannot start with current IP settings.", size=14),
                        error_msg,
                        ip_suggestions,
                        api_ip_input,
                        server_host_input,
                        ft.Row(
                            [
                                ft.ElevatedButton("Save & Retry", on_click=save_click, icon=ft.icons.SAVE),
                                ft.TextButton("Cancel / Exit", on_click=cancel_click),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                ),
                padding=20,
            )
        )
        page.update()

    ft.app(target=config_app)
    return result["action"]


def main():
    # Ensure required folders exist
    import os

    for folder in ["assets", "setting", "logs"]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Load config and pre-startup checks
    cfg = get_config()
    api_ip = cfg["API_IP"]
    pre_startup_check()

    # Perform database startup check loop.
    while True:
        if database_startup_check():
            break
        
        log_error("Database check failed. Showing configuration window.")
        action = show_db_config_window()
        if action == "exit":
            log_info("User chose to exit. Shutting down.")
            return

    log_info("Database check passed. Continuing with application startup.")

    # Network Configuration Check
    while True:
        # Load fresh config in case it was changed
        cfg = get_config()
        api_ip = cfg.get("API_IP", "127.0.0.1")
        server_host = cfg.get("SERVER_HOST", "127.0.0.1")

        # Validate API_IP
        if not validate_binding(api_ip):
            log_error(f"Cannot bind to API_IP: {api_ip}")
            action = show_network_config_window(failed_ip=api_ip)
            if action == "exit":
                log_info("User chose to exit during network config.")
                return
            continue # Retry loop

        # Validate SERVER_HOST (Optional: only if we want to ensure CBC server can also start)
        # Note: server.py handles its own bind errors, but catching it here prevents partial startup.
        if cfg.get("AUTO_START_CBC_SERVER", True):
             if not validate_binding(server_host):
                log_error(f"Cannot bind to SERVER_HOST: {server_host}")
                action = show_network_config_window(failed_ip=server_host)
                if action == "exit":
                    log_info("User chose to exit during network config.")
                    return
                continue # Retry loop
        
        break

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
        flet_process.terminate()

    # Terminate FastAPI process on exit
    log_info("Shutting down FastAPI server...")
    fastapi_process.terminate()
    fastapi_process.join(timeout=3.0)
    if fastapi_process.is_alive():
        log_info("FastAPI process did not exit gracefully, killing...")
    
    log_info("Application shutdown complete.")


if __name__ == "__main__":
    multiprocessing.freeze_support()

    main()
