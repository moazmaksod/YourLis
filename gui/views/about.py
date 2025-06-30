# flet_app/views/about.py
import flet as ft
from setting.config import get_config, save_config

cfg = get_config()  # Load configuration from file
app_ver = cfg['VERSION']
app_name = cfg["APPLICATION_NAME"]



def about_view():
    """
    About view content.
    """
    return ft.Column(
        controls=[
            ft.Text("About the App", style=ft.TextThemeStyle.HEADLINE_LARGE),
            ft.Text(
                f"{app_name} application, \nis a cutting-edge Laboratory Information System (LIS) designed to streamline laboratory workflows and improve efficiency. \nIt adheres to the HL7 protocol, ensuring seamless integration with other healthcare systems and devices. \nHealthMesh is powered by a robust Microsoft SQL Server (MSSQL) database for secure and efficient data management.",
                style=ft.TextThemeStyle.BODY_LARGE,
                text_align=ft.TextAlign.JUSTIFY,
            ),

            ft.Divider(height=20, thickness=2, color=ft.Colorss.GREY_300), # Theme-neutral divider

            ft.Text("Supported Applications", style=ft.TextThemeStyle.HEADLINE_MEDIUM),
            ft.Row(
                controls=[
                    ft.Image(src=r"assets\images\reallab.PNG", width=150, height=150),
                    ft.Column([ft.Text("RealLab", style=ft.TextThemeStyle.TITLE_LARGE),
                                ft.Text(f"RealLab For laboratory managment software", style=ft.TextThemeStyle.BODY_MEDIUM, text_align=ft.TextAlign.JUSTIFY)
                                ] )
                ],
                expand=True
            ),

            ft.Divider(height=20, thickness=2, color=ft.Colorss.GREY_300), # Theme-neutral divider

            ft.Text("Supported Devices", style=ft.TextThemeStyle.HEADLINE_MEDIUM),


            ft.Row(
                controls=[
                    ft.Image(src=r"assets\images\genrui_kt60.jpg", width=150, height=150),
                    ft.Column([ft.Text("Genrui KT-60", style=ft.TextThemeStyle.TITLE_LARGE),
                            ft.Text(f"Genrui KT-60 is an up-to-date hematology analyzer providing smart counting mode for low-value samples with only 9μL whole blood required. \nRFID card closed system and wider linearity brings the real card closed system and more widely clinical application. \nIt is a wise choice for the small and medium labs, clinics or hospitals which require cost-effective solutions by offering a complete solution with a built-in system and reliable clinical supports.",
                                    style=ft.TextThemeStyle.BODY_MEDIUM,
                                    text_align=ft.TextAlign.JUSTIFY)
                            ] )
                ],
                expand=True
            )
        ],
        expand=True,
        spacing=20,
        scroll=ft.ScrollMode.AUTO
    )
