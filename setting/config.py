from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import json
import base64
import secrets
import pyodbc
from log.logger import log_info, log_error, log_warning
from typing import Dict, Any, List, Optional, Tuple, Type # Added Type for type hinting
import importlib # For dynamic adapter loading


SOURCE = "Config"


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
DB_NAME = "patients"

# server setting
SERVER_HOST = "192.168.1.103"
SERVER_PORT = 4000

APP_USER = "admin"
APP_PASSWORD = "123"


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
    "APP_USER",
    "APP_PASSWORD",
]  # List of keys to encrypt


default_config_data = {
    "APPLICATION_NAME": APPLICATION_NAME,
    "APPLICATION_SLOGAN": APPLICATION_SLOGAN,  # Add slogan to config
    "VERSION": VERSION,
    "LOG_DIR": LOG_DIR,
    "LOG_FILE_NAME": LOG_FILE_NAME,
    "CONFIG_URL": CONFIG_URL,
    "DARK_MODE": DARK_MODE,
    "CBC_TEST_CODE": CBC_TEST_CODE,
    "HGB_TEST_CODE": HGB_TEST_CODE,
    "TEST_FINISH_CODE": TEST_FINISH_CODE,
    "SERVER_HOST": SERVER_HOST,
    "SERVER_PORT": SERVER_PORT,
    "API_PORT": API_PORT,
    "API_IP": API_IP,
    "DB_TYPE": DB_TYPE,
    "DB_DRIVE": DB_DRIVE,
    "DB_HOST": DB_HOST,
    "DB_PORT": DB_PORT,
    "DB_NAME": DB_NAME,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "APP_USER": APP_USER,
    "APP_PASSWORD": APP_PASSWORD,
    "SUPPORTED_DEVICES": SUPPORTED_DEVICES,
    # New adapter settings
    "DATABASE_ADAPTER_CLASS": "database.mssql_adapter.MssqlAdapter",
    "DEVICE_ADAPTER_CONFIG": {
        "Genrui_KT60": {"class_path": "hl7msghandel.placeholder_adapter.PlaceholderDeviceAdapter"}
        # Add other devices here, e.g.
        # "Sysmex_XN1000": {"class_path": "hl7msghandel.sysmex_xn1000_adapter.SysmexXn1000Adapter"}
    },
    "ACTIVE_DEVICE_ADAPTER_NAME": "Genrui_KT60", # Default active device
}

# Define constants for new adapter settings (defaults)
DATABASE_ADAPTER_CLASS = default_config_data["DATABASE_ADAPTER_CLASS"]
DEVICE_ADAPTER_CONFIG = default_config_data["DEVICE_ADAPTER_CONFIG"]
ACTIVE_DEVICE_ADAPTER_NAME = default_config_data["ACTIVE_DEVICE_ADAPTER_NAME"]


def load_adapter_class(class_path_string: str) -> Optional[Type]:
    """
    Dynamically loads a class given its full path string.

    Args:
        class_path_string: The full path to the class (e.g., "module.submodule.ClassName").

    Returns:
        The loaded class if successful, None otherwise.
    """
    if not class_path_string or not isinstance(class_path_string, str):
        log_error(f"Invalid class_path_string: '{class_path_string}'. Must be a non-empty string.", source=SOURCE)
        return None
    try:
        module_path, class_name = class_path_string.rsplit('.', 1)
        module = importlib.import_module(module_path)
        adapter_class = getattr(module, class_name)
        log_info(f"Successfully loaded adapter class: {class_name} from {module_path}", source=SOURCE)
        return adapter_class
    except ImportError as e:
        log_error(f"Error importing module {module_path}: {e}", source=SOURCE)
        return None
    except AttributeError as e:
        log_error(f"Error getting class {class_name} from module {module_path}: {e}", source=SOURCE)
        return None
    except ValueError as e: # Handles cases where rsplit fails if class_path_string is not like "a.b"
        log_error(f"Invalid class_path_string format '{class_path_string}': {e}. Expected 'module.ClassName'.", source=SOURCE)
        return None
    except Exception as e: # Catch any other unexpected errors
        log_error(f"An unexpected error occurred while loading adapter class '{class_path_string}': {e}", source=SOURCE)
        return None


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
        log_error(f"Encryption error: {e}", source=SOURCE)
        raise


