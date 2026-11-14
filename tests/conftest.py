import sys
from unittest.mock import MagicMock

# Mock pyodbc before it is imported by any module to avoid ImportError due to missing system libraries
mock_pyodbc = MagicMock()
class MockOperationalError(Exception): pass
class MockDatabaseError(Exception): pass
class MockInterfaceError(Exception): pass
class MockIntegrityError(Exception): pass
class MockProgrammingError(Exception): pass
class MockDataError(Exception): pass
class MockError(Exception): pass
mock_pyodbc.OperationalError = MockOperationalError
mock_pyodbc.DatabaseError = MockDatabaseError
mock_pyodbc.InterfaceError = MockInterfaceError
mock_pyodbc.IntegrityError = MockIntegrityError
mock_pyodbc.ProgrammingError = MockProgrammingError
mock_pyodbc.DataError = MockDataError
mock_pyodbc.Error = MockError
sys.modules["pyodbc"] = mock_pyodbc

import pytest
from unittest.mock import AsyncMock, mock_open
import os

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(autouse=True)
def reset_connection_pool():
    """Resets the singleton connection pool before and after each test."""
    try:
        from database.sqlconnection import get_connection_pool
        get_connection_pool().close_all()
    except Exception:
        pass
    yield
    try:
        from database.sqlconnection import get_connection_pool
        get_connection_pool().close_all()
    except Exception:
        pass

@pytest.fixture
def mock_logger(mocker):
    """Mocks the logger to suppress output."""
    mocker.patch("log.logger.log_info")
    mocker.patch("log.logger.log_error")
    mocker.patch("log.logger.log_warning")

@pytest.fixture
def mock_db_connection(mocker):
    """Mocks the database connection and cursor."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Setup default behavior for cursor
    mock_cursor.execute.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_cursor.description = []
    mock_cursor.nextset.return_value = None

    # Since we mocked pyodbc in sys.modules, we need to ensure tests can still access/patch it if needed
    # But usually patching pyodbc.connect in tests works on the mock object in sys.modules
    mocker.patch("pyodbc.connect", return_value=mock_conn)

    return mock_conn, mock_cursor

@pytest.fixture
def mock_config(mocker):
    """Mocks the configuration dictionary."""
    config_data = {
        "APPLICATION_NAME": "TestApp",
        "VERSION": "1.0.0",
        "DB_DRIVE": "ODBC Driver 17 for SQL Server",
        "DB_HOST": "localhost",
        "DB_PORT": 1433,
        "DB_NAME": "TestDB",
        "DB_USER": "sa",
        "DB_PASSWORD": "password",
        "DB_TYPE": "local",
        "SERVER_HOST": "127.0.0.1",
        "SERVER_PORT": 4000,
        "CBC_TEST_CODE": 56,
        "HGB_TEST_CODE": 50,
        "TEST_FINISH_CODE": False,
        "SUPPORTED_DEVICES": {},
        "KEY_URL": "test_key.key",
        "CONFIG_URL": "test_config.json",
        "API_PORT": 8000,
        "API_IP": "127.0.0.1"
    }
    mocker.patch("setting.config.get_config", return_value=config_data)
    return config_data
