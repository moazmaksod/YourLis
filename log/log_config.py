import logging
import logging.handlers
import os
import datetime





LOG_DIR = 'logs'
LOG_FILE_NAME = 'HealthMesh_log'
APPLICATION_NAME = "HealthMesh"



# Define the log configuration
def configure_logging():
    """
    Configures logging with file rotation, console output, and a custom GUI handler.

    Args:
        output_text_widget (ctk.Text): The text widget in your GUI to display log messages.
    """

    # Ensure the log directory exists
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Generate a timestamp for the log file name
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(LOG_DIR, f"{LOG_FILE_NAME}_{timestamp}.log")

    # Create a logger
    logger = logging.getLogger(APPLICATION_NAME)


    if logger.handlers:  # Check if handlers already exist
        logger.handlers.clear()  # Remove all existing handlers
    
    logger.setLevel(logging.DEBUG)  # Set the base logging level

    # Formatter for log messages
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(source)s] - %(message)s"
    )

    # File handler with log rotation (max 1 MB per file, keep 5 backup files)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=1 * 1024 * 1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # Capture all logs to the file
    file_handler.setFormatter(formatter)

    # Console handler for WARNING and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Only WARNING and above to console
    console_handler.setFormatter(formatter)


    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

 

    return logger