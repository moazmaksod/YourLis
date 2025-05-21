from log.logger import log_info, log_error
from setting.config import get_config, save_config
from database.sqlqueries import *
from database.sqldbdictionary import *
from hl7msghandel.hl7dictionary import *
from datetime import datetime


# Define the source for logging purposes
SOURCE = "HL7Message"

cfg = get_config()  # Load configuration from file
CBC_TEST_CODE = cfg["CBC_TEST_CODE"]
HGB_TEST_CODE = cfg["HGB_TEST_CODE"]
TEST_FINISH_CODE = cfg["TEST_FINISH_CODE"]
APPLICATION_NAME = cfg["APPLICATION_NAME"]
VERSION = cfg["VERSION"]


def time_now():

    TIME_NOW = datetime.now().strftime("%Y%m%d%H%M%S")

    return TIME_NOW


def generate_response_message(hl7_message):
    """
    Generates a response message based on the incoming HL7 message type.

    Args:
        hl7_message (hl7.Message): The parsed HL7 message object.

    Returns:
        str: Response HL7 message string.
    """

    try:

        # Access the first segment and ensure it's parsed correctly
        hl7_msh = hl7_message.segments("MSH")[0]

        if len(hl7_msh) <= 8:
            log_error("Insufficient MSH fields.", source=SOURCE)

            raise ValueError("Insufficient MSH fields.")

        # Check the MSH-9 field to determine the message type
        hl7_message_type = str(hl7_msh[9])

        # accsess device name and version from MSH segment
        try:
            sender_name_ver = f"{hl7_msh[3]} {hl7_msh[4]}"

        except Exception as e:
            log_error(
                f"Error retrieving device name and version from MSH segment: {e}",
                source=SOURCE,
            )
            sender_name_ver = None

        # accsess message id from MSH segment
        msg_id = hl7_message.segments("MSH")[0][10]

        log_info(f"Processing HL7 message type ({hl7_message_type})", source=SOURCE)

        if hl7_message_type == "ORU^R01":  # CBC device result_msg <<<

            # handel result message and generate ack message
            return {
                "respose": handel_result_message(hl7_message, msg_id),
                "sender": sender_name_ver,
            }

        elif hl7_message_type == "ORM^O01":  # CBC device info_request_msg <<<

            # handel info request message and generate info message for send it
            return {
                "respose": handel_info_request_message(hl7_message, msg_id),
                "sender": sender_name_ver,
            }

        elif hl7_message_type == "ACK^O02":  # CBC device info_msg_ack <<<
            log_info(
                f"Analyser Succsessfully recevie patient info.\n No need to Respond to message NO.:{msg_id} with type:{hl7_message_type}.",
                source=SOURCE,
            )
            return {"respose": None, "sender": sender_name_ver}
        else:
            log_info(
                f"Unknown message type {hl7_message_type}, message NO.:{msg_id}.",
                source=SOURCE,
            )
            return {"respose": None, "sender": sender_name_ver}
    except Exception as e:
        log_error(f"Error generating HL7 response: {e}", source=SOURCE)
        return {"respose": None, "sender": None}


def handel_result_message(hl7_message, msg_id):
    """
    Handles the incoming result message and generates a response message.
    handel "ORU^R01" # CBC device result_msg <<<
    """

    ack_code = True
    try:
        patient_requested = data_select_for(
            PATIENT_TEST_SQL, PATIENT_TEST_HL7, hl7_message
        )

        test_code = None
        test_finish = None

        if patient_requested and type(patient_requested) == dict:

            try:
                test_code = patient_requested["TEST_CODE"]
                test_finish = patient_requested["RESULT_STATE"]
            except Exception as e:
                log_error(
                    f"Error retrieving patient request test list from MSSQL: {e}",
                    source=SOURCE,
                )

            # Get patient info for request date from MSSQL
            patient_info = data_select_for(
                PATIENT_INFO_SQL, PATIENT_INFO_ORU_HL7, hl7_message
            )
            request_date = {"REQ_DATE": time_now()}

            patient_name = None

            if patient_info and type(patient_info) == dict:
                try:
                    request_date["REQ_DATE"] = patient_info["REQ_DATE"]
                    patient_name = patient_info["NAME"]
                except Exception as e:
                    log_error(
                        f"Error retrieving patient info from MSSQL: {e}", source=SOURCE
                    )

                result_exist = data_select_for(
                    RESULT_EXIST_SQL, RESULT_EXIST_HL7, hl7_message
                )

                if test_code == CBC_TEST_CODE and test_finish == TEST_FINISH_CODE:
                    if not result_exist:
                        # insert the new record
                        data_insert_for(
                            CBC_RESULT_SQL, CBC_RESULT_HL7, hl7_message, request_date
                        )
                        log_info(
                            f"CBC result for : {patient_name} saved succsesfully",
                            source=SOURCE,
                        )
                    else:
                        # update the existing record
                        data_update_for(
                            CBC_RESULT_SQL, CBC_RESULT_HL7, hl7_message, request_date
                        )
                        log_info(
                            f"CBC result for : {patient_name} updated succsesfully",
                            source=SOURCE,
                        )

                elif test_code == HGB_TEST_CODE and test_finish == TEST_FINISH_CODE:

                    if not result_exist:
                        # insert the new record
                        data_insert_for(
                            HGB_RESULT_SQL, HGB_RESULT_HL7, hl7_message, request_date
                        )
                        log_info(
                            f"Haemoglobin result for : {patient_name} saved succsesfully",
                            source=SOURCE,
                        )
                    else:
                        # update the existing record
                        data_update_for(
                            HGB_RESULT_SQL, HGB_RESULT_HL7, hl7_message, request_date
                        )
                        log_info(
                            f"Haemoglobin result for : {patient_name} updated succsesfully",
                            source=SOURCE,
                        )
                else:
                    log_error(
                        f"Unknown test code {test_code}, message NO.:{msg_id}.",
                        source=SOURCE,
                    )
                    ack_code = False
            else:
                log_error(f"Error patient info not exist in MSSQL.", source=SOURCE)
                ack_code = False
        else:
            log_info(f"This patient id didn't requested.", source=SOURCE)
            ack_code = False

    except Exception as e:
        log_error(f"Error processing result message: {e}", source=SOURCE)
        ack_code = False

    # "ACK^R01",       # >>> Interface result_msg_ack
    return generate_ack_message(msg_id, ack_code)


