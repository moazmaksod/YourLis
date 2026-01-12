from fastapi.testclient import TestClient
from api.app import app
import pytest

client = TestClient(app)

def test_get_server_status(mocker):
    mocker.patch("api.app.is_server_running", return_value=True)
    mocker.patch("api.app.clients_with_names", {"127.0.0.1": "TestClient"})

    response = client.get("/server/status")

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "Online"
    assert data["clients"] == {"127.0.0.1": "TestClient"}

def test_get_messages(mocker):
    messages = [
        {"timestamp": "2024-01-01", "client_name": "Test", "client_address": "127.0.0.1", "message": "msg", "direction": "in"},
        {"timestamp": "2024-01-01", "client_name": "Test", "client_address": None, "message": "msg", "direction": "in"}
    ]
    mocker.patch("api.app.get_communication_messages", return_value=messages)

    response = client.get("/server/messages")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[1]["client_address"] == "Unknown Client"

def test_start_server_api(mocker):
    mock_start = mocker.patch("api.app.start_server", new_callable=mocker.AsyncMock)

    response = client.post("/server/start")

    assert response.status_code == 200
    mock_start.assert_called_once()

def test_stop_server_api(mocker):
    mock_stop = mocker.patch("api.app.stop_server", new_callable=mocker.AsyncMock)

    response = client.post("/server/stop")

    assert response.status_code == 200
    mock_stop.assert_called_once()
