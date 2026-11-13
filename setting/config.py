import os
import socket
import json
import base64
import secrets
import threading
import tempfile
import time
import contextlib
import pyodbc
import portalocker
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from log.logger import log_info, log_error, log_warning
from typing import Dict, Any, List


SOURCE = "Config"
_config_lock = threading.Lock()
LOCK_URL = r"setting\config.lock"


def _atomic_replace_with_retry(src: str, dst: str, max_retries: int = 15, delay: float = 0.05) -> None:
    """
    Atomically replaces dst with src on Windows and POSIX with bounded retry on PermissionError/WinError 32.
    """
    for attempt in range(max_retries):
        try:
            os.replace(src, dst)
            return
        except PermissionError as e:
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                raise e


@contextlib.contextmanager
def _config_file_lock(lock_path: str = None, timeout: float = 5.0):
    """
    Acquires an exclusive cross-process file lock using portalocker alongside the thread lock.
    Gracefully falls back to thread lock if file locking fails (e.g. mock_open in unit tests).
    """
    path = lock_path or os.environ.get("HEALTHMESH_LOCK_PATH", LOCK_URL)
    lock_dir = os.path.dirname(path)
    if lock_dir and not os.path.exists(lock_dir):
        try:
            os.makedirs(lock_dir, exist_ok=True)
        except OSError:
            pass

    with _config_lock:
        lock = None
        try:
            lock = portalocker.Lock(path, timeout=timeout)
            lock.acquire()
        except Exception:
            lock = None
        try:
            yield
        finally:
            if lock is not None:
                try:
                    lock.release()
                except Exception:
                    pass


# Constants for security
SALT_LENGTH = 16
KEY_LENGTH = 32
ITERATIONS = 100000
MIN_PASSWORD_LENGTH = 8


# item not saved in .json
KEY_URL = r"setting\key.key"
CONFIG_URL = r"setting\config.json"

API_PORT = 8000
API_IP = "127.0.0.1"
API_BASE_URL = f"http://{API_IP}:{API_PORT}"


# application Configuration settings
APPLICATION_NAME = "HealthMesh"
APPLICATION_SLOGAN = " - Laboratory Information System"  # Add a default slogan
VERSION = "1.0.0"
LOG_DIR = "logs"
LOG_FILE_NAME = "HealthMesh.log"
CONFIG_URL = r"setting\config.json"
DARK_MODE = True
AUTO_START_CBC_SERVER = True  # Auto start CBC device listening server


# Some db value
CBC_TEST_CODE = 56
HGB_TEST_CODE = 50
TEST_FINISH_CODE = False

# Default database settings
DB_USER = "sa"  # Encrypt
DB_PASSWORD = "123456"  # Encrypt
DB_TYPE = "local"
DB_DRIVE = "ODBC Driver 17 for SQL Server"
DB_HOST = "localhost"
DB_PORT = 1433
DB_NAME = "YourLIS_DB"

# server setting
SERVER_HOST = "192.168.1.103"
SERVER_PORT = 4000


# connected deviced from hl7 message

# supported devices dict

SUPPORTED_DEVICES = {
    "Genrui KT-60": {
        "LOGO_URL": r"assets\images\genrui_kt60.jpg",
        "INFO": "Genrui KT-60 is an up-to-date hematology analyzer providing smart counting mode for low-value samples with only 9μL whole blood required. \nRFID card closed system and wider linearity brings the real card closed system and more widely clinical application. \nIt is a wise choice for the small and medium labs, clinics or hospitals which require cost-effective solutions by offering a complete solution with a built-in system and reliable clinical supports.",
    }
}

encrypt_list = [
    "DB_USER",
    "DB_PASSWORD",
    "API_TOKEN",
]  # List of keys to encrypt


default_config_data = {
    "APPLICATION_NAME": APPLICATION_NAME,
    "APPLICATION_SLOGAN": APPLICATION_SLOGAN,  # Add slogan to config
    "VERSION": VERSION,
    "LOG_DIR": LOG_DIR,
    "LOG_FILE_NAME": LOG_FILE_NAME,
    "CONFIG_URL": CONFIG_URL,
    "DARK_MODE": DARK_MODE,
    "AUTO_START_CBC_SERVER": AUTO_START_CBC_SERVER,
    "CBC_TEST_CODE": CBC_TEST_CODE,
    "HGB_TEST_CODE": HGB_TEST_CODE,
    "TEST_FINISH_CODE": TEST_FINISH_CODE,
    "SERVER_HOST": SERVER_HOST,
    "SERVER_PORT": SERVER_PORT,
    "API_PORT": API_PORT,
    "API_IP": API_IP,
    "API_TOKEN": "",
    "DB_TYPE": DB_TYPE,
    "DB_DRIVE": DB_DRIVE,
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "DB_NAME": DB_NAME,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "SUPPORTED_DEVICES": SUPPORTED_DEVICES,
}


def generate_secure_key() -> bytes:
    """Generate a secure encryption key using PBKDF2."""
    salt = secrets.token_bytes(SALT_LENGTH)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=salt,
        iterations=ITERATIONS,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secrets.token_bytes(32)))
    return key


