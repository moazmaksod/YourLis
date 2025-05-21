from log.logger import log_info, log_error
from hl7msghandel.hl7parser import parse_hl7_message
from hl7msghandel.hl7responder import generate_response_message
from threading import Thread
import queue

# Define the source for logging purposes
SOURCE = "Server"

def handle_incoming_data(message):

    """
    Handles and processes data received from a client.

    Args:
        message (str): The incoming message from the client.

    Returns: 
        str: The response to be sent back to the client.
    """
    try:
        # Create a simple response to echo back to the client
        msg = parse_hl7_message(message, "Incomming")


        # Use a Queue to get the response from the thread
        response_queue = queue.Queue()

        # Define a function to generate the response in a separate thread
        def threaded_response_generation(queue):
            try:
                # Generate the response using the parsed message
                response = generate_response_message(msg)
                response_queue.put(response)  # Put the result in the queue
            except Exception as e:
                log_error(f"Error generating response in thread: {e}", source=SOURCE)
                response_queue.put(None)  # Put None in case of error

        # Start the thread
        response_thread = Thread(target=threaded_response_generation, args=(response_queue,))
        response_thread.start()

        # Get the response from the queue (blocking with timeout)
        try:
            handel_response = response_queue.get(timeout=10)  # Adjust timeout as needed
            response = handel_response["respose"]
            sender_name_ver = handel_response["sender"]
            parse_hl7_message(response, "Response")
        except queue.Empty:
            log_error("Timeout waiting for response from thread.", source=SOURCE)
            return None  # Or a suitable timeout response

        if response is None:
            return None # Handle the error case

        return response,sender_name_ver
    
    except Exception as e:
        log_error(f"Error handling incoming data>: {e}", source=SOURCE)




