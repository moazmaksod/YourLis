import flet as ft
import datetime
import math
import asyncio
from log.logger import log_info, log_error
from database.sqlqueries import exec_procedure_for, exec_procedure_no_return
from database.sqldbdictionary import (
    SEND_OUT_SEARCH_SQL,
    INSERT_SEND_OUT_LOG_SQL,
    GET_DESTINATION_LABS_SQL,
    UPDATE_SEND_OUT_FINANCIALS_SQL,
)

# Date format settings from patient view
gui_time_format = "%d-%m-%Y"
sql_time_format = "%Y-%m-%d"

RESULTS_PER_PAGE = 20

async def fetch_send_out_data(
    patient_id=None, patient_name=None, destination_lab=None, start_date=None, end_date=None, status=None
):
    """
    Placeholder function to fetch send-out sample data.
    Replace this with your actual database query.
    """
    try:
        params = {
            "PatientID": patient_id or None,
            "PatientName": patient_name or None,
            "DestinationLab": destination_lab or None,
            "StartDate": start_date or None,
            "EndDate": end_date or None,
            "Status": status or None,
        }
        # Run blocking DB call in thread
        return await exec_procedure_for(SEND_OUT_SEARCH_SQL, params) or []
    except Exception as e:
        log_error(f"Error fetching send-out data: {e}")
        return []


async def fetch_destination_labs():
    """
    Fetches the list of destination labs.
    """
    try:
        result = await exec_procedure_for(GET_DESTINATION_LABS_SQL, {})
        log_info(f"Fetched {len(result) if result else 0} destination labs.")
        return result or []
    except Exception as e:
        log_error(f"Error fetching destination labs: {e}")
        return []

