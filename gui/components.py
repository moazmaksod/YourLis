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
        await status_updater.periodic_status_check()  # Refresh status immediately after toggle

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
        status_indicator, server_button, server_status, clients_avatars, page
    )

    divider = ft.Text("     ")

    # App header layout
    return ft.Row(
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


def login_dialog(page: ft.Page):
    """
    Show a login dialog for the app.
    """

    cfg = get_config()  # Load configuration from file
    try:
        app_user = cfg["APP_USER"]
        app_password = cfg["APP_PASSWORD"]
    except KeyError:
        app_user = "admin"
        app_password = "admin"

    # Input fields for username and password
    username_field = ft.TextField(label="Username", value=app_user)
    password_field = ft.TextField(
        label="Password",
        value=app_password,
        password=True,
        can_reveal_password=True,
    )
    remember_me = ft.Checkbox(label="Remember me", value=False)
    login_message = ft.Text("")

    # Handlers for login and close actions
    def login_click(e):
        username = username_field.value.strip() if username_field.value != None else ""
        password = password_field.value.strip() if password_field.value != None else ""

        # Example validation logic (replace with your logic)
        if username == app_user and password == app_password:
            login_message.value = "Login successful!"
            login_dialog.open = False  # Close the dialog
            # Navigate to the main page or perform further actions
            if remember_me.value:
                save_config({"APP_USER": username, "APP_PASSWORD": password})

        else:
            login_message.value = "Invalid username or password!"

        page.update()

    # Close confirmation dialog handlers
    async def close_click(e):
        # Perform cleanup or saving logic here if needed
        await close_app(page)

    # Login dialog with username and password fields
    login_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Login"),
        content=ft.Column(
            controls=[
                username_field,
                password_field,
                login_message,
            ],
            tight=True,
        ),
        actions=[
            remember_me,
            ft.Divider(opacity=0),
            ft.Row(
                [
                    ft.ElevatedButton("Login", on_click=login_click),
                    ft.OutlinedButton("Close", on_click=close_click),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # Show the dialog
    page.overlay.append(login_dialog)
    login_dialog.open = True
    page.update()

    return login_dialog


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
        confirm_dialog.open = False  # Close the dialog
        page.update()  # Update the page to reflect changes

    # Confirmation dialog
    confirm_dialog = ft.AlertDialog(
        title=ft.Text("Please confirm"),
        content=ft.Text("Do you really want to exit this app?"),
        actions=[
            ft.ElevatedButton("Yes", on_click=yes_click),
            ft.OutlinedButton("No", on_click=no_click),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    return confirm_dialog



