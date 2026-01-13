import pyodbc
import os
from log.logger import log_info, log_error, log_warning
from setting import config


# Define the source for logging
SOURCE = "Database"


def get_db_connection():
    """
    Establishes a connection to the MSSQL database based on the provided configuration.
    Supports both local and online database connections.

    Returns:
        pyodbc.Connection: A pyodbc connection object for the database.

    Raises:
        ValueError: If the `DB_TYPE` is invalid.
        ConnectionError: If a connection to the database could not be established.
    """
    try:

        cfg = config.get_config()  # Load configuration from file
        DB_DRIVE = cfg["DB_DRIVE"]
        DB_HOST = cfg["DB_HOST"]
        DB_PORT = cfg["DB_PORT"]
        DB_NAME = cfg["DB_NAME"]
        log_info(f"Using database name: {DB_NAME}", source=SOURCE)
        DB_USER = cfg["DB_USER"]
        DB_PASSWORD = cfg["DB_PASSWORD"]
        DB_TYPE = cfg["DB_TYPE"]

        # Determine the connection type and build the connection string
        if DB_TYPE == "local":
            # Local database connection string
            connection_string = (
                f"DRIVER={DB_DRIVE};"
                f"SERVER={DB_HOST};"  # No port required for local connections
                f"DATABASE={DB_NAME};"
                f"UID={DB_USER};"
                f"PWD={DB_PASSWORD};"
            )
            log_info(
                f"Attempting to connect to local database at {DB_HOST}.", source=SOURCE
            )

        elif DB_TYPE == "online":
            # Online database connection string
            connection_string = (
                f"DRIVER={DB_DRIVE};"
                f"SERVER={DB_HOST},{DB_PORT};"
                f"DATABASE={DB_NAME};"
                f"UID={DB_USER};"
                f"PWD={DB_PASSWORD};"
            )
            log_info(
                f"Attempting to connect to online database at {DB_HOST}:{DB_PORT}.",
                source=SOURCE,
            )

        else:
            # Invalid DB_TYPE specified
            log_error(
                "Invalid DB_TYPE specified. Use 'local' or 'online'.", source=SOURCE
            )
            raise ValueError("Invalid DB_TYPE specified. Use 'local' or 'online'.")

        # Attempt to establish the connection with a short timeout (3 seconds)
        connection = pyodbc.connect(connection_string, timeout=3)
        log_info("Successfully connected to the database.", source=SOURCE)
        
        return connection

    except ValueError as ve:
        # Log and re-raise ValueError for invalid `DB_TYPE`
        log_error(f"ValueError: {ve}", source=SOURCE)
        raise

    except Exception as e:
        # Log and re-raise exceptions for any other issues
        log_error(f"Failed to connect to database: {e}", source=SOURCE)
        raise ConnectionError(f"Failed to connect to database: {e}")


def test_db_connection(db_params: dict) -> bool:
    """
    Test database connection with the provided parameters.
    Returns True if successful, raises Exception if failed.
    """
    try:
        DB_DRIVE = db_params.get("DB_DRIVE", "")
        DB_HOST = db_params.get("DB_HOST", "")
        DB_PORT = db_params.get("DB_PORT", "")
        DB_NAME = db_params.get("DB_NAME", "")
        DB_USER = db_params.get("DB_USER", "")
        DB_PASSWORD = db_params.get("DB_PASSWORD", "")
        DB_TYPE = db_params.get("DB_TYPE", "local")

        # Determine the connection type and build the connection string
        if DB_TYPE == "local":
            connection_string = (
                f"DRIVER={{{DB_DRIVE}}};" # Enclose driver in braces
                f"SERVER={DB_HOST};"
                f"DATABASE={DB_NAME};"
                f"UID={DB_USER};"
                f"PWD={DB_PASSWORD};"
            )
        elif DB_TYPE == "online":
             connection_string = (
                f"DRIVER={{{DB_DRIVE}}};"
                f"SERVER={DB_HOST},{DB_PORT};"
                f"DATABASE={DB_NAME};"
                f"UID={DB_USER};"
                f"PWD={DB_PASSWORD};"
            )
        else:
            raise ValueError(f"Invalid DB_TYPE: {DB_TYPE}")

        log_info(f"Testing DB connection to {DB_HOST}...", source=SOURCE)
        
        # Test connection with timeout
        conn = pyodbc.connect(connection_string, timeout=3)
        conn.close()
        return True
    except Exception as e:
        log_error(f"Test connection failed: {e}", source=SOURCE)
        raise e
