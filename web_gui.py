from gui.main_flet import main as flet_main
import flet as ft






ft.app(target=flet_main, assets_dir="assets", view=ft.AppView.WEB_BROWSER, port=9080)