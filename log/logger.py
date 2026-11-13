from log.log_config import configure_logging, PHIRedactingFilter

# Configure the logger using the configuration file
app_logger = configure_logging()


def mask_identifier(val) -> str:
    """
    Masks a sensitive string (e.g. patient name, ID, MRN) preserving only the first
    and last characters for correlation while redacting the rest.
    Example: 'DOE JOHN' -> 'D******N', '12345' -> '1***5'
    """
    if val is None:
        return "<NULL>"
    val_str = str(val).strip()
    if not val_str:
        return ""
    if len(val_str) <= 2:
        return "**"
    return val_str[0] + "*" * (len(val_str) - 2) + val_str[-1]


def sanitize_parameters(values):
    """
    Sanitizes SQL parameters tuple/list, masking sensitive text values to prevent PHI leakage.
    """
    if values is None:
        return ()
    if isinstance(values, (list, tuple)):
        sanitized = []
        for v in values:
            if v is None:
                sanitized.append(None)
            elif isinstance(v, (int, float, bool)):
                sanitized.append(v)
            else:
                sanitized.append(mask_identifier(str(v)))
        return tuple(sanitized) if isinstance(values, tuple) else sanitized
    return mask_identifier(str(values))


def redact_hl7_text(text: str) -> str:
    """Redacts raw HL7 text using the PHIRedactingFilter."""
    return PHIRedactingFilter.redact_text(text)


def log_debug(message, source='General'):
    """Logs a debug-level message."""
    app_logger.debug(f"{message}", extra={"source": source})


def log_info(message, source='General'):
    """Logs an info-level message."""
    app_logger.info(f"{message}", extra={"source": source})


def log_warning(message, source='General'):
    """Logs a warning-level message."""
    app_logger.warning(f"{message}", extra={"source": source})


def log_error(message, source='General'):
    """Logs an error-level message."""
    app_logger.error(f"{message}", extra={"source": source})


def log_critical(message, source='General'):
    """Logs a critical-level message."""
    app_logger.critical(f"{message}", extra={"source": source})
