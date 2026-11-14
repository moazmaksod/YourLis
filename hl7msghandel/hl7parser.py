from hl7 import parse
from log.logger import log_info, log_error
from hl7msghandel.hl7validator import validate_hl7_message


# Define the source for logging purposes
SOURCE = "HL7Message"


def parse_hl7_message(raw_message, message_direction):
    """
    Parses a raw HL7 message string into an hl7 message container.

    Args:
        raw_message (str or bytes): The raw HL7 message string or bytes.
        message_direction (str): Direction of the message ('IN', 'OUT', etc.).

    Returns:
        hl7.Message: Parsed HL7 message object, or None if parsing or validation fails.
    """
    try:
        log_info(f"Parsing {message_direction} HL7 message.", source=SOURCE)
        if isinstance(raw_message, bytes):
            raw_message = raw_message.decode("utf-8", errors="replace")

        # Normalize carriage returns and newlines: standard HL7 segment delimiter is \r
        raw_message = raw_message.replace("\r\n", "\r").replace("\n", "\r").strip("\r")
        hl7_message = parse(raw_message)  # Parse HL7 into a container

        if not validate_hl7_message(hl7_message, message_direction):
            log_error(f"Validation failed for {message_direction} HL7 message.", source=SOURCE)
            return None

        log_info(
            f"{message_direction} HL7 message parsed successfully: With ({(len(hl7_message))}) Segments.",
            source=SOURCE,
        )
        return hl7_message
    except Exception as e:
        log_error(f"Error parsing HL7 message: {e}", source=SOURCE)
        return None
