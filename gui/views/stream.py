import flet as ft
from datetime import datetime
from gui.api_methods import fetch_communication_messages
import asyncio
from collections import defaultdict
from log.logger import log_info, log_error


class MessageBubble(ft.Container):
    """A theme-aware chat bubble that builds its content on initialization."""

    def __init__(self, message: dict, theme: ft.Theme):
        super().__init__()
        self.message = message
        self.theme = theme  # Store the passed theme object
        self.timestamp = datetime.fromisoformat(message["timestamp"])

        # Build the control's UI directly in the constructor using the provided theme.
        is_server = self.message["direction"] == "server"
        is_info = self.message["direction"] == "info"
        is_error = self.message["direction"] == "error"

        if is_info:
            client_color = ft.Colors.GREY_700
        elif is_error:
            client_color = ft.Colors.RED_600
        else:  # Server or Client
            client_color = (
                self.theme.color_scheme.primary
                if is_server
                else self.theme.color_scheme.secondary
            )

        message_text = ft.Container(
            content=ft.Text(
                self.message["message"],
                selectable=True,
                no_wrap=False,
                max_lines=None,
            ),
            # bgcolor=self.theme.color_scheme.surface_variant,
            padding=10,
            border_radius=10,
            width=350,
        )

        content_column = ft.Column(
            controls=[
                ft.Text(
                    f"{self.message['client_name']} ({self.message['direction']})",
                    weight=ft.FontWeight.BOLD,
                    color=client_color,
                    selectable=True,
                ),
                message_text,
                ft.Text(
                    self.timestamp.strftime("%H:%M:%S"),
                    size=10,
                    color=self.theme.color_scheme.on_surface_variant,
                    selectable=True,
                ),
            ],
            spacing=4,
            alignment=(
                ft.MainAxisAlignment.START if is_server else ft.MainAxisAlignment.END
            ),
            horizontal_alignment=(
                ft.CrossAxisAlignment.START if is_server else ft.CrossAxisAlignment.END
            ),
            tight=True,
        )

        self.content = content_column
        self.alignment = (
            ft.alignment.center_left if is_server else ft.alignment.center_right
        )
        self.margin = ft.margin.symmetric(vertical=5)
        self.padding = ft.padding.symmetric(horizontal=10)
        self.width = 400


class DeviceTab(ft.Container):
    """A tab containing messages for a specific device."""

    def __init__(self, device_name: str, page: ft.Page, theme: ft.Theme):
        super().__init__(expand=True)
        self.message_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=20,
            auto_scroll=False,
            on_scroll=self.on_list_scroll,
        )
        self.content = ft.Container(
            content=self.message_list,
            expand=True,
            border=ft.border.all(1, theme.color_scheme.outline if hasattr(theme, 'color_scheme') and theme.color_scheme else ft.Colors.GREY_400),
            border_radius=8,
            padding=10,
        )
        self.device_name = device_name
        self.page = page  # Still needed for checking if control is mounted
        self.theme = theme  # Store the passed theme object
        self.messages = []
        self.scroll_position = 0

    def update_theme(self, new_theme):
        self.theme = new_theme
        if hasattr(self, "message_list") and getattr(self, "message_list", None) and getattr(self.message_list, "controls", None):
            for i, msg in enumerate(self.messages):
                if i < len(self.message_list.controls) and hasattr(self.message_list.controls[i], 'theme'):
                    self.message_list.controls[i].theme = new_theme
            self.update_messages(self.messages)

        self.message_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=20,
            auto_scroll=False,
            on_scroll=self.on_list_scroll,
        )

        # Build UI directly in constructor using the provided theme.
        self.content = ft.Container(
            content=self.message_list,
            expand=True,
            border=ft.border.all(1, self.theme.color_scheme.outline),
            border_radius=8,
            padding=10,
        )

    def on_list_scroll(self, e: ft.ScrollEvent):
        self.scroll_position = e.pixels

    def update_messages(self, messages: list):
        sorted_messages = sorted(messages, key=lambda x: x["timestamp"])

        if sorted_messages != self.messages:
            current_scroll = self.scroll_position
            self.messages = sorted_messages.copy()
            # Pass the theme object to the MessageBubble
            self.message_list.controls = [
                MessageBubble(msg, self.theme) for msg in sorted_messages
            ]

            # Check if the ListView itself is on the page before scrolling.
            if self.message_list.page:
                self.message_list.scroll_to(offset=current_scroll, duration=0)

            return True
        return False


class TabInfo:
    """Helper class to store tab information"""

    def __init__(self, tab: ft.Tab, content: DeviceTab):
        self.tab = tab
        self.content = content


