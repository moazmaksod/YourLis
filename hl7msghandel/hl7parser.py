from hl7 import parse
from log.logger import log_info, log_error
from hl7msghandel.hl7validator import validate_hl7_message


# Define the source for logging purposes
SOURCE = "HL7Message"


def parse_hl7_message(raw_message, message_direction):
    """
    Parses a raw HL7 message string into an hl7 message container.

    Args:
        raw_message (str): The raw HL7 message string.

    Returns:
        hl7.Message: Parsed HL7 message object, or None if parsing fails.
    """
    try:

        log_info(f"Parsing {message_direction} HL7 message.", source=SOURCE)
        hl7_message = parse(raw_message)  # Parse HL7 into a container
        log_info(
            f"{message_direction} HL7 message parsed successfully: With ({(len(hl7_message))}) Segments.",
            source=SOURCE,
        )

        validate_hl7_message(
            hl7_message, message_direction
        )  # Validate the parsed message

        return hl7_message
    except Exception as e:
        log_error(f"Error parsing HL7 message: {e}", source=SOURCE)
        return None
