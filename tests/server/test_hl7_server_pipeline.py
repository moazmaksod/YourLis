import asyncio
import pytest
from unittest.mock import patch, MagicMock
from server.client_handler import handle_client_connection


@pytest.mark.asyncio
async def test_end_to_end_mllp_tcp_pipeline(mocker):
    """
    Integration test: starts an in-process TCP server, connects a client,
    and exchanges multiple MLLP-framed HL7 messages (ORU^R01, ORM^O01, and invalid),
    verifying proper ACK/ORR/NAK framing and socket persistence across messages.
    """
    # Mock DB calls in hl7responder so tests run without live SQL Server
    mocker.patch(
        "hl7msghandel.hl7responder.data_select_for",
        side_effect=lambda sql, map_dict, msg: {
            "TEST_CODE": 56,
            "RESULT_STATE": False,
            "PATIENT_ID": "PAT02",
            "NAME": "DOE^JANE",
            "SEX": "F",
            "AGE": "28",
            "AGE_UNIT": "Y",
        },
    )
    mocker.patch("hl7msghandel.hl7responder.data_insert_for", return_value=None)
    mocker.patch("hl7msghandel.hl7responder.data_update_for", return_value=None)
    mocker.patch("hl7msghandel.hl7responder.CBC_TEST_CODE", 56)
    mocker.patch("hl7msghandel.hl7responder.TEST_FINISH_CODE", False)

    server = await asyncio.start_server(handle_client_connection, "127.0.0.1", 0)
    server_port = server.sockets[0].getsockname()[1]

    async def run_client():
        reader, writer = await asyncio.open_connection("127.0.0.1", server_port)

        # 1. Send ORU^R01 result message
        oru_frame = (
            b"\x0bMSH|^~\\&|Analyzer|Lab|||20260101120000||ORU^R01|MSG_ORU_100|P|2.3.1\r"
            b"PID|1||PAT01||DOE^JOHN\r"
            b"OBX|1|NM|WBC||6.5|10^3/uL\r\x1c\r"
        )
        writer.write(oru_frame)
        await writer.drain()

        # Read ACK response
        ack_data = await asyncio.wait_for(reader.readuntil(b"\x1c\r"), timeout=5.0)
        ack_text = ack_data.decode("utf-8")
        assert "MSA|AA|MSG_ORU_100|" in ack_text
        assert ack_text.startswith("\x0bMSH|")

        # 2. Send ORM^O01 order query message on the SAME socket connection
        orm_frame = (
            b"\x0bMSH|^~\\&|Analyzer|Lab|||20260101120000||ORM^O01|MSG_ORM_200|P|2.3.1\r"
            b"ORC|NW|ORD01|PAT02\r\x1c\r"
        )
        writer.write(orm_frame)
        await writer.drain()

        # Read ORR^O02 response
        orr_data = await asyncio.wait_for(reader.readuntil(b"\x1c\r"), timeout=5.0)
        orr_text = orr_data.decode("utf-8")
        assert "MSA|AA|MSG_ORM_200|" in orr_text
        assert "ORR^O02" in orr_text
        assert "PID|1||PAT02|DOE^JANE|" in orr_text

        # 3. Send unsupported message type on the SAME socket to verify NAK and persistence
        unsupported_frame = (
            b"\x0bMSH|^~\\&|Analyzer|Lab|||20260101120000||ADT^A01|MSG_ADT_300|P|2.3.1\r\x1c\r"
        )
        writer.write(unsupported_frame)
        await writer.drain()

        # Read NAK response
        nak_data = await asyncio.wait_for(reader.readuntil(b"\x1c\r"), timeout=5.0)
        nak_text = nak_data.decode("utf-8")
        assert "MSA|AR|MSG_ADT_300|" in nak_text

        # Clean close
        writer.close()
        await writer.wait_closed()

    try:
        await run_client()
    finally:
        server.close()
        await server.wait_closed()
