import flet as ft
import datetime
from gui.views.cbc_normal_ranges import determine_age_group, get_normal_range, set_flag,NORMAL_RANGES

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
		self.age = int(self.patient_info.get("Age", ""))
		self.age_unit = self.patient_info.get("Age Unit", "")
		self.gender = self.patient_info.get("Gender", "")

		requested_date_value = self.patient_info.get("Requested Date", None)
		if requested_date_value and hasattr(requested_date_value, 'strftime'):
			self.requested_date = requested_date_value.strftime(gui_time_format)
		else:
			self.requested_date = "N/A"
		self.report_date = datetime.date.today().strftime(gui_time_format)

		self.content = ft.Row(
			controls=[
				ft.Column(
					[
						ft.Text(value=f"Name : {self.name}"),
						ft.Text(value=f"Age : {self.age} {self.age_unit}"),
						ft.Text(value=f"Sex : {self.gender}"),
					],
					spacing=2, # Reduced vertical spacing between text lines
					expand=True,
				),
				ft.Column(
					[
						ft.Text(value=f"ID : {self.patient_id}"),
						ft.Text(value=f"Requested Date : {self.requested_date}"),
						ft.Text(value=f"Report Date : {self.report_date}"),
					],
					spacing=2, # Reduced vertical spacing between text lines
					expand=True,
				),
			],
			expand=True,
		)


class ReportPatientResult(ft.Container):
	def __init__(self, patient_result: dict):
		super().__init__(
			padding=10,
			border=ft.border.all(1),
			width=794,
			expand=True,
		)
		# build the table once and drop it in
		self.content = self.build_datatable(patient_result)

	# ---------- helpers ---------------------------------------------------

	def _style_map(self) -> dict:
		"""
		Central place for sizes / icons / indents.
		"""
		return {
			# HGB
			"Hemoglobin (HGB)":               dict(size=16, space=0, icon="❤️"),

			# RBC block
			"Red Blood Cells (RBC)":          dict(size=16, space=0, icon="🩸"),
			"Hematocrit (HCT)":               dict(size=14, space=15, icon="🩸"),
			"Mean Corpuscular Volume (MCV)":  dict(size=14, space=15, icon="🩸"),
			"Mean Corpuscular Hemoglobin (MCH)":  dict(size=14, space=15, icon="🩸"),
			"Mean Corpuscular Hemoglobin Concentration (MCHC)": dict(size=14, space=15, icon="🩸"),
			"Red Cell Distribution Width (RDW)": dict(size=14, space=15, icon="🩸"),

			# PLT block
			"Platelets (PLT)":                dict(size=16, space=0, icon="🧫"),
			"Plateletcrit (PCT)":             dict(size=14, space=15, icon="🧫"),
			"Mean Platelet Volume (MPV)":     dict(size=14, space=15, icon="🧫"),
			"Platelet Distribution Width (PDW)": dict(size=14, space=15, icon="🧫"),

			# WBC block
			"White Blood Cells (WBC)":        dict(size=16, space=0, icon="🛡️"),
			"Neutrophils":                    dict(size=14, space=15, icon="🛡️"),
			"Lymphocytes":                    dict(size=14, space=15, icon="🛡️"),
			"Monocytes":                      dict(size=14, space=15, icon="🛡️"),
			"Eosinophils":                    dict(size=14, space=15, icon="🛡️"),
			"Basophils":                      dict(size=14, space=15, icon="🛡️"),
		}

	# ---------- table builder ---------------------------------------------

	def build_datatable(self, patient_result: dict) -> ft.DataTable:
		style = self._style_map()
		rows: list[ft.DataRow] = []

		# helper: skip non-test keys
		skip = {
			"Patient ID", "Name", "Age", "Age Unit", "Gender", "Requested Date"
		}

		for test_name, test_value in patient_result.items():
			if test_name in skip or test_value in (None, ""):
				continue

			# ---- laboratory logic ----------------------------------------
			age         = int(patient_result["Age"])
			age_unit    = patient_result["Age Unit"]
			gender      = patient_result["Gender"]
			age_group   = determine_age_group(age, age_unit)

			normal_range = get_normal_range(test_name, age_group, gender)
			unit         = NORMAL_RANGES[test_name]["unit"]
			range_txt    = (
				f"{normal_range[0]} - {normal_range[1]}"
				if isinstance(normal_range, tuple) else "N/A"
			)

			flag, flag_color = set_flag(test_value, normal_range)
			s = style[test_name]

			# ---- compose first cell: indent + icon + name ----------------
			first_cell = ft.Row(
				#spacing=4,
				controls=[
					ft.Container(width=s["space"]),      # indent
					ft.Text(s["icon"], size=s["size"]),
					ft.Text(test_name,       size=s["size"])
				])

			# ---- build the DataRow ---------------------------------------
			rows.append(
				ft.DataRow(
					cells=[
						ft.DataCell(first_cell),
						ft.DataCell(ft.Text(str(test_value),
											size= s["size"],
											color=flag_color)),
						ft.DataCell(ft.Text(flag,
											 size=16,
											 color=flag_color)),
						ft.DataCell(ft.Row(
									[
									ft.Text(range_txt,
											size=s["size"]),
									ft.Text(unit,
											size=s["size"],
											color=ft.Colors.GREY_600) # Adjusted color
									],
									),
						),
					]
				)
			)

		# header columns
		columns = [
			ft.DataColumn(ft.Text("Investigation")),
			ft.DataColumn(ft.Text("Result")),
			ft.DataColumn(ft.Text("Flag")),
			ft.DataColumn(ft.Text("Reference")),
		]

		return ft.DataTable(
			columns=columns,
			rows=rows,
			column_spacing=12,
			data_row_min_height=35, # Reduced row height
			data_row_max_height=35  # Reduced row height
		)
