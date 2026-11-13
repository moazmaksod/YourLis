from fastapi.testclient import TestClient
from api.app import app
from setting.config import get_api_token
import pytest

client = TestClient(app, headers={"X-Internal-Token": get_api_token()})

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


def test_get_patients_endpoint(mocker):
    fake_patients = [
        {"Patient ID": "P100", "Name": "John Doe", "Age": 30, "Gender": "M"}
    ]
    mocker.patch("database.sqlqueries.exec_procedure_for", mocker.AsyncMock(return_value=fake_patients))

    response = client.get("/api/v1/patients?name=John&status=Pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["Patient ID"] == "P100"


def test_get_patient_cbc_endpoint(mocker):
    fake_cbc = [{"Patient ID": "P100", "WBC": 7.5, "RBC": 4.8}]
    mocker.patch("database.sqlqueries.exec_procedure_for", mocker.AsyncMock(return_value=fake_cbc))

    response = client.get("/api/v1/patients/P100/cbc")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["WBC"] == 7.5


def test_get_send_outs_endpoint(mocker):
    fake_send_outs = [{"Patient ID": "P101", "Test Name": "Vitamin D", "Status": "Pending"}]
    mocker.patch("database.sqlqueries.exec_procedure_for", mocker.AsyncMock(return_value=fake_send_outs))

    response = client.get("/api/v1/send-out?status=Pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["Test Name"] == "Vitamin D"


def test_get_send_out_destinations_endpoint(mocker):
    fake_destinations = [{"gehahname": "Alpha Lab"}, {"gehahname": "Beta Diagnostics"}]
    mocker.patch("database.sqlqueries.exec_procedure_for", mocker.AsyncMock(return_value=fake_destinations))

    response = client.get("/api/v1/send-out/destinations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["gehahname"] == "Alpha Lab"


def test_update_send_out_financials_endpoint(mocker):
    mock_exec = mocker.patch("database.sqlqueries.exec_procedure_no_return", mocker.AsyncMock(return_value=None))

    payload = {
        "patient_id": "P100",
        "test_name": "CBC",
        "price": 150.0,
        "amount_paid": 150.0,
        "destination_lab": "Central Lab",
        "status": "Paid",
    }
    response = client.post("/api/v1/send-out/financials", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_exec.assert_called_once()


def test_mark_send_out_sent_endpoint(mocker):
    mock_exec = mocker.patch("database.sqlqueries.exec_procedure_no_return", mocker.AsyncMock(return_value=None))

    payload = {
        "patient_id": "P100",
        "test_name": "CBC",
    }
    response = client.post("/api/v1/send-out/sent", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_exec.assert_called_once()


def test_cors_middleware_headers():
    response = client.options(
        "/api/v1/patients",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # When allow_credentials=True, CORS echoes back the allowed origin
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_unauthenticated_protected_endpoint_returns_401():
    """
    Verify that protected endpoints reject requests without internal token with 401 Unauthorized. (B-3 fix)
    """
    unauth_client = TestClient(app)

    # 1. Domain endpoint
    resp1 = unauth_client.get("/api/v1/patients")
    assert resp1.status_code == 401

    # 2. Server control endpoint
    resp2 = unauth_client.post("/server/start")
    assert resp2.status_code == 401

    # 3. Server messages endpoint
    resp3 = unauth_client.get("/server/messages")
    assert resp3.status_code == 401

    # Public endpoint remains accessible without token
    resp_pub = unauth_client.get("/server/status")
    assert resp_pub.status_code == 200


def test_websocket_authentication():
    """
    Verify WebSocket rejects unauthenticated connections and accepts authenticated ones with token query param. (B-3 fix)
    """
    from starlette.websockets import WebSocketDisconnect

    unauth_client = TestClient(app)

    # Unauthenticated connection attempt
    with pytest.raises((WebSocketDisconnect, Exception)):
        with unauth_client.websocket_connect("/ws") as ws:
            ws.receive_json()

    # Authenticated connection attempt with token in query param
    token = get_api_token()
    with unauth_client.websocket_connect(f"/ws?token={token}") as ws:
        data = ws.receive_json()
        assert data["type"] == "status"