def decrypt_value(encrypted_value: str, key: bytes) -> str:
    """Decrypt a string value using Fernet."""
    try:
        f = Fernet(key)
        return f.decrypt(encrypted_value.encode()).decode()
    except Exception as e:
        log_error(f"Decryption error: {e}", source=SOURCE)
        raise


def _load_config(
    config_url: str, encrypt_list: List[str], key_url: str
) -> Dict[str, Any]:
    """Load and decrypt configuration from file."""
    try:
        # Load or generate encryption key
        if os.path.exists(key_url):
            with open(key_url, "rb") as file:
                key = file.read()
        else:
            log_info("Key file not found. Generating new secure key.", source=SOURCE)
            key = generate_secure_key()
            with open(key_url, "wb") as file:
                file.write(key)

        # Load configuration
        if os.path.exists(config_url):
            with open(config_url, "r") as file:
                config = json.load(file)

            # Decrypt sensitive values
            for item in encrypt_list:
                if item in config:
                    try:
                        config[item] = decrypt_value(config[item], key)
                    except Exception as e:
                        log_error(f"Decryption error for {item}: {e}", source=SOURCE)
            return config
        else:
            log_info("Config file not found. Using default settings.", source=SOURCE)
            return {}
    except Exception as e:
        log_error(f"Error loading config: {e}", source=SOURCE)
        return {}


def get_config() -> Dict[str, Any]:
    """Get the current configuration."""
    config_data = _load_config(CONFIG_URL, encrypt_list, KEY_URL)
    loaded_config = default_config_data.copy() # Start with defaults
    if config_data: # If file loaded something
        loaded_config.update(config_data) # Override defaults with file contents

    # Ensure DB_DRIVE is valid - existing logic
    if not validate_sql_driver(loaded_config.get("DB_DRIVE", "")):
        loaded_config["DB_DRIVE"] = get_default_sql_driver()
        log_info(f"Updated DB_DRIVE to {loaded_config['DB_DRIVE']}", source=SOURCE)
    
    # Ensure new adapter config keys exist, using defaults if not present in file
    # This is mostly handled by starting with default_config_data.copy() and updating.
    # However, for nested dicts like DEVICE_ADAPTER_CONFIG, a simple update might not merge deeply.
    # For this specific case, default_config_data.update(file_config) is usually sufficient if
    # the entire DEVICE_ADAPTER_CONFIG is expected to be in the file or the default is used.
    # If partial updates to DEVICE_ADAPTER_CONFIG were desired, more complex merging would be needed.

    return loaded_config # Return the merged config


def save_config(config_data_to_save: Dict[str, Any]) -> None:
    """Save configuration with encryption for sensitive data."""
    try:
        # Load existing configuration
        existing_config = _load_config(CONFIG_URL, encrypt_list, KEY_URL)
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
        if os.path.exists(KEY_URL):
            with open(KEY_URL, "rb") as file:
                key = file.read()
        else:
            key = generate_secure_key()
            with open(KEY_URL, "wb") as file:
                file.write(key)

        # Encrypt sensitive data
        for item in encrypt_list:
            if item in existing_config:
                try:
                    existing_config[item] = encrypt_value(
                        str(existing_config[item]), key
                    )
                except Exception as e:
                    log_error(f"Encryption error for {item}: {e}", source=SOURCE)

        # Save configuration
        with open(CONFIG_URL, "w") as file:
            json.dump(existing_config, file, indent=4)

        log_info("Configuration saved successfully.", source=SOURCE)
    except Exception as e:
        log_error(f"Error saving configuration: {e}", source=SOURCE)
        raise


def get_available_sql_drivers() -> List[str]:
    """
    Get a list of available SQL Server drivers on the system.
    Returns a list of driver names.
    """
    try:
        drivers = pyodbc.drivers()
        sql_drivers = [driver for driver in drivers if "SQL Server" in driver]
        if not sql_drivers:
            log_warning("No SQL Server drivers found on the system", source=SOURCE)
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
    # Check config.json existence
    if not os.path.exists(CONFIG_URL):
        log_info("Config file not found. Creating with default values.", source=SOURCE)
        save_config(default_config_data)
    else:
        log_info("Config file found.", source=SOURCE)

    # Check SQL Server driver
    drivers = get_available_sql_drivers()
    if not drivers:
        log_warning("No SQL Server driver found. Application may not work properly.", source=SOURCE)
    else:
        log_info(f"SQL Server drivers available: {drivers}", source=SOURCE)
