import flet as ft
from datetime import datetime
from gui.api_methods import fetch_communication_messages
import asyncio
from collections import defaultdict
from log.logger import log_info, log_error


class MessageBubble(ft.Container):
    """A chat bubble to display a single message"""
    def __init__(self, message: dict):
        self.message = message
        self.timestamp = datetime.fromisoformat(message["timestamp"])
        
        # Determine message type and styling
        is_server = message["direction"] == "server"
        is_info = message["direction"] == "info"
        is_error = message["direction"] == "error"
        
        # Set colors based on message type
        if is_info:
            client_color = ft.Colors.GREY
            message_color = ft.Colors.GREY
            bg_color = ft.Colors.WHITE70
        elif is_error:
            client_color = ft.Colors.RED
            message_color = ft.Colors.RED
            bg_color = ft.Colors.RED_50
        else:
            client_color = ft.Colors.BLUE if is_server else ft.Colors.GREEN
            message_color = ft.Colors.WHITE
            bg_color = ft.Colors.BLUE_900 if is_server else ft.Colors.GREEN_900
        
        # Create message content with HL7 formatting
        message_text = ft.Container(
            content=ft.Text(
                message["message"],
                selectable=True,
                no_wrap=False,
                max_lines=None,
                size=14,
                weight=ft.FontWeight.NORMAL,
                color=message_color,  # Set specific color for message text
            ),
            bgcolor=bg_color,
            padding=10,
            width=350  # Fixed width for better readability
        )
        
        content = ft.Column(
            controls=[
                ft.Text(
                    f"{message['client_name']} ({message['direction']})",
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=client_color,  # Use client-specific color
                    selectable=True
                ),
                message_text,
                ft.Text(
                    self.timestamp.strftime("%H:%M:%S"),
                    size=10,
                    color=ft.Colors.GREY_700,  # Darker grey for better visibility
                    selectable=True
                ),
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.START if is_server else ft.MainAxisAlignment.END,
            tight=True
        )
        
        super().__init__(
            content=content,
            alignment=ft.alignment.center_right if not is_server else ft.alignment.center_left,
            margin=ft.margin.symmetric(vertical=5),
            animate=300,  # Simple animation duration
            padding=ft.padding.symmetric(horizontal=10),
            width=400,
        )

class DeviceTab(ft.Container):
    """A tab containing messages for a specific device"""
    def __init__(self, device_name: str):
        super().__init__(expand=True)
        self.device_name = device_name
        self.messages = []  # Store message history
        self.scroll_position = 0  # Store scroll position
        
        # Message list with scrolling but without auto_scroll
        self.message_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=20,
            auto_scroll=False,  # Disable auto-scroll to end
            on_scroll=self.on_list_scroll,  # Track scroll position
        )
        
        # Wrap ListView in a Container for border and padding
        self.content = ft.Container(
            content=self.message_list,
            expand=True,
            border=ft.border.all(1, ft.Colors.GREY_300),
            padding=10
        )
    
    def on_list_scroll(self, e: ft.ScrollEvent):
        """Track scroll position of the list"""
        self.scroll_position = e.pixels
        
    def update_messages(self, messages: list):
        """Update messages in this tab"""
        # Sort messages by timestamp
        sorted_messages = sorted(messages, key=lambda x: x["timestamp"])
        
        # Check if messages have changed
        if sorted_messages != self.messages:
            current_scroll = self.scroll_position  # Save current scroll position
            
            self.messages = sorted_messages.copy()  # Make a copy to prevent reference issues
            self.message_list.controls = [MessageBubble(msg) for msg in sorted_messages]
            
            # Restore scroll position after update
            self.message_list.scroll_to(offset=current_scroll, duration=0)
            return True
        return False

class TabInfo:
    """Helper class to store tab information"""
    def __init__(self, tab: ft.Tab, content: DeviceTab):
        self.tab = tab
        self.content = content

