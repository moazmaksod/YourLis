import flet as ft
from gui.components import (
    login_dialog,
    server_control,
    side_menu,
    close_confirm_dialog,
    title_bar,
    footer,
    db_conn_fail_dialog,  # import the new dialog
)
from gui.views.dashboard import dashboard_view
from gui.views.stream import stream_view
from gui.views.patient import patient_view
from gui.views.settings import settings_view
from gui.views.about import about_view
from gui.theme import get_app_themes, app_fonts  # Import themes and fonts

import os
import sys

# Get the absolute path of the current script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level to the project root
project_root = os.path.dirname(script_dir)
# Add the project root to the Python path to ensure correct module resolution
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Construct the absolute path to the 'setting' directory
setting_dir = os.path.join(project_root, "setting")

# Ensure the setting directory exists before importing from it
if not os.path.exists(setting_dir):
    os.makedirs(setting_dir)

from setting.config import get_config


cfg = get_config()  # Load configuration from file
APPLICATION_NAME = cfg["APPLICATION_NAME"]
APPLICATION_SLOGAN = cfg["APPLICATION_SLOGAN"]
dark_mode = cfg["DARK_MODE"]


def main(page: ft.Page):
    page.title = APPLICATION_NAME + APPLICATION_SLOGAN

    # Apply themes and fonts
    light_theme, dark_theme_obj = (
        get_app_themes()
    )  # Renamed dark_theme to dark_theme_obj to avoid conflict
    page.theme = light_theme
    page.dark_theme = dark_theme_obj
    page.fonts = app_fonts  # Register custom fonts

    page.theme_mode = ft.ThemeMode.DARK if dark_mode else ft.ThemeMode.LIGHT

    # page.window.bgcolor = ft.Colors.with_opacity(0, "BLACK")
    # page.bgcolor = ft.Colors.with_opacity(0, "BLACK")
    # page.window.title_bar_hidden = True
    # page.window.title_bar_buttons_hidden = True
    # page.window.frameless = True
    # page.window.shadow = True
    # page.padding = 5
    # page.spacing = 0

    # handel close window
    confirm_dialog = close_confirm_dialog(page)

    # Show DB connection fail dialog as overlay if DB is not connected at startup
    from database.sqlconnection import get_db_connection

    def show_settings_view():
        # Use the same logic as side menu navigation to settings
        selected = 3  # index for settings
        views_map = {
            0: "dashboard",
            1: "Stream",
            2: "patient",
            3: "settings",
            4: "about",
        }
        view_key = views_map.get(selected)
        if view_key not in cached_views:
            cached_views[view_key] = settings_view(page)
        current_view.controls.clear()
        current_view.controls.append(cached_views[view_key])
        page.update()

    try:
        get_db_connection()
    except Exception:
        dialog = db_conn_fail_dialog(page, on_settings=show_settings_view)
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    # Handle window close events
    def handle_window_event(e):
        if e.data == "close":
            confirm_dialog.open = True  # Show the confirmation dialog
            page.overlay.append(confirm_dialog)
            page.update()

    # Prevent default close behavior and attach the event handler
    page.window.prevent_close = True
    page.window.on_event = handle_window_event

    # --- ROLLBACK: USE STATIC LOGIN ---
    # login_dialog(page)
    # Below is the old app rendering logic (no login gating needed)

    # Navigation state
    current_view = ft.Column(expand=True)

    cached_views = {}  # Cache for views

    # Navigation change handler with caching
    def on_side_menu_change(e):
        selected = e.control.selected_index

        # Map menu index to views
        views_map = {
            0: "dashboard",
            1: "Stream",
            2: "patient",
            3: "settings",
            4: "about",
        }

        view_key = views_map.get(selected)
        if not view_key:
            return

        # Check if the view is cached
        if view_key not in cached_views:
            if view_key == "dashboard":
                cached_views[view_key] = dashboard_view(page)
            elif view_key == "Stream":
                cached_views[view_key] = stream_view(page)  # Pass the page parameter
            elif view_key == "patient":
                cached_views[view_key] = patient_view(page)
            elif view_key == "settings":
                cached_views[view_key] = settings_view(page)
            elif view_key == "about":
                cached_views[view_key] = about_view()

        # Update the current view with the cached or newly created view
        current_view.controls.clear()
        current_view.controls.append(cached_views[view_key])
        page.update()

    # title bar container
    title_bar_container = ft.Container(
        title_bar(
            app_name=APPLICATION_NAME,
            app_slogan=APPLICATION_SLOGAN,
            close_method=close_confirm_dialog,
            page=page,
        )
    )

    # Add UI components to the page
    page.add(
        ft.Container(
            content=ft.Row(
                controls=[
                    side_menu(on_side_menu_change),  # Side menu
                    ft.Container(  # Wrap the right-side content
                        content=ft.Column(
                            controls=[
                                ft.Container(content=server_control(page)),
                                ft.Container(
                                    content=current_view, expand=True
                                ),  # Ensure it stretches
                                ft.Container(content=footer()),
                            ],
                            expand=True,  # Allow column to stretch vertically
                        ),
                        expand=True,  # Allow container to stretch horizontally
                    ),
                ],
                expand=True,  # Allow row to stretch horizontally
            ),
            expand=True,  # Allow row to stretch vertically
        ),
    )

    # Load the initial view
    current_view.controls.append(dashboard_view(page))

    page.update()


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
