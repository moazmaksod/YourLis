from server.incoming_data import handle_incoming_data
from server.outcoming_data import send_outgoing_data
from log.logger import log_info, log_error


# Dictionary to store active clients (address -> writer)
clients = {}

# Dictionary to store active clients with ans asighn names
clients_with_names = {}

# Define the source for logging purposes
SOURCE = "Server"

# Buffer size limit for reading data from the client
BUFFER_SIZE_LIMIT = 4096

# Constants for HL7 messages
MESSAGE_END_MARKER = b"\x1c"
MESSAGE_START_MARKER = b"\x0b"


async def handle_client_connection(reader, writer):
    """
    Manages individual client connections.

    Args:
        reader (StreamReader): StreamReader for reading client data.
        writer (StreamWriter): StreamWriter for sending data to the client.
    """
    client_address = writer.get_extra_info("peername")
    log_info(f"Client connected: {client_address}", source=SOURCE)

    clients_with_names.update(
        {client_address: None}
    )  # Initialize the client with no name

    # Register the client in the active clients dictionary
    clients[client_address] = writer

    buffer = bytearray()  # Use bytearray for efficient appending
    messages = []  # List to store extracted messages

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
                message = buffer[
                    start_index : end_index + 1
                ]  # +1 to skip the start marker

                messages.append(bytes(message))  # Store the message as bytes

                # Remove the processed part from the buffer
                del buffer[: end_index + 1]  # +1 to skip the end marker

            for message in messages:

                log_info(
                    f"({len(message)})of Data received from ({client_address})",
                    source=SOURCE,
                )

                # Process the incoming data and get a response
                handel_response = handle_incoming_data(message)

                # Send the response back to the client if available
                if handel_response != None:
                    response = handel_response[0]  # Extract the response from the tuple
                    clients_with_names.update(
                        {client_address: handel_response[1]}
                    )  # Update the client name if available
                    await send_outgoing_data(writer, response)
                else:
                    log_info(
                        f"No response generated for {client_address}: {message}",
                        source=SOURCE,
                    )

                messages.pop(messages.index(message))

    except Exception as e:
        log_error(f"Error with client {client_address}: {e}", source=SOURCE)
    finally:
        # Handle client disconnection
        log_info(f"Client disconnected: {client_address}", source=SOURCE)
        writer.close()
        await writer.wait_closed()
        clients.pop(client_address, None)
        clients_with_names.pop(client_address, None)
