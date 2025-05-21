# flet_app/views/settings.py
import flet as ft

def report_view():
    """
    report view content.
    """
    return ft.Column(
        controls=[
            ft.Text("Reports", size=20, weight=ft.FontWeight.W_900),
            ft.Text("Here you can manage your reports page."),
        ],
        expand=True,
    )
