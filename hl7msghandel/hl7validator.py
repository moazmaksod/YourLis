from log.logger import log_info, log_error, log_warning


# Define the source for logging purposes
SOURCE = "HL7Message"


def validate_hl7_message(hl7_message, message_direction):
    """
    Validates an HL7 message.

    Args:
        hl7_message (hl7.Message): The parsed HL7 message object.

    Returns:
        bool: True if the message has valid HL7 structure with MSH, False otherwise.
    """
    try:
        log_info(f"Validating {message_direction} HL7 message.", source=SOURCE)
        # Check if the HL7 message is present and has segments
        if not hl7_message or len(hl7_message) == 0:
            log_error(f"Invalid {message_direction} HL7 message: No segments found.", source=SOURCE)
            return False

        # Validate the MSH segment
        try:
            msh_segs = hl7_message.segments('MSH')
            if not msh_segs or str(msh_segs[0][0]) != "MSH":
                log_error(f"Invalid {message_direction} HL7 message: Missing or incorrect MSH segment.", source=SOURCE)
                return False
        except Exception:
            log_error(f"Invalid {message_direction} HL7 message: Missing or incorrect MSH segment.", source=SOURCE)
            return False

        # Extract message type from MSH segment (MSH-9)
        msg_type = str(msh_segs[0][9])

        # Check recommended segments based on message type
        required_segments = get_required_segments(msg_type)
        for segment in required_segments:
            try:
                segs = hl7_message.segments(segment)
                if not segs:
                    log_warning(f"{message_direction} HL7 message Type {msg_type}: Missing recommended segment {segment}.", source=SOURCE)
            except Exception:
                log_warning(f"{message_direction} HL7 message Type {msg_type}: Missing recommended segment {segment}.", source=SOURCE)

        log_info(f"{message_direction} HL7 message Type ({msg_type}) validation succeeded.", source=SOURCE)
        return True

    except Exception as e:
        log_error(f"Error validating {message_direction} HL7 message: {e}", source=SOURCE)
        return False

def get_required_segments(msg_type):
    """
    Returns a list of required segments based on the message type.

    Args:
        msg_type (str): The type of the HL7 message.

    Returns:
        list: A list of required segment identifiers.
    """
    # Define required segments for different message types
    if msg_type.startswith("ORM"):
        return ["ORC"]  # Order messages require ORC (Common Order)
    
    elif msg_type == "ORU^R01":
        return ["PID", "OBX"]  # Result messages require patient and observation
    
    elif msg_type.startswith("ACK"):
        return ["MSA"]  # Acknowledgment messages require MSA segment
    
    elif msg_type.startswith("ORR"):
        return ["MSA"]  # Order response requires MSA
    
    else:
        return []