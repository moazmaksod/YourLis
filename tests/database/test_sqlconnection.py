import pytest
import pyodbc
from database.sqlconnection import get_db_connection

def test_get_db_connection_local(mocker, mock_config):
    mock_config["DB_TYPE"] = "local"
    mocker.patch("setting.config.get_config", return_value=mock_config)

    mock_connect = mocker.patch("pyodbc.connect")

    get_db_connection()

    mock_connect.assert_called_once()
    args, kwargs = mock_connect.call_args
    conn_str = args[0]
    assert "SERVER=localhost" in conn_str
    assert "DATABASE=TestDB" in conn_str

def test_get_db_connection_online(mocker, mock_config):
    mock_config["DB_TYPE"] = "online"
    mocker.patch("setting.config.get_config", return_value=mock_config)

    mock_connect = mocker.patch("pyodbc.connect")

    get_db_connection()

    mock_connect.assert_called_once()
    args, kwargs = mock_connect.call_args
    conn_str = args[0]
    assert "SERVER=localhost,1433" in conn_str

def test_get_db_connection_invalid(mocker, mock_config):
    mock_config["DB_TYPE"] = "invalid"
    mocker.patch("setting.config.get_config", return_value=mock_config)

    with pytest.raises(ValueError):
        get_db_connection()

def test_get_db_connection_failure(mocker, mock_config):
    mock_config["DB_TYPE"] = "local"
    mocker.patch("setting.config.get_config", return_value=mock_config)

    mocker.patch("pyodbc.connect", side_effect=Exception("Connection failed"))

    with pytest.raises(ConnectionError):
        get_db_connection()
