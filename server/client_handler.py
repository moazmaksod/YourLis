import asyncio
from server.incoming_data import handle_incoming_data
from server.outcoming_data import send_outgoing_data
from log.logger import log_info, log_error, redact_hl7_text
from datetime import datetime
from collections import deque


# Dictionary to store active clients (address -> writer)
clients = {}

# Dictionary to store active clients with assigned names
clients_with_names = {}

# Queue to store communication messages
communication_messages = deque(maxlen=100)  # Store last 100 messages

# Define the source for logging purposes
SOURCE = "Server"

# Buffer size limit for individual socket reads
BUFFER_SIZE_LIMIT = 4096

# MLLP Framing standard constants (VT = 0x0B, FS = 0x1C, CR = 0x0D)
MESSAGE_START_MARKER = b"\x0b"
MESSAGE_END_MARKER = b"\x1c"
MESSAGE_CR_BYTE = 0x0D

# Guard against unbounded buffer memory growth (5 MB DoS threshold)
MAX_BUFFER_LIMIT = 5 * 1024 * 1024


def add_communication_message(client_address, message, direction):
    """
    Add a message to the communication queue, with PHI redacted for storage/display.
    """
    addr_key = client_address
    if isinstance(client_address, tuple):
        addr_key = f"{client_address[0]},{client_address[1]}"
    
    client_name = clients_with_names.get(addr_key)
    if client_name is None:
        if isinstance(client_address, tuple):
            ip, port = client_address
            client_name = f"{ip}"
        else:
            client_name = str(client_address)

    raw_text = message.decode('utf-8', errors='replace') if isinstance(message, bytes) else str(message)
    sanitized_text = redact_hl7_text(raw_text)

    msg = {
        "timestamp": datetime.now().isoformat(),
        "client_name": client_name,
        "client_address": addr_key,
        "message": sanitized_text,
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
    Manages individual client connections with robust MLLP framing,
    TCP fragmentation handling, and bounded buffer protection.

    Args:
        reader (StreamReader): StreamReader for reading client data.
        writer (StreamWriter): StreamWriter for sending data to the client.
    """
    peername = writer.get_extra_info("peername")
    if isinstance(peername, tuple):
        client_address = f"{peername[0]},{peername[1]}"
    else:
        client_address = str(peername)

    log_info(f"Client connected: {client_address}", source=SOURCE)
    add_communication_message(client_address, "Connected", "info")

    clients_with_names.update({client_address: None})
    clients[client_address] = writer

    # Enable TCP keepalive if supported by platform socket
    try:
        raw_sock = writer.get_extra_info("socket")
        if raw_sock:
            import socket
            raw_sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    except Exception:
        pass

    buffer = bytearray()

    try:
        while True:
            # Read incoming stream bytes with 300s inactivity timeout to reclaim half-open sockets
            try:
                data = await asyncio.wait_for(reader.read(BUFFER_SIZE_LIMIT), timeout=300.0)
            except asyncio.TimeoutError:
                log_info(f"Client {client_address} idle read timeout reached. Closing connection.", source=SOURCE)
                break

            is_eof = not data
            if data:
                buffer.extend(data)
            elif not buffer:
                break  # Peer disconnected and buffer is empty

            # Check bounded buffer limit to prevent DoS memory exhaustion
            if len(buffer) > MAX_BUFFER_LIMIT:
                log_error(
                    f"Client {client_address} exceeded maximum buffer limit ({MAX_BUFFER_LIMIT} bytes). Disconnecting.",
                    source=SOURCE,
                )
                break

            # Parse and process all complete MLLP frames in the buffer (handles bursts / coalesced packets)
            while True:
                start_index = buffer.find(MESSAGE_START_MARKER)
                if start_index == -1:
                    # If no start marker exists in buffer, discard leading bytes beyond safety window
                    if len(buffer) > 4096:
                        buffer.clear()
                    break

                # Discard any leading noise/orphaned bytes before the start marker
                if start_index > 0:
                    del buffer[:start_index]
                    start_index = 0

                # Search for MLLP end marker (0x1C) starting after start marker
                end_pos = buffer.find(MESSAGE_END_MARKER, start_index + 1)
                if end_pos == -1:
                    # Frame is fragmented across TCP packets; await more data
                    break

                # If 0x1C is the very last byte in buffer, check if trailing \r (0x0D) arrives in next TCP chunk.
                # Use a bounded wait (100ms) to avoid protocol deadlock when an analyzer sends standalone \x1c.
                if len(buffer) == end_pos + 1 and not is_eof:
                    try:
                        more_data = await asyncio.wait_for(reader.read(BUFFER_SIZE_LIMIT), timeout=0.1)
                        if more_data:
                            buffer.extend(more_data)
                        else:
                            is_eof = True
                    except asyncio.TimeoutError:
                        pass

                # Determine end delimiter length (standard \x1c\r or standalone \x1c, plus optional \n)
                delimiter_len = 1
                if len(buffer) > end_pos + 1 and buffer[end_pos + 1] == MESSAGE_CR_BYTE:
                    delimiter_len = 2
                    if len(buffer) > end_pos + 2 and buffer[end_pos + 2] == 0x0A:
                        delimiter_len = 3

                full_frame_end = end_pos + delimiter_len
                message = bytes(buffer[start_index:full_frame_end])

                # Advance buffer past processed frame
                del buffer[:full_frame_end]

                log_info(
                    f"({len(message)}) of Data received from ({client_address})",
                    source=SOURCE,
                )

                # Frame-level processing with resilient error isolation (Task 2.2)
                try:
                    # Log incoming message
                    add_communication_message(client_address, message, "device")

                    # Asynchronously process incoming HL7 data
                    handel_response = await handle_incoming_data(message)

                    if handel_response is not None and handel_response[0] is not None:
                        response = handel_response[0]
                        if handel_response[1]:
                            clients_with_names.update({client_address: handel_response[1]})

                        # Log outgoing message
                        add_communication_message(client_address, response, "server")

                        result = send_outgoing_data(writer, response)
                        if hasattr(result, "__await__"):
                            await result
                    elif handel_response is not None and handel_response[1]:
                        clients_with_names.update({client_address: handel_response[1]})
                    else:
                        log_info(
                            f"No response generated for {client_address}",
                            source=SOURCE,
                        )
                except Exception as frame_err:
                    log_error(
                        f"Error processing frame from {client_address}: {frame_err}",
                        source=SOURCE,
                    )
                    add_communication_message(
                        client_address, f"Error processing frame: {frame_err}", "error"
                    )
                    # Send NAK response so client analyzer does not timeout/hang
                    try:
                        from hl7msghandel.hl7responder import generate_nak_response
                        nak_frame = generate_nak_response(message, str(frame_err), "AE")
                        add_communication_message(client_address, nak_frame, "server")
                        result = send_outgoing_data(writer, nak_frame)
                        if hasattr(result, "__await__"):
                            await result
                    except Exception as nak_err:
                        log_error(
                            f"Failed to transmit NAK to {client_address}: {nak_err}",
                            source=SOURCE,
                        )

            if is_eof:
                break

    except Exception as e:
        log_error(f"Error with client {client_address}: {e}", source=SOURCE)
        add_communication_message(client_address, f"Error: {str(e)}", "error")
    finally:
        log_info(f"Client disconnected: {client_address}", source=SOURCE)
        add_communication_message(client_address, "Disconnected", "info")
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        clients.pop(client_address, None)
        clients_with_names.pop(client_address, None)
