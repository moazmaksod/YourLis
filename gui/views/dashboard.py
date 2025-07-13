import flet as ft
import datetime
from gui.views.patient import fetch_patient_data, gui_time_format, sql_time_format
from log.logger import log_error
import asyncio
# No need to import select_patient_ids_from_cbc anymore

# Card color mapping by result state (will use theme at runtime)
CARD_COLOR_KEYS = {
    "Requested Only": ("error", "on_error"),      # Red
    "Pending": ("secondary", "on_secondary"),     # Yellow/Accent
    "Completed": ("primary", "on_primary"),       # Green/Primary
}

# Group mapping
GROUP_LABELS = [
    ("Requested Only", "Requested Only (No CBC Record)"),
    ("Pending", "Pending (CBC Received)"),
    ("Completed", "Completed"),
]

# SQL to get all CBC patient IDs for a date
CBC_IDS_SQL = "SELECT DISTINCT [Patient ID] FROM cbc WHERE [Requested Date]=?"


def dashboard_view(page: ft.Page):
    today = datetime.date.today()
    today_str = today.strftime(gui_time_format)

    # Date picker
    date_field = ft.TextField(value=today_str, width=120, disabled=True)

    def on_date_change(e):
        if e.control.value:
            date_field.value = e.control.value.strftime(gui_time_format)
            date_field.update()
            page.run_task(load_cards)

    date_picker = ft.DatePicker(
        first_date=datetime.date(2000, 1, 1),
        last_date=datetime.date(2060, 12, 31),
        current_date=today,
        on_change=on_date_change,
    )
    date_picker_btn = ft.ElevatedButton(
        text="Select Date",
        on_click=lambda _: page.open(date_picker),
        height=40,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

    # Container for cards
    card_groups = {k: [] for k, _ in GROUP_LABELS}
    cards_column = ft.Column([])

    async def load_cards():
        page.splash = ft.ProgressBar(visible=True)
        page.update()
        try:
            # Convert date to SQL format
            date_val = date_field.value
            date_sql = datetime.datetime.strptime(date_val, gui_time_format).strftime(
                sql_time_format
            )
            # Fetch all patients for the selected date
            patients = await fetch_patient_data(start_date=date_sql, end_date=date_sql)
            if hasattr(patients, "__await__") or hasattr(
                patients, "send"
            ):  # is coroutine
                patients = await patients
            if patients is None:
                patients = []
            # Group patients by result state and CBC existence
            for k, _ in GROUP_LABELS:
                card_groups[k] = []
            for patient in patients:
                result_state = patient.get("Result State", 0)  # 'Pending' or 'Completed'
                cbc_exists = patient.get("CBC_Exists", 0)  # 1 or 0
                # Normalize values
                is_pending = str(result_state).lower() == "pending" or result_state == 0
                is_completed = str(result_state).lower() == "completed" or result_state == 1
                cbc_exists = int(cbc_exists) == 1
                # Group logic
                if is_pending and not cbc_exists:
                    group = "Requested Only"
                elif is_pending and cbc_exists:
                    group = "Pending"
                elif is_completed and cbc_exists:
                    group = "Completed"
                else:
                    group = "Requested Only"  # fallback
                # Get theme colors robustly
                theme = page.theme if page.theme_mode == ft.ThemeMode.LIGHT else page.dark_theme
                color_key, text_key = CARD_COLOR_KEYS[group]
                color_scheme = getattr(theme, "color_scheme", None)
                if color_scheme:
                    card_bg = getattr(color_scheme, color_key)
                    card_fg = getattr(color_scheme, text_key)
                else:
                    fallback_colors = {
                        "error": ft.Colors.RED_200,
                        "on_error": ft.Colors.BLACK,
                        "secondary": ft.Colors.YELLOW_200,
                        "on_secondary": ft.Colors.BLACK,
                        "primary": ft.Colors.GREEN_200,
                        "on_primary": ft.Colors.BLACK,
                    }
                    card_bg = fallback_colors.get(color_key, ft.Colors.GREY_200)
                    card_fg = fallback_colors.get(text_key, ft.Colors.BLACK)
                card = ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                f"Name: {patient.get('Name', '')}",
                                weight=ft.FontWeight.BOLD,
                                color=card_fg,
                            ),
                            ft.Text(f"ID: {patient.get('Patient ID', '')}", color=card_fg),
                            ft.Text(
                                f"Requested Test: {patient.get('Requested Test', '')}", color=card_fg
                            ),
                            ft.Text(f"Result State: {group}", color=card_fg),
                        ],
                        spacing=2,
                    ),
                    bgcolor=card_bg,
                    border_radius=10,
                    padding=15,
                    margin=5,
                    width=300,
                )
                card_groups[group].append(card)
            # Build the grouped cards
            cards_column.controls = []
            for k, label in GROUP_LABELS:
                group_cards = card_groups[k]
                if group_cards:
                    cards_column.controls.append(
                        ft.Text(label, size=18, weight=ft.FontWeight.BOLD)
                    )
                    cards_column.controls.append(ft.Row(group_cards, wrap=True))
            page.update()
        except Exception as e:
            log_error(f"Dashboard load_cards error: {e}")
            page.snack_bar = ft.SnackBar(
                ft.Text("Error loading dashboard: " + str(e)), open=True
            )
            page.update()
        finally:
            page.splash = None
            page.update()

    # Initial load
    page.run_task(load_cards)

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Dashboard", size=24, weight=ft.FontWeight.BOLD),
                        ft.Container(width=20),
                        date_picker_btn,
                        date_field,
                    ],
                    spacing=10,
                ),
                ft.Divider(),
                cards_column,
            ],
            expand=True,
        ),
        expand=True,
    )
