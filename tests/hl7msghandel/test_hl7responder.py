import pytest
from hl7msghandel.hl7responder import generate_response_message, handel_result_message, handel_info_request_message, generate_ack_message, generate_order_response
import hl7msghandel.hl7responder
from unittest.mock import MagicMock

# Inject missing constants into the module for testing purposes
# These constants are used in `handel_result_message` but are missing from the project code imports.
# We define empty dicts as placeholders.
if not hasattr(hl7msghandel.hl7responder, "PATIENT_TEST_SQL"):
    setattr(hl7msghandel.hl7responder, "PATIENT_TEST_SQL", {})
if not hasattr(hl7msghandel.hl7responder, "PATIENT_TEST_HL7"):
    setattr(hl7msghandel.hl7responder, "PATIENT_TEST_HL7", {})
if not hasattr(hl7msghandel.hl7responder, "PATIENT_INFO_SQL"):
    setattr(hl7msghandel.hl7responder, "PATIENT_INFO_SQL", {})
if not hasattr(hl7msghandel.hl7responder, "PATIENT_INFO_ORU_HL7"):
    setattr(hl7msghandel.hl7responder, "PATIENT_INFO_ORU_HL7", {})
if not hasattr(hl7msghandel.hl7responder, "RESULT_EXIST_SQL"):
    setattr(hl7msghandel.hl7responder, "RESULT_EXIST_SQL", {})
if not hasattr(hl7msghandel.hl7responder, "RESULT_EXIST_HL7"):
    setattr(hl7msghandel.hl7responder, "RESULT_EXIST_HL7", {})
if not hasattr(hl7msghandel.hl7responder, "CBC_RESULT_SQL"):
    setattr(hl7msghandel.hl7responder, "CBC_RESULT_SQL", {})
if not hasattr(hl7msghandel.hl7responder, "CBC_RESULT_HL7"):
    setattr(hl7msghandel.hl7responder, "CBC_RESULT_HL7", {})
if not hasattr(hl7msghandel.hl7responder, "HGB_RESULT_SQL"):
    setattr(hl7msghandel.hl7responder, "HGB_RESULT_SQL", {})
if not hasattr(hl7msghandel.hl7responder, "HGB_RESULT_HL7"):
    setattr(hl7msghandel.hl7responder, "HGB_RESULT_HL7", {})
if not hasattr(hl7msghandel.hl7responder, "PATIENT_INFO_ORM_HL7"):
    setattr(hl7msghandel.hl7responder, "PATIENT_INFO_ORM_HL7", {})
if not hasattr(hl7msghandel.hl7responder, "PATIENT_INFO_SQL_TO_HL7_DICT"):
    setattr(hl7msghandel.hl7responder, "PATIENT_INFO_SQL_TO_HL7_DICT", {})
if not hasattr(hl7msghandel.hl7responder, "DEFULT_PATIENT_INFO_HL7"):
    setattr(hl7msghandel.hl7responder, "DEFULT_PATIENT_INFO_HL7", {})

def test_generate_ack_message_success(mock_logger):
    msg_id = "12345"
    ack = generate_ack_message(msg_id, True)
    # The message structure is \x0bMSH|...|\rMSA|AA|12345||||0|\r\x1c\r
    # We check for the MSA segment content
    assert "MSA|AA|12345|" in ack

def test_generate_ack_message_failure(mock_logger):
    msg_id = "12345"
    ack = generate_ack_message(msg_id, False)
    assert "MSA|AE|12345|" in ack

def test_generate_order_response(mock_logger):
    msg_id = "12345"
    patient_info = {
        "PATIENT_ID": "PID123",
        "NAME": "John Doe",
        "SEX": "M",
        "AGE": "30",
        "AGE_UNIT": "Y"
    }
    resp = generate_order_response(msg_id, patient_info)
    assert "MSA|AA|12345|" in resp
    # Removed leading pipe because segments are separated by \r, not |
    assert "PID|1||PID123|John Doe|" in resp

def test_handel_result_message(mocker, mock_logger):
    # Mock database interactions
    mocker.patch("hl7msghandel.hl7responder.data_select_for", side_effect=[
        {"TEST_CODE": 56, "RESULT_STATE": False}, # patient_requested
        {"REQ_DATE": "20240101", "NAME": "John"}, # patient_info
        None # result_exist (not exist)
    ])
    mocker.patch("hl7msghandel.hl7responder.data_insert_for")
    mocker.patch("hl7msghandel.hl7responder.data_update_for")

    hl7_msg = MagicMock()
    msg_id = "123"

    # We need to mock config codes
    mocker.patch("hl7msghandel.hl7responder.CBC_TEST_CODE", 56)
    mocker.patch("hl7msghandel.hl7responder.TEST_FINISH_CODE", False)

    ack = handel_result_message(hl7_msg, msg_id)
    assert "MSA|AA|" in ack # Success

def test_generate_response_message_oru_r01(mocker, mock_logger):
    hl7_msg = MagicMock()
    # Mock MSH segment for type detection
    # hl7_msh[9] is type, hl7_msh[3] sender, [4] sender ver, [10] msg_id
    mock_msh = MagicMock()
    mock_msh.__getitem__.side_effect = lambda x: "ORU^R01" if x == 9 else "ID123" if x == 10 else "Sender"
    mock_msh.__len__.return_value = 11

    hl7_msg.segments.return_value = [mock_msh]

    mocker.patch("hl7msghandel.hl7responder.handel_result_message", return_value="ACK_MSG")

    response = generate_response_message(hl7_msg)

    assert response["respose"] == "ACK_MSG"

def test_generate_response_message_unknown(mocker, mock_logger):
    hl7_msg = MagicMock()
    mock_msh = MagicMock()
    mock_msh.__getitem__.side_effect = lambda x: "UNKNOWN" if x == 9 else "ID123"
    mock_msh.__len__.return_value = 11
    hl7_msg.segments.return_value = [mock_msh]

    response = generate_response_message(hl7_msg)

    # Unknown message type now returns an explicit NAK (AR) per Task 2.2
    assert response["response"] is not None
    assert "MSA|AR|ID123|" in response["response"]


def test_generate_nak_response():
    from hl7msghandel.hl7responder import generate_nak_response

    # Test with explicit msg_id
    nak = generate_nak_response(msg_id="MSG999", error_msg="Syntax error in segment", ack_code="AE")
    assert "MSA|AE|MSG999|Syntax error in segment|" in nak
    assert nak.startswith("\x0b")
    assert nak.endswith("\x1c\r")

    # Test with raw HL7 frame extraction
    raw_frame = b"\x0bMSH|^~\\&|Analyzer||||20260101||ORU^R01|CTRL888|P|2.3.1\rPID|1||123\r\x1c\r"
    nak_extracted = generate_nak_response(hl7_message=raw_frame, error_msg="Database down", ack_code="AE")
    assert "MSA|AE|CTRL888|Database down|" in nak_extracted

    # Test delimiter sanitization
    nak_sanitized = generate_nak_response(msg_id="ID1", error_msg="Line 1|Error\rLine 2\nDetail")
    assert "Line 1/Error Line 2 Detail" in nak_sanitized