class CommunicationView(ft.Column):
    """Main view for device-server communication"""
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.page = page
        self.running = True
        self.device_tabs = {}  # Store TabInfo objects
        self.message_cutoff_times = {}  # Track cutoff time for messages per device
        self.update_pending = False  # Flag to prevent multiple simultaneous updates
        self.last_selected_tab = None  # Track the last selected tab
        
        # Create tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            expand=True,
            on_change=self.on_tab_change  # Track tab changes
        )
        
        # Add controls to view
        self.controls = [
            self.tabs
        ]
        
        # Start message updates
        if self.page:
            self.page.run_task(self.update_loop)
    
    def on_tab_change(self, e):
        """Handle tab changes and restore scroll positions"""
        if self.last_selected_tab is not None and len(self.tabs.tabs) > 0:
            # Find the newly selected tab
            new_tab_info = None
            for device_addr, tab_info in self.device_tabs.items():
                if tab_info.tab == self.tabs.tabs[self.tabs.selected_index]:
                    new_tab_info = tab_info
                    break
            
            if new_tab_info:
                # Restore the scroll position for the newly selected tab
                new_tab_info.content.message_list.scroll_to(
                    offset=new_tab_info.content.scroll_position,
                    duration=0
                )
        
        self.last_selected_tab = self.tabs.selected_index
    
    def will_unmount(self):
        """Cleanup when view is unmounted"""
        self.running = False
        self.device_tabs.clear()
        self.message_cutoff_times.clear()
    
    def close_tab(self, device_address: str):
        """Close a device tab and clean up its resources"""
        if device_address in self.device_tabs:
            tab_info = self.device_tabs[device_address]
            # Remove tab from view
            if tab_info.tab in self.tabs.tabs:
                self.tabs.tabs.remove(tab_info.tab)
            # Clean up device data
            del self.device_tabs[device_address]
            # Set message cutoff time to now for this device
            self.message_cutoff_times[device_address] = datetime.now()
            
            self.update()
            if len(self.tabs.tabs) > 0:
                self.tabs.selected_index = 0
    
    def get_device_tab(self, device_name: str, device_address: str) -> TabInfo:
        """Get or create a tab for the specified device"""

        # device logo for icon if available
        device_logo_url = f'assets/logo/{device_name.lower()}.png' if '192.168' not in device_name else 'assets/logo/default_device.png'

        device_logo = ft.Image(
            src=device_logo_url,
            width=32,
            height=32,
            border_radius=16,
            fit=ft.ImageFit.FILL,
        )
        if device_address not in self.device_tabs:
            # Create new device tab content
            device_tab_content = DeviceTab(device_address)
            
            new_tab_index = len(self.device_tabs) + 1  # New tab index
            # Create tab text and close button
            tab_text = ft.Row(
                controls=[
                    ft.Text(f"{new_tab_index} - {device_name}"),
                    device_logo,
                    ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        icon_size=14,
                        on_click=lambda e, addr=device_address: self.close_tab(addr),
                        style=ft.ButtonStyle(
                            color={"hovered": ft.Colors.RED_400},
                            padding=5
                        )
                    )
                ],
                spacing=5,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )

            # Create new tab
            tab = ft.Tab(
                tab_content=tab_text,
                content=device_tab_content
            )
            
            # Store tab info
            tab_info = TabInfo(tab=tab, content=device_tab_content)
            self.device_tabs[device_address] = tab_info
            
            # Add tab to tabs control
            self.tabs.tabs.append(tab)
            self.update()
        else:
            exist_tab_index = self.tabs.tabs.index(self.device_tabs[device_address].tab)
            # Update existing tab name if needed
            tab_info = self.device_tabs[device_address]
            current_device_name = tab_info.tab.tab_content.controls[0].value
            new_device_name = f"{exist_tab_index + 1} - {device_name}"
            if new_device_name != current_device_name:
                tab_info.tab.tab_content.controls[0].value = new_device_name
                self.update()
            # update device logo if needed
            new_device_logo_url = f'assets/logo/{device_name.lower()}.png' if '192.168' not in device_name else r'assets/logo/default_device.png'

            if new_device_logo_url != tab_info.tab.tab_content.controls[1].src:
                tab_info.tab.tab_content.controls[1].src = new_device_logo_url


        return self.device_tabs[device_address]
    
    def filter_new_messages(self, messages: list) -> dict:
        """Filter messages to only include new ones after tab closure"""
        device_messages = defaultdict(list)
        
        for msg in messages:
            if msg.get("client_address"):
                client_address = msg["client_address"]
                msg_timestamp = datetime.fromisoformat(msg["timestamp"])
                
                # Check if we have a cutoff time for this device
                cutoff_time = self.message_cutoff_times.get(client_address)
                
                # Include message if:
                # 1. No cutoff time exists (tab was never closed) OR
                # 2. Message is newer than the cutoff time
                if not cutoff_time or msg_timestamp > cutoff_time:
                    device_messages[client_address].append(msg)
        
        return device_messages
    
    def update_device_tabs(self, messages: list):
        """Update all device tabs with their respective messages"""
        try:
            if not messages:
                return False

            # Filter and group messages by device
            device_messages = self.filter_new_messages(messages)
            updated = False
            
            # Update or create device-specific tabs
            for client_address, device_msgs in device_messages.items():
                if device_msgs:  # Only process if there are new messages
                    device_name = device_msgs[-1]["client_name"]
                    tab_info = self.get_device_tab(device_name, client_address)
                    
                    if tab_info and tab_info.content.update_messages(device_msgs):
                        updated = True

            return updated
            
        except Exception as e:
            log_error(f"Error updating device tabs: {e}")
            return False
    
    async def update_loop(self):
        """Main update loop for fetching and displaying messages"""
        last_messages = []  # Keep track of last processed messages
        
        while self.running:
            try:
                if not self.update_pending:
                    self.update_pending = True
                    messages = await fetch_communication_messages()
                    
                    # Only update if messages have changed
                    if messages != last_messages:
                        last_messages = messages.copy()
                        if self.update_device_tabs(messages):
                            self.page.update()
                    
                    self.update_pending = False
                    
            except Exception as e:
                log_error(f"Error in update loop: {e}")
                self.update_pending = False
            
            await asyncio.sleep(5)

def result_view(page: ft.Page):
    """Create the communication view"""
    return CommunicationView(page)
