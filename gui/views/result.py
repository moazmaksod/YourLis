from http import client
import flet as ft
from datetime import datetime

from httpx import Client
from gui.api_methods import fetch_communication_messages
import asyncio
from collections import defaultdict

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
        
        # Message list with scrolling
        self.message_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=20,
            auto_scroll=True
        )
        
        # Wrap ListView in a Container for border and padding
        self.content = ft.Container(
            content=self.message_list,
            expand=True,
            border=ft.border.all(1, ft.Colors.GREY_300),
            padding=10
        )
    
    def update_messages(self, messages: list):
        """Update messages in this tab"""
        # Sort messages by timestamp
        sorted_messages = sorted(messages, key=lambda x: x["timestamp"])
        
        # Check if messages have changed
        if sorted_messages != self.messages:
            self.messages = sorted_messages.copy()  # Make a copy to prevent reference issues
            self.message_list.controls = [MessageBubble(msg) for msg in sorted_messages]
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
        self.last_messages = []  # Cache last message set
        self.update_pending = False  # Flag to prevent multiple simultaneous updates
        
        # Create header
        self.header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(name=ft.Icons.CHAT, color=ft.Colors.BLUE),
                    ft.Text(
                        "Device-Server Communication",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER
            ),
            margin=ft.margin.only(bottom=10)
        )
        
      
        
        # Create tabs
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            expand=True,
        )
        

        
        # Add controls to view
        self.controls = [
            self.header,
            self.tabs
        ]
        
        # Start message updates
        if self.page:
            self.page.run_task(self.update_loop)
    
    def will_unmount(self):
        """Cleanup when view is unmounted"""
        self.running = False
    
    def get_device_tab(self, device_name: str, device_address: str) -> TabInfo:
        """Get or create a tab for the specified device"""


        if device_address not in self.device_tabs:
            # Create new device tab content
            device_tab_content = DeviceTab(device_address)
            

            # Create new tab
            tab = ft.Tab(
                text=f"{ len(self.device_tabs) + 1 } - {device_name}",
                icon=ft.Icon(name=ft.Icons.DEVICES),
                content=device_tab_content
            )
            
            # Store tab info
            tab_info = TabInfo(tab=tab, content=device_tab_content)
            self.device_tabs[device_address] = tab_info
            
            # Add tab to tabs control
            self.tabs.tabs.append(tab)
            self.update()
        else:
            # Update existing tab name
            tab_info = self.device_tabs[device_address]
            if device_name not in tab_info.tab.text:
                tab_info.tab.text = f"{device_name}"
                self.update()
        
        return self.device_tabs[device_address]
    
    def update_device_tabs(self, messages: list):
        """Update all device tabs with their respective messages"""
        try:
            if not messages:
                return False
             

            # Group messages by device
            device_messages = defaultdict(list)
            for msg in messages:
                if msg.get("client_address"):  # Only process messages with valid client
                    device_messages[msg["client_address"]].append(msg)


            updated = False
            
            # Update or create device-specific tabs
            for client_address, device_msgs in device_messages.items():
                device_name = device_msgs[-1]["client_name"]  # Use the last message's client name
                tab_info = self.get_device_tab(device_name, client_address)
                if tab_info.content.update_messages(device_msgs):
                    updated = True

            return updated
            
        except Exception as e:
            print(f"Error updating device tabs: {e}")
            return False
    
    def messages_changed(self, new_messages: list) -> bool:
        """Check if messages have actually changed"""
        if len(new_messages) != len(self.last_messages):
            return True
            
        for new_msg, old_msg in zip(new_messages, self.last_messages):
            if (new_msg.get("timestamp") != old_msg.get("timestamp") or 
                new_msg.get("message") != old_msg.get("message") or
                new_msg.get("client_name") != old_msg.get("client_name") or
                new_msg.get("client_address") != old_msg.get("client_address")):
                return True
        return False
    
    async def update_loop(self):
        """Main update loop for fetching and displaying messages"""
        while self.running:
            try:
                if not self.update_pending:
                    self.update_pending = True
                    messages = await fetch_communication_messages()
                    
                    if messages and self.messages_changed(messages):
                        self.last_messages = messages.copy()
                        if self.update_device_tabs(messages):
                            self.page.update()  # Regular synchronous update
                    
                    self.update_pending = False
                    
            except Exception as e:
                print(f"Error in update loop: {e}")
                self.update_pending = False
            
            await asyncio.sleep(1)  # Check frequently but don't update unless needed

def result_view(page: ft.Page):
    """Create the communication view"""
    return CommunicationView(page)