def validate_password(password: str) -> bool:
    """Validate password strength."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return False
    # Add more password validation rules as needed
    return True


def encrypt_value(value: str, key: bytes) -> str:
    """Encrypt a string value using Fernet."""
    try:
        f = Fernet(key)
        return f.encrypt(value.encode()).decode()
    except Exception as e:
        err_msg = str(e) or e.__class__.__name__
        log_error(f"Encryption error: {err_msg}", source=SOURCE)
        raise


def decrypt_value(encrypted_value: str, key: bytes) -> str:
    """Decrypt a string value using Fernet."""
    try:
        f = Fernet(key)
        return f.decrypt(encrypted_value.encode()).decode()
    except Exception as e:
        err_msg = str(e) or e.__class__.__name__
        log_error(f"Decryption error: {err_msg}", source=SOURCE)
        raise


def mask_config_credentials(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a copy of config with sensitive credentials masked (e.g. for API/GUI transmission).
    """
    if not isinstance(config_dict, dict):
        return {}
    masked = config_dict.copy()
    for sensitive_key in encrypt_list:
        if sensitive_key in masked and masked[sensitive_key]:
            masked[sensitive_key] = "********"
    return masked


def get_encryption_key(key_url: str = None) -> bytes:
    """
    Retrieve encryption key with precedence:
    1. HEALTHMESH_SECRET_KEY environment variable.
    2. Key file from HEALTHMESH_KEY_PATH env var or key_url parameter.
    3. Auto-generate key and persist to key file.
    """
    env_key = os.environ.get("HEALTHMESH_SECRET_KEY")
    if env_key:
        if isinstance(env_key, str):
            env_key = env_key.strip().encode("utf-8")
        try:
            Fernet(env_key)
            return env_key
        except Exception as e:
            log_error(
                f"Invalid HEALTHMESH_SECRET_KEY environment variable ({e}). "
                "Fernet key must be 32 url-safe base64-encoded bytes. "
                "Falling back to key file.",
                source=SOURCE,
            )

    target_key_url = key_url or os.environ.get("HEALTHMESH_KEY_PATH", KEY_URL)
    setting_dir = os.path.dirname(target_key_url)
    if setting_dir and not os.path.exists(setting_dir):
        try:
            os.makedirs(setting_dir, exist_ok=True)
        except OSError:
            pass

    if os.path.exists(target_key_url):
        with open(target_key_url, "rb") as file:
            return file.read().strip()
    else:
        log_info("Key file not found. Generating new secure key.", source=SOURCE)
        key = generate_secure_key()
        with open(target_key_url, "wb") as file:
            file.write(key)
        return key


def _load_config(
    config_url: str = CONFIG_URL, encrypt_list: List[str] = encrypt_list, key_url: str = KEY_URL
) -> Dict[str, Any]:
    """Load and decrypt configuration from file."""
    try:
        # Ensure the setting directory exists
        setting_dir = os.path.dirname(config_url)
        if setting_dir and not os.path.exists(setting_dir):
            os.makedirs(setting_dir, exist_ok=True)
            log_info(f"Created directory: {setting_dir}", source=SOURCE)

        # Load or generate encryption key
        key = get_encryption_key(key_url)

        # Load configuration
        if os.path.exists(config_url):
            with open(config_url, "r") as file:
                config = json.load(file)

            # Decrypt sensitive values
            for item in encrypt_list:
                if item in config and config[item]:
                    try:
                        config[item] = decrypt_value(config[item], key)
                    except Exception as e:
                        err_msg = str(e) or e.__class__.__name__
                        log_error(f"Decryption error for {item}: {err_msg}", source=SOURCE)
            return config
        else:
            log_info("Config file not found. Using default settings.", source=SOURCE)
            return {}
    except Exception as e:
        log_error(f"Error loading config: {e}", source=SOURCE)
        return {}


def get_api_token() -> str:
    """
    Retrieve or generate persistent internal API bearer token for service-boundary authentication.
    """
    env_token = os.environ.get("HEALTHMESH_API_TOKEN")
    if env_token and env_token.strip():
        return env_token.strip()

    cfg = get_config()
    token = cfg.get("API_TOKEN")
    if token and str(token).strip():
        return str(token).strip()

    new_token = secrets.token_hex(32)
    save_config({"API_TOKEN": new_token})
    return new_token


def get_config(config_url: str = CONFIG_URL, key_url: str = KEY_URL) -> Dict[str, Any]:
    """Get the current configuration with cross-process consistency."""
    with _config_file_lock(config_url + ".lock"):
        config_data = _load_config(config_url, encrypt_list, key_url)
        if not config_data:
            config_data = default_config_data.copy()

        # Ensure DB_DRIVE is valid
        if not validate_sql_driver(config_data.get("DB_DRIVE", "")):
            config_data["DB_DRIVE"] = get_default_sql_driver()
            log_info(f"Updated DB_DRIVE to {config_data['DB_DRIVE']}", source=SOURCE)

        return config_data.copy()


