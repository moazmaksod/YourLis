import pyodbc
import os
import queue
import threading
from contextlib import contextmanager
from log.logger import log_info, log_error, log_warning
from setting import config

SOURCE = "Database"

# Enable ODBC-level connection pooling in pyodbc
pyodbc.pooling = True


def build_connection_string(cfg=None):
    """
    Builds the PyODBC connection string based on the configuration dictionary.
    """
    if cfg is None:
        cfg = config.get_config()

    db_driver = cfg.get("DB_DRIVE", "")
    db_host = cfg.get("DB_HOST", "")
    db_port = cfg.get("DB_PORT", "")
    db_name = cfg.get("DB_NAME", "")
    db_user = cfg.get("DB_USER", "")
    db_password = cfg.get("DB_PASSWORD", "")
    db_type = cfg.get("DB_TYPE", "local")

    extra_flags = ""
    if "ODBC Driver 18" in db_driver:
        extra_flags = "TrustServerCertificate=yes;"

    if db_type == "local":
        return (
            f"DRIVER={db_driver};"
            f"SERVER={db_host};"
            f"DATABASE={db_name};"
            f"UID={db_user};"
            f"PWD={db_password};"
            f"{extra_flags}"
        )
    elif db_type == "online":
        return (
            f"DRIVER={db_driver};"
            f"SERVER={db_host},{db_port};"
            f"DATABASE={db_name};"
            f"UID={db_user};"
            f"PWD={db_password};"
            f"{extra_flags}"
        )
    else:
        raise ValueError("Invalid DB_TYPE specified. Use 'local' or 'online'.")


class ConnectionPool:
    """
    Thread-safe connection pool for PyODBC database connections.
    Reuses open connections across threads and queries to prevent ephemeral
    port exhaustion and TCP/TDS handshake latency.
    """

    def __init__(self, max_connections=10, timeout=3):
        self.max_connections = max_connections
        self.timeout = timeout
        self._pool = queue.Queue(maxsize=max_connections)
        self._lock = threading.Lock()
        self._active_count = 0

    def _create_raw_connection(self):
        conn_str = build_connection_string()
        log_info("Creating new raw database connection...", source=SOURCE)
        return pyodbc.connect(conn_str, timeout=self.timeout)

    def _is_alive(self, conn):
        """Fast pre-ping check to verify the connection is alive and clean of uncommitted transactions."""
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            try:
                conn.rollback()
            except Exception:
                pass
            return True
        except Exception:
            return False

    def get_connection(self):
        """Acquires a healthy connection from the pool, creating one if needed."""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                if self._is_alive(conn):
                    return conn
                else:
                    self._close_conn(conn)
                    with self._lock:
                        self._active_count = max(0, self._active_count - 1)
            except queue.Empty:
                break

        # Pool is empty or all checked connections were stale: create a new connection
        try:
            conn = self._create_raw_connection()
            with self._lock:
                self._active_count += 1
            log_info("Database connection acquired.", source=SOURCE)
            return conn
        except ValueError:
            raise
        except Exception as e:
            log_error(f"Failed to connect to database: {e}", source=SOURCE)
            raise ConnectionError(f"Failed to connect to database: {e}")

    def release_connection(self, conn, discard=False):
        """Returns a connection to the pool after rolling back open transactions, or discards it if broken."""
        if conn is None:
            return
        if not discard:
            try:
                conn.rollback()
            except Exception:
                discard = True

        if discard:
            self._close_conn(conn)
            with self._lock:
                self._active_count = max(0, self._active_count - 1)
            return

        try:
            self._pool.put_nowait(conn)
        except queue.Full:
            self._close_conn(conn)
            with self._lock:
                self._active_count = max(0, self._active_count - 1)

    def _close_conn(self, conn):
        try:
            conn.close()
        except Exception:
            pass

    def close_all(self):
        """Closes all idle connections in the pool."""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                self._close_conn(conn)
            except queue.Empty:
                break
        with self._lock:
            self._active_count = 0


# Global singleton connection pool
_global_pool = ConnectionPool()


def get_connection_pool() -> ConnectionPool:
    """Returns the singleton ConnectionPool instance."""
    return _global_pool


@contextmanager
def get_db_connection_context():
    """
    Context manager yielding a pooled database connection.
    Automatically releases the connection back to the pool on completion,
    or evicts the connection if an unhandled connection error occurs.
    """
    conn = None
    discard = False
    try:
        conn = _global_pool.get_connection()
        yield conn
    except (pyodbc.OperationalError, pyodbc.DatabaseError, ConnectionError):
        discard = True
        raise
    finally:
        if conn is not None:
            _global_pool.release_connection(conn, discard=discard)


def get_db_connection():
    """
    Establishes or acquires a connection to the MSSQL database based on the provided configuration.
    Supports both local and online database connections with connection pooling.

    Returns:
        pyodbc.Connection: A pyodbc connection object for the database.
    """
    try:
        return _global_pool.get_connection()
    except ValueError as ve:
        log_error(f"ValueError: {ve}", source=SOURCE)
        raise
    except ConnectionError:
        raise
    except Exception as e:
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
                f"DRIVER={{{DB_DRIVE}}};"
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
