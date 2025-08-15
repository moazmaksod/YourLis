import flet as ft
import datetime
from gui.views.patient import fetch_patient_data, gui_time_format, sql_time_format
from log.logger import log_error

# Internal group keys
GROUP_AWAITING_ANALYSIS = "awaiting_analysis"
GROUP_UNDER_REVIEW = "under_review"
GROUP_FINALIZED = "finalized"

# Mapping internal keys to user-friendly display labels
GROUP_LABELS = {
    GROUP_AWAITING_ANALYSIS: "Waiting for Analysis",
    GROUP_UNDER_REVIEW: "Under Review",
    GROUP_FINALIZED: "Report Finalized",
}

# Explicit card color mapping for both light and dark mode
CARD_COLORS = {
    GROUP_AWAITING_ANALYSIS: {
        "light": {"bg": ft.Colors.BLACK38, "fg": ft.Colors.WHITE},
        "dark": {"bg": ft.Colors.BLACK38, "fg": ft.Colors.WHITE},
    },
    GROUP_UNDER_REVIEW: {
        "light": {"bg": ft.Colors.YELLOW_400, "fg": ft.Colors.BLACK},
        "dark": {"bg": ft.Colors.YELLOW_700, "fg": ft.Colors.BLACK},
    },
    GROUP_FINALIZED: {
        "light": {"bg": ft.Colors.GREEN_400, "fg": ft.Colors.WHITE},
        "dark": {"bg": ft.Colors.GREEN_700, "fg": ft.Colors.WHITE},
    },
}

# Card hover color mapping for both light and dark mode
CARD_HOVER_COLORS = {
    GROUP_AWAITING_ANALYSIS: {
        "light": ft.Colors.GREY_700,
        "dark": ft.Colors.GREY_900,
    },
    GROUP_UNDER_REVIEW: {
        "light": ft.Colors.YELLOW_200,
        "dark": ft.Colors.YELLOW_800,
    },
    GROUP_FINALIZED: {
        "light": ft.Colors.GREEN_200,
        "dark": ft.Colors.GREEN_900,
    },
}


