# flet_app/views/settings.py
import flet as ft

def report_view():
    """
    report view content.
    """
    return ft.Column(
        controls=[
            ft.Text("Reports", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
            ft.Text("Here you can manage your reports page."), # Will use default body style
        ],
        expand=True,
    )
