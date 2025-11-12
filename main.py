import multiprocessing
import asyncio
import time
import httpx
from setting.config import get_config, save_config, pre_startup_check
from gui.main_flet import main as flet_main
from log.logger import log_info, log_error
import flet as ft
from database.sqlconnection import get_db_connection
import os


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
    Check DB connection and ensure required stored procedures exist, creating them if missing.
    If connection fails, return False.
    """

    # List of required procedures and their .sql files
    required_procs = [
        (
            "GetPatientInfo",
            os.path.join("Sql_reqirement_querys", "Reallab", "GetPatientInfo.sql"),
        ),
        (
            "GetPatientCBCResult",
            os.path.join("Sql_reqirement_querys", "Reallab", "GetPatientCBCResult.sql"),
        ),
    ]
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        log_info("Database connection established for startup check.")
        for proc_name, sql_path in required_procs:
            # Check if procedure exists
            cursor.execute(
                """
                SELECT COUNT(*) FROM sys.objects WHERE type = 'P' AND name = ?
            """,
                (proc_name,),
            )
            row = cursor.fetchone()
            exists = row[0] if row else 0
            if not exists:
                log_info(
                    f"Stored procedure '{proc_name}' not found. Creating from {sql_path}."
                )
                with open(sql_path, encoding="utf-8") as f:
                    sql = f.read()
                # Remove USE/GO lines for pyodbc execution
                sql_lines = [
                    line
                    for line in sql.splitlines()
                    if not line.strip().upper().startswith(("USE ", "GO"))
                ]
                # Find the first line with CREATE or ALTER PROCEDURE
                for idx, line in enumerate(sql_lines):
                    if (
                        line.strip()
                        .upper()
                        .startswith(("CREATE PROCEDURE", "ALTER PROCEDURE"))
                    ):
                        sql_lines = sql_lines[idx:]
                        break
                sql = "\n".join(sql_lines)
                try:
                    cursor.execute(sql)
                    conn.commit()
                    log_info(f"Stored procedure '{proc_name}' created.")
                except Exception as e:
                    log_error(f"Error creating procedure {proc_name}: {e}\nSQL: {sql}")
            else:
                log_info(f"Stored procedure '{proc_name}' exists.")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        log_error(f"Database startup check failed: {e}")
        return False


def show_db_error_window():
    import flet as ft
    from gui.main_flet import main as flet_main

    def notify(page: ft.Page):
        # Show notification
        snack = ft.SnackBar(
            ft.Text(
                "Database connection failed! Please check settings and correct DB info."
            ),
            open=True,
        )
        page.overlay.append(snack)
        page.update()
        # Try to navigate to settings page if possible
        try:
            if hasattr(page, "go"):
                page.go("/settings")
        except Exception:
            pass

    # Open the main app, and let the app itself handle redirecting to settings if DB is not connected
    ft.app(target=flet_main, assets_dir="assets")


def main():
    # Ensure required folders exist
    import os

    for folder in ["assets", "setting"]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Load config and pre-startup checks
    cfg = get_config()
    api_ip = cfg["API_IP"]
    pre_startup_check()
    database_startup_check()  # Always run, but do not block app startup
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
