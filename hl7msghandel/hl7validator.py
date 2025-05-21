from log.logger import log_info, log_error


# Define the source for logging purposes
SOURCE = "HL7Message"


def validate_hl7_message(hl7_message, message_direction):
    """
    Validates an HL7 message.

    Args:
        hl7_message (hl7.Message): The parsed HL7 message object.

    Returns:
        bool: True if the message is valid, False otherwise.
    """
    try:
        log_info(f"Validating {message_direction} HL7 message.", source=SOURCE)
        # Check if the HL7 message is present and has segments
        if not hl7_message or len(hl7_message) == 0:
            log_error(f"Invalid {message_direction} HL7 message: No segments found.", source=SOURCE)
            return False


        # Validate the MSH segment
        if str(hl7_message.segments('MSH')[0][0]) != "MSH":
            log_error(f"Invalid {message_direction} HL7 message: Missing or incorrect MSH segment.", source=SOURCE)
            return False

        # Extract message type from MSH segment
        msg_type = str(hl7_message.segments('MSH')[0][9])  # MSH-9: Message Type


        # Validate required segments based on message type
        required_segments = get_required_segments(msg_type)

        if len(required_segments) > 0:
            for segment in required_segments:
                if segment not in [str(seg[0]) for seg in hl7_message.segments(segment)[0]]:
                    
                    log_error(f"Invalid {message_direction} HL7 message Type: {msg_type}: Missing required segment {segment}.", source=SOURCE)
                    return False

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
        return ["ORC", "OBX"]  # Example for ORM messages
    
    elif msg_type == "ORU^R01":
        return ["PID", "OBR", "OBX"]  # Example for ORU^R01 messages
    
    elif msg_type == "ACK":
        return ["MSA"]  # Acknowledgment messages typically require MSA segment
    
    elif msg_type == "ORR^O02":
        return ["MSA","PID", "ORC", "OBR", "OBX"]  # Example for ORR^O02 messages
    
    # Add more message types and their required segments as needed
    else:
        return []  # Default case if message type is unknown