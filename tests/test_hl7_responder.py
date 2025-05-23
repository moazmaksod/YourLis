import unittest
from unittest.mock import patch, MagicMock, ANY # ANY is useful for some call assertions
import queue # Though not directly used by hl7responder, it was in incoming_data

# Modules to be tested
from hl7msghandel import hl7responder
from hl7msghandel.hl7responder import generate_response_message, handel_result_message, handel_info_request_message

# Adapters that will be mocked
from database.database_adapter import DatabaseAdapter
from hl7msghandel.device_adapter import DeviceAdapter

# Mock for a parsed HL7 message (simulating hl7.Message object)
# This needs to be more flexible to simulate different segments and fields
def create_mock_parsed_message(message_type="ORU^R01", msh_fields=None, pid_fields=None, orc_fields=None, obr_fields=None):
    mock_msg = MagicMock()

    # Default MSH fields if not provided
    _msh_fields = msh_fields if msh_fields else ["MSH", "^~\\&", "Sender", "SenderFac", "Receiver", "ReceiverFac", "20230101120000", "", message_type, "MSGCTRL001", "P", "2.3.1"]
    
    # Ensure MSH fields list is long enough if specific indices are accessed
    # Pad with empty strings if necessary, common for optional trailing fields.
    # MSH.10 (Message Control ID) is index 9, MSH.9 (Message Type) is index 8
    # The code accesses up to index 10 for msg_id
    min_msh_len = 11 
    if len(_msh_fields) < min_msh_len:
        _msh_fields.extend([""] * (min_msh_len - len(_msh_fields)))


    mock_msg.segment = MagicMock(return_value=MagicMock()) # Default for segment('XYZ')
    mock_msg.segments = MagicMock(return_value=[MagicMock()]) # Default for segments('XYZ')

    # Configure specific segment behaviors
    def get_segment_by_name(name):
        if name == "MSH":
            msh_seg_mock = MagicMock()
            # Allow both direct indexing and string representation
            for i, val in enumerate(_msh_fields):
                msh_seg_mock.__getitem__.side_effect = lambda idx, _fields=_msh_fields: _fields[idx] if idx < len(_fields) else ""
            msh_seg_mock.__str__ = lambda: "|".join(map(str, _msh_fields))
            msh_seg_mock.__len__ = lambda: len(_msh_fields) # For length checks
            return msh_seg_mock
        if name == "PID" and pid_fields:
            pid_seg_mock = MagicMock()
            for i, val in enumerate(pid_fields):
                 pid_seg_mock.__getitem__.side_effect = lambda idx, _fields=pid_fields: _fields[idx] if idx < len(_fields) else ""
            return pid_seg_mock
        # Add ORC, OBR if needed for specific tests, though current responder doesn't deep dive them directly
        return MagicMock() # Default for other segments

    def get_segments_by_name(name):
        if name == "MSH":
            return [get_segment_by_name("MSH")]
        if name == "PID" and pid_fields:
            return [get_segment_by_name("PID")]
        return [MagicMock()] # Default for other segments

    mock_msg.segment.side_effect = get_segment_by_name
    mock_msg.segments.side_effect = get_segments_by_name
    
    return mock_msg


