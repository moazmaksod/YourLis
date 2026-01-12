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

def test_save_config(mocker):
    mock_data = {"APPLICATION_NAME": "NewName"}

    mocker.patch("setting.config._load_config", return_value=config.default_config_data.copy())
    mocker.patch("os.path.exists", return_value=True)

    # Mock open for both reading key and writing config/key
    m = mock_open(read_data=b"somekey")
    mocker.patch("builtins.open", m)

    mocker.patch("setting.config.encrypt_value", return_value="encrypted")

    config.save_config(mock_data)

    # Verify file was written
    # We expect calls to write key and write config
    assert m.call_count >= 1


def test_validate_sql_driver(mocker):
    mocker.patch("pyodbc.drivers", return_value=["SQL Server Native Client 11.0", "ODBC Driver 17 for SQL Server"])
    assert config.validate_sql_driver("ODBC Driver 17 for SQL Server") is True
    assert config.validate_sql_driver("Non Existent Driver") is False

def test_get_available_sql_drivers(mocker):
    mocker.patch("pyodbc.drivers", return_value=["SQL Server Native Client 11.0", "PostgreSQL Unicode"])
    drivers = config.get_available_sql_drivers()
    assert "SQL Server Native Client 11.0" in drivers
    assert "PostgreSQL Unicode" not in drivers
