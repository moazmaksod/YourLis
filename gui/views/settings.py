import flet as ft
from setting.config import get_config, save_config, get_available_sql_drivers

temp_value = "change"
changed_db_user = "Write new user"
changed_db_password = "Write new password"


def settings_view(page: ft.Page):
    """
    Settings view content with collapsible sections and scrollable layout.
    """
    cfg = get_config()  # Load configuration from file

    def save_settings(e):
        # Save settings to the configuration file
        setting_to_save = {
            "CONFIG_URL": config_url.value,
            "DARK_MODE": dark_mode.value,
            "SERVER_HOST": server_host.value,
            "SERVER_PORT": server_port.value,
            "DB_TYPE": database_type.value,
            "DB_DRIVE": database_driver.value,
            "DB_HOST": database_host.value,
            "DB_PORT": database_port.value,
            "DB_NAME": database_name.value,
        }

        if database_user.value != temp_value:
            setting_to_save.update({"DB_USER": database_user.value})

        if database_password.value != temp_value:
            setting_to_save.update({"DB_PASSWORD": database_password.value})

        save_config(setting_to_save)

    def theme_change(e):
        if dark_mode.value:
            page.theme_mode = ft.ThemeMode.DARK
        else:
            page.theme_mode = ft.ThemeMode.LIGHT
        page.update()

    def show_user(e):
        # show hidden password
        if e.control.icon == ft.Icons.REMOVE_RED_EYE_OUTLINED:
            # show password value
            database_user.password = False
            e.control.icon = ft.Icons.REMOVE_RED_EYE
            page.update()
        elif e.control.icon == ft.Icons.REMOVE_RED_EYE:
            # hide password value
            database_user.password = True
            e.control.icon = ft.Icons.REMOVE_RED_EYE_OUTLINED
            page.update()

    def show_password(e):
        # show hidden password
        if e.control.icon == ft.Icons.REMOVE_RED_EYE_OUTLINED:
            # show password value
            database_password.password = False
            e.control.icon = ft.Icons.REMOVE_RED_EYE
            page.update()
        elif e.control.icon == ft.Icons.REMOVE_RED_EYE:
            # hide password value
            database_password.password = True
            e.control.icon = ft.Icons.REMOVE_RED_EYE_OUTLINED
            page.update()

    def on_text_change(e):
        if e.control.value == temp_value:
            e.control.value = ""
        elif e.control.value == "":
            e.control.value = temp_value
        page.update()

    # Get available SQL Server drivers
    available_drivers = get_available_sql_drivers()
    if not available_drivers:
        available_drivers = ["No SQL Server drivers found"]

    # settings controls initializing
    config_url = ft.TextField(label="Configuration URL", value=cfg["CONFIG_URL"])
    dark_mode = ft.Switch(label="Dark mode", value=cfg["DARK_MODE"], on_change=theme_change)
    server_host = ft.TextField(label="Server Host", value=cfg["SERVER_HOST"])
    server_port = ft.TextField(label="Server Port", value=cfg["SERVER_PORT"])
    database_type = ft.TextField(label="Database Type", value=cfg["DB_TYPE"])
    
    # Create dropdown for database drivers
    database_driver = ft.Dropdown(
        label="Database Driver",
        value=cfg["DB_DRIVE"],
        options=[ft.dropdown.Option(driver) for driver in available_drivers],
        width=300,
        hint_text="Select SQL Server driver",
    )

    database_host = ft.TextField(label="Database Host", value=cfg["DB_HOST"])
    database_port = ft.TextField(label="Database Port", value=cfg["DB_PORT"])
    database_name = ft.TextField(label="Database Name", value=cfg["DB_NAME"])
    database_user = ft.TextField(
        label="Database User",
        hint_text="Enter your database user",
        password=True,
        can_reveal_password=True,
        value=cfg["DB_USER"],
    )
    database_password = ft.TextField(
        label="Database Password",
        hint_text="Enter your database password",
        password=True,
        can_reveal_password=True,
        value=cfg["DB_PASSWORD"],
    )

    application_settings = ft.Container(
        ft.Column(
            [
                ft.Text("Application Settings", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("Configure the application's appearance and behavior."),
                ft.Divider(opacity=0),
                ft.Row(controls=[config_url, dark_mode]),
            ]
        )
    )

    server_settings = ft.Container(
        ft.Column(
            [
                ft.Text("Server Settings", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("Configure the server's network settings."),
                ft.Divider(opacity=0),
                ft.Row(controls=[server_host, server_port]),
            ]
        )
    )

    database_settings = ft.Container(
        ft.Column(
            [
                ft.Text("Database Settings", size=18, weight=ft.FontWeight.BOLD),
                ft.Text("Configure the database's connection settings."),
                ft.Divider(opacity=0),
                ft.Row(
                    controls=[
                        ft.Column([database_type, database_driver]),
                        ft.Column([database_host, database_port]),
                        ft.Column(
                            [
                                database_name,
                                ft.Row([database_user]),
                                ft.Row([database_password]),
                            ]
                        ),
                    ]
                ),
            ]
        )
    )

    # Save button
    save_button = ft.ElevatedButton(text="Save Settings", on_click=save_settings)

    # Scrollable settings view
    return ft.Column(
        controls=[
            application_settings,
            server_settings,
            database_settings,
            save_button,
        ],
        scroll=ft.ScrollMode.AUTO,  # Enable scrolling
        expand=True,  # Ensure it stretches vertically
    )
