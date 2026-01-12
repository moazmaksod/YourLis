import pytest
import asyncio
from server.server import is_valid_ip, is_server_running, run_server, start_server, stop_server
from unittest.mock import AsyncMock, MagicMock

def test_is_valid_ip():
    assert is_valid_ip("127.0.0.1") is True
    assert is_valid_ip("256.256.256.256") is False
    assert is_valid_ip("localhost") is False # inet_aton doesn't resolve names generally

def test_is_server_running_default():
    # It might be running or not depending on order, but we can check it returns boolean
    assert isinstance(is_server_running(), bool)

@pytest.mark.asyncio
async def test_server_lifecycle(mocker, mock_logger, mock_config):
    # Mock asyncio.start_server
    mock_server = AsyncMock()
    mock_server.serve_forever = AsyncMock()
    mock_server.wait_closed = AsyncMock()
    mock_server.close = MagicMock()

    # We need to support async context manager for `async with server:`
    mock_server.__aenter__.return_value = mock_server
    mock_server.__aexit__.return_value = None

    mocker.patch("asyncio.start_server", return_value=mock_server)

    # Run server in background task
    task = asyncio.create_task(run_server())

    # Allow some time for it to "start"
    await asyncio.sleep(0.1)

    assert is_server_running() is True

    # Stop server
    await stop_server()

    await task

    assert is_server_running() is False

from server.server import client_connected
@pytest.mark.asyncio
async def test_client_connected(mocker, mock_logger):
    reader = AsyncMock()
    writer = MagicMock()

    mocker.patch("server.server.handle_client_connection", new_callable=AsyncMock)

    await client_connected(reader, writer)

    # handle_client_connection should have been called
    import server.server
    server.server.handle_client_connection.assert_called_once()