class CommunicationView(ft.Column):
    """Main view for device-server communication (streaming)"""

    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.page = page
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            expand=True,
            on_change=self.on_tab_change,
        )
        self.running = False
        self.device_tabs = {}
        self.message_cutoff_times = {}
        self.update_pending = False
        self.last_selected_tab = None

        # FIX: Determine the active theme once during initialization.
        self.active_theme = (
            page.dark_theme if page.theme_mode == ft.ThemeMode.DARK else page.theme
        )

        self.controls = [self.tabs]

    def update_all_tab_themes(self, new_theme):
        for tab_info in self.device_tabs.values():
            tab_info.content.update_theme(new_theme)
        self.active_theme = new_theme
        self.update()

    def did_mount(self):
        self.page.pubsub.subscribe(self.on_pubsub_update)
        # Initial messages fetch
        self.page.run_task(self.manual_messages_refresh)
        
        log_info("CommunicationView mounted, subscribed to updates.")
        # Listen for theme changes and update all tabs
        def on_theme_change(e):
            new_theme = self.page.dark_theme if self.page.theme_mode == ft.ThemeMode.DARK else self.page.theme
            self.update_all_tab_themes(new_theme)
        self.page.on_theme_change = on_theme_change

    def will_unmount(self):
        try:
            self.page.pubsub.unsubscribe(self.on_pubsub_update)
        except Exception:
            pass
        log_info("CommunicationView unmounted, unsubscribed.")

    async def manual_messages_refresh(self):
        messages = await fetch_communication_messages()
        if self.update_device_tabs(messages) and self.page:
            self.page.update()

    async def on_pubsub_update(self, message):
        if message.get("type") == "messages":
            if self.update_device_tabs(message.get("data")) and self.page:
                self.page.update()


    def on_tab_change(self, e):
        if self.last_selected_tab is not None and len(self.tabs.tabs) > 0:
            new_tab_info = None
            if self.tabs.selected_index < len(self.tabs.tabs):
                selected_tab_control = self.tabs.tabs[self.tabs.selected_index]
                for tab_info in self.device_tabs.values():
                    if tab_info.tab == selected_tab_control:
                        new_tab_info = tab_info
                        break

            # Check if the tab's content has a page object, which confirms it's mounted.
            if new_tab_info and new_tab_info.content.page:
                new_tab_info.content.message_list.scroll_to(
                    offset=new_tab_info.content.scroll_position, duration=0
                )

        self.last_selected_tab = self.tabs.selected_index

    def close_tab(self, device_address: str):
        if device_address in self.device_tabs:
            tab_info = self.device_tabs.pop(device_address)
            if tab_info.tab in self.tabs.tabs:
                self.tabs.tabs.remove(tab_info.tab)
            self.message_cutoff_times[device_address] = datetime.now()

            if self.tabs.tabs and self.tabs.selected_index >= len(self.tabs.tabs):
                self.tabs.selected_index = len(self.tabs.tabs) - 1

            self.update()

    def get_device_tab(self, device_name: str, device_address: str) -> TabInfo:
        if device_address not in self.device_tabs:
            # Always use only device_address as the key, not theme
            device_tab_content = DeviceTab(device_name, self.page, self.active_theme)

            new_tab_index = len(self.device_tabs) + 1
            tab_text = ft.Row(
                controls=[
                    ft.Text(f"{new_tab_index} - {device_name}"),
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=14,
                        on_click=lambda _, addr=device_address: self.close_tab(addr),
                        style=ft.ButtonStyle(
                            color={"hovered": ft.Colors.RED_700}, padding=5
                        ),
                    ),
                ],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

            tab = ft.Tab(tab_content=tab_text, content=device_tab_content)

            tab_info = TabInfo(tab=tab, content=device_tab_content)
            self.device_tabs[device_address] = tab_info

            self.tabs.tabs.append(tab)
            # This update is crucial to ensure the new tab is rendered before any further actions.
            self.page.update()
        else:
            # Update tab name if device_name has changed
            tab_info = self.device_tabs[device_address]
            tab_row = tab_info.tab.tab_content
            # tab_row.controls[0] is the ft.Text for the device name
            current_label = (
                tab_row.controls[0].value
                if hasattr(tab_row.controls[0], "value")
                else tab_row.controls[0].text
            )
            new_tab_index = list(self.device_tabs.keys()).index(device_address) + 1
            new_label = f"{new_tab_index} - {device_name}"
            if current_label != new_label:
                if hasattr(tab_row.controls[0], "value"):
                    tab_row.controls[0].value = new_label
                else:
                    tab_row.controls[0].text = new_label
                self.page.update()
        return self.device_tabs[device_address]

    def filter_new_messages(self, messages: list) -> dict:
        device_messages = defaultdict(list)
        for msg in messages:
            if client_address := msg.get("client_address"):
                msg_timestamp = datetime.fromisoformat(msg["timestamp"])
                cutoff_time = self.message_cutoff_times.get(client_address)
                if not cutoff_time or msg_timestamp > cutoff_time:
                    device_messages[client_address].append(msg)
        return device_messages

    def update_device_tabs(self, messages: list):
        try:
            if not messages:
                return False

            device_messages = self.filter_new_messages(messages)
            updated = False

            for client_address, device_msgs in device_messages.items():
                if device_msgs:
                    device_name = device_msgs[-1]["client_name"]
                    tab_info = self.get_device_tab(device_name, client_address)
                    # Only add truly new messages (by timestamp)
                    existing_timestamps = set(msg["timestamp"] for msg in tab_info.content.messages)
                    new_msgs = [msg for msg in device_msgs if msg["timestamp"] not in existing_timestamps]
                    if new_msgs:
                        tab_info.content.update_messages(tab_info.content.messages + new_msgs)
                        updated = True
            return updated
        except Exception as e:
            log_error(f"Error updating device tabs: {e}")
            return False



def stream_view(page: ft.Page):
    """Create the communication view"""
    return CommunicationView(page)
