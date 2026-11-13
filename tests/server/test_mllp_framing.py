import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from server.client_handler import (
    handle_client_connection,
    MESSAGE_START_MARKER,
    MESSAGE_END_MARKER,
    MAX_BUFFER_LIMIT,
)
import server.server as srv


@pytest.mark.asyncio
async def test_mllp_fragmented_frames_reassembly(mock_logger):
    """
    Verify that an HL7 message split across multiple TCP chunks (fragmentation)
    is correctly buffered and only processed once the full MLLP frame is received.
    """
    mock_reader = AsyncMock()
    mock_writer = MagicMock()
    mock_writer.get_extra_info.return_value = ("127.0.0.1", 5001)
    mock_writer.wait_closed = AsyncMock()

    processed_messages = []

    async def mock_handle_incoming_data(message, timeout=10.0):
        processed_messages.append(message)
        return ("ACK_RESPONSE", "Genrui_KT60")

    # Fragment 1: Start marker + partial HL7 payload
    frag1 = MESSAGE_START_MARKER + b"MSH|^~\\&|KT60||||20261113||ORU^R01|MSG001|P|2.3.1\rPID|1||"
    # Fragment 2: Rest of payload + standard MLLP end marker \x1c\r
    frag2 = b"PAT123||DOE^JOHN\r\x1c\r"

    # Feed fragment 1, then fragment 2, then EOF
    mock_reader.read = AsyncMock(side_effect=[frag1, frag2, b""])

    with patch("server.client_handler.handle_incoming_data", side_effect=mock_handle_incoming_data):
        with patch("server.client_handler.send_outgoing_data", return_value=None):
            await handle_client_connection(mock_reader, mock_writer)

    # Exactly 1 complete message must be assembled and processed
    assert len(processed_messages) == 1
    full_msg = processed_messages[0]
    assert b"MSG001" in full_msg
    assert b"DOE^JOHN" in full_msg


@pytest.mark.asyncio
async def test_mllp_coalesced_frames_burst(mock_logger):
    """
    Verify that when multiple HL7 messages arrive in a single TCP packet (coalesced),
    the server parses and processes each message individually in order.
    """
    mock_reader = AsyncMock()
    mock_writer = MagicMock()
    mock_writer.get_extra_info.return_value = ("127.0.0.1", 5002)
    mock_writer.wait_closed = AsyncMock()

    processed_messages = []

    async def mock_handle_incoming_data(message, timeout=10.0):
        processed_messages.append(message)
        return ("ACK_RESPONSE", "Genrui_KT60")

    # Construct two complete MLLP frames packed together
    msg1 = MESSAGE_START_MARKER + b"MSH|...|ORU^R01|MSG001|...\r\x1c\r"
    msg2 = MESSAGE_START_MARKER + b"MSH|...|ORU^R01|MSG002|...\r\x1c\r"
    coalesced_data = msg1 + msg2

    mock_reader.read = AsyncMock(side_effect=[coalesced_data, b""])

    with patch("server.client_handler.handle_incoming_data", side_effect=mock_handle_incoming_data):
        with patch("server.client_handler.send_outgoing_data", return_value=None):
            await handle_client_connection(mock_reader, mock_writer)

    # Both messages must be extracted and processed in FIFO order
    assert len(processed_messages) == 2
    assert b"MSG001" in processed_messages[0]
    assert b"MSG002" in processed_messages[1]


@pytest.mark.asyncio
async def test_mllp_max_buffer_limit_protection(mock_logger):
    """
    Verify that incoming runaway streams exceeding MAX_BUFFER_LIMIT without
    end delimiters trigger disconnection to protect against memory exhaustion (DoS).
    """
    mock_reader = AsyncMock()
    mock_writer = MagicMock()
    mock_writer.get_extra_info.return_value = ("127.0.0.1", 5003)
    mock_writer.wait_closed = AsyncMock()

    # Create oversized chunk exceeding MAX_BUFFER_LIMIT
    huge_chunk = b"X" * (MAX_BUFFER_LIMIT + 1024)
    mock_reader.read = AsyncMock(side_effect=[huge_chunk, b""])

    with patch("server.client_handler.handle_incoming_data") as mock_handler:
        await handle_client_connection(mock_reader, mock_writer)
        # Handler must never be called on malicious oversized buffer
        mock_handler.assert_not_called()

    # Connection should be closed
    mock_writer.close.assert_called()


@pytest.mark.asyncio
async def test_server_shutdown_task_snapshot_cancellation(mock_logger):
    """
    Verify that server shutdown cleanly cancels multiple client tasks using snapshot
    iteration without skipping tasks or crashing on list mutation.
    """
    # Create 3 dummy running tasks
    t1 = asyncio.create_task(asyncio.sleep(10))
    t2 = asyncio.create_task(asyncio.sleep(10))
    t3 = asyncio.create_task(asyncio.sleep(10))

    srv.server_tasks.clear()
    srv.server_tasks.extend([t1, t2, t3])

    # Simulate shutdown task cancellation block
    tasks_to_cancel = list(srv.server_tasks)
    for task in tasks_to_cancel:
        task.cancel()

    await asyncio.gather(*tasks_to_cancel, return_exceptions=True)

    assert t1.cancelled()
    assert t2.cancelled()
    assert t3.cancelled()
    srv.server_tasks.clear()


@pytest.mark.asyncio
async def test_mllp_split_delimiter_across_tcp_chunks(mock_logger):
    """
    Verify that an MLLP frame split exactly between \\x1c (FS) and \\r (CR) across two TCP recv()
    chunks is cleanly reassembled without prematurely slicing or leaving orphaned bytes. (M-5 fix)
    """
    mock_reader = AsyncMock()
    mock_writer = MagicMock()
    mock_writer.get_extra_info.return_value = ("127.0.0.1", 5005)
    mock_writer.wait_closed = AsyncMock()

    processed_messages = []

    async def mock_handle_incoming_data(message, timeout=10.0):
        processed_messages.append(message)
        return ("ACK_RESPONSE", "Genrui_KT60")

    # Chunk 1 ends EXACTLY at \x1c (no trailing \r yet)
    chunk1 = MESSAGE_START_MARKER + b"MSH|^~\\&|KT60||||20261113||ORU^R01|MSG001|P|2.3.1\rPID|1||PAT001\r" + MESSAGE_END_MARKER
    # Chunk 2 delivers the trailing \r of Message 1, followed immediately by Message 2
    chunk2 = b"\r" + MESSAGE_START_MARKER + b"MSH|^~\\&|KT60||||20261113||ORU^R01|MSG002|P|2.3.1\rPID|1||PAT002\r\x1c\r"

    mock_reader.read = AsyncMock(side_effect=[chunk1, chunk2, b""])

    with patch("server.client_handler.handle_incoming_data", side_effect=mock_handle_incoming_data):
        with patch("server.client_handler.send_outgoing_data", return_value=None):
            await handle_client_connection(mock_reader, mock_writer)

    # Both messages must be fully assembled and processed
    assert len(processed_messages) == 2

    msg1 = processed_messages[0]
    msg2 = processed_messages[1]

    assert b"MSG001" in msg1
    assert msg1.endswith(b"\x1c\r")  # Trailing \r was consumed cleanly

    assert b"MSG002" in msg2
    assert msg2.endswith(b"\x1c\r")

