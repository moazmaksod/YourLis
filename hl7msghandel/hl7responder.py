from log.logger import log_info, log_error
from setting.config import get_config
from datetime import datetime
from typing import Dict, Any, Union # For type hinting

# Import adapter abstract base classes
from database.database_adapter import DatabaseAdapter
from hl7msghandel.device_adapter import DeviceAdapter


# Define the source for logging purposes
SOURCE = "HL7Responder" # Changed source name slightly for clarity

cfg = get_config()  # Load configuration from file
CBC_TEST_CODE = cfg["CBC_TEST_CODE"]
HGB_TEST_CODE = cfg["HGB_TEST_CODE"]
TEST_FINISH_CODE = cfg["TEST_FINISH_CODE"]
# APPLICATION_NAME and VERSION might be better sourced from device_adapter or passed if they vary by device
# For now, keep them as global config values if they are truly global for this application instance.
APPLICATION_NAME = cfg["APPLICATION_NAME"]
VERSION = cfg["VERSION"]

# Default patient info for ORM^O01 response if DB lookup fails.
# This structure should align with what device_adapter.create_order_response_message expects for patient_info
DEFULT_PATIENT_INFO_HL7 = {
    "PATIENT_ID": "UNKNOWN", # Usually taken from incoming message
    "NAME": "UNKNOWN",
    "SEX": "U", # HL7 'U' for Unknown
    "AGE": "0",
    "AGE_UNIT": "Y", # HL7 'a' for years, but older HL7 might use Y. Adapter should handle.
    # Add other fields as required by the specific create_order_response_message implementation
}


def time_now_hl7():
    """Generates a timestamp string in HL7 format (YYYYMMDDHHMMSS)."""
    return datetime.now().strftime("%Y%m%d%H%M%S")


def generate_response_message(
    raw_hl7_message: str,
    device_adapter: DeviceAdapter,
    database_adapter: DatabaseAdapter
) -> Dict[str, Union[str, None]]:
    """
    Generates a response message based on the incoming HL7 message type.
    Uses DeviceAdapter to parse and create messages, and DatabaseAdapter for DB interactions.

    Args:
        raw_hl7_message (str): The raw HL7 message string.
        device_adapter (DeviceAdapter): Instance of a DeviceAdapter implementation.
        database_adapter (DatabaseAdapter): Instance of a DatabaseAdapter implementation.

    Returns:
        Dict[str, Union[str, None]]: A dictionary containing 'response' (HL7 string or None)
                                     and 'sender' (device identifier or None).
    """
    try:
        parsed_message = device_adapter.parse_message(raw_hl7_message)
        if not parsed_message:
            log_error("Failed to parse HL7 message.", source=SOURCE)
            # Consider creating an ACK AE if message ID is parseable, or returning specific error
            return {"response": None, "sender": None} # Or an ACK with error

        # Extract common MSH details using device_adapter
        # Assuming MSH.10 is message_control_id
        message_control_id = str(parsed_message.segments("MSH")[0][10]) # Fallback, ideally adapter method
        # A more robust way: message_control_id = device_adapter.get_message_control_id(parsed_message)
        # For now, direct access, but this should be an adapter method if MSH structure varies.

        hl7_message_type = device_adapter.get_message_type(parsed_message)
        sender_name_ver = device_adapter.get_device_identifier(parsed_message)

        log_info(f"Processing HL7 message type ({hl7_message_type}) from sender ({sender_name_ver}) with ID ({message_control_id})", source=SOURCE)

        if hl7_message_type == "ORU^R01":  # Result message
            response_hl7 = handel_result_message(
                parsed_message, message_control_id, device_adapter, database_adapter
            )
            return {"response": response_hl7, "sender": sender_name_ver}

        elif hl7_message_type == "ORM^O01":  # Order message (info request)
            response_hl7 = handel_info_request_message(
                parsed_message, message_control_id, device_adapter, database_adapter
            )
            return {"response": response_hl7, "sender": sender_name_ver}

        elif hl7_message_type == "ACK": # Generic ACK, usually MSH.9.1 is ACK
             # For ACK^O02, original code implies MSH.9 was "ACK^O02"
             # device_adapter.get_message_type should return "ACK" or "ACK^O02"
            log_info(
                f"Received ACK message from {sender_name_ver}. No response needed for message ID: {message_control_id}.",
                source=SOURCE,
            )
            return {"response": None, "sender": sender_name_ver}
        else:
            log_info(
                f"Unknown or unhandled message type '{hl7_message_type}' from {sender_name_ver}, message ID: {message_control_id}.",
                source=SOURCE,
            )
            # Optionally send an ACK AR (Application Reject) for unsupported message types
            # ack_response = device_adapter.create_ack_message(message_control_id, "AR", f"Unsupported message type: {hl7_message_type}")
            # return {"response": ack_response, "sender": sender_name_ver}
            return {"response": None, "sender": sender_name_ver}

    except Exception as e:
        log_error(f"Error generating HL7 response: {e}", source=SOURCE)
        # Try to get message_control_id for ACK if possible, even in error
        # This is difficult if parsing itself failed early.
        # ack_response = device_adapter.create_ack_message("UNKNOWN_ID", "AE", str(e)) # If adapters are available
        return {"response": None, "sender": None}


