# flet_app/views/dashboard.py
import flet as ft

def dashboard_view():
    """
    Dashboard view content.
    """
    return ft.Column(
        controls=[
            ft.Text("Welcome to the Dashboard!"),
            ft.Text("Here is where you can see an overview of your app."),
        ],
        expand=True,
    )
