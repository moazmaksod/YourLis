import flet as ft
import datetime


# Date format settings
gui_time_format = "%d-%m-%Y"
sql_time_format = "%Y-%m-%d"


# Dictionary for normal ranges of CBC parameters based on age
# The ranges are hypothetical and should be replaced with actual clinical data
NORMAL_RANGES = {
    "Hemoglobin (HGB)": {
        "unit": "g/dL",
        "newborn": (14, 24),
        "infant": (10, 15),
        "child": (11, 16),
        "adult": {
            "male": (13.5, 18),
            "female": (12, 16)
        }
    },
    "Red Blood Cells (RBC)": {
        "unit": "x10^6/uL",
        "newborn": (4.1, 6.1),
        "infant": (3.8, 5.5),
        "child": (4.1, 5.5),
        "adult": {
            "male": (4.7, 6.1),
            "female": (4.2, 5.4)
        }
    },
    "Hematocrit (HCT)": {
        "unit": "%",
        "newborn": (42, 65),
        "infant": (33, 41),
        "child": (34, 43),
        "adult": {
            "male": (41, 52),
            "female": (36, 48)
        }
    },
    "White Blood Cells (WBC)": {
        "unit": "x10^3/uL",
        "newborn": (9, 30),
        "infant": (6, 17.5),
        "child": (5, 14.5),
        "adult": (4.5, 11)
    },
    "Platelets (PLT)": {
        "unit": "x10^3/uL",
        "newborn": (150, 450),
        "infant": (150, 450),
        "child": (150, 450),
        "adult": (150, 450)
    },
    "Mean Corpuscular Volume (MCV)": {
        "unit": "fL",
        "newborn": (95, 120),
        "infant": (70, 85),
        "child": (75, 87),
        "adult": (80, 100)
    },
    "Mean Corpuscular Hemoglobin (MCH)": {
        "unit": "pg",
        "newborn": (30, 37),
        "infant": (24, 30),
        "child": (25, 31),
        "adult": (27, 33)
    },
    "Mean Corpuscular Hemoglobin Concentration (MCHC)": {
        "unit": "g/dL",
        "newborn": (30, 36),
        "infant": (30, 36),
        "child": (32, 36),
        "adult": (33, 36)
    },
    "Red Cell Distribution Width (RDW)": {
        "unit": "%",
        "newborn": (14, 20),
        "infant": (12, 16),
        "child": (11, 15),
        "adult": (11, 15)
    },
    "Plateletcrit (PCT)": {
        "unit": "%",
        "newborn": (0.15, 0.45),
        "infant": (0.15, 0.45),
        "child": (0.15, 0.45),
        "adult": (0.15, 0.45)
    },
    "Mean Platelet Volume (MPV)": {
        "unit": "fL",
        "newborn": (7, 11),
        "infant": (7, 11),
        "child": (7, 11),
        "adult": (7, 11)
    },
    "Platelet Distribution Width (PDW)": {
        "unit": "fL",
        "newborn": (10, 18),
        "infant": (10, 18),
        "child": (10, 18),
        "adult": (10, 18)
    },
    "Neutrophils": {
        "unit": "%",
        "newborn": (40, 80),
        "infant": (20, 50),
        "child": (30, 60),
        "adult": (40, 70)
    },
    "Lymphocytes": {
        "unit": "%",
        "newborn": (20, 40),
        "infant": (40, 70),
        "child": (30, 50),
        "adult": (20, 40)
    },
    "Monocytes": {
        "unit": "%",
        "newborn": (2, 12),
        "infant": (2, 10),
        "child": (2, 10),
        "adult": (2, 8)
    },
    "Eosinophils": {
        "unit": "%",
        "newborn": (1, 4),
        "infant": (1, 4),
        "child": (1, 4),
        "adult": (1, 4)
    },
    "Basophils": {
        "unit": "%",
        "newborn": (0, 1),
        "infant": (0, 1),
        "child": (0, 1),
        "adult": (0, 1)
    }
}


def get_normal_range(parameter, age_group, gender):
    """
    Get the normal range for a given CBC parameter, age group, and gender.

    :param parameter: The CBC parameter (e.g., "Hemoglobin (HGB)").
    :param age_group: The age group (e.g., "adult", "child").
    :param gender: The gender ("male" or "female").
    :return: A tuple representing the normal range (min, max) or None if not found.
    """

    param_info = NORMAL_RANGES.get(parameter, {})
    range_data = param_info.get(age_group)


    if isinstance(range_data, dict):  # e.g., adult has male/female
        return range_data.get(gender.lower())
    else:
        return range_data  # For non-gendered groups like child, infant, etc.


def determine_age_group(age, age_unit):
    """
    Determine the age group based on the age and age unit.

    :param age: The age as a number.
    :param age_unit: The unit of age (e.g., "days", "months", "years").
    :return: The age group (e.g., "newborn", "infant", "child", "adult").
    """
    if age_unit == "days" and age <= 28:
        return "newborn"
    elif age_unit == "months" and age <= 12:
        return "infant"
    elif age_unit == "years" and age < 18:
        return "child"
    else:
        return "adult"

def set_flag(value,normal_range):
    """
    Set a flag for a given CBC parameter value to indicate if it is high or low.

    :param value: The measured value of the parameter.
    :param parameter: The CBC parameter (e.g., "Hemoglobin (HGB)").
    :param age_group: The age group (e.g., "adult", "child").
    :return: A string flag ("High", "Low", or "Normal").
    """

    if not normal_range:
        return "Unknown"  # Return "Unknown" if no range is defined

    FLAG_LOW_COL = "yellow700"
    FLAG_HIGH_COL = "red700"
    Flag_NORMAL_COL = "green700"

    min_value, max_value = normal_range

    if value:
        if float(value) < min_value:
            return "L", FLAG_LOW_COL
        elif float(value) > max_value:
            return "H", FLAG_HIGH_COL
        else:
            return "", Flag_NORMAL_COL
    else:
            return None


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
        self.age = int(self.patient_info.get("Age", ""))
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

            if test_value:
                # Normal range
                age = int(patient_result["Age"])
                age_unit = patient_result["Age Unit"]
                gender = patient_result["Gender"]
                age_group = determine_age_group(age, age_unit)
                normal_range = get_normal_range(test_name,age_group,gender)
                test_unit = NORMAL_RANGES[test_name]['unit'] if test_name in NORMAL_RANGES else None
                flag = set_flag(test_value, normal_range)[0]
                flag_color = set_flag(test_value, normal_range)[1]

                rows.append(
                    ft.Row(
                        controls=[
                            ft.Icon(name=ft.Icons.API, size=10),
                            ft.Text(value=str(test_name)),
                            ft.Text(value=str(test_value),color=flag_color, expand=True),
                            ft.Text(value=flag,color=flag_color, expand=True),
                            ft.Text(value= normal_range,  expand=True),
                            ft.Text(value= test_unit, expand=True),
                        ],
                        expand=True,
                    )
                )

        return rows
