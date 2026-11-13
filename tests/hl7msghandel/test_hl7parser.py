import pytest
from hl7msghandel.hl7parser import parse_hl7_message
from hl7msghandel.hl7validator import validate_hl7_message, get_required_segments
from unittest.mock import MagicMock

def test_parse_hl7_message_valid(mocker, mock_logger):
    # Simple HL7 message
    raw_message = "MSH|^~\\&|Sender|Receiver|20240101||ORU^R01|123|P|2.3.1\rPID|1||12345||Doe^John"

    # We mock validate to focus on parser
    mocker.patch("hl7msghandel.hl7parser.validate_hl7_message", return_value=True)

    parsed = parse_hl7_message(raw_message, "test_direction")

    assert parsed is not None
    # Verify MSH access using the actual parsed object structure
    # With hl7 library, parsed is a list of segments.
    # parsed.segments('MSH') returns a list of MSH segments.
    # [0] is the first MSH segment.
    # [0] is the first field of that segment.
    assert str(parsed.segments("MSH")[0][0]) == "MSH"

def test_parse_hl7_message_invalid(mocker, mock_logger):
    # Invalid message (exception during parsing)
    mocker.patch("hl7msghandel.hl7parser.parse", side_effect=Exception("Parse error"))

    parsed = parse_hl7_message("BadMessage", "test_direction")
    assert parsed is None

def test_validate_hl7_message_valid(mock_logger):
    # Create a mock HL7 message object
    mock_msg = MagicMock()
    # Mock __len__ to simulate having segments
    mock_msg.__len__.return_value = 2

    # MSH segment: Simple list of strings works for explicit index access like [0] and [9]
    mock_msh_segment = ["MSH", "", "", "", "", "", "", "", "", "ORU^R01"]

    # PID/OBR/OBX segments: Must be list of lists (simulating fields with components)
    # because the validation logic iterates fields and checks str(field[0])
    mock_pid_segment = [["PID"], ["1"]]
    mock_obr_segment = [["OBR"]]
    mock_obx_segment = [["OBX"]]

    # Mock the segments method
    # It returns a list of segments
    def segments_side_effect(name):
        if name == "MSH": return [mock_msh_segment]
        if name == "PID": return [mock_pid_segment]
        if name == "OBR": return [mock_obr_segment]
        if name == "OBX": return [mock_obx_segment]
        return []

    mock_msg.segments.side_effect = segments_side_effect

    assert validate_hl7_message(mock_msg, "in") is True

def test_validate_hl7_message_missing_msh(mock_logger):
    mock_msg = MagicMock()
    mock_msg.__len__.return_value = 1
    # Missing MSH
    mock_msg.segments.side_effect = lambda name: []

    assert validate_hl7_message(mock_msg, "in") is False

def test_get_required_segments():
    assert "OBX" in get_required_segments("ORM^O01")
    assert "PID" in get_required_segments("ORU^R01")
    assert "MSA" in get_required_segments("ACK")
    assert get_required_segments("Unknown") == []
