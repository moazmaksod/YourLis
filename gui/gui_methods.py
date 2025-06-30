import flet as ft
from gui.api_methods import fetch_server_status, stop_server  # Import API methods
from setting.config import get_config
import asyncio


cfg = get_config()  # Load configuration from file

SUPPORTED_DEVICES = cfg["SUPPORTED_DEVICES"]


class ServerStatusUpdater(ft.Text):
    """
    A UI component that periodically fetches and updates server status and client avatars.
    """

    def __init__(
        self, status_indicator, server_button, server_status, clients_avatars, page
    ):
        super().__init__()
        self.status_indicator = status_indicator
        self.server_button = server_button
        self.server_status = server_status
        self.clients_avatars = clients_avatars
        self.page = page

    def did_mount(self):
        """Initializes the updater and starts periodic server status checks upon mounting."""
        self.running = True
        if self.page:
            self.page.run_task(self.periodic_status_check)

    def will_unmount(self):
        """
        Stops the server status updater by setting the running flag to False.
        """
        self.running = False

    def client_connected_avatar(self, client_dict):
        """
        Generates a container with client avatars based on the provided client dictionary.

        Args:
            client_dict (dict): A dictionary mapping client identifiers to device names.

        Returns:
            ft.Container: A container holding the client avatars or an error icon if no clients are connected.
        """
        clients_avatar = []

        for client in client_dict:
            device_name = client_dict[client]
            device_ip, device_port = client.split(",")

            if device_name == None:
                device_name = "Unknown Device"

            if device_name in SUPPORTED_DEVICES:
                img_url = f'assets/logo/{device_name.lower()}.png'
            else:
                img_url = "assets/images/default_device.png"  # Default image URL if device name is not supported

            tooltip_text = f"Name: {device_name}\nIP: {device_ip}\nPort: {device_port}"

            client_avatar = ft.Image(
                src=img_url,
                width=32,
                height=32,
                border_radius=16,
                fit=ft.ImageFit.FILL,
                tooltip=tooltip_text,
            )
            clients_avatar.append(client_avatar)

        if len(clients_avatar) > 0:
            # Create a container to hold the client Avatars
            clients_container = ft.Container(
                content=ft.Row(clients_avatar, spacing=10),
                tooltip="No clients connected",
            )
        else:
            clients_container = ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(
                            name=ft.Icons.ERROR_OUTLINE, color=ft.colors.AMBER_500, size=32 # Changed to a specific Amber shade
                        )
                    ],
                    spacing=10,
                ),
                tooltip="No clients connected",
            )

        return clients_container  # Return the list of CircleAvatars

    async def periodic_status_check(self):
        """
        Periodically checks and updates the server status and related UI components.
        """
        while self.running:
            status = await fetch_server_status()  # Fetch status using the API
            self.server_status.update(status)
            # Use Flet color objects for theme consistency
            if status["state"] == "Online":
                self.status_indicator.bgcolor = ft.colors.GREEN_500 # Theme-friendly green
            else:
                self.status_indicator.bgcolor = ft.colors.RED_500   # Theme-friendly red

            self.status_indicator.tooltip = (
                f"State: {status['state']}\nDetails: {status['text']}"
            )

            # Update the clients avatars container
            self.clients_avatars.content = self.client_connected_avatar(
                status["clients"]
            )  # Update controls directly
            self.server_button.text = (
                "Stop Server" if status["state"] == "Online" else "Start Server"
            )

            if self.page:
                self.page.update()
            await asyncio.sleep(5)


async def close_app(page: ft.Page):
    """
    Close the application by stopping the server and destroying the application window.

    Args:
        page (ft.Page): The Flet page instance to be closed.
    """
    # Perform cleanup or saving logic here if needed
    await stop_server()

    page.window.destroy()  # Close the app
