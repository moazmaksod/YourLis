import pytest
from server.client_handler import add_communication_message, get_communication_messages, communication_messages, clients_with_names
from collections import deque

def test_add_communication_message(mock_logger):
    # Clear existing messages
    communication_messages.clear()
    clients_with_names.clear()

    clients_with_names["127.0.0.1,1234"] = "TestDevice"

    add_communication_message(("127.0.0.1", 1234), "Test Message", "in")

    msgs = get_communication_messages()
    assert len(msgs) == 1
    assert msgs[0]["client_name"] == "TestDevice"
    assert msgs[0]["message"] == "Test Message"

def test_add_communication_message_unknown_client(mock_logger):
    communication_messages.clear()

    add_communication_message(("192.168.1.1", 5555), b"BytesMessage", "out")

    msgs = get_communication_messages()
    assert len(msgs) == 1
    assert msgs[0]["client_name"] == "192.168.1.1" # Should use IP if name unknown
    assert msgs[0]["message"] == "BytesMessage"


@pytest.mark.asyncio
async def test_handle_client_connection_resilient_error_nak(mocker, mock_logger):
    from server.client_handler import handle_client_connection
    from unittest.mock import AsyncMock, MagicMock

    bad_frame = b"\x0bMSH|^~\\&|BadDevice||||20260101||ORU^R01|MSG_ERR|P|2.3.1\r\x1c\r"
    good_frame = b"\x0bMSH|^~\\&|GoodDevice||||20260101||ORU^R01|MSG_OK|P|2.3.1\r\x1c\r"

    mock_reader = AsyncMock()
    mock_reader.read.side_effect = [bad_frame, good_frame, b""]

    written_packets = []
    mock_writer = MagicMock()
    mock_writer.get_extra_info.return_value = ("127.0.0.1", 9999)
    mock_writer.write.side_effect = lambda data: written_packets.append(data)
    mock_writer.drain = AsyncMock()
    mock_writer.wait_closed = AsyncMock()

    # handle_incoming_data raises error on first frame, succeeds on second
    async def mock_handle_incoming(msg):
        if b"MSG_ERR" in msg:
            raise ValueError("Simulated DB parsing failure")
        return ("\x0bMSH|...|\rMSA|AA|MSG_OK|\r\x1c\r", "GoodDevice")

    mocker.patch("server.client_handler.handle_incoming_data", side_effect=mock_handle_incoming)

    await handle_client_connection(mock_reader, mock_writer)

    # Verify both packets were answered
    assert len(written_packets) == 2
    # First response is NAK (MSA|AE|MSG_ERR)
    first_resp = written_packets[0].decode("utf-8") if isinstance(written_packets[0], bytes) else written_packets[0]
    assert "MSA|AE|MSG_ERR|" in first_resp
    # Second response is success ACK (MSA|AA|MSG_OK)
    second_resp = written_packets[1].decode("utf-8") if isinstance(written_packets[1], bytes) else written_packets[1]
    assert "MSA|AA|MSG_OK|" in second_resp