def handel_result_message(
    parsed_hl7_message: Any, # Type from device_adapter.parse_message
    original_message_id: str,
    device_adapter: DeviceAdapter,
    database_adapter: DatabaseAdapter
) -> Union[str, None]:
    """
    Handles HL7 ORU_R01 messages (test results).
    Extracts data, saves/updates it via DatabaseAdapter, and generates an ACK via DeviceAdapter.
    """
    ack_successful = False
    error_message_for_ack = None

    try:
        # Extract patient_id and result_data using device_adapter
        # extract_result_data returns: (test_type, patient_id, results_dict)
        # The 'test_type' from here might be a general panel code.
        # We'll rely on database_adapter.get_patient_test_request for specific test codes like CBC/HGB.
        _extracted_test_panel, patient_id, results_dict = device_adapter.extract_result_data(parsed_hl7_message)

        if not patient_id or not results_dict:
            log_error(f"Could not extract patient ID or results from message ID: {original_message_id}", source=SOURCE)
            error_message_for_ack = "Missing patient ID or result data in message"
            return device_adapter.create_ack_message(original_message_id, "AE", error_message_for_ack)

        # Check what test was requested for this patient
        # get_patient_test_request should return a dict like {'TEST_CODE': 'CBC', 'RESULT_STATE': 'Pending'}
        patient_request_details = database_adapter.get_patient_test_request(patient_id)

        if patient_request_details:
            db_test_code = patient_request_details.get("TEST_CODE")
            db_result_state = patient_request_details.get("RESULT_STATE") # Or a similar key like 'status'

            # Get patient info (like name, actual request date) from DB
            # get_patient_info might return {'name': 'John Doe', 'requestDate': '2023-01-15 10:00:00', ...}
            db_patient_info = database_adapter.get_patient_info(patient_id)
            
            actual_request_date_str = time_now_hl7() # Default to now
            patient_name_from_db = "Unknown"

            if db_patient_info:
                # Adapter should return date in 'YYYY-MM-DD HH:MM:SS' or similar standard format
                # The save/update methods in DB adapter expect 'YYYY-MM-DD HH:MM:SS'
                # This key 'requestDate' or 'REQ_DATE' needs to be consistent from get_patient_info
                actual_request_date_str = db_patient_info.get("requestDate", db_patient_info.get("REQ_DATE", actual_request_date_str))
                patient_name_from_db = db_patient_info.get("name", db_patient_info.get("NAME", patient_name_from_db))
            else:
                log_warning(f"No detailed patient info found in DB for Patient ID: {patient_id}. Using defaults.", source=SOURCE)
                error_message_for_ack = f"Patient ID {patient_id} not found or missing details in system."
                # Decide if this is an error or just a warning. If critical, set ack_successful = False.

            # Check if the test is finished and matches expected codes
            if db_result_state == TEST_FINISH_CODE: # TEST_FINISH_CODE from config
                result_exists_in_db = database_adapter.check_result_exists(patient_id) # Checks if *any* result for this patient for this test type exists

                if db_test_code == CBC_TEST_CODE:
                    if not result_exists_in_db:
                        database_adapter.save_cbc_result(patient_id, results_dict, actual_request_date_str)
                        log_info(f"CBC result for patient {patient_name_from_db} (ID: {patient_id}) saved successfully.", source=SOURCE)
                    else:
                        database_adapter.update_cbc_result(patient_id, results_dict, actual_request_date_str)
                        log_info(f"CBC result for patient {patient_name_from_db} (ID: {patient_id}) updated successfully.", source=SOURCE)
                    ack_successful = True
                elif db_test_code == HGB_TEST_CODE:
                    if not result_exists_in_db:
                        database_adapter.save_hgb_result(patient_id, results_dict, actual_request_date_str)
                        log_info(f"HGB result for patient {patient_name_from_db} (ID: {patient_id}) saved successfully.", source=SOURCE)
                    else:
                        database_adapter.update_hgb_result(patient_id, results_dict, actual_request_date_str)
                        log_info(f"HGB result for patient {patient_name_from_db} (ID: {patient_id}) updated successfully.", source=SOURCE)
                    ack_successful = True
                else:
                    log_error(f"Unknown or unhandled test code '{db_test_code}' for patient ID {patient_id}, message ID: {original_message_id}.", source=SOURCE)
                    error_message_for_ack = f"Unknown test code '{db_test_code}' in system for patient."
            else:
                log_warning(f"Test for patient ID {patient_id} not in 'finish' state (state: {db_result_state}), message ID: {original_message_id}.", source=SOURCE)
                error_message_for_ack = f"Test for patient {patient_id} not ready for results (state: {db_result_state})."
        else:
            log_info(f"No active test request found for patient ID {patient_id}, message ID: {original_message_id}.", source=SOURCE)
            error_message_for_ack = f"No active test request for patient ID {patient_id}."

    except Exception as e:
        log_error(f"Error processing result message (ID: {original_message_id}): {e}", source=SOURCE)
        error_message_for_ack = f"Server error processing result: {str(e)}"
        ack_successful = False # Ensure it's false on exception

    # Generate ACK message using device_adapter
    ack_type = "AA" if ack_successful else "AE"
    return device_adapter.create_ack_message(original_message_id, ack_type, error_message_for_ack)


