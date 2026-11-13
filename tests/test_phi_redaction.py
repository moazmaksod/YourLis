import logging
import pytest
from log.logger import mask_identifier, sanitize_parameters, redact_hl7_text, log_info, log_error
from log.log_config import PHIRedactingFilter


def test_mask_identifier_various_lengths():
    """Verify mask_identifier properly redacts middle characters of identifiers."""
    assert mask_identifier("JOHN DOE") == "J******E"
    assert mask_identifier("123456789") == "1*******9"
    assert mask_identifier("AB") == "**"
    assert mask_identifier("A") == "**"
    assert mask_identifier("") == ""
    assert mask_identifier(None) == "<NULL>"


def test_sanitize_parameters_masks_sensitive_values():
    """Verify SQL parameters tuple/list masks strings while preserving numbers and None."""
    params = ("JOHN DOE", 42, 13.5, None, "SECRET_ID_99")
    sanitized = sanitize_parameters(params)

    assert isinstance(sanitized, tuple)
    assert sanitized[0] == "J******E"
    assert sanitized[1] == 42
    assert sanitized[2] == 13.5
    assert sanitized[3] is None
    assert sanitized[4] == "S**********9"


def test_phi_redacting_filter_hl7_pid_and_preserves_msh10():
    """
    Verify that raw HL7 frames logged to disk have patient identifiers redacted
    from the PID segment while preserving MSH-10 Message Control ID.
    """
    filter_instance = PHIRedactingFilter()

    raw_hl7 = (
        "MSH|^~\\&|KT60|LAB|||20261113||ORU^R01|MSG_CTRL_789|P|2.3.1\r"
        "PID|1||PATIENT_ID_456||DOE^JOHN||19850101|M\r"
        "OBR|1|||||||||||||||||||||||Genrui\r"
        "OBX|1|NM|WBC||7.5|10^3/uL\r"
    )

    record = logging.LogRecord(
        name="HealthMesh",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg=f"Raw HL7 message: {raw_hl7}",
        args=(),
        exc_info=None,
    )

    filter_instance.filter(record)

    # MSH-10 Message Control ID MUST be preserved for traceability
    assert "MSG_CTRL_789" in record.msg

    # PID patient identifiers MUST be redacted
    assert "PATIENT_ID_456" not in record.msg
    assert "DOE^JOHN" not in record.msg
    assert "P************6" in record.msg or "P*" in record.msg
    assert "D******N" in record.msg or "D*" in record.msg


def test_phi_redacting_filter_passwords():
    """Verify connection string passwords and config passwords are redacted."""
    filter_instance = PHIRedactingFilter()

    conn_str = "DRIVER=ODBC Driver 17;SERVER=127.0.0.1;DATABASE=LIS;UID=sa;PWD=SuperSecretPassword123;"
    record = logging.LogRecord(
        name="HealthMesh",
        level=logging.INFO,
        pathname=__file__,
        lineno=20,
        msg=f"Connecting with {conn_str}",
        args=(),
        exc_info=None,
    )

    filter_instance.filter(record)
    assert "SuperSecretPassword123" not in record.msg
    assert "PWD=********" in record.msg


def test_log_record_missing_source_does_not_crash():
    """Verify third-party log records missing 'source' attribute do not crash the formatter with KeyError."""
    filter_instance = PHIRedactingFilter()

    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=30,
        msg="GET /server/status 200 OK",
        args=(),
        exc_info=None,
    )

    # record initially has no 'source' attribute
    assert not hasattr(record, "source")
    filter_instance.filter(record)

    # Filter must inject default 'General' source
    assert hasattr(record, "source")
    assert record.source == "General"

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(source)s] - %(message)s"
    )
    formatted = formatter.format(record)
    assert "[General]" in formatted
    assert "GET /server/status 200 OK" in formatted


def test_phi_redacting_filter_sql_duplicate_key_exception():
    """
    Verify that SQL Server duplicate key error messages containing cleartext clinical identifiers
    are masked by PHIRedactingFilter to prevent PHI leakage. (M-7 fix)
    """
    filter_instance = PHIRedactingFilter()

    error_msg = (
        "pyodbc.IntegrityError: ('23000', \"[23000] [Microsoft][ODBC Driver 17 for SQL Server][SQL Server]"
        "Cannot insert duplicate key in object 'dbo.Patient' with value (987654, JANE DOE). (2627) (SQLExecDirectW)\")"
    )

    record = logging.LogRecord(
        name="HealthMesh",
        level=logging.ERROR,
        pathname=__file__,
        lineno=40,
        msg=f"Error executing query: {error_msg}",
        args=(),
        exc_info=None,
    )

    filter_instance.filter(record)

    # Identifiers must not be present in cleartext
    assert "987654" not in record.msg
    assert "JANE DOE" not in record.msg
    # Masked versions must be present
    assert "9****4" in record.msg
    assert "J******E" in record.msg

