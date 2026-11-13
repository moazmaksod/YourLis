import pytest
from hl7msghandel.hl7fitsql import update_hl7_dictionary
from unittest.mock import MagicMock

def test_update_hl7_dictionary_sql_data(mock_logger):
    hl7_msg = MagicMock()

    hl7_dict = {
        "COLUMN_NAME": {"Col1": "SQL"},
        "CONDITION": {}
    }

    sql_data = {"Col1": "NewValue"}

    updated = update_hl7_dictionary(hl7_msg, hl7_dict, sql_data=sql_data)

    assert updated["COLUMN_NAME"]["Col1"] == "NewValue"

def test_update_hl7_dictionary_manual_data(mock_logger):
    hl7_msg = MagicMock()

    hl7_dict = {
        "COLUMN_NAME": {"Col1": "MANUAL"},
        "CONDITION": {}
    }

    manual_data = {"Col1": "ManualValue"}

    updated = update_hl7_dictionary(hl7_msg, hl7_dict, manual_data=manual_data)

    # Logic says for MANUAL: update if provided, then append to delete list?
    # Code:
    # if manual_data is not None: result_dictionary[key] = manual_data[key]
    # result_dictionary_deleted_list.append(key)
    # ...
    # del result_dictionary[result]

    # So it updates it then deletes it from result_dictionary?
    # Let's check logic:
    # "Remove keys from the result dictionary that were marked for deletion"

    # If it is deleted, it won't be in the output.
    assert "Col1" not in updated["COLUMN_NAME"]

def test_update_hl7_dictionary_from_msg(mock_logger):
    hl7_msg = MagicMock()
    # Mock segments access
    # segment = result_dictionary[key]["S"] -> e.g. "PID"
    # s_number = int(result_dictionary[key]["N"]) -> e.g. 0
    # field = int(result_dictionary[key]["F"]) -> e.g. 3

    # Setup mock to return "ValueFromMsg" for segments("PID")[0][3]
    mock_segment = MagicMock()
    mock_segment.__getitem__.return_value = "ValueFromMsg" # field access

    hl7_msg.segments.return_value = [mock_segment] # segment list access

    hl7_dict = {
        "COLUMN_NAME": {
            "Col1": {"S": "PID", "N": "0", "F": "3"}
        },
        "CONDITION": {
            "Cond1": {"S": "MSH", "N": "0", "F": "9"}
        }
    }

    updated = update_hl7_dictionary(hl7_msg, hl7_dict)

    assert updated["COLUMN_NAME"]["Col1"] == "ValueFromMsg"
    # Verify call
    hl7_msg.segments.assert_any_call("PID")


def test_update_hl7_dictionary_missing_segment_sets_none(mock_logger):
    """
    Verify that when an HL7 segment extraction fails (missing segment/field),
    the field value is set explicitly to None instead of leaving dictionary metadata.
    """
    hl7_msg = MagicMock()
    # Simulate missing OBX segment throwing IndexError
    hl7_msg.segments.side_effect = IndexError("Segment not found")

    hl7_dict = {
        "COLUMN_NAME": {
            "MissingTest": {"S": "OBX", "N": "15", "F": "5"}
        },
        "CONDITION": {
            "MissingCond": {"S": "OBX", "N": "15", "F": "3"}
        }
    }

    updated = update_hl7_dictionary(hl7_msg, hl7_dict)

    # Values must be None (representing SQL NULL), NOT the {"S": ..., "N": ..., "F": ...} dict!
    assert updated["COLUMN_NAME"]["MissingTest"] is None
    assert updated["CONDITION"]["MissingCond"] is None

