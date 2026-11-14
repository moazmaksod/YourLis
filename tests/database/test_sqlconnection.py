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


def test_connection_pool_reuses_connection(mocker, mock_config):
    """Verify that multiple consecutive queries reuse the pooled connection without reconnecting."""
    from database.sqlconnection import get_db_connection_context, get_connection_pool

    mock_conn = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    mock_connect = mocker.patch("pyodbc.connect", return_value=mock_conn)

    # First checkout
    with get_db_connection_context() as conn1:
        assert conn1 is mock_conn

    # Second checkout should reuse the connection without calling pyodbc.connect again
    with get_db_connection_context() as conn2:
        assert conn2 is mock_conn

    # pyodbc.connect should have been called only once
    mock_connect.assert_called_once()


def test_connection_pool_evicts_broken_connection(mocker, mock_config):
    """Verify that broken connections throwing OperationalError are evicted and not returned to pool."""
    from database.sqlconnection import get_db_connection_context, get_connection_pool
    pool = get_connection_pool()

    mock_conn1 = mocker.MagicMock()
    mock_conn2 = mocker.MagicMock()

    mock_connect = mocker.patch("pyodbc.connect", side_effect=[mock_conn1, mock_conn2])

    # First checkout encounters an OperationalError (e.g. server reset)
    with pytest.raises(pyodbc.OperationalError):
        with get_db_connection_context() as conn:
            assert conn is mock_conn1
            raise pyodbc.OperationalError("Communication link failure")

    # Conn1 should be closed/discarded
    mock_conn1.close.assert_called()

    # Next checkout should acquire a new healthy connection (conn2)
    with get_db_connection_context() as conn:
        assert conn is mock_conn2

    assert mock_connect.call_count == 2


def test_connection_pool_rollback_on_release_and_is_alive(mocker, mock_config):
    """
    Verify ConnectionPool executes rollback on _is_alive ping and release_connection
    to prevent dangling transactions on SQL Server. (M-3 fix)
    """
    from database.sqlconnection import get_connection_pool

    pool = get_connection_pool()
    mock_conn = mocker.MagicMock()
    mock_cursor = mocker.MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # 1. Test _is_alive rolls back after SELECT 1
    alive = pool._is_alive(mock_conn)
    assert alive is True
    mock_cursor.execute.assert_called_with("SELECT 1")
    mock_conn.rollback.assert_called()

    # 2. Test release_connection rolls back before returning to pool
    mock_conn.reset_mock()
    pool.release_connection(mock_conn, discard=False)
    mock_conn.rollback.assert_called_once()

    # 3. Test release_connection discards connection if rollback throws error
    mock_broken_conn = mocker.MagicMock()
    mock_broken_conn.rollback.side_effect = Exception("Broken socket")
    pool.release_connection(mock_broken_conn, discard=False)
    mock_broken_conn.close.assert_called_once()


def test_connection_pool_bounds_max_connections_and_timeout(mocker, mock_config):
    """Verify ConnectionPool raises ConnectionError when pool is exhausted."""
    from database.sqlconnection import ConnectionPool
    pool = ConnectionPool(max_connections=2, timeout=0.1)

    mock_conn1 = mocker.MagicMock()
    mock_conn2 = mocker.MagicMock()
    mocker.patch("pyodbc.connect", side_effect=[mock_conn1, mock_conn2])

    c1 = pool.get_connection()
    c2 = pool.get_connection()

    # Attempting 3rd checkout must timeout and raise ConnectionError
    with pytest.raises(ConnectionError, match="exhausted"):
        pool.get_connection()

    # Once a connection is released, checkout succeeds
    pool.release_connection(c1)
    c3 = pool.get_connection()
    assert c3 is c1


def test_connection_pool_prevents_double_release(mocker, mock_config):
    """Verify releasing the same connection twice does not corrupt semaphore or pool queue."""
    from database.sqlconnection import ConnectionPool
    pool = ConnectionPool(max_connections=2, timeout=0.1)

    mock_conn = mocker.MagicMock()
    mocker.patch("pyodbc.connect", return_value=mock_conn)

    c = pool.get_connection()
    pool.release_connection(c)
    # Second release should be safely ignored
    pool.release_connection(c)

    # Queue should contain only 1 instance of c
    assert pool._pool.qsize() == 1


def test_setup_database_schema_executes_all_scripts(mocker, mock_db_connection):
    from database.db_schema import setup_database_schema
    conn, cursor = mock_db_connection
    mocker.patch("database.db_schema.get_db_connection", return_value=conn)
    setup_database_schema()
    assert cursor.execute.call_count >= 8
    conn.commit.assert_called_once()

