import flet as ft
from gui.gui_methods import ServerStatusUpdater, close_app
from gui.api_methods import toggle_server_state
from setting.config import get_config, save_config


cfg = get_config()  # Load configuration from file
app_name = cfg["APPLICATION_NAME"]
app_ver = cfg["VERSION"]

# Server status tracker
server_status = {
    "state": "Offline",
    "text": "Server is offline",
    "color": "red",
    "clients": {},
}


def title_bar(app_name: str, app_slogan: str, close_method, page: ft.Page):

    close_button = ft.IconButton(
        icon=ft.Icons.CLOSE, tooltip="Close", on_click=lambda _: page.window.close()
    )

    app_name_text = ft.Text(app_name)
    app_name_slogan = ft.Text(app_slogan)
    app_name_icon = ft.Icon(name=ft.Icons.HEALTH_AND_SAFETY)

    return ft.ResponsiveRow(
        [
            ft.WindowDragArea(
                ft.Row(
                    [
                        ft.Container(
                            ft.Row([app_name_icon, app_name_text, app_name_slogan])
                        ),
                        ft.Container(ft.Row([close_button])),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                )
            )
        ]
    )


def server_control(page: ft.Page):
    """
    Create a header with the app name, server status, and a button to control the server state.
    """

    async def on_server_button_click(e):
        """
        Toggle server state on button click.
        """
        result = await toggle_server_state(
            server_status["state"]
        )  # Toggle server state using the API
        
        message = result.get("message", "")
        if "Failed" in message or "Exception" in message:
             page.snack_bar = ft.SnackBar(ft.Text(message), bgcolor="red")
             page.snack_bar.open = True
             page.update()

        await status_updater.manual_status_refresh()  # Refresh status immediately after toggle

    # Server status indicator
    status_indicator = ft.Container(
        width=32,
        height=32,
        bgcolor=server_status["color"],
        border_radius=16,
        tooltip=f"State: {server_status['state']}\nDetails: {server_status['text']}",
    )

    clients_avatars = ft.Container()  # Initialize as a container

    # Server control button
    server_button = ft.OutlinedButton(
        text="Start Server", on_click=on_server_button_click
    )

    # Server status updater
    status_updater = ServerStatusUpdater(
        status_indicator, server_button, server_status, clients_avatars
    )

    divider = ft.Text("     ")

    # App header layout
    header_row = ft.Row(
        controls=[
            status_updater,
            ft.Row(
                controls=[
                    status_indicator,
                    divider,
                    clients_avatars,
                    divider,
                    server_button,
                    divider,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                spacing=30,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )
    
    # Return both the UI and the status_updater instance for manual subscription setup
    return header_row, status_updater


def side_menu(on_item_click):
    """
    Create a side menu for navigation with an app logo.
    """
    return ft.Container(
        content=ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.SELECTED,
            on_change=on_item_click,
            destinations=[
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.SPACE_DASHBOARD), label="Dashboard"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.INSERT_COMMENT_ROUNDED), label="Stream"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.SEND_AND_ARCHIVE_OUTLINED), label="Send Out"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.GROUPS_SHARP), label="patient"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.SETTINGS), label="Settings"
                ),
                ft.NavigationRailDestination(
                    icon=ft.Icon(ft.Icons.INFO), label="About"
                ),
            ],
        ),
        height=600,
    )


def footer():
    """
    Create a footer with copyright information.
    """

    return ft.Container(
        content=ft.Row(
            [
                ft.Text(f"{app_name} © 2025"),
                ft.Text(" | "),
                ft.Text("All rights reserved"),
                ft.Text(" | "),
                ft.Text(f"Version {app_ver}"),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
    )


def close_confirm_dialog(page: ft.Page):
    """
    Return a confirmation dialog for closing the app.
    """

    # Close confirmation dialog handlers
    async def yes_click(e):
        # Perform cleanup or saving logic here if needed
        await close_app(page)

    def no_click(e):
        dismiss_dialog(page, confirm_dialog)

    # Confirmation dialog
    primary_btn_cls = getattr(ft, "FilledButton", getattr(ft, "ElevatedButton", ft.Button))
    outlined_btn_cls = getattr(ft, "OutlinedButton", ft.Button)

    confirm_dialog = ft.AlertDialog(
        title=ft.Text("Please confirm"),
        content=ft.Text("Do you really want to exit this app?"),
        actions=[
            primary_btn_cls("Yes", on_click=yes_click),
            outlined_btn_cls("No", on_click=no_click),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    return confirm_dialog


def db_conn_fail_dialog(page: ft.Page, on_settings=None):
    """
    Return an alert dialog for database connection failure with options to configure settings or exit.
    """
    async def exit_click(e):
        await close_app(page)

    def settings_click(e):
        dismiss_dialog(page, conn_dialog)
        if on_settings:
            on_settings()

    primary_btn_cls = getattr(ft, "FilledButton", getattr(ft, "ElevatedButton", ft.Button))
    outlined_btn_cls = getattr(ft, "OutlinedButton", ft.Button)

    conn_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Database Connection Failed"),
        content=ft.Text(
            "Could not connect to the database. Please check your database credentials or server configuration."
        ),
        actions=[
            primary_btn_cls("Open Settings", on_click=settings_click),
            outlined_btn_cls("Exit", on_click=exit_click),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    return conn_dialog


def show_dialog(page: ft.Page, dialog: ft.AlertDialog):
    """Safely opens a modal or alert dialog across all Flet versions without leaving orphaned modal barriers."""
    if hasattr(page, "open"):
        page.open(dialog)
    else:
        if dialog not in page.overlay:
            page.overlay.append(dialog)
        dialog.open = True
        page.update()


def dismiss_dialog(page: ft.Page, dialog: ft.AlertDialog):
    """Safely closes an alert dialog across all Flet versions without tearing down the widget tree during transition."""
    dialog.open = False
    if hasattr(page, "close") and callable(getattr(page, "close")):
        try:
            page.close(dialog)
        except Exception:
            pass
    if hasattr(page, "update") and callable(getattr(page, "update")):
        try:
            page.update()
        except Exception:
            pass