def save_config(config_data_to_save: Dict[str, Any], config_url: str = CONFIG_URL, key_url: str = KEY_URL) -> None:
    """Save configuration with encryption for sensitive data using atomic file writes and cross-process lock."""
    with _config_file_lock(config_url + ".lock"):
        try:
            # Load existing configuration
            existing_config = _load_config(config_url, encrypt_list, key_url)
            if not existing_config:
                existing_config = default_config_data.copy()

            # Type validation and conversion
            for key, value in config_data_to_save.items():
                if key in default_config_data:
                    target_type = type(default_config_data[key])
                    try:
                        if target_type == int:
                            config_data_to_save[key] = int(value)
                        elif target_type == float:
                            config_data_to_save[key] = float(value)
                        elif target_type == bool:
                            config_data_to_save[key] = bool(value)
                    except (ValueError, TypeError) as e:
                        log_error(f"Type conversion error for {key}: {e}", source=SOURCE)
                        continue

            # Validate SQL driver if being updated
            if "DB_DRIVE" in config_data_to_save:
                if not validate_sql_driver(config_data_to_save["DB_DRIVE"]):
                    log_error(
                        f"Invalid SQL driver: {config_data_to_save['DB_DRIVE']}",
                        source=SOURCE,
                    )
                    config_data_to_save["DB_DRIVE"] = get_default_sql_driver()
                    log_info(
                        f"Using default SQL driver: {config_data_to_save['DB_DRIVE']}",
                        source=SOURCE,
                    )

            # Update configuration
            existing_config.update(config_data_to_save)

            # Load encryption key
            key = get_encryption_key(key_url)

            # Encrypt sensitive data
            for item in encrypt_list:
                if item in existing_config and existing_config[item]:
                    try:
                        existing_config[item] = encrypt_value(
                            str(existing_config[item]), key
                        )
                    except Exception as e:
                        log_error(f"Encryption error for {item}: {e}", source=SOURCE)

            # Atomic save configuration: write to temp file then atomic replace with retry
            setting_dir = os.path.dirname(config_url) or "."
            if not os.path.exists(setting_dir):
                os.makedirs(setting_dir, exist_ok=True)

            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    dir=setting_dir,
                    delete=False,
                    encoding="utf-8",
                    suffix=".tmp",
                ) as temp_file:
                    temp_path = temp_file.name
                    json.dump(existing_config, temp_file, indent=4)
                    temp_file.flush()
                    try:
                        os.fsync(temp_file.fileno())
                    except OSError:
                        pass
                _atomic_replace_with_retry(temp_path, config_url)
            except Exception as replace_err:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except OSError:
                        pass
                raise replace_err

            log_info("Configuration saved successfully.", source=SOURCE)
        except Exception as e:
            log_error(f"Error saving configuration: {e}", source=SOURCE)
            raise


PREFERRED_SQL_DRIVERS = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "ODBC Driver 13.1 for SQL Server",
    "ODBC Driver 13 for SQL Server",
    "ODBC Driver 11 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server Native Client 10.0",
    "SQL Server",
]


def get_available_sql_drivers() -> List[str]:
    """
    Get a list of available SQL Server drivers on the system, ordered by preference.
    Returns a list of driver names.
    """
    try:
        drivers = pyodbc.drivers()
        sql_drivers = [driver for driver in drivers if "SQL Server" in driver]
        if not sql_drivers:
            log_warning("No SQL Server drivers found on the system", source=SOURCE)
            return []

        sql_drivers.sort(
            key=lambda d: PREFERRED_SQL_DRIVERS.index(d)
            if d in PREFERRED_SQL_DRIVERS
            else 999
        )
        return sql_drivers
    except Exception as e:
        log_error(f"Error getting SQL drivers: {e}", source=SOURCE)
        return []


def validate_sql_driver(driver: str) -> bool:
    """
    Validate if a SQL Server driver is available on the system.
    """
    return driver in get_available_sql_drivers()


def get_default_sql_driver() -> str:
    """
    Get the default SQL Server driver, preferring newer versions.
    Returns a message if no drivers are found.
    """
    drivers = get_available_sql_drivers()
    if not drivers:
        return "No SQL Server drivers found."
    return drivers[0]  # Return the first available driver


def pre_startup_check():
    """
    Ensure config.json exists with defaults if missing, and check SQL Server driver availability.
    """
    # Ensure the setting directory exists
    setting_dir = os.path.dirname(CONFIG_URL)
    if setting_dir and not os.path.exists(setting_dir):
        os.makedirs(setting_dir)
        log_info(f"Created directory: {setting_dir}", source=SOURCE)

    # Check config.json existence
    if not os.path.exists(CONFIG_URL):
        log_info("Config file not found. Creating with default values.", source=SOURCE)
        save_config(default_config_data)
    else:
        log_info("Config file found.", source=SOURCE)

    # Check SQL Server driver
    drivers = get_available_sql_drivers()
    if not drivers:
        log_warning(
            "No SQL Server driver found. Application may not work properly.",
            source=SOURCE,
        )
    else:
        log_info(f"SQL Server drivers available: {drivers}", source=SOURCE)


def validate_binding(ip_address: str) -> bool:
    """
    Check if we can bind to the given IP address.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((ip_address, 0))
        return True
    except Exception:
        return False
