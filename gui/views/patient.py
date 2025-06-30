import flet as ft
from database.sqlqueries import exec_procedure_for
from database.sqldbdictionary import PATIENT_SEARCH_SQL
from gui.views.cbc_report import cbc_report_view
from log.logger import log_info, log_error
import datetime

# Date format settings
gui_time_format = "%d-%m-%Y"
sql_time_format = "%Y-%m-%d"

# Number of results per page
RESULTS_PER_PAGE = 20


class PaginatedDataTable(ft.DataTable):
    """
    A DataTable that supports pagination.
    """

    def __init__(self, page: ft.Page, results_per_page):
        super().__init__(
            columns=[
                ft.DataColumn(ft.Text("Patient ID")),
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Age")),
                ft.DataColumn(ft.Text("Age Unit")),
                ft.DataColumn(ft.Text("Gender")),
                ft.DataColumn(ft.Text("Requested Date")),
                ft.DataColumn(ft.Text("Requested Test")),
                ft.DataColumn(ft.Text("Result State")),
                ft.DataColumn(ft.Text("Result")),
            ],
            rows=[],
            expand=True,
            width=2000,
            # vertical_lines=ft.BorderSide(width=0.5, color=ft.Colors.WHITE),
            divider_thickness=0.5,
        )
        self.page = page
        self.results_per_page = results_per_page
        self.total_pages = 1
        self.all_data = []

    async def load_page(self, page_number):
        """Loads only the relevant rows for the given page number."""
        if not self.all_data:
            log_info("No data to display in the table.")

            self.rows.clear()  # type: ignore
            self.update()
            return

        start = (page_number - 1) * self.results_per_page
        end = start + self.results_per_page

        log_info(f"Loading page {page_number}: Displaying records {start} to {end}")

        # Clear old rows and load only the relevant ones

        self.rows.clear()  # type: ignore
        self.rows.extend(  # type: ignore
            create_patient_row(self.page, patient)
            for patient in self.all_data[start:end]
        )
        self.update()


async def fetch_patient_data(
    patient_id=None,
    patient_name=None,
    start_date=None,
    end_date=None,
    result_finished=None,
):
    """
    Fetches patient data based on the provided filters.
    """
    try:
        params = {
            "PATIENT_ID": patient_id or None,
            "PATIENT_NAME": patient_name or None,
            "START_DATE": start_date or None,
            "END_DATE": end_date or None,
            "RESULT_FINISHED": result_finished,
        }

        return await exec_procedure_for(PATIENT_SEARCH_SQL, params) or []
    except Exception as e:
        log_error(f"Error fetching patient data: {e}")
        return []


def create_patient_row(page, patient):
    """
    Creates a DataRow for the patient table.
    """
    requested_date = patient.get("Requested Date", "")
    requested_date = requested_date.strftime(gui_time_format)
    age = str(int(patient["Age"])) if patient["Age"] else ""

    async def view_results_click(e):
        await on_view_results_click(page, patient["Patient ID"])

    return ft.DataRow(
        cells=[
            ft.DataCell(ft.Text(patient["Patient ID"])),
            ft.DataCell(ft.Text(patient["Name"])),
            ft.DataCell(ft.Text(age)),
            ft.DataCell(ft.Text(patient["Age Unit"])),
            ft.DataCell(ft.Text(patient["Gender"])),
            ft.DataCell(ft.Text(requested_date)),
            ft.DataCell(ft.Text(patient["Requested Test"])),
            ft.DataCell(ft.Text(patient["Result State"])),
            ft.DataCell(
                ft.ElevatedButton(
                    text="View Result",
                    on_click=view_results_click,
                )
            ),
        ]
    )


async def on_search_click(
    patient_table,
    patient_id_field,
    patient_name_field,
    start_date_field,
    end_date_field,
    result_state_variable,
):
    """
    Handles the search button click event with pagination.
    """
    try:

        result_condition = {"Pending": 0, "Completed": 1}.get(
            result_state_variable.value, None
        )

        start_date = (
            datetime.datetime.strptime(
                start_date_field.value, gui_time_format
            ).strftime(sql_time_format)
            if start_date_field.value
            else None
        )

        end_date = (
            datetime.datetime.strptime(end_date_field.value, gui_time_format).strftime(
                sql_time_format
            )
            if end_date_field.value
            else None
        )

        log_info(
            f"Executing patient search with filters: "
            f"ID={patient_id_field.value.strip()}, Name={patient_name_field.value.strip()}, "
            f"Start Date={start_date}, End Date={end_date}, Result Finished={result_condition}"
        )

        # Fetch data from database
        all_patient_data = await fetch_patient_data(
            patient_id=patient_id_field.value.strip(),
            patient_name=patient_name_field.value.strip(),
            start_date=start_date,
            end_date=end_date,
            result_finished=result_condition,
        )

        if not all_patient_data:
            log_info("No patients found, clearing table.")
            patient_table.rows.clear()
            patient_table.update()
            return

        log_info(f"Search completed. Found {len(all_patient_data)} records.")

        # Store all data in the table and paginate
        patient_table.all_data = all_patient_data
        patient_table.total_pages = max(
            1,
            len(all_patient_data) // RESULTS_PER_PAGE
            + (len(all_patient_data) % RESULTS_PER_PAGE > 0),
        )

        log_info(f"Total pages: {patient_table.total_pages}")

        # Load the first page of results
        await patient_table.load_page(1)

    except Exception as e:
        log_error(f"Error during search: {e}")


