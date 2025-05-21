from log.log_config import configure_logging

# Configure the logger using the configuration file
app_logger = configure_logging()

def log_debug(message, source='General'):
    """
    Logs a debug-level message.
    """
    app_logger.debug(f"{message}", extra={"source": source})

def log_info(message, source='General'):
    """
    Logs an info-level message.
    """
    app_logger.info(f"{message}", extra={"source": source})

def log_warning(message, source='General'):
    """
    Logs a warning-level message.
    """
    app_logger.warning(f"{message}", extra={"source": source})

def log_error(message, source='General'):
    """
    Logs an error-level message.
    """
    app_logger.error(f"{message}", extra={"source": source})

def log_critical(message, source='General'):
    """
    Logs a critical-level message.
    """
    app_logger.critical(f"{message}", extra={"source": source})
