import hl7
from datetime import datetime
from typing import Any, Dict, Tuple, Union, Optional # Added Optional

from hl7msghandel.device_adapter import DeviceAdapter
from setting.config import get_config
from log.logger import log_info, log_error, log_warning # For logging

SOURCE_CONTEXT = "GenruiKt60Adapter"

class GenruiKt60Adapter(DeviceAdapter):
    """
    Device Adapter for Genrui KT-60.
    Implements HL7 message parsing and creation specific to this device.
    """

    def __init__(self):
        config = get_config()
        self.application_name = config.get("APPLICATION_NAME", "HealthMeshLIS")
        self.application_version = config.get("VERSION", "1.0")
        
        # Hypothetical mapping: OBX-3.1 (Observation Identifier) to Generic Analyte Name
        # This should be verified with actual Genrui KT-60 HL7 specifications.
        # Using placeholder string identifiers for now.
        self._obx_id_to_analyte_map = {
            "GENRUI-WBC": "WBC",
            "GENRUI-LYM%": "LYMPH%", # Lymphocyte percentage
            "GENRUI-MON%": "MONO%",  # Monocyte percentage
            "GENRUI-NEUT%": "NEUT%", # Neutrophil percentage
            "GENRUI-EOS%": "EO%",    # Eosinophil percentage
            "GENRUI-BASO%": "BASO%", # Basophil percentage
            "GENRUI-LYM#": "LYM#",   # Lymphocyte count (absolute)
            "GENRUI-MON#": "MON#",
            "GENRUI-NEUT#": "NEUT#",
            "GENRUI-EOS#": "EOS#",
            "GENRUI-BASO#": "BASO#",
            "GENRUI-RBC": "RBC",
            "GENRUI-HGB": "HGB",
            "GENRUI-HCT": "HCT",
            "GENRUI-MCV": "MCV",
            "GENRUI-MCH": "MCH",
            "GENRUI-MCHC": "MCHC",
            "GENRUI-RDW-CV": "RDW", # RDW-CV often just RDW
            "GENRUI-PLT": "PLT",
            "GENRUI-MPV": "MPV",
            "GENRUI-PDW": "PDW",
            "GENRUI-PCT": "PCT",
            # Add other parameters as needed based on device output
        }
        # If Genrui KT-60 truly relies on fixed OBX segment order, the map would be like:
        # self._obx_segment_index_to_analyte_map = { 1: "WBC", 2: "LYM%", ... }
        # And extract_result_data would iterate OBX segments using their index.

    def _get_hl7_timestamp(self) -> str:
        """Generates a timestamp string in HL7 format (YYYYMMDDHHMMSS)."""
        return datetime.now().strftime("%Y%m%d%H%M%S")

    def parse_message(self, raw_hl7_message: str, direction: str = "incoming") -> Optional[hl7.Message]:
        """
        Parses a raw HL7 message string into an hl7.Message object.
        Performs basic validation (e.g., check for MSH segment).
        """
        try:
            if not raw_hl7_message or not isinstance(raw_hl7_message, str):
                log_error(f"Invalid raw_hl7_message: Must be a non-empty string. Received: {type(raw_hl7_message)}", source=SOURCE_CONTEXT)
                return None
            
            # HL7 messages often start with VT (ASCII 11) and end with FS (ASCII 28) CR (ASCII 13)
            # The hl7 library might handle this, but stripping can be safer.
            processed_message = raw_hl7_message.strip("\x0b\x1c\r")
            
            parsed_msg = hl7.parse(processed_message)
            if not parsed_msg or not parsed_msg.segments("MSH"):
                log_error("Failed to parse HL7 message or MSH segment not found.", source=SOURCE_CONTEXT)
                return None
            # Basic check for MSH segment length
            if len(parsed_msg.segment("MSH")) < 9: # MSH.9 (Message Type) is crucial
                 log_error(f"MSH segment is too short: {len(parsed_msg.segment('MSH'))} fields.", source=SOURCE_CONTEXT)
                 return None
            log_info(f"Successfully parsed {direction} HL7 message.", source=SOURCE_CONTEXT)
            return parsed_msg
        except Exception as e:
            log_error(f"Error parsing HL7 message: {e}. Raw message (first 100 chars): '{raw_hl7_message[:100]}'", source=SOURCE_CONTEXT)
            return None

    def get_message_type(self, parsed_hl7_message: hl7.Message) -> str:
        """Extracts the HL7 message type (e.g., "ORU_R01") from MSH.9."""
        try:
            # MSH.9 is Message Type, which can be composite (MSH.9.1 ^ MSH.9.2)
            # e.g. ORU^R01. We typically want the full type.
            return str(parsed_hl7_message.segment("MSH")[9])
        except Exception as e:
            log_error(f"Error extracting message type from MSH.9: {e}", source=SOURCE_CONTEXT)
            return "UNKNOWN"

    def get_patient_id_from_message(self, parsed_hl7_message: hl7.Message) -> Optional[str]:
        """Extracts the patient ID from PID.3 (first occurrence)."""
        try:
            pid_segment = parsed_hl7_message.segment("PID")
            # PID.3 is Patient Identifier List. It can be repeating. We take the first one's ID.
            patient_id_field = pid_segment[3]
            if isinstance(patient_id_field, list): # If PID.3 repeats
                return str(patient_id_field[0][0]) # CX.1 - ID Number
            return str(patient_id_field[0]) # CX.1 - ID Number
        except Exception as e:
            log_warning(f"Could not extract patient ID from PID.3: {e}", source=SOURCE_CONTEXT)
            return None

    def get_device_identifier(self, parsed_hl7_message: hl7.Message) -> Optional[str]:
        """
        Attempts to identify the sending application/facility from MSH.3 and MSH.4.
        Returns "SendingApplication^SendingFacility" or parts if available.
        """
        try:
            msh = parsed_hl7_message.segment("MSH")
            sending_app = str(msh[3]) if len(msh) > 3 else ""
            sending_facility = str(msh[4]) if len(msh) > 4 else ""
            
            if sending_app and sending_facility:
                return f"{sending_app}^{sending_facility}"
            elif sending_app:
                return sending_app
            elif sending_facility:
                return sending_facility
            return None
        except Exception as e:
            log_error(f"Error extracting device identifier from MSH: {e}", source=SOURCE_CONTEXT)
            return None

    def extract_order_info(self, parsed_hl7_message: hl7.Message) -> Optional[Dict[str, Any]]:
        """
        Extracts relevant information from an HL7 order message (e.g., ORM_O01).
        For Genrui KT-60, this might be minimal if it primarily sends ORU.
        """
        # This method would parse ORC, OBR segments if the device sends detailed orders.
        # For now, assuming it's not a primary function or details are unknown.
        log_info("extract_order_info called, but Genrui KT-60 specific ORM parsing is not fully implemented. Returning None.", source=SOURCE_CONTEXT)
        return None

    def extract_result_data(self, parsed_hl7_message: hl7.Message) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, Any]]]:
        """
        Extracts test type, patient ID, and result values from an ORU_R01 message.
        """
        patient_id = self.get_patient_id_from_message(parsed_hl7_message)
        results_dict = {}
        test_type = None # e.g., 'CBC', 'HGB_ONLY' or a panel code from OBR-4

        try:
            # Determine test_type from OBR-4 (Universal Service Identifier) if possible
            # This is a more robust way than assuming all ORU_R01 are CBC.
            obr_segment = parsed_hl7_message.segment("OBR")
            if obr_segment and len(obr_segment) > 4:
                service_id = str(obr_segment[4][0]) # OBR-4.1 (Identifier)
                # Placeholder: Map service_id to a generic test_type like 'CBC'
                # This mapping would be specific to lab setup / device configuration.
                if "CBC" in service_id.upper() or service_id in ["GENRUI-CBC-PANEL"]: # Example panel code
                    test_type = "CBC"
                elif "HGB" in service_id.upper(): # Example if device sends HGB alone
                    test_type = "HGB" 
                else:
                    test_type = service_id # Use the code itself if not mapped
                log_info(f"Determined test_type as '{test_type}' from OBR-4.1: {service_id}", source=SOURCE_CONTEXT)

            for obx in parsed_hl7_message.segments("OBX"):
                if len(obx) < 5: # Need at least up to OBX.5 (Observation Value)
                    log_warning(f"Short OBX segment skipped: {obx}", source=SOURCE_CONTEXT)
                    continue

                obs_id_field = obx[3] # OBX.3 - Observation Identifier (CE type)
                obs_value_field = obx[5] # OBX.5 - Observation Value

                obs_id_code = str(obs_id_field[0]) # CE.1 - Identifier
                
                analyte_name = self._obx_id_to_analyte_map.get(obs_id_code)
                
                if analyte_name:
                    value = str(obs_value_field)
                    # Basic type conversion attempt (can be made more robust)
                    try:
                        if '.' in value:
                            results_dict[analyte_name] = float(value)
                        else:
                            results_dict[analyte_name] = int(value)
                    except ValueError:
                        results_dict[analyte_name] = value # Store as string if conversion fails
                else:
                    log_warning(f"Unmapped OBX identifier: {obs_id_code} (Description: {str(obs_id_field[1]) if len(obs_id_field) > 1 else 'N/A'}). Value: {str(obs_value_field)}", source=SOURCE_CONTEXT)

            if not results_dict:
                log_warning(f"No results extracted for patient ID {patient_id}. Check OBX mapping and message structure.", source=SOURCE_CONTEXT)
                return test_type, patient_id, None
            
            # If test_type wasn't found from OBR-4, try to infer it (e.g. if HGB is present, it's at least HGB related)
            if not test_type and results_dict:
                if "HGB" in results_dict and "WBC" in results_dict: # Basic check for CBC
                    test_type = "CBC"
                elif "HGB" in results_dict:
                    test_type = "HGB" # Fallback if only HGB found
                else:
                    test_type = "UNKNOWN_PANEL"
                log_info(f"Inferred test_type as '{test_type}' based on found analytes.", source=SOURCE_CONTEXT)


            return test_type, patient_id, results_dict

        except Exception as e:
            log_error(f"Error extracting result data for patient ID {patient_id}: {e}", source=SOURCE_CONTEXT)
            return None, patient_id, None


    def create_ack_message(self, original_message_id: str, ack_code: str = "AA", error_message: Optional[str] = None) -> str:
        """
        Generates an HL7 Acknowledgment (ACK) message string.
        ack_code: "AA" (Application Accept), "AE" (Application Error), "AR" (Application Reject).
        """
        timestamp = self._get_hl7_timestamp()
        ack_type = "ACK" # MSH.9.1 should be ACK. MSH.9.2 can specify original type if needed.

        # Basic MSH and MSA segments for an ACK
        # MSH|^~\&|ReceivingApp|ReceivingFacility|SendingApp|SendingFacility|Timestamp||ACKType^TriggerEvent^MessageType|MessageControlID|ProcessingID|Version|||||CountryCode|Charset
        # MSA|AckCode|OriginalMessageControlID|TextMessage|ExpectedSequenceNumber|DelayedAckType|ErrorCondition
        
        # For Genrui, SendingApp/Facility in ACK MSH should be this LIS's details
        # ReceivingApp/Facility should be what was in the original message's MSH.3/MSH.4 (if known, else placeholders)
        # However, simple ACKs often just put LIS details as sender and original sender as receiver.
        # Let's assume original_message object is not available here, only its ID.
        
        msh_segment = f"MSH|^~\\&|{self.application_name}|{self.application_version}|||{timestamp}||{ack_type}|{self._get_hl7_timestamp()}{original_message_id[-6:]}ACK|P|2.3.1|||||CHA|UTF-8|||"
        msa_segment = f"MSA|{ack_code}|{original_message_id}"
        
        if error_message and (ack_code == "AE" or ack_code == "AR"):
            msa_segment += f"|{error_message}"
        
        # Standard HL7 message delimiters
        # VT (ASCII 11) at the beginning, FS (ASCII 28) and CR (ASCII 13) at the end.
        hl7_ack_str = f"\x0b{msh_segment}\r{msa_segment}\r\x1c\r"
        log_info(f"Created ACK message for original ID {original_message_id} with code {ack_code}.", source=SOURCE_CONTEXT)
        return hl7_ack_str

    def create_order_response_message(self, original_message_id: str, patient_info: Dict[str, Any]) -> str:
        """
        Generates an HL7 order response message (ORR_O02) for Genrui KT-60.
        patient_info is a generic dict from DatabaseAdapter.
        """
        timestamp = self._get_hl7_timestamp()
        response_message_id = f"{timestamp}{original_message_id[-6:]}ORR" # Create a unique ID for this response

        # Default values if not in patient_info
        pid = patient_info.get("PATIENT_ID", patient_info.get("patientId", "UNKNOWN"))
        # Name mapping: HL7 typically "LastName^FirstName^MiddleName"
        # Assuming patient_info['NAME'] is "LastName^FirstName" or just "LastName, FirstName"
        name_str = patient_info.get("NAME", patient_info.get("name", "UNKNOWN"))
        # Basic split for "LastName, FirstName" into "LastName^FirstName"
        if ',' in name_str:
            parts = name_str.split(',', 1)
            name_str = f"{parts[0].strip()}^{parts[1].strip()}"
        
        sex = patient_info.get("SEX", patient_info.get("sex", "U")) # HL7 codes: M, F, O, U
        # Age and Age Unit need to be mapped if not already in correct format
        age = str(patient_info.get("AGE", patient_info.get("age", "0")))
        age_unit = str(patient_info.get("AGE_UNIT", patient_info.get("ageUnit", "Y"))) # e.g., Y, M, D

        # MSH segment for ORR_O02
        msh = f"MSH|^~\\&|{self.application_name}|{self.application_version}|||{timestamp}||ORR^O02|{response_message_id}|P|2.3.1|||||CHA|UTF-8|||"
        # MSA segment (usually AA for acceptance of the order/query that triggered this response)
        msa = f"MSA|AA|{original_message_id}" # Acknowledging the original message (e.g. ORM_O01)
        # PID segment
        pid_seg = f"PID|1||{pid}|{name_str}|{name_str}|||{sex}|||||||||||||||||||||||" # Simplified PID
        # ORC segment (Common Order) - AF might not be right for ORR_O02. Often 'RE' (Results) or 'OK'
        # For Genrui, the example in hl7responder used 'AF'. Let's stick to that if it's device specific.
        # However, 'SC' (Status Change) or 'IP' (In Process) might be more typical for ORR.
        # Given it's a response to an info request, 'OK' or 'AF' might be fine.
        orc = f"ORC|AF|{pid}" # Using AF as per old example, may need review for Genrui spec.
        # OBR segment (Observation Request) - details about the order being responded to
        obr = f"OBR|1|||||||||||||||||||||||||||Genrui" # Minimal OBR, Genrui as placer/filler
        
        # OBX segments for specific parameters requested (e.g., Blood Mode, Test Mode, Age)
        # These are typically part of the *order* (ORM) or *result* (ORU), less common in ORR this way
        # unless confirming specific order details. The old example had these.
        obx1 = "OBX|2|IS|^Blood Mode^||WH||||||F|||||||" # WH for Whole Blood
        obx2 = "OBX|3|IS|^Test Mode^||CBC||||||F|||||||" # CBC as test mode
        obx3 = f"OBX|5|IS|^Age^||{age}|{age_unit}|||||F|||||||"

        response_hl7_str = f"\x0b{msh}\r{msa}\r{pid_seg}\r{orc}\r{obr}\r{obx1}\r{obx2}\r{obx3}\r\x1c\r"
        log_info(f"Created ORR_O02 message for original ID {original_message_id}.", source=SOURCE_CONTEXT)
        return response_hl7_str

    # All abstract methods from DeviceAdapter should be implemented.
    # parse_message, get_message_type, get_patient_id_from_message, extract_order_info,
    # extract_result_data, create_ack_message, create_order_response_message, get_device_identifier.
    # All seem to be defined.File `hl7msghandel/genrui_kt60_adapter.py` created successfully.

