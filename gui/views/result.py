# flet_app/views/settings.py
import flet as ft

def result_view():
    """
    Result view content.
    """
    return ft.Column(
        controls=[
            ft.Text("Results", size=20, weight=ft.FontWeight.BOLD),
            ft.Text("Here you can manage your cbc results."),
        ],
        expand=True,
    )