def dashboard_view(page: ft.Page):
    # Use a local state dictionary instead of custom page attributes
    state = {}
    selected_date = datetime.date.today()
    state["dashboard_date"] = selected_date
    selected_date_str = selected_date.strftime(gui_time_format)

    # Date picker
    date_field = ft.TextField(value=selected_date_str, width=120, disabled=True)

    def update_date_field(new_date):
        state["dashboard_date"] = new_date
        date_field.value = new_date.strftime(gui_time_format)
        date_field.update()
        page.run_task(load_cards)

    def on_prev_day(e):
        if not date_field.value:
            return
        current_date = datetime.datetime.strptime(
            date_field.value, gui_time_format
        ).date()
        prev_date = current_date - datetime.timedelta(days=1)
        update_date_field(prev_date)

    def on_next_day(e):
        if not date_field.value:
            return
        current_date = datetime.datetime.strptime(
            date_field.value, gui_time_format
        ).date()
        next_date = current_date + datetime.timedelta(days=1)
        update_date_field(next_date)

    def on_date_change(e):
        if e.control.value:
            update_date_field(e.control.value)

    date_picker = ft.DatePicker(
        first_date=datetime.date(2000, 1, 1),
        last_date=datetime.date(2060, 12, 31),
        current_date=selected_date,
        on_change=on_date_change,
    )
    prev_day_btn = ft.ElevatedButton(
        text="<<",
        on_click=on_prev_day,
        height=40,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )
    next_day_btn = ft.ElevatedButton(
        text=">>",
        on_click=on_next_day,
        height=40,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )
    date_picker_btn = ft.ElevatedButton(
        text="Select Date",
        on_click=lambda _: page.open(date_picker),
        height=40,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

    # Container for cards
    card_groups = {k: [] for k in GROUP_LABELS.keys()}
    cards_column = ft.Column(
        [],
        expand=True,
    )

    async def load_cards():
        # Helper to resolve coroutine to final result
        async def resolve_patients(result):
            while hasattr(result, "__await__"):
                result = await result
            return result

        page.update()
        try:
            # Convert date to SQL format
            date_val = date_field.value or ""
            date_sql = datetime.datetime.strptime(date_val, gui_time_format).strftime(
                sql_time_format
            )
            # Use local state for caching
            if "dashboard_patients" in state and "dashboard_patients_date" in state:
                if state["dashboard_patients_date"] == date_val:
                    patients = state["dashboard_patients"]
                else:
                    result = fetch_patient_data(start_date=date_sql, end_date=date_sql)
                    patients = await resolve_patients(result)
                    if patients is None:
                        patients = []
                    state["dashboard_patients"] = patients
                    state["dashboard_patients_date"] = date_val
            else:
                result = fetch_patient_data(start_date=date_sql, end_date=date_sql)
                patients = await resolve_patients(result)
                if patients is None:
                    patients = []
                state["dashboard_patients"] = patients
                state["dashboard_patients_date"] = date_val
            # Group patients by result state and CBC existence
            for k in GROUP_LABELS.keys():
                card_groups[k] = []

            for patient in patients:
                result_state = patient.get(
                    "Result State", 0
                )  # 'Pending' or 'Completed'
                cbc_exists = patient.get("CBC_Exists", 0)  # 1 or 0
                # Normalize values
                is_pending = str(result_state).lower() == "pending" or result_state == 0
                is_completed = (
                    str(result_state).lower() == "completed" or result_state == 1
                )
                cbc_exists = int(cbc_exists) == 1
                # Group logic
                if is_pending and not cbc_exists:
                    group = GROUP_AWAITING_ANALYSIS
                elif is_pending and cbc_exists:
                    group = GROUP_UNDER_REVIEW
                elif is_completed and cbc_exists:
                    group = GROUP_FINALIZED
                else:
                    group = GROUP_AWAITING_ANALYSIS  # fallback

                # Get theme colors robustly
                mode = "dark" if page.theme_mode == ft.ThemeMode.DARK else "light"
                card_bg = CARD_COLORS[group][mode]["bg"]
                card_fg = CARD_COLORS[group][mode]["fg"]
                card_info = (
                    f"Name: {patient.get('Name', '')}\n"
                    f"ID: {patient.get('Patient ID', '')}\n"
                    f"Requested Test: {patient.get('Requested Test', '')}\n"
                    f"Sample State: {GROUP_LABELS[group]}"
                )
                card_hover = CARD_HOVER_COLORS[group][mode]

                # Use a mutable container to allow dynamic bgcolor change
                def on_card_hover(e):
                    e.control.bgcolor = card_hover if e.data == "true" else card_bg
                    e.control.update()

                # Add View Result button if CBC exists
                async def view_results_click(e, patient_id=patient.get("Patient ID")):
                    from gui.views.cbc_report import cbc_report_view

                    await cbc_report_view(page, patient_id)

                card_content: list = [
                    ft.TextField(
                        value=card_info,
                        read_only=True,
                        multiline=True,
                        border_radius=10,
                        bgcolor=card_bg,
                        color=card_fg,
                        border_color=card_bg,
                        cursor_color=card_fg,
                        text_size=14,
                        min_lines=4,
                        max_lines=8,
                        expand=False,
                    )
                ]
                if cbc_exists:
                    # Add View Result button only if CBC exists
                    view_result_btn = ft.ElevatedButton(
                        text="View Result",
                        on_click=view_results_click,
                        height=40,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10)
                        ),
                    )
                    card_content.append(view_result_btn)

                card = ft.Container(
                    content=ft.Column(card_content, expand=True),
                    bgcolor=card_bg,
                    border_radius=10,
                    padding=15,
                    margin=5,
                    width=300,
                    ink=True,
                    on_hover=on_card_hover,
                )
                card_groups[group].append(card)

            # Build the grouped cards
            cards_column.controls = []
            for group_key, group_label in GROUP_LABELS.items():
                group_cards = card_groups[group_key]
                if group_cards:
                    cards_column.controls.append(
                        ft.Text(group_label, size=18, weight=ft.FontWeight.BOLD)
                    )
                    cards_column.controls.append(ft.Row(group_cards, wrap=True))

            page.update()
        except Exception as e:
            log_error(f"Dashboard load_cards error: {e}")
            # page.snack_bar = ft.SnackBar(
            #     ft.Text("Error loading dashboard: " + str(e)), open=True
            # )  # Commented: not a valid Page attribute
            page.update()
        finally:
            # page.splash = None  # Commented: not a valid Page attribute
            page.update()

    # Initial load
    page.run_task(load_cards)

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(width=20),
                        date_picker_btn,
                        prev_day_btn,
                        date_field,
                        next_day_btn,
                    ],
                    spacing=10,
                ),
                ft.Column(
                    [
                        ft.Divider(),
                        cards_column,
                    ],
                    expand=True,
                    # scroll="auto",  # Removed: not a valid argument
                ),
            ],
            expand=True,
        ),
        expand=True,
    )
