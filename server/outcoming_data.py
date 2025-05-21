from log.logger import log_info, log_error


# Define the source for logging purposes
SOURCE = "Server"


async def send_outgoing_data(writer, response):
    """
    Sends a message to a target client.

    Args:
        writer (StreamWriter): StreamWriter for the target client.
        response (str): The message to send.
    """
    try:
        # Encode the response and write it to the client
        writer.write(response.encode())
        await writer.drain()
        log_info(
            f"Response succdesfully sent to : {writer.get_extra_info('peername')}",
            source=SOURCE,
        )

    except Exception as e:
        log_error(f"Error sending data to client: {e}", source=SOURCE)
