import pytest
from setting import config
import json
import os
from unittest.mock import mock_open, patch

def test_generate_secure_key():
    key = config.generate_secure_key()
    assert isinstance(key, bytes)
    assert len(key) > 0

def test_encrypt_decrypt_value():
    key = config.generate_secure_key()
    original_value = "SecretPassword"
    encrypted = config.encrypt_value(original_value, key)
    assert encrypted != original_value
    decrypted = config.decrypt_value(encrypted, key)
    assert decrypted == original_value

def test_validate_password():
    assert config.validate_password("12345678") is True
    assert config.validate_password("short") is False

def test_get_config_with_mock(mocker):
    # This test bypasses the fixture to test the actual logic with file mocks

    mock_data = config.default_config_data.copy()
    mock_json = json.dumps(mock_data)

    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("builtins.open", mock_open(read_data=mock_json))
    mocker.patch("setting.config._load_config", return_value=mock_data)

    cfg = config.get_config()
    assert cfg["APPLICATION_NAME"] == "HealthMesh"

def test_save_config(tmp_path):
    mock_data = {"APPLICATION_NAME": "NewName"}
    test_cfg = str(tmp_path / "test_config.json")
    test_key = str(tmp_path / "test_key.key")

    key = config.generate_secure_key()
    with open(test_key, "wb") as f:
        f.write(key)

    config.save_config(mock_data, config_url=test_cfg, key_url=test_key)

    assert os.path.exists(test_cfg)
    with open(test_cfg, "r", encoding="utf-8") as f:
        saved = json.load(f)
    assert saved["APPLICATION_NAME"] == "NewName"


def test_validate_sql_driver(mocker):
    mocker.patch("pyodbc.drivers", return_value=["SQL Server Native Client 11.0", "ODBC Driver 17 for SQL Server"])
    assert config.validate_sql_driver("ODBC Driver 17 for SQL Server") is True
    assert config.validate_sql_driver("Non Existent Driver") is False

def test_get_available_sql_drivers(mocker):
    mocker.patch("pyodbc.drivers", return_value=["SQL Server Native Client 11.0", "PostgreSQL Unicode"])
    drivers = config.get_available_sql_drivers()
    assert "SQL Server Native Client 11.0" in drivers
    assert "PostgreSQL Unicode" not in drivers

def test_get_encryption_key_from_env(monkeypatch):
    custom_key = b"custom_secret_key_from_environment_var_1234="
    monkeypatch.setenv("HEALTHMESH_SECRET_KEY", custom_key.decode("utf-8"))
    key = config.get_encryption_key()
    assert key == custom_key

def test_mask_config_credentials():
    sample_cfg = {
        "APPLICATION_NAME": "HealthMesh",
        "DB_USER": "admin",
        "DB_PASSWORD": "SuperSecretPassword123!",
        "SERVER_PORT": 4000,
    }
    masked = config.mask_config_credentials(sample_cfg)
    assert masked["APPLICATION_NAME"] == "HealthMesh"
    assert masked["SERVER_PORT"] == 4000
    assert masked["DB_PASSWORD"] == "********"
    assert masked["DB_USER"] == "********"
    # Ensure original dict is unmodified
    assert sample_cfg["DB_PASSWORD"] == "SuperSecretPassword123!"

def test_atomic_save_and_load_config(tmp_path, monkeypatch):
    test_key_file = str(tmp_path / "test_key.key")
    test_cfg_file = str(tmp_path / "test_config.json")
    generated_key = config.generate_secure_key()
    with open(test_key_file, "wb") as f:
        f.write(generated_key)

    data_to_save = {
        "APPLICATION_NAME": "YourLIS_Testing",
        "SERVER_PORT": 5050,
        "DB_PASSWORD": "TestPassword456",
    }
    config.save_config(data_to_save, config_url=test_cfg_file, key_url=test_key_file)

    # Verify ciphertext on disk
    with open(test_cfg_file, "r") as f:
        disk_json = json.load(f)
    assert disk_json["APPLICATION_NAME"] == "YourLIS_Testing"
    assert disk_json["SERVER_PORT"] == 5050
    assert disk_json["DB_PASSWORD"] != "TestPassword456"

    # Verify roundtrip decryption via _load_config
    loaded = config._load_config(test_cfg_file, config.encrypt_list, test_key_file)
    assert loaded["DB_PASSWORD"] == "TestPassword456"


def test_atomic_replace_with_retry_recovers_from_transient_permission_error(tmp_path, mocker):
    """
    Verify that _atomic_replace_with_retry retries upon Windows file lock collision
    (PermissionError / WinError 32) and succeeds once the collision clears. (B-2 fix)
    """
    src_file = str(tmp_path / "src.tmp")
    dst_file = str(tmp_path / "dst.json")
    with open(src_file, "w") as f:
        f.write("test data")

    call_count = 0
    real_replace = os.replace

    def flaky_replace(src, dst):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise PermissionError("[WinError 32] The process cannot access the file because it is being used by another process")
        real_replace(src, dst)

    mocker.patch("os.replace", side_effect=flaky_replace)
    config._atomic_replace_with_retry(src_file, dst_file, max_retries=5, delay=0.01)

    assert call_count == 3
    assert os.path.exists(dst_file)


def test_get_api_token_from_env_or_generated(monkeypatch):
    """
    Verify get_api_token prefers HEALTHMESH_API_TOKEN environment variable when set. (B-3 fix)
    """
    monkeypatch.setenv("HEALTHMESH_API_TOKEN", "custom_secret_api_token_123")
    token = config.get_api_token()
    assert token == "custom_secret_api_token_123"

