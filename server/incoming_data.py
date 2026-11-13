import asyncio
from log.logger import log_info, log_error
from hl7msghandel.hl7parser import parse_hl7_message
from hl7msghandel.hl7responder import generate_response_message

# Define the source for logging purposes
SOURCE = "Server"


def _process_incoming_data_sync(message):
    """
    Synchronously parses HL7 incoming frame and generates response.
    Designed to be executed in a worker thread via asyncio.to_thread.
    """
    try:
        msg = parse_hl7_message(message, "Incomming")
        handel_response = generate_response_message(msg)
        if not handel_response:
            return None

        # Support both 'response' and legacy 'respose' typo
        response = handel_response.get("response")
        if response is None:
            response = handel_response.get("respose")

        sender_name_ver = handel_response.get("sender")

        if response is not None:
            parse_hl7_message(response, "Response")
            return response, sender_name_ver

        return None
    except Exception as e:
        log_error(f"Error processing incoming data: {e}", source=SOURCE)
        return None


async def handle_incoming_data(message, timeout: float = 10.0):
    """
    Handles and processes data received from a client asynchronously.
    Offloads heavy parsing and DB queries to a thread pool via asyncio.to_thread,
    preventing the asyncio event loop from freezing.

    Args:
        message (bytes or str): The incoming message from the client.
        timeout (float): Max seconds to wait for response generation before timeout.

    Returns:
        tuple (response, sender_name_ver) or None
    """
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_process_incoming_data_sync, message),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        log_error("Timeout waiting for response from processing thread.", source=SOURCE)
        return None
    except Exception as e:
        log_error(f"Error handling incoming data: {e}", source=SOURCE)
        return None