The `GenruiKt60Adapter` class has been defined with the following structure and implementations:

1.  **Inheritance**: Inherits from `DeviceAdapter`.
2.  **Imports**: Necessary modules like `hl7`, `datetime`, `DeviceAdapter`, `get_config`, and typing utilities are imported. Logging is also set up.
3.  **`__init__`**:
    *   Loads application name and version from `get_config()`.
    *   Initializes `_obx_id_to_analyte_map` with hypothetical OBX-3.1 identifiers for common CBC analytes. This map is crucial for `extract_result_data` and should be verified against actual device specifications.

4.  **`_get_hl7_timestamp`**: Helper to generate HL7 compliant timestamps.

5.  **`parse_message`**:
    *   Uses `hl7.parse()` to parse the raw HL7 string.
    *   Includes basic validation for the input string and checks for the presence and minimal length of the MSH segment.
    *   Strips common HL7 wrapper characters (VT, FS, CR).

6.  **`get_message_type`**: Extracts message type from MSH.9.

7.  **`get_patient_id_from_message`**: Extracts patient ID from PID.3.1 (first occurrence).

8.  **`get_device_identifier`**: Extracts sending application and facility from MSH.3 and MSH.4.

9.  **`extract_order_info`**: Currently returns `None`, as Genrui KT-60 is primarily assumed to send results (ORU). Full implementation would depend on whether it sends ORM messages and their structure.

