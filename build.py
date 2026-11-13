import PyInstaller.__main__
import os
import platform

# --- Configuration ---
APP_NAME = "HealthMesh"
ENTRY_POINT = "main.py"
# You can specify the path to your icon file here.
# For Windows, it's recommended to use a .ico file.
# Example: ICON_PATH = "assets/logo/your_icon.ico"
ICON_PATH = None 

ASSETS_PATH = "assets"
SQL_QUERIES_PATH = "Sql_reqirement_querys"


def main():
    """
    Runs PyInstaller to build the executable.
    """

    # --- Platform-specific adjustments ---
    separator = ';' if platform.system() == "Windows" else ':'

    # --- Build Command ---
    command = [
        '--name', APP_NAME,
        '--onefile',
        '--windowed',  # Use for GUI applications to not show a console
        f'--add-data={ASSETS_PATH}{separator}assets',
        f'--add-data={SQL_QUERIES_PATH}{separator}Sql_reqirement_querys',
        '--hidden-import=pyodbc',
        '--hidden-import=uvicorn',
        '--hidden-import=flet',
        '--hidden-import=fastapi',
        '--hidden-import=pydantic',
        '--hidden-import=cryptography',
        '--hidden-import=hl7',
        '--hidden-import=gui.main_flet',
        '--hidden-import=api.app',
        ENTRY_POINT,
    ]

    if ICON_PATH:
        command.extend(['--icon', ICON_PATH])

    print(f"Running PyInstaller with command: pyinstaller {" ".join(command)}")
    
    try:
        PyInstaller.__main__.run(command)
        print("\nBuild process finished successfully!")
        print(f"Executable created in the 'dist' folder: {APP_NAME}.exe")
    except Exception as e:
        print(f"\nAn error occurred during the build process: {e}")
        print("Please check the PyInstaller logs for more details.")

if __name__ == "__main__":
    print("Starting the build process...")
    main()