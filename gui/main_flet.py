import flet as ft
from gui.components import (
    login_dialog,
    server_control,
    side_menu,
    close_confirm_dialog,
    title_bar,
    footer,
)
from gui.views.dashboard import dashboard_view
from gui.views.result import result_view
from gui.views.patient import patient_view
from gui.views.settings import settings_view
from gui.views.about import about_view
from gui.views.report import report_view

from setting.config import get_config


cfg = get_config()  # Load configuration from file
APPLICATION_NAME = cfg["APPLICATION_NAME"]
APPLICATION_SLOGAN = cfg["APPLICATION_SLOGAN"]
dark_mode = cfg["DARK_MODE"]


def main(page: ft.Page):
    page.title = APPLICATION_NAME + APPLICATION_SLOGAN

    page.theme_mode = "dark" if dark_mode else "light"


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

    # Handle window close events
    def handle_window_event(e):
        if e.data == "close":
            confirm_dialog.open = True  # Show the confirmation dialog
            page.overlay.append(confirm_dialog)
            page.update()

    # Prevent default close behavior and attach the event handler
    page.window.prevent_close = True
    page.window.on_event = handle_window_event

    login_dialog(page)

    # Navigation state
    current_view = ft.Column(expand=True)

    cached_views = {}  # Cache for views

    # Navigation change handler with caching
    def on_side_menu_change(e):
        selected = e.control.selected_index

        # Map menu index to views
        views_map = {
            0: "dashboard",
            1: "result",
            2: "patient",
            3: "report",
            4: "settings",
            5: "about",
        }

        view_key = views_map.get(selected)
        if not view_key:
            return

        # Check if the view is cached
        if view_key not in cached_views:
            if view_key == "dashboard":
                cached_views[view_key] = dashboard_view()
            elif view_key == "result":
                cached_views[view_key] = result_view(page)  # Pass the page parameter
            elif view_key == "patient":
                cached_views[view_key] = patient_view(page)
            elif view_key == "report":
                cached_views[view_key] = report_view()
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
    current_view.controls.append(dashboard_view())

    page.update()


if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