async def on_view_results_click(page: ft.Page, patient_id):
    """Handles the 'View Results' button click event."""
    log_info(f"View results for Patient ID: {patient_id}")
    await cbc_report_view(page, patient_id)


def patient_view(page: ft.Page):
    """
    Main patient page layout with pagination.
    """
    # today dates
    today_date_str = datetime.date.today().strftime(gui_time_format)

    # Search filters
    patient_id_field = ft.TextField(label="ID", width=180)
    patient_name_field = ft.TextField(label="Name", expand=True)

    # Date pickers
    def create_date_picker(label, date_field):
        date_picker = ft.DatePicker(
            first_date=datetime.date(2000, 1, 1),
            last_date=datetime.date(2060, 12, 31),
            current_date=datetime.date.today(),
            on_change=lambda e: on_date_change(e, date_field),
        )
        return ft.ElevatedButton(
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            height=50,
            text=label,
            on_click=lambda _: page.open(date_picker),
        )

    # Date picker functions
    def on_date_change(e, date_field):
        """Updates the date field with the selected date in DD-MM-YYYY format."""
        if e.control.value:
            date_field.value = e.control.value.strftime(gui_time_format)
            date_field.update()

    start_date_field = ft.TextField(
        value=today_date_str,
        width=120,
        disabled=True,
    )
    start_date_picker_button = create_date_picker("From", start_date_field)

    end_date_field = ft.TextField(
        value=today_date_str,
        width=120,
        disabled=True,
    )
    end_date_picker_button = create_date_picker("To", end_date_field)

    # Result state dropdown
    result_state_variable = ft.Dropdown(
        options=[
            ft.dropdown.Option("All"),
            ft.dropdown.Option("Completed"),
            ft.dropdown.Option("Pending"),
        ],
        value="Pending",
        width=150,
    )

    # Pagination state
    global current_page
    current_page = 1
    total_pages = ft.Text(" / 1")

    async def update_page_number(e):
        global current_page
        if e.control.value.isdigit():
            if 0 < int(e.control.value) <= patient_table.total_pages:
                current_page = int(e.control.value)
                await patient_table.load_page(current_page)
                await update_pagination_display(current_page)
            else:
                e.control.value = current_page
                e.control.update()
        else:
            e.control.value = current_page
            e.control.update()

    # Total page input and pagination controls
    total_page_input = ft.TextField(value="1", width=50, on_blur=update_page_number)

    # Pagination display and controls
    async def update_pagination_display(current_page):
        total_page_input.value = current_page
        total_pages.value = f" / {max(1, patient_table.total_pages)}"
        total_page_input.update()
        total_pages.update()

    # Buttons for navigating to the previous and next pages
    async def next_page(_):
        global current_page
        if current_page < patient_table.total_pages:
            current_page += 1
            await patient_table.load_page(current_page)
            await update_pagination_display(current_page)

    async def prev_page(_):
        global current_page
        if current_page > 1:
            current_page -= 1
            await patient_table.load_page(current_page)
            await update_pagination_display(current_page)

    prev_button = ft.ElevatedButton(
        "← Previous",
        on_click=prev_page,
        height=50,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )
    next_button = ft.ElevatedButton(
        "Next →",
        on_click=next_page,
        height=50,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

    pagination_controls = ft.Row(
        [prev_button, total_page_input, total_pages, next_button],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    # Search button
    async def search_handler(e):
        global current_page
        current_page = 1

        await on_search_click(
            patient_table,
            patient_id_field,
            patient_name_field,
            start_date_field,
            end_date_field,
            result_state_variable,
        )

        await update_pagination_display(current_page)  # Ensure the UI shows Page 1

    search_button = ft.ElevatedButton(
        text="Search",
        on_click=search_handler,
        height=50,
        expand=True,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

    # Patient table with pagination
    patient_table = PaginatedDataTable(page, RESULTS_PER_PAGE)

    # Full page layout
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        patient_id_field,
                        patient_name_field,
                        start_date_picker_button,
                        start_date_field,
                        end_date_picker_button,
                        end_date_field,
                        result_state_variable,
                        search_button,
                    ],
                    spacing=5,
                ),
                ft.Divider(),
                ft.Column([patient_table], expand=True, scroll=ft.ScrollMode.AUTO),
                ft.Divider(),
                pagination_controls,
            ],
            expand=True,
        ),
        expand=True,
    )
