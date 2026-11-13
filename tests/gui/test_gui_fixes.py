import csv
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import flet as ft
from gui.components import db_conn_fail_dialog
from gui.views.stream_controls import ExportButton
from gui.views.message_components import MessageDataExtractor, HL7MessageParser


def test_db_conn_fail_dialog_structure_and_callbacks():
    """
    Verify db_conn_fail_dialog constructs an ft.AlertDialog with correct
    actions and properly triggers the on_settings callback.
    """
    mock_page = MagicMock(spec=ft.Page)
    mock_on_settings = MagicMock()

    dialog = db_conn_fail_dialog(mock_page, on_settings=mock_on_settings)

    assert isinstance(dialog, ft.AlertDialog)
    assert dialog.title.value == "Database Connection Failed"
    assert len(dialog.actions) == 2

    settings_btn = dialog.actions[0]
    exit_btn = dialog.actions[1]

    settings_text = getattr(settings_btn, "text", None) or getattr(settings_btn, "content", None)
    exit_text = getattr(exit_btn, "text", None) or getattr(exit_btn, "content", None)

    assert settings_text == "Open Settings"
    assert exit_text == "Exit"

    # Simulate settings button click
    settings_btn.on_click(MagicMock())
    assert dialog.open is False
    mock_page.update.assert_called()
    mock_on_settings.assert_called_once()


def test_main_flet_import_db_conn_fail_dialog():
    """
    Verify that gui.main_flet cleanly imports db_conn_fail_dialog without NameError or ImportError.
    """
    import gui.main_flet
    assert hasattr(gui.main_flet, "db_conn_fail_dialog")
    assert gui.main_flet.db_conn_fail_dialog is db_conn_fail_dialog


def test_export_to_csv_clean_execution(tmp_path):
    """
    Verify ExportButton.export_to_csv generates valid CSV with structured HL7 data
    without raising ImportError or formatting errors.
    """
    sample_hl7_str = (
        "MSH|^~\\&|KT-60|LAB|||20231010120000||ORU^R01|MSG001|P|2.3.1\r"
        "PID|1||PAT999||SMITH^JANE\r"
        "OBX|1|NM|WBC||8.2|10^3/uL\r"
    )

    sample_hl7_bytes = (
        b"MSH|^~\\&|KT-60|LAB|||20231010120000||ORM^O01|MSG002|P|2.3.1\r"
        b"PID|1||PAT888||DOE^JOHN\r"
    )

    messages = [
        {
            "timestamp": "2026-11-13T20:00:00",
            "direction": "device",
            "client_name": "Genrui_KT60",
            "client_address": "192.168.1.50,4000",
            "message": sample_hl7_str,
        },
        {
            "timestamp": "2026-11-13T20:01:00",
            "direction": "server",
            "client_name": "Genrui_KT60",
            "client_address": "192.168.1.50,4000",
            "message": sample_hl7_bytes,
        },
    ]

    filepath_str = ExportButton.export_to_csv(
        messages=messages,
        device_name="Genrui KT60",
        save_path=str(tmp_path)
    )

    assert filepath_str is not None
    # Verify CSV contents
    with open(filepath_str, "r", newline="", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
        assert len(reader) == 2

        # Check Row 1 (ORU^R01)
        row1 = reader[0]
        assert row1["Client Name"] == "Genrui_KT60"
        assert row1["Message Type"] == "ORU^R01"
        assert row1["Patient ID"] == "PAT999"
        assert row1["Patient Name"] == "SMITH JANE"
        assert "WBC" in row1["Test Results"] or "White Blood Cell" in row1["Test Results"] or "8.2" in row1["Test Results"]

        # Check Row 2 (ORM^O01)
        row2 = reader[1]
        assert row2["Message Type"] == "ORM^O01"
        assert row2["Patient ID"] == "PAT888"
        assert row2["Patient Name"] == "DOE JOHN"


def test_hl7_message_parser_backwards_compatibility():
    """
    Verify HL7MessageParser exists as an alias for MessageDataExtractor and provides parse_hl7.
    """
    assert HL7MessageParser is MessageDataExtractor
    res = HL7MessageParser.parse_hl7("MSH|^~\\&|KT-60||||2023||ORU^R01|1|P|2.3.1\rPID|1||ID1\r")
    assert res["message_type"] == "ORU^R01"
    assert res["patient_id"] == "ID1"


def test_create_patient_row_safe_date_and_age_formatting():
    """
    Verify create_patient_row handles REST API string dates (ISO), datetime objects,
    missing dates, and decimal age strings without raising AttributeError or ValueError. (B-1 fix)
    """
    import datetime
    from gui.views.patient import create_patient_row

    mock_page = MagicMock(spec=ft.Page)

    # 1. Patient with ISO string date from FastAPI JSON and float string age
    patient_iso = {
        "Patient ID": "P101",
        "Name": "Alice Smith",
        "Age": "28.5",
        "Age Unit": "Years",
        "Gender": "F",
        "Requested Date": "2026-11-13T10:30:00",
        "Requested Test": "CBC",
        "Result State": "Completed",
    }
    row_iso = create_patient_row(mock_page, patient_iso)
    assert isinstance(row_iso, ft.DataRow)
    # The cell at index 5 is Requested Date, index 2 is Age
    assert row_iso.cells[5].content.value == "13-11-2026"
    assert row_iso.cells[2].content.value == "28"

    # 2. Patient with datetime object
    patient_dt = {
        "Patient ID": "P102",
        "Name": "Bob Jones",
        "Age": 45,
        "Age Unit": "Years",
        "Gender": "M",
        "Requested Date": datetime.datetime(2026, 11, 13, 14, 0),
        "Requested Test": "CBC",
        "Result State": "Pending",
    }
    row_dt = create_patient_row(mock_page, patient_dt)
    assert row_dt.cells[5].content.value == "13-11-2026"
    assert row_dt.cells[2].content.value == "45"

    # 3. Patient with empty/missing date and None age
    patient_empty = {
        "Patient ID": "P103",
        "Name": "Charlie Brown",
        "Age": None,
        "Age Unit": "Years",
        "Gender": "M",
        "Requested Date": "",
        "Requested Test": "CBC",
        "Result State": "Pending",
    }
    row_empty = create_patient_row(mock_page, patient_empty)
    assert row_empty.cells[5].content.value == ""
    assert row_empty.cells[2].content.value == ""