class PaginatedSendOutTable(ft.DataTable):
    """
    A DataTable for send-out samples that supports pagination.
    """

    def __init__(self, page: ft.Page, results_per_page):
        super().__init__(
            columns=[
                ft.DataColumn(ft.Text("Patient ID")),
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Test Name")),
                ft.DataColumn(ft.Text("Destination Lab")),
                ft.DataColumn(ft.Text("Price")),
                ft.DataColumn(ft.Text("Amount Paid")),
                ft.DataColumn(ft.Text("Sent Date")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Actions")),
            ],
            rows=[],
            expand=True,
            width=2000,
            divider_thickness=0.5,
        )
        self.page = page
        self.results_per_page = results_per_page
        self.total_pages = 1
        self.all_data = []

    async def load_page(self, page_number):
        """Loads the relevant rows for the given page number."""
        if not self.all_data:
            log_info("No send-out data to display in the table.")
            self.rows.clear()
            self.update()
            return

        start = (page_number - 1) * self.results_per_page
        end = start + self.results_per_page

        log_info(
            f"Loading send-out page {page_number}: Displaying records {start} to {end}"
        )

        self.rows.clear()
        self.rows.extend(
            create_send_out_row(self.page, sample)
            for sample in self.all_data[start:end]
        )
        self.update()


def create_send_out_row(page, sample):
    """
    Creates a DataRow for the send-out table.
    """
    sent_date_obj = sample.get("Sent Date")
    sent_date = "N/A"
    if sent_date_obj:
        try:
            # First, try to format it as if it's a datetime or date object
            sent_date = sent_date_obj.strftime(gui_time_format)
        except AttributeError:
            # If that fails, it might be a string
            if isinstance(sent_date_obj, str):
                try:
                    # Try to parse a known string format
                    dt = datetime.datetime.strptime(
                        sent_date_obj.strip(), "%Y-%m-%d %H:%M:%S"
                    )
                    sent_date = dt.strftime(gui_time_format)
                except (ValueError, TypeError):
                    # If parsing fails, just use the string as is
                    sent_date = sent_date_obj
            else:
                # For any other type, convert to string
                sent_date = str(sent_date_obj)

    # Controls for Price and Amount Paid to allow UI updates
    price_text_control = ft.Text(str(sample.get("Price", "")), expand=True)
    paid_text_control = ft.Text(str(sample.get("Amount Paid", "0")), expand=True)

    # Controls for Sent Date and Status to allow UI updates
    sent_date_text_control = ft.Text(sent_date, expand=True)
    status_text_control = ft.Text(str(sample.get("Status", "")), expand=True)

    async def edit_financials_click(e):
        """Handles the 'Edit' button click event."""
        price_field = ft.TextField(label="Price", value=price_text_control.value)
        paid_field = ft.TextField(label="Amount Paid", value=paid_text_control.value)
        
        # Fetch labs for dropdown
        labs = await fetch_destination_labs()
        lab_options = [ft.dropdown.Option(text=lab.get("gehahname", ""), key=lab.get("gehahname", "")) for lab in labs]
        
        dest_lab_field = ft.Dropdown(
            label="Destination Lab",
            options=lab_options,
            value=sample.get("Destination Lab", "")
        )

        status_field = ft.Dropdown(
            label="Status",
            options=[ft.dropdown.Option("Pending"), ft.dropdown.Option("Sent")],
            value=sample.get("Status", "Pending")
        )

        async def save_financials(e):
            try:
                new_price = float(price_field.value)
                new_paid = float(paid_field.value)
            except ValueError:
                page.snack_bar = ft.SnackBar(ft.Text("Invalid number format"), open=True)
                page.update()
                return

            params = {
                "PatientID": sample["Patient ID"],
                "TestName": sample["Test Name"],
                "Price": new_price,
                "AmountPaid": new_paid,
                "DestinationLab": dest_lab_field.value,
                "EditDate": datetime.datetime.now().strftime("%d-%b-%Y %I:%M %p"),
                "Status": status_field.value,
            }

            try:
                # Execute update procedure
                await exec_procedure_no_return(UPDATE_SEND_OUT_FINANCIALS_SQL, params)

                # Update UI and local data
                sample["Price"] = new_price
                sample["Amount Paid"] = new_paid
                sample["Destination Lab"] = dest_lab_field.value
                sample["Status"] = status_field.value
                
                price_text_control.value = str(new_price)
                paid_text_control.value = str(new_paid)
                status_text_control.value = status_field.value
                
                # Update the row cells to reflect changes immediately
                e.control.page.update()
                
                page.update()
                page.close(dlg)
            except Exception as ex:
                log_error(f"Error updating financials: {ex}")
                page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), open=True)
                page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Edit Financials"),
            content=ft.Column([price_field, paid_field, dest_lab_field, status_field], tight=True, width=300),
            actions=[ft.TextButton("Cancel", on_click=lambda e: page.close(dlg)), ft.TextButton("Save", on_click=save_financials)],
        )
        page.open(dlg)

    # Define send_button variable for closure access
    send_button = None
    pay_button = None

    async def pay_and_send_click(e):
        """Handles the 'Pay' button click event."""
        try:
            price = float(sample.get("Price") or 0)
            new_paid = price
            
            params = {
                "PatientID": sample["Patient ID"],
                "TestName": sample["Test Name"],
                "Price": price,
                "AmountPaid": new_paid,
                "DestinationLab": sample.get("Destination Lab", ""),
                "EditDate": datetime.datetime.now().strftime("%d-%b-%Y %I:%M %p"),
                "Status": "Sent",
            }

            await exec_procedure_no_return(UPDATE_SEND_OUT_FINANCIALS_SQL, params)

            # Update local data
            sample["Amount Paid"] = new_paid
            sample["Status"] = "Sent"
            sample["Sent Date"] = datetime.datetime.now()

            # Update UI controls
            paid_text_control.value = str(new_paid)
            status_text_control.value = "Sent"
            sent_date_text_control.value = datetime.date.today().strftime(gui_time_format)

            # Update Send button style
            if send_button:
                send_button.text = "Sent"
                send_button.icon = ft.Icons.CHECK
                send_button.bgcolor = ft.Colors.GREEN
                send_button.color = ft.Colors.WHITE
                send_button.disabled = True

            # Update Pay button style
            if pay_button:
                pay_button.text = "Paid"
                pay_button.icon = ft.Icons.CHECK
                pay_button.bgcolor = ft.Colors.GREEN
                pay_button.color = ft.Colors.WHITE
                pay_button.disabled = True
            
            page.update()
        except Exception as ex:
            log_error(f"Error paying and sending: {ex}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), open=True)
            page.update()

    async def mark_as_sent_click(e):
        """Handles the 'Mark as Sent' button click event."""
        try:
            patient_id = sample["Patient ID"]
            test_name = sample["Test Name"]
            log_info(
                f"Marking sample as sent for Patient ID: {patient_id}, Test: {test_name}"
            )

            # Disable button immediately for responsiveness
            e.control.disabled = True
            page.update()

            params = {
                "PatientID": patient_id,
                "TestName": test_name,
                "SentDate": datetime.datetime.now(),
            }

            # Run blocking DB call in thread
            await exec_procedure_no_return(INSERT_SEND_OUT_LOG_SQL, params)

            # Update the UI to reflect the change
            e.control.text = "Sent"
            e.control.icon = ft.Icons.CHECK
            e.control.bgcolor = ft.Colors.GREEN
            e.control.color = ft.Colors.WHITE
            
            # Update controls directly and local data
            sent_date_text_control.value = datetime.date.today().strftime(gui_time_format)
            status_text_control.value = "Sent"
            sample["Status"] = "Sent"
            sample["Sent Date"] = datetime.datetime.now()
            page.update()
        except Exception as ex:
            log_error(f"Error marking sample as sent: {ex}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), open=True)

    is_sent = sample.get("Status") == "Sent"
    send_button = ft.ElevatedButton(
        text="Sent" if is_sent else "Send",
        icon=ft.Icons.CHECK if is_sent else None,
        bgcolor=ft.Colors.GREEN if is_sent else None,
        color=ft.Colors.WHITE if is_sent else None,
        on_click=mark_as_sent_click,
        disabled=is_sent,
    )

    price = float(sample.get("Price") or 0)
    paid = float(sample.get("Amount Paid") or 0)
    is_paid = paid >= price and price > 0

    pay_button = ft.ElevatedButton(
        text="Paid" if is_paid else "Pay",
        icon=ft.Icons.CHECK if is_paid else None,
        bgcolor=ft.Colors.GREEN if is_paid else None,
        color=ft.Colors.WHITE if is_paid else None,
        on_click=pay_and_send_click,
        disabled=is_paid,
    )

    return ft.DataRow(
        cells=[
            ft.DataCell(ft.Text(str(sample.get("Patient ID", "")), expand=True)),
            ft.DataCell(ft.Text(str(sample.get("Name", "")), expand=True)),
            ft.DataCell(ft.Text(str(sample.get("Test Name", "")), expand=True)),
            ft.DataCell(ft.Text(str(sample.get("Destination Lab", "")), expand=True)),
            ft.DataCell(price_text_control),
            ft.DataCell(paid_text_control),
            ft.DataCell(sent_date_text_control),
            ft.DataCell(status_text_control),
            ft.DataCell(
                ft.Row(
                    [
                        send_button,
                        pay_button,
                        ft.IconButton(icon=ft.Icons.EDIT, tooltip="Edit Price/Paid", on_click=edit_financials_click),
                    ],
                    spacing=5,
                ),
            ),
        ]
    )


def send_out_view(page: ft.Page):
    """
    Main view for managing samples sent to other labs.
    """
    today_date_str = datetime.date.today().strftime(gui_time_format)

    # --- Search Filters ---
    patient_id_field = ft.TextField(label="Patient ID", width=150)
    patient_name_field = ft.TextField(label="Patient Name", width=200)
    destination_lab_dropdown = ft.Dropdown(
        label="Destination Lab",
        width=200,
        options=[ft.dropdown.Option(text="All", key="")],
        on_change=lambda e: page.run_task(search_handler, e),
    )

    # Date pickers setup, similar to patient_view
    def on_date_change(e, date_field):
        """Updates the date field with the selected date in DD-MM-YYYY format."""
        if e.control.value:
            date_field.value = e.control.value.strftime(gui_time_format)
            date_field.update()

    def create_date_picker(label, date_field):
        def open_date_picker(e, picker):
            picker.open = True
            page.update()

        date_picker = ft.DatePicker(
            first_date=datetime.date(2000, 1, 1),
            last_date=datetime.date(2060, 12, 31),
            current_date=datetime.date.today(),
            on_change=lambda e: on_date_change(e, date_field),
        )
        page.overlay.append(date_picker)  # Add date picker to the page overlay

        return ft.ElevatedButton(
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            height=50,
            text=label,
            on_click=lambda e: open_date_picker(e, date_picker),
        )

    start_date_field = ft.TextField(value=today_date_str, width=120, disabled=True)
    start_date_picker_button = create_date_picker("From", start_date_field)

    end_date_field = ft.TextField(value=today_date_str, width=120, disabled=True)
    end_date_picker_button = create_date_picker("To", end_date_field)

    status_dropdown = ft.Dropdown(
        options=[
            ft.dropdown.Option("All"),
            ft.dropdown.Option("Pending"),
            ft.dropdown.Option("Sent"),
        ],
        value="Pending",
        width=180,
        on_change=lambda e: page.run_task(search_handler, e),
    )

    send_out_table = PaginatedSendOutTable(page, RESULTS_PER_PAGE)

    # --- Search Logic ---
    async def search_handler(e):
        page.splash = ft.ProgressBar(visible=True)
        page.update()

        try:
            status_val = (
                status_dropdown.value if status_dropdown.value != "All" else None
            )
            destination_lab_val = (
                destination_lab_dropdown.value if destination_lab_dropdown.value and destination_lab_dropdown.value != "All" else None
            )
            start_date = (
                datetime.datetime.strptime(
                    start_date_field.value, gui_time_format
                ).strftime(sql_time_format)
                if start_date_field.value
                else None
            )
            end_date = (
                datetime.datetime.strptime(
                    end_date_field.value, gui_time_format
                ).strftime(sql_time_format)
                if end_date_field.value
                else None
            )
            data = await fetch_send_out_data(
                patient_id=patient_id_field.value,
                patient_name=patient_name_field.value,
                destination_lab=destination_lab_val,
                start_date=start_date,
                end_date=end_date,
                status=status_val,
            )

            if not data:
                log_info("No send-out samples found, clearing table.")
                send_out_table.all_data = []
                send_out_table.rows.clear()
            else:
                log_info(f"Search completed. Found {len(data)} send-out records.")
                # Convert rows to dicts to ensure mutability and avoid pyodbc.Row issues
                send_out_table.all_data = [dict(row) for row in data]

            send_out_table.total_pages = max(
                1, math.ceil(len(send_out_table.all_data) / RESULTS_PER_PAGE)
            )

            await send_out_table.load_page(1)
            await update_pagination_display(1)

        except Exception as ex:
            log_error(f"Error in send_out search_handler: {ex}")
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {ex}"), open=True)

        finally:
            page.splash = None
            page.update()

    # --- Pagination ---
    current_page = 1
    total_pages_text = ft.Text(f" / {send_out_table.total_pages}")
    page_input = ft.TextField(value="1", width=50, text_align=ft.TextAlign.CENTER)

    async def update_pagination_display(page_num):
        nonlocal current_page
        current_page = page_num
        page_input.value = str(current_page)
        total_pages_text.value = f" / {send_out_table.total_pages}"
        page.update()

    async def go_to_page(e):
        try:
            page_num = int(page_input.value)
            if 1 <= page_num <= send_out_table.total_pages:
                await send_out_table.load_page(page_num)
                await update_pagination_display(page_num)
            else:
                page_input.value = str(current_page)  # Revert to current page
                page.update()
        except (ValueError, TypeError):
            page_input.value = str(current_page)  # Revert on invalid input
            page.update()

    page_input.on_blur = go_to_page

    async def prev_page_click(e):
        if current_page > 1:
            await send_out_table.load_page(current_page - 1)
            await update_pagination_display(current_page - 1)

    async def next_page_click(e):
        if current_page < send_out_table.total_pages:
            await send_out_table.load_page(current_page + 1)
            await update_pagination_display(current_page + 1)

    pagination_controls = ft.Row(
        [
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=prev_page_click),
            page_input,
            total_pages_text,
            ft.IconButton(ft.Icons.ARROW_FORWARD, on_click=next_page_click),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    search_button = ft.ElevatedButton(
        text="Search",
        on_click=search_handler,
        height=50,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

    # Initial data load
    page.run_task(search_handler, None)

    # --- Load Destination Labs ---
    async def load_labs_task():
        # Give the UI a moment to mount
        await asyncio.sleep(0.5)
        labs = await fetch_destination_labs()
        options = [ft.dropdown.Option(text="All", key="")]
        if labs:
            options.extend(
                ft.dropdown.Option(text=lab.get("gehahname", "Unknown"), key=lab.get("gehahname", ""))
                for lab in labs
            )
        destination_lab_dropdown.options = options
        if destination_lab_dropdown.page:
            try:
                destination_lab_dropdown.update()
            except Exception as e:
                log_error(f"Error updating destination lab dropdown: {e}")

    page.run_task(load_labs_task)

    # --- Layout ---
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        patient_id_field,
                        patient_name_field,
                        destination_lab_dropdown,
                        start_date_picker_button,
                        start_date_field,
                        end_date_picker_button,
                        end_date_field,
                        status_dropdown,
                        search_button,
                    ],
                    spacing=5,
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Divider(),
                ft.Column([send_out_table], expand=True, scroll=ft.ScrollMode.AUTO),
                ft.Divider(),
                pagination_controls,
            ],
            expand=True,
        ),
        expand=True,
        padding=10,
    )