def handel_info_request_message(hl7_message, msg_id):
    """
    Handles the incoming info request message and generates a response message.
    handel "ORM^O01" # CBC device info_request_msg <<<
    """

    patient_id = hl7_message.segments("ORC")[0][3]

    # Get patient info from MSSQL
    patient_info = data_select_for(PATIENT_INFO_SQL, PATIENT_INFO_ORM_HL7, hl7_message)

    # set patient info to defult if patient info not found in db

    if patient_info and type(patient_info) == dict:
        for key in patient_info.keys():
            if patient_info[key] in PATIENT_INFO_SQL_TO_HL7_DICT.keys():
                patient_info[key] = PATIENT_INFO_SQL_TO_HL7_DICT[patient_info[key]]
    else:
        patient_info = DEFULT_PATIENT_INFO_HL7

    # add patient id to the patient info dict
    patient_info["PATIENT_ID"] = patient_id

    # send  "ORR^O02"  >>> Interface info_msg
    return generate_order_response(msg_id, patient_info)


def generate_ack_message(msg_id, ack_code):
    """
    Generates a basic ACK response for the incoming HL7 message.

    Args:
        hl7_message (hl7.Message): The parsed HL7 message object.

    Returns:
        str: ACK HL7 message string.
    """
    msg_type = "ACK^R01"
    if ack_code == True:
        ack_code = "AA"  # Success code
        log_info(f"Server generate ack message with success code.", source=SOURCE)
    else:
        ack_code = "AE"  # Failure code
        log_info(f"Server generate ack message with Failure code.", source=SOURCE)

    try:

        ack_message = f"\x0bMSH|^~\\&|{APPLICATION_NAME}|{VERSION}|||{time_now()}||{msg_type}|{msg_id}|P|2.3.1|||||CHA|UTF-8|||\rMSA|{ack_code}|{msg_id}||||0|\r\x1c\r"

        return ack_message

    except Exception as e:
        log_error(f"Error generating ACK message: {e}", source=SOURCE)
        return None


def generate_order_response(msg_id, patient_info: dict):
    """
    Generates a sample order response for ORM^O01 messages.

    Args:
        hl7_message (hl7.Message): The parsed HL7 message object.

    Returns:
        str: HL7 order response message string.
    """
    msg_type = "ORR^O02"

    try:

        # access patient name from ORC segment order request mesage
        patient_id = patient_info["PATIENT_ID"]
        patient_name = patient_info["NAME"]
        patient_sex = patient_info["SEX"]
        patient_age = patient_info["AGE"]
        patient_age_unit = patient_info["AGE_UNIT"]

        response_message = f"\x0bMSH|^~\\&|{APPLICATION_NAME}|{VERSION}|||{time_now()}||{msg_type}|{msg_id}|P|2.3.1|||||CHA|UTF-8|||\rMSA|AA|{msg_id}||||0|\rPID|1||{patient_id}|{patient_name}|{patient_name}|||{patient_sex}|||||||||||||||||||||||\rPV1|1||||||||||||||||||||||||||||||||||||||||||||||||||||\rORC|AF|{patient_id}|||||||||||||||||||||||\rOBR|1|||||||||||||||||||||||||||||||Genrui||||||||||||||\rOBX|2|IS|^Blood Mode^||WH||||||F|||||||\rOBX|3|IS|^Test Mode^||CBC||||||F|||||||\rOBX|5|IS|^Age^||{patient_age}|{patient_age_unit}|||||F|||||||\r\x1c\r"

        log_info(f"Generate order response message successfully.", source=SOURCE)

        return response_message

    except Exception as e:
        log_error(f"Error generating order response: {e}", source=SOURCE)
        return None
