from database.sqlqueries import exec_procedure_for
from database.sqldbdictionary import PATIENT_CBC_RESULT_SQL
from gui.views.report_component import ReportPatientInfo, ReportPatientResult
from log.logger import log_info, log_error
import datetime
import flet as ft


async def fetch_patient_cbc_result(patient_id=None):
    """
    Fetches patient data based on the provided filters.
    """
    try:
        params = {
            "PATIENT_ID": patient_id or None,
        }

        return await exec_procedure_for(PATIENT_CBC_RESULT_SQL, params) or []
    except Exception as e:
        log_error(f"Error fetching patient cbc result: {e}")
        return []


async def cbc_report_view(page: ft.Page, patient_id):
    """
    CBC report view content.
    """

    result_data = await fetch_patient_cbc_result(patient_id)

    result_data = result_data[0]

    if result_data:

        patient_info_view = ReportPatientInfo(result_data)  # type: ignore
        patient_result_view = ReportPatientResult(result_data)  # type: ignore

        def close_report_view(e):
            if report_view:
                report_view.open = False
                page.update()  # Update the page to reflect changes

        report_view = ft.AlertDialog(
            modal=True,
            scrollable=True,
            title=ft.Text("Hematology Report"),
            content=ft.Column([patient_info_view, patient_result_view]),
            actions=[
                ft.ElevatedButton("Close", on_click=close_report_view),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(report_view)
        report_view.open = True

    page.update()
