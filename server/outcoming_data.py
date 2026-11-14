from log.logger import log_info, log_error


# Define the source for logging purposes
SOURCE = "Server"


async def send_outgoing_data(writer, response):
    """
    Sends a message to a target client with safe type normalization.

    Args:
        writer (StreamWriter): StreamWriter for the target client.
        response (str, bytes or None): The message to send.
    """
    if response is None:
        return

    try:
        if isinstance(response, str):
            payload = response.encode("utf-8")
        elif isinstance(response, (bytes, bytearray)):
            payload = bytes(response)
        else:
            payload = str(response).encode("utf-8")

        # Write and drain response to the client socket
        writer.write(payload)
        await writer.drain()
        log_info(
            f"Response successfully sent to : {writer.get_extra_info('peername')}",
            source=SOURCE,
        )

    except Exception as e:
        log_error(f"Error sending data to client: {e}", source=SOURCE)