def handel_info_request_message(
    parsed_hl7_message: Any, # Type from device_adapter.parse_message
    original_message_id: str,
    device_adapter: DeviceAdapter,
    database_adapter: DatabaseAdapter
) -> Union[str, None]:
    """
    Handles HL7 ORM^O01 messages (patient info requests).
    Fetches patient info via DatabaseAdapter and generates an ORR response via DeviceAdapter.
    """
    try:
        patient_id = device_adapter.get_patient_id_from_message(parsed_hl7_message)
        if not patient_id:
            log_error(f"Could not extract patient ID from info request message ID: {original_message_id}", source=SOURCE)
            # Cannot easily send ACK AE without original_message_id if that parsing failed.
            # If parsed_hl7_message is available, we can use original_message_id.
            return device_adapter.create_ack_message(original_message_id, "AE", "Missing patient ID in request")

        # Get patient info from DB using database_adapter
        # This should return a generic dict like {'name': 'Doe^John', 'dob': '19900101', ...}
        patient_info_from_db = database_adapter.get_patient_info(patient_id)

        response_patient_info: Dict[str, Any] # Ensure it's a dict for the adapter

        if patient_info_from_db:
            log_info(f"Patient info found for ID {patient_id}.", source=SOURCE)
            response_patient_info = patient_info_from_db
            # The device_adapter.create_order_response_message will handle mapping this generic dict
            # to the specific HL7 fields it needs.
        else:
            log_warning(f"Patient info not found for ID {patient_id}. Using default info.", source=SOURCE)
            response_patient_info = dict(DEFULT_PATIENT_INFO_HL7) # Use a copy
            # The patient_id from the message should override the default if it's part of DEFULT_PATIENT_INFO_HL7
            
        # Ensure patient_id from the message is in the info going to the response
        response_patient_info["PATIENT_ID"] = patient_id 

        # Generate ORR (Order Response) message using device_adapter
        # The device_adapter.create_order_response_message needs original_message_id and patient_info dict
        order_response_hl7 = device_adapter.create_order_response_message(
            original_message_id,
            response_patient_info
            # application_name=APPLICATION_NAME, # These might be needed if not configured in adapter
            # version=VERSION
        )
        
        if order_response_hl7:
            log_info(f"Generated ORR message for patient ID {patient_id}, original msg ID: {original_message_id}.", source=SOURCE)
        else:
            log_error(f"Failed to generate ORR message for patient ID {patient_id}, original msg ID: {original_message_id}.", source=SOURCE)
            # If response generation fails, we might send an ACK AE instead, or just return None
            # For simplicity, returning None here. A more robust solution might send ACK AE.

        return order_response_hl7

    except Exception as e:
        log_error(f"Error processing info request message (ID: {original_message_id}): {e}", source=SOURCE)
        # Attempt to send an ACK AE if possible
        return device_adapter.create_ack_message(original_message_id, "AE", f"Server error: {str(e)}")
