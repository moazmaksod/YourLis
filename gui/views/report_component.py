import flet as ft
import datetime

# Date format settings
gui_time_format = "%d-%m-%Y"
sql_time_format = "%Y-%m-%d"


class ReportPatientInfo(ft.Container):

    def __init__(self, patient_info: dict):
        super().__init__(
            content=None,
            padding=ft.padding.all(10),
            border=ft.border.all(1),
            width=794,
        )
        self.patient_info = patient_info

        self.patient_id = self.patient_info.get("Patient ID", "")
        self.name = self.patient_info.get("Name", "")
        self.age = str(self.patient_info.get("Age", ""))
        self.age_unit = self.patient_info.get("Age Unit", "")
        self.gender = self.patient_info.get("Gender", "")

        self.requested_date = self.patient_info.get("Requested Date", "").strftime(
            gui_time_format
        )
        self.report_date = datetime.date.today().strftime(gui_time_format)

        self.content = ft.Row(
            controls=[
                ft.Column(
                    [
                        ft.Text(value=f"Name : {self.name}"),
                        ft.Text(value=f"Age : {self.age} {self.age_unit}"),
                        ft.Text(value=f"Sex : {self.gender}"),
                    ],
                    expand=True,
                ),
                ft.Column(
                    [
                        ft.Text(value=f"ID : {self.patient_id}"),
                        ft.Text(value=f"Requested Date : {self.requested_date}"),
                        ft.Text(value=f"Report Date : {self.report_date}"),
                    ],
                    expand=True,
                ),
            ],
            expand=True,
        )


class ReportPatientResult(ft.Container):

    def __init__(self, patient_result: dict):
        super().__init__(
            content=None,
            padding=ft.padding.all(10),
            border=ft.border.all(1),
            width=794,
            expand=True,
        )

        self.content = ft.Column(controls=self.create_result_rows(patient_result))

    def create_result_rows(self, patient_result: dict):
        rows = []

        rows.append(
            ft.Row(
                controls=[
                    ft.Text(value="Compleate Blood Count", width=200, expand=True),
                    ft.Divider(),
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )

        rows.append(
            ft.Row(
                controls=[
                    ft.Text(value="Investigation", width=250),
                    ft.Text(value="Result", width=100, expand=True),
                    ft.Text(value="Condition", width=100, expand=True),
                    ft.Text(value="Refrence Value", width=200, expand=True),
                    ft.Text(value="Unit", width=100, expand=True),
                ],
                expand=True,
            )
        )

        for test_name, test_value in patient_result.items():
            if test_name in [
                "Patient ID",
                "Name",
                "Age",
                "Age Unit",
                "Gender",
                "Requested Date",
            ]:
                continue
            rows.append(
                ft.Row(
                    controls=[
                        ft.Icon(name=ft.Icons.API, size=10),
                        ft.Text(value=str(test_name), width=250),
                        ft.Text(value=str(test_value), width=100, expand=True),
                        ft.Text(value="Normal", width=200, expand=True),
                        ft.Text(value="Normal range", width=200, expand=True),
                        ft.Text(value="mg/dl", width=100, expand=True),
                    ],
                    expand=True,
                )
            )

        return rows
