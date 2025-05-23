import abc
from typing import Any, Dict, Tuple, Union # Union is used for str | None

class DeviceAdapter(abc.ABC):
    """
    Abstract base class for HL7 device adapters.
    Defines a common interface for HL7 message processing operations.
    """

    @abc.abstractmethod
    def parse_message(self, raw_hl7_message: str, direction: str = "incoming") -> Any:
        """
        Parses a raw HL7 message string into a message object.

        Args:
            raw_hl7_message: The raw HL7 message string.
            direction: Indicates the direction of the message, e.g., "incoming" or "outgoing".
                       This can be useful for context-specific parsing rules if any.

        Returns:
            A parsed HL7 message object (e.g., an hl7.Message object).
        """
        pass

    @abc.abstractmethod
    def get_message_type(self, parsed_hl7_message: Any) -> str:
        """
        Extracts the HL7 message type (e.g., "ORU_R01", "ORM_O01") from a parsed message.

        Args:
            parsed_hl7_message: The parsed HL7 message object.

        Returns:
            The message type string.
        """
        pass

    @abc.abstractmethod
    def get_patient_id_from_message(self, parsed_hl7_message: Any) -> Union[str, None]:
        """
        Extracts the patient ID from a parsed HL7 message.

        Args:
            parsed_hl7_message: The parsed HL7 message object.

        Returns:
            The patient ID string if found, otherwise None.
        """
        pass

    @abc.abstractmethod
    def extract_order_info(self, parsed_hl7_message: Any) -> Union[Dict[str, Any], None]:
        """
        Extracts relevant information from an HL7 order message (e.g., ORM^O01)
        into a generic dictionary.

        Args:
            parsed_hl7_message: The parsed HL7 order message object.

        Returns:
            A dictionary containing order information (e.g., placer order number,
            requested tests, patient details) if applicable, otherwise None.
        """
        pass

    @abc.abstractmethod
    def extract_result_data(self, parsed_hl7_message: Any) -> Tuple[Union[str, None], Union[str, None], Union[Dict[str, Any], None]]:
        """
        Extracts test type, patient ID, and result values from an HL7 result message
        (e.g., ORU^R01) into a generic dictionary for the results.

        Args:
            parsed_hl7_message: The parsed HL7 result message object.

        Returns:
            A tuple containing:
            - Test type (e.g., 'CBC', 'HGB', or a more specific battery code).
            - Patient ID string.
            - A dictionary of result values (e.g., {'HGB': 12.3, 'RBC': 4.5, ...}).
            Returns (None, None, None) if data cannot be extracted.
        """
        pass

    @abc.abstractmethod
    def create_ack_message(self, original_message_id: str, ack_code: str = "AA", error_message: Union[str, None] = None) -> str:
        """
        Generates an HL7 Acknowledgment (ACK) message string.

        Args:
            original_message_id: The message control ID (MSH.10) of the message
                                 being acknowledged.
            ack_code: The acknowledgment code (e.g., "AA" for Application Accept,
                      "AE" for Application Error, "AR" for Application Reject).
            error_message: An optional error message to include in the ACK,
                           typically in an ERR segment if ack_code is "AE" or "AR".

        Returns:
            A raw HL7 ACK message string.
        """
        pass

    @abc.abstractmethod
    def create_order_response_message(self, original_message_id: str, patient_info: Dict[str, Any]) -> str:
        """
        Generates an HL7 order response message string (e.g., ORR^O02, OUL^R22-R24 for unsolicited results).
        This method might be more specific depending on the exact response type needed.
        For now, a generic order response.

        Args:
            original_message_id: The message control ID of the original order message.
            patient_info: A generic dictionary containing patient information to be included
                          in the response. This should align with the format used by
                          DatabaseAdapter.get_patient_info.

        Returns:
            A raw HL7 order response message string.
        """
        pass

    @abc.abstractmethod
    def get_device_identifier(self, parsed_hl7_message: Any) -> Union[str, None]:
        """
        Attempts to identify the sending application/facility from the MSH segment.

        Args:
            parsed_hl7_message: The parsed HL7 message object.

        Returns:
            A string identifier for the device/application (e.g., "SendingApplication^SendingFacility"
            from MSH.3 and MSH.4), or None if not found.
        """
        pass
