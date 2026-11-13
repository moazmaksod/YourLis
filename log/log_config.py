import logging
import logging.handlers
from concurrent_log_handler import ConcurrentRotatingFileHandler
import os
import datetime
import re

LOG_DIR = 'logs'
LOG_FILE_NAME = 'HealthMesh_log'
APPLICATION_NAME = "HealthMesh"


class PHIRedactingFilter(logging.Filter):
    """
    Log filter that redacts Protected Health Information (PHI), Personally
    Identifiable Information (PII), and database passwords from log records
    while preserving MSH-10 Message Control IDs for clinical auditability.
    Also ensures record.source is always populated, avoiding KeyError: 'source'.
    """

    # Regex to mask PWD=... in connection strings or config
    PASSWORD_PATTERN = re.compile(r'((?:PWD|Password)\s*=\s*)([^;]+)', re.IGNORECASE)
    PASSWORD_JSON_PATTERN = re.compile(r'("DB_PASSWORD":\s*")([^"]+)', re.IGNORECASE)

    # Regex to sanitize PID segments in raw HL7 strings:
    # PID|SetID|PatientIDExt|PatientIDInt|AltID|PatientName|...
    PID_PATTERN = re.compile(r'(PID\|[^|\r\n]*\|[^|\r\n]*\|)([^|\r\n]*)(\|[^|\r\n]*\|)([^|\r\n]*)')

    # Regex to sanitize SQL Server duplicate key error strings embedding clinical identifiers
    # Example: "Cannot insert duplicate key in object 'dbo.Patient' with value (12345, DOE JOHN)."
    SQL_DUPLICATE_KEY_PATTERN = re.compile(
        r'(duplicate key [^)]*with value \()([^)]+)(\))',
        re.IGNORECASE
    )

    def filter(self, record: logging.LogRecord) -> bool:
        # Prevent third-party logger crash if 'source' is not in extra
        if not hasattr(record, "source") or not record.source:
            record.source = "General"

        # Redact message string
        if isinstance(record.msg, str):
            record.msg = self.redact_text(record.msg)
        elif hasattr(record, "message") and isinstance(record.message, str):
            record.message = self.redact_text(record.message)

        return True

    @classmethod
    def redact_text(cls, text: str) -> str:
        if not text:
            return text

        # 1. Mask passwords
        text = cls.PASSWORD_PATTERN.sub(r'\1********', text)
        text = cls.PASSWORD_JSON_PATTERN.sub(r'\1********', text)

        # 2. Redact PID segment identifiers (Patient ID & Patient Name)
        def _redact_pid(match):
            prefix = match.group(1)      # 'PID|SetID|PatientIDExt|'
            pid_int = match.group(2)     # Patient ID Internal
            mid = match.group(3)         # '|AltID|'
            pname = match.group(4)       # Patient Name

            redacted_id = cls.mask_string(pid_int) if pid_int else ""
            redacted_name = cls.mask_string(pname) if pname else ""
            return f"{prefix}{redacted_id}{mid}{redacted_name}"

        text = cls.PID_PATTERN.sub(_redact_pid, text)

        # 3. Redact SQL duplicate key exception values
        def _redact_sql_duplicate(match):
            prefix = match.group(1)
            raw_vals = match.group(2)
            suffix = match.group(3)
            parts = [cls.mask_string(p.strip().strip("'\"")) for p in raw_vals.split(",")]
            return f"{prefix}{', '.join(parts)}{suffix}"

        text = cls.SQL_DUPLICATE_KEY_PATTERN.sub(_redact_sql_duplicate, text)

        return text

    @staticmethod
    def mask_string(val: str) -> str:
        val = str(val).strip()
        if not val:
            return ""
        if len(val) <= 2:
            return "**"
        return val[0] + "*" * (len(val) - 2) + val[-1]


def configure_logging():
    """
    Configures logging with file rotation, console output, and PHI redaction.
    """
    # Ensure the log directory exists
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Generate a timestamp for the log file name
    timestamp = datetime.datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(LOG_DIR, f"{LOG_FILE_NAME}_{timestamp}.log")

    # Create logger
    logger = logging.getLogger(APPLICATION_NAME)

    if logger.handlers:
        logger.handlers.clear()

    logger.setLevel(logging.DEBUG)

    # Formatter for log messages (with safe source display)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(source)s] - %(message)s"
    )

    phi_filter = PHIRedactingFilter()

    # File handler with log rotation (max 1 MB per file, keep 5 backup files)
    file_handler = ConcurrentRotatingFileHandler(
        log_file, maxBytes=1 * 1024 * 1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(phi_filter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(phi_filter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.addFilter(phi_filter)

    return logger
