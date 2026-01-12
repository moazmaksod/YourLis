import pytest
from server.client_handler import add_communication_message, get_communication_messages, communication_messages, clients_with_names
from collections import deque

def test_add_communication_message(mock_logger):
    # Clear existing messages
    communication_messages.clear()
    clients_with_names.clear()

    clients_with_names[("127.0.0.1", 1234)] = "TestDevice"

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
