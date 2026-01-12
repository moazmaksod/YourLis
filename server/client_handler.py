from server.incoming_data import handle_incoming_data
from server.outcoming_data import send_outgoing_data
from log.logger import log_info, log_error
from datetime import datetime
from collections import deque


# Dictionary to store active clients (address -> writer)
clients = {}

# Dictionary to store active clients with ans asighn names
clients_with_names = {}

# Queue to store communication messages
communication_messages = deque(maxlen=100)  # Store last 100 messages

# Define the source for logging purposes
SOURCE = "Server"

# Buffer size limit for reading data from the client
BUFFER_SIZE_LIMIT = 4096

# Constants for HL7 messages
MESSAGE_END_MARKER = b"\x1c"
MESSAGE_START_MARKER = b"\x0b"


def add_communication_message(client_address, message, direction):
    """
    Add a message to the communication queue
    """
    client_name = clients_with_names.get(client_address)
    if client_name is None:
        # If no name is assigned, use the address as string
        if isinstance(client_address, tuple):
            ip, port = client_address
            client_name = f"{ip}"
        else:
            client_name = str(client_address)

    msg = {
        "timestamp": datetime.now().isoformat(),
        "client_name": client_name,
        "client_address": str(client_address),  # Store address as string"
        "message": message.decode() if isinstance(message, bytes) else str(message),
        "direction": direction,
    }
    communication_messages.append(msg)


def get_communication_messages():
    """
    Get all stored communication messages
    """
    return list(communication_messages)


async def handle_client_connection(reader, writer):
    """
    Manages individual client connections.

    Args:
        reader (StreamReader): StreamReader for reading client data.
        writer (StreamWriter): StreamWriter for sending data to the client.
    """
    client_address = writer.get_extra_info("peername")
    log_info(f"Client connected: {client_address}", source=SOURCE)
    add_communication_message(client_address, "Connected", "info")

    clients_with_names.update(
        {client_address: None}
    )  # Initialize the client with no name

    # Register the client in the active clients dictionary
    clients[client_address] = writer

    buffer = bytearray()  # Use bytearray for efficient appending

    try:
        while True:
            # Read data in chunks
            data = await reader.read(BUFFER_SIZE_LIMIT)  # Adjust the size as needed

            if not data:
                break  # End of stream

            buffer.extend(data)  # Accumulate data in the buffer

            # Process messages from the buffer
            while True:
                start_index = buffer.find(MESSAGE_START_MARKER)
                end_index = buffer.find(MESSAGE_END_MARKER, start_index)

                if start_index == -1 or end_index == -1:
                    break  # No more complete messages

                # Extract the message
                message = bytes(buffer[start_index : end_index + 1])

                # Remove the processed part from the buffer
                del buffer[: end_index + 1]

                log_info(
                    f"({len(message)}) of Data received from ({client_address})",
                    source=SOURCE,
                )

                # Log incoming message
                add_communication_message(client_address, message, "device")

                # Process the incoming data and get a response
                handel_response = handle_incoming_data(message)

                # Send the response back to the client if available
                if handel_response is not None:
                    response = handel_response[0]  # Extract the response from the tuple
                    clients_with_names.update(
                        {client_address: handel_response[1]}
                    )  # Update the client name if available

                    # Log outgoing message
                    add_communication_message(client_address, response, "server")

                    result = send_outgoing_data(writer, response)
                    if hasattr(result, "__await__"):
                        await result
                else:
                    log_info(
                        f"No response generated for {client_address}: {message}",
                        source=SOURCE,
                    )


    except Exception as e:
        log_error(f"Error with client {client_address}: {e}", source=SOURCE)
        add_communication_message(client_address, f"Error: {str(e)}", "error")
    finally:
        # Handle client disconnection
        log_info(f"Client disconnected: {client_address}", source=SOURCE)
        add_communication_message(client_address, "Disconnected", "info")
        writer.close()
        await writer.wait_closed()
        clients.pop(client_address, None)
        clients_with_names.pop(client_address, None)