class TestHL7Responder(unittest.TestCase):

    def setUp(self):
        self.mock_db_adapter = MagicMock(spec=DatabaseAdapter)
        self.mock_device_adapter = MagicMock(spec=DeviceAdapter)

        # Mock config values that hl7responder uses
        self.mock_config = {
            "CBC_TEST_CODE": "CBC", # Assuming test codes are strings now based on hl7responder logic
            "HGB_TEST_CODE": "HGB",
            "TEST_FINISH_CODE": "FINISHED", # Assuming a string state
            "APPLICATION_NAME": "TestLIS",
            "VERSION": "1.0"
        }
        # Patch get_config used at the module level in hl7responder
        self.patcher_get_config = patch('hl7msghandel.hl7responder.get_config', return_value=self.mock_config)
        self.mock_get_config = self.patcher_get_config.start()
        
        # Refresh constants in hl7responder if they are set at module load time
        # This is a bit tricky. If hl7responder.py sets its global CBC_TEST_CODE etc.
        # only once at import time, our patch won't affect them unless we reload the module
        # or patch those constants directly. Let's patch them directly for safety.
        self.patcher_cbc_code = patch('hl7msghandel.hl7responder.CBC_TEST_CODE', self.mock_config["CBC_TEST_CODE"])
        self.patcher_hgb_code = patch('hl7msghandel.hl7responder.HGB_TEST_CODE', self.mock_config["HGB_TEST_CODE"])
        self.patcher_finish_code = patch('hl7msghandel.hl7responder.TEST_FINISH_CODE', self.mock_config["TEST_FINISH_CODE"])
        
        self.mock_cbc_code = self.patcher_cbc_code.start()
        self.mock_hgb_code = self.patcher_hgb_code.start()
        self.mock_finish_code = self.patcher_finish_code.start()

    def tearDown(self):
        self.patcher_get_config.stop()
        self.patcher_cbc_code.stop()
        self.patcher_hgb_code.stop()
        self.patcher_finish_code.stop()

    # --- Tests for generate_response_message ---
    @patch('hl7msghandel.hl7responder.handel_result_message')
    def test_generate_response_message_oru_r01(self, mock_handel_result):
        mock_parsed_msg = create_mock_parsed_message(message_type="ORU^R01", msh_fields=["MSH","^~\\&","App","Fac","","","20230101","","ORU^R01","MSGID001","P","2.3.1"])
        self.mock_device_adapter.parse_message.return_value = mock_parsed_msg # This line was missing in plan, but is implied
        self.mock_device_adapter.get_message_type.return_value = "ORU^R01"
        self.mock_device_adapter.get_device_identifier.return_value = "TestSender"
        mock_handel_result.return_value = "ACK_FOR_ORU"

        # Note: generate_response_message in refactored code expects raw_hl7_message, not parsed_msg
        # The initial plan was for generate_response_message to take raw, then call device_adapter.parse_message
        # Let's assume it's called with a raw message and it internally calls parse_message.
        raw_msg_str = "MSH|^~\\&|App|Fac|||20230101||ORU^R01|MSGID001|P|2.3.1" # Minimal raw message
        
        # If generate_response_message takes raw string:
        self.mock_device_adapter.parse_message.return_value = mock_parsed_msg
        # The MSH.10 (message_control_id) is extracted directly in generate_response_message
        # from the parsed_message, so mock_parsed_msg needs to support that.
        
        response_dict = generate_response_message(raw_msg_str, self.mock_device_adapter, self.mock_db_adapter)

        self.mock_device_adapter.parse_message.assert_called_once_with(raw_msg_str)
        self.mock_device_adapter.get_message_type.assert_called_once_with(mock_parsed_msg)
        self.mock_device_adapter.get_device_identifier.assert_called_once_with(mock_parsed_msg)
        mock_handel_result.assert_called_once_with(mock_parsed_msg, "MSGID001", self.mock_device_adapter, self.mock_db_adapter)
        self.assertEqual(response_dict, {"response": "ACK_FOR_ORU", "sender": "TestSender"})

    @patch('hl7msghandel.hl7responder.handel_info_request_message')
    def test_generate_response_message_orm_o01(self, mock_handel_info):
        mock_parsed_msg = create_mock_parsed_message(message_type="ORM^O01", msh_fields=["MSH","^~\\&","App","Fac","","","20230101","","ORM^O01","MSGID002","P","2.3.1"])
        self.mock_device_adapter.parse_message.return_value = mock_parsed_msg
        self.mock_device_adapter.get_message_type.return_value = "ORM^O01"
        self.mock_device_adapter.get_device_identifier.return_value = "TestOrderSender"
        mock_handel_info.return_value = "ORR_FOR_ORM"
        
        raw_msg_str = "MSH|^~\\&|App|Fac|||20230101||ORM^O01|MSGID002|P|2.3.1"
        response_dict = generate_response_message(raw_msg_str, self.mock_device_adapter, self.mock_db_adapter)

        mock_handel_info.assert_called_once_with(mock_parsed_msg, "MSGID002", self.mock_device_adapter, self.mock_db_adapter)
        self.assertEqual(response_dict, {"response": "ORR_FOR_ORM", "sender": "TestOrderSender"})

    def test_generate_response_message_ack(self):
        mock_parsed_msg = create_mock_parsed_message(message_type="ACK", msh_fields=["MSH","^~\\&","App","Fac","","","20230101","","ACK","MSGID003","P","2.3.1"])
        self.mock_device_adapter.parse_message.return_value = mock_parsed_msg
        self.mock_device_adapter.get_message_type.return_value = "ACK"
        self.mock_device_adapter.get_device_identifier.return_value = "AckSender"

        raw_msg_str = "MSH|^~\\&|App|Fac|||20230101||ACK|MSGID003|P|2.3.1"
        response_dict = generate_response_message(raw_msg_str, self.mock_device_adapter, self.mock_db_adapter)
        self.assertEqual(response_dict, {"response": None, "sender": "AckSender"})

    def test_generate_response_message_unknown_type(self):
        mock_parsed_msg = create_mock_parsed_message(message_type="UNKNOWN^XYZ", msh_fields=["MSH","^~\\&","App","Fac","","","20230101","","UNKNOWN^XYZ","MSGID004","P","2.3.1"])
        self.mock_device_adapter.parse_message.return_value = mock_parsed_msg
        self.mock_device_adapter.get_message_type.return_value = "UNKNOWN^XYZ"
        self.mock_device_adapter.get_device_identifier.return_value = "UnknownSender"

        raw_msg_str = "MSH|^~\\&|App|Fac|||20230101||UNKNOWN^XYZ|MSGID004|P|2.3.1"
        response_dict = generate_response_message(raw_msg_str, self.mock_device_adapter, self.mock_db_adapter)
        self.assertEqual(response_dict, {"response": None, "sender": "UnknownSender"})
        # Optionally, check for an ACK AR if the responder logic was updated to send one

    def test_generate_response_message_parse_failure(self):
        self.mock_device_adapter.parse_message.return_value = None
        raw_msg_str = "MALFORMED_HL7_MESSAGE"
        response_dict = generate_response_message(raw_msg_str, self.mock_device_adapter, self.mock_db_adapter)
        self.assertEqual(response_dict, {"response": None, "sender": None})

    # --- Tests for handel_result_message ---
    def test_handel_result_message_cbc_insert_success(self):
        mock_parsed_msg = create_mock_parsed_message() # Default ORU^R01
        msg_id = "ORU_MSG_001"
        self.mock_device_adapter.extract_result_data.return_value = ('CBC_PANEL', 'PID123', {'HGB': 12.5, 'WBC': 5.0})
        self.mock_db_adapter.get_patient_test_request.return_value = {'TEST_CODE': self.mock_config["CBC_TEST_CODE"], 'RESULT_STATE': self.mock_config["TEST_FINISH_CODE"]}
        self.mock_db_adapter.get_patient_info.return_value = {'name': 'Test Patient', 'requestDate': '20230101100000'}
        self.mock_db_adapter.check_result_exists.return_value = False # For insert

        handel_result_message(mock_parsed_msg, msg_id, self.mock_device_adapter, self.mock_db_adapter)

        self.mock_db_adapter.save_cbc_result.assert_called_once_with('PID123', {'HGB': 12.5, 'WBC': 5.0}, '20230101100000')
        self.mock_device_adapter.create_ack_message.assert_called_once_with(msg_id, "AA", None)

    def test_handel_result_message_cbc_update_success(self):
        mock_parsed_msg = create_mock_parsed_message()
        msg_id = "ORU_MSG_002"
        self.mock_device_adapter.extract_result_data.return_value = ('CBC_PANEL', 'PID124', {'HGB': 12.6})
        self.mock_db_adapter.get_patient_test_request.return_value = {'TEST_CODE': self.mock_config["CBC_TEST_CODE"], 'RESULT_STATE': self.mock_config["TEST_FINISH_CODE"]}
        self.mock_db_adapter.get_patient_info.return_value = {'name': 'Test Patient Upd', 'requestDate': '20230102100000'}
        self.mock_db_adapter.check_result_exists.return_value = True # For update

        handel_result_message(mock_parsed_msg, msg_id, self.mock_device_adapter, self.mock_db_adapter)

        self.mock_db_adapter.update_cbc_result.assert_called_once_with('PID124', {'HGB': 12.6}, '20230102100000')
        self.mock_device_adapter.create_ack_message.assert_called_once_with(msg_id, "AA", None)

    def test_handel_result_message_hgb_insert_success(self):
        mock_parsed_msg = create_mock_parsed_message()
        msg_id = "ORU_MSG_003"
        self.mock_device_adapter.extract_result_data.return_value = ('HGB_PANEL', 'PID125', {'HGB': 10.0})
        self.mock_db_adapter.get_patient_test_request.return_value = {'TEST_CODE': self.mock_config["HGB_TEST_CODE"], 'RESULT_STATE': self.mock_config["TEST_FINISH_CODE"]}
        self.mock_db_adapter.get_patient_info.return_value = {'name': 'Test Patient HGB', 'requestDate': '20230103100000'}
        self.mock_db_adapter.check_result_exists.return_value = False

        handel_result_message(mock_parsed_msg, msg_id, self.mock_device_adapter, self.mock_db_adapter)
        self.mock_db_adapter.save_hgb_result.assert_called_once_with('PID125', {'HGB': 10.0}, '20230103100000')
        self.mock_device_adapter.create_ack_message.assert_called_once_with(msg_id, "AA", None)

    def test_handel_result_message_patient_request_not_found(self):
        mock_parsed_msg = create_mock_parsed_message()
        msg_id = "ORU_MSG_004"
        self.mock_device_adapter.extract_result_data.return_value = ('CBC_PANEL', 'PID126', {'WBC': 1.0})
        self.mock_db_adapter.get_patient_test_request.return_value = None # Patient request not found

        handel_result_message(mock_parsed_msg, msg_id, self.mock_device_adapter, self.mock_db_adapter)
        self.mock_device_adapter.create_ack_message.assert_called_once_with(msg_id, "AE", ANY) # Error message can be specific

    def test_handel_result_message_test_not_finished_state(self):
        mock_parsed_msg = create_mock_parsed_message()
        msg_id = "ORU_MSG_005"
        self.mock_device_adapter.extract_result_data.return_value = ('CBC_PANEL', 'PID127', {'WBC': 1.0})
        self.mock_db_adapter.get_patient_test_request.return_value = {'TEST_CODE': self.mock_config["CBC_TEST_CODE"], 'RESULT_STATE': "PENDING"} # Not finished

        handel_result_message(mock_parsed_msg, msg_id, self.mock_device_adapter, self.mock_db_adapter)
        self.mock_device_adapter.create_ack_message.assert_called_once_with(msg_id, "AE", ANY)

    def test_handel_result_message_unknown_db_test_code(self):
        mock_parsed_msg = create_mock_parsed_message()
        msg_id = "ORU_MSG_006"
        self.mock_device_adapter.extract_result_data.return_value = ('CBC_PANEL', 'PID128', {'WBC': 1.0})
        self.mock_db_adapter.get_patient_test_request.return_value = {'TEST_CODE': "UNKNOWN_CODE", 'RESULT_STATE': self.mock_config["TEST_FINISH_CODE"]}
        self.mock_db_adapter.get_patient_info.return_value = {'name': 'Test Patient', 'requestDate': '20230101100000'} # Needed to reach the test code check

        handel_result_message(mock_parsed_msg, msg_id, self.mock_device_adapter, self.mock_db_adapter)
        self.mock_device_adapter.create_ack_message.assert_called_once_with(msg_id, "AE", ANY)
        
    # --- Tests for handel_info_request_message ---
    def test_handel_info_request_message_patient_found(self):
        mock_parsed_msg = create_mock_parsed_message(message_type="ORM^O01")
        msg_id = "ORM_MSG_001"
        self.mock_device_adapter.get_patient_id_from_message.return_value = "PID_FOUND"
        db_patient_info = {'name': 'Doe^John', 'sex': 'M', 'age': '30', 'ageUnit': 'Y'}
        self.mock_db_adapter.get_patient_info.return_value = db_patient_info

        handel_info_request_message(mock_parsed_msg, msg_id, self.mock_device_adapter, self.mock_db_adapter)
        
        expected_info_for_response = db_patient_info.copy()
        expected_info_for_response["PATIENT_ID"] = "PID_FOUND" # PATIENT_ID is added
        self.mock_device_adapter.create_order_response_message.assert_called_once_with(msg_id, expected_info_for_response)

    def test_handel_info_request_message_patient_not_found(self):
        mock_parsed_msg = create_mock_parsed_message(message_type="ORM^O01")
        msg_id = "ORM_MSG_002"
        self.mock_device_adapter.get_patient_id_from_message.return_value = "PID_NOT_FOUND"
        self.mock_db_adapter.get_patient_info.return_value = None # Patient not found in DB

        # Access default patient info from hl7responder module
        default_info = hl7responder.DEFULT_PATIENT_INFO_HL7.copy()
        default_info["PATIENT_ID"] = "PID_NOT_FOUND"

        handel_info_request_message(mock_parsed_msg, msg_id, self.mock_device_adapter, self.mock_db_adapter)
        self.mock_device_adapter.create_order_response_message.assert_called_once_with(msg_id, default_info)

    def test_handel_info_request_message_no_pid_in_message(self):
        mock_parsed_msg = create_mock_parsed_message(message_type="ORM^O01")
        msg_id = "ORM_MSG_003"
        self.mock_device_adapter.get_patient_id_from_message.return_value = None # No PID extracted

        handel_info_request_message(mock_parsed_msg, msg_id, self.mock_device_adapter, self.mock_db_adapter)
        self.mock_device_adapter.create_ack_message.assert_called_once_with(msg_id, "AE", ANY)
        self.mock_device_adapter.create_order_response_message.assert_not_called()

if __name__ == '__main__':
    unittest.main()