10. **`extract_result_data`**:
    *   Retrieves patient ID using `get_patient_id_from_message`.
    *   Attempts to determine `test_type` from OBR-4.1 (Universal Service Identifier), defaulting to "CBC" or "HGB" based on common patterns or inferring from found analytes if OBR-4 is not definitive.
    *   Iterates through OBX segments:
        *   Extracts the observation identifier from OBX-3.1.
        *   Uses `self._obx_id_to_analyte_map` to map this identifier to a generic analyte name (e.g., 'HGB', 'WBC').
        *   Extracts the observation value from OBX-5 and attempts basic type conversion (float/int).
        *   Stores results in `results_dict` with generic keys.
    *   Returns `(test_type, patient_id, results_dict)`. Includes logging for unmapped OBX segments.

11. **`create_ack_message`**:
    *   Generates a standard HL7 ACK message string (MSH and MSA segments).
    *   Uses `self.application_name` and `self.application_version` for MSH.3 and MSH.4.
    *   Includes `ack_code` and `original_message_id` in the MSA segment.
    *   Adds `error_message` to MSA if `ack_code` is "AE" or "AR".

12. **`create_order_response_message`**:
    *   Generates an ORR^O02 message string.
    *   Uses `self.application_name` and `self.application_version`.
    *   Populates PID segment using the generic `patient_info` dictionary (mapping keys like 'PATIENT_ID', 'NAME', 'SEX', 'AGE', 'AGE_UNIT').
    *   Includes MSA, ORC, and OBR segments, adapted from the previous structure in `hl7responder.py`.
    *   Includes the same static OBX segments for "Blood Mode", "Test Mode", and "Age" as were in the old `generate_order_response` function, which might need review for Genrui KT-60 specifics in an ORR context.

The adapter implements all required methods. The accuracy of `extract_result_data` (specifically the `_obx_id_to_analyte_map`) and the exact structure of `create_order_response_message` will depend on the detailed HL7 specifications of the Genrui KT-60 device.
I will now submit the subtask report.
