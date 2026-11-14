import flet as ft
import threading
from datetime import datetime
from gui.api_methods import fetch_communication_messages
import asyncio
from collections import defaultdict
from log.logger import log_info, log_error
from gui.views.message_components import MessageCard, DeviceConnectionBadge
from gui.views.stream_controls import StreamToolbar, LoadingSkeleton, EmptyState, ExportButton


MAX_STREAM_MESSAGES = 200


def _safe_border_all(width: float, color: str):
    """Safely construct a border across Flet versions."""
    if hasattr(ft, "Border") and hasattr(ft.Border, "all"):
        return ft.Border.all(width, color)
    if hasattr(ft, "border") and hasattr(ft.border, "all"):
        return ft.border.all(width, color)
    return None


def _safe_margin_only(left=0, top=0, right=0, bottom=0):
    """Safely construct margin across Flet versions."""
    if hasattr(ft, "Margin"):
        return ft.Margin(left=left, top=top, right=right, bottom=bottom)
    if hasattr(ft, "margin") and hasattr(ft.margin, "only"):
        return ft.margin.only(left=left, top=top, right=right, bottom=bottom)
    return None


def _safe_animation(duration: int, curve=None):
    """Safely construct an Animation across Flet versions."""
    anim_cls = getattr(ft, "Animation", getattr(ft, "animation", None))
    if hasattr(anim_cls, "Animation"):
        anim_cls = anim_cls.Animation
    if anim_cls:
        return anim_cls(duration, curve) if curve else anim_cls(duration)
    return duration


class DevicePanel(ft.Container):
    """Enhanced device message panel with search, export, and modern UI."""
    
    def __init__(self, device_name: str, device_address: str, page: ft.Page, theme: ft.Theme):
        super().__init__(expand=True)
        self.device_name = device_name
        self.device_address = device_address
        self._page_ref = page
        self.theme = theme
        self._lock = threading.Lock()
        self.messages = []
        self.filtered_messages = []
        self.search_query = ""
        self.auto_scroll_enabled = True
        self.is_loading = True
        
        # Message list view
        self.message_list = ft.ListView(
            expand=True,
            spacing=12,
            padding=20,
            auto_scroll=True,
        )
        
        # Toolbar
        self.toolbar = StreamToolbar(
            page=page,
            theme=theme,
            on_search_change=self._on_search_change,
            on_export=self._on_export,
            on_auto_scroll_toggle=self._on_auto_scroll_toggle,
            on_clear_messages=self._on_clear_messages
        )
        
        # Device connection badge
        self.connection_badge = DeviceConnectionBadge(
            device_name=device_name,
            device_address=device_address,
            is_connected=True,
            theme=theme
        )
        
        # Loading skeleton
        self.loading_skeleton = LoadingSkeleton(theme)
        
        # Empty state
        self.empty_state = EmptyState(
            theme=theme,
            message=f"No messages for {device_name}"
        )
        
        # Main content container
        self.message_container = ft.Container(
            content=self.loading_skeleton,
            expand=True,
            border=_safe_border_all(1, theme.color_scheme.outline),
            border_radius=8,
            padding=10,
            bgcolor=ft.Colors.with_opacity(0.01, theme.color_scheme.on_surface)
        )
        
        # Build layout
        self.content = ft.Column(
            controls=[
                self.connection_badge,
                self.toolbar,
                self.message_container,
            ],
            spacing=12,
            expand=True
        )
    
    def update_theme(self, new_theme: ft.Theme):
        """Update theme for all components."""
        self.theme = new_theme
        # Rebuild all messages with new theme
        if self.messages:
            self.update_messages(self.messages)
    
    def _on_search_change(self, query: str):
        """Handle search query change."""
        self.search_query = query.lower()
        self._filter_messages()
    
    def _filter_messages(self):
        """Filter messages based on search query."""
        with self._lock:
            if not self.search_query:
                self.filtered_messages = list(self.messages)
            else:
                self.filtered_messages = [
                    msg for msg in self.messages
                    if self.search_query in str(msg.get("message", "")).lower()
                    or self.search_query in str(msg.get("client_name", "")).lower()
                    or self.search_query in str(msg.get("direction", "")).lower()
                ]
        
        self._refresh_message_list()
    
    def _refresh_message_list(self):
        """Refresh the message list view."""
        with self._lock:
            if not self.filtered_messages:
                # Show empty state
                self.message_container.content = self.empty_state
            else:
                # Show messages
                self.message_list.controls = [
                    MessageCard(msg, self.theme, on_copy=self._copy_to_clipboard)
                    for msg in list(self.filtered_messages)
                ]
                self.message_container.content = self.message_list
            
            # Auto-scroll to bottom if enabled
            if self.auto_scroll_enabled and self._page_ref:
                self._page_ref.run_task(self._scroll_to_bottom)
        
        self.is_loading = False
        try:
            self.update()
        except (RuntimeError, AssertionError):
            pass
    
    async def _scroll_to_bottom(self):
        """Scroll to the bottom of the message list."""
        await asyncio.sleep(0.1)  # Small delay to ensure rendering
        if self.message_list.page:
            self.message_list.scroll_to(offset=-1, duration=300)
    
    def _on_auto_scroll_toggle(self, enabled: bool):
        """Handle auto-scroll toggle."""
        self.auto_scroll_enabled = enabled
        if enabled and self._page_ref:
            self._page_ref.run_task(self._scroll_to_bottom)
    
    def _on_clear_messages(self):
        """Clear all messages."""
        with self._lock:
            self.messages = []
            self.filtered_messages = []
        self._refresh_message_list()
    
    def _on_export(self):
        """Export messages to CSV."""
        if not self.messages:
            self._show_snackbar("No messages to export", error=True)
            return
        
        try:
            filepath = ExportButton.export_to_csv(
                messages=self.messages,
                device_name=self.device_name
            )
            self._show_snackbar(f"Exported to {filepath}")
        except Exception as e:
            log_error(f"Export failed: {e}")
            self._show_snackbar(f"Export failed: {str(e)}", error=True)
    
    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        if self._page_ref:
            self._page_ref.set_clipboard(text)
        self._show_snackbar("Copied to clipboard")
    
    def _show_snackbar(self, message: str, error: bool = False):
        """Show a snackbar notification safely without overlay mutation."""
        if self._page_ref:
            from gui.components import show_snack_bar
            bgcolor = self.theme.color_scheme.error if error else self.theme.color_scheme.primary
            show_snack_bar(self._page_ref, message, bgcolor=bgcolor)
    
    def update_messages(self, messages: list):
        """Update the message list with incremental rendering and bounded buffer."""
        with self._lock:
            sorted_messages = sorted(messages, key=lambda x: x["timestamp"])
            if len(sorted_messages) > MAX_STREAM_MESSAGES:
                sorted_messages = sorted_messages[-MAX_STREAM_MESSAGES:]

            if sorted_messages == self.messages:
                return False

            # Fast path: incremental update for live append without active search
            if (
                not self.search_query
                and self.message_container.content == self.message_list
                and len(sorted_messages) > len(self.messages)
                and sorted_messages[:len(self.messages)] == self.messages
            ):
                new_messages = sorted_messages[len(self.messages):]
                self.messages = sorted_messages.copy()
                self.filtered_messages = list(self.messages)

                for msg in new_messages:
                    self.message_list.controls.append(
                        MessageCard(msg, self.theme, on_copy=self._copy_to_clipboard)
                    )

                # Prune oldest controls exceeding bound
                excess = len(self.message_list.controls) - MAX_STREAM_MESSAGES
                if excess > 0:
                    del self.message_list.controls[:excess]

                if self.auto_scroll_enabled and self._page_ref:
                    self._page_ref.run_task(self._scroll_to_bottom)

                try:
                    self.update()
                except (RuntimeError, AssertionError):
                    pass
                return True

            # Standard path: full refresh
            self.messages = sorted_messages.copy()

        self._filter_messages()
        return True
    
    def update_connection_status(self, is_connected: bool):
        """Update the connection status badge."""
        self.connection_badge = DeviceConnectionBadge(
            device_name=self.device_name,
            device_address=self.device_address,
            is_connected=is_connected,
            theme=self.theme
        )
        self.content.controls[0] = self.connection_badge
        try:
            self.update()
        except (RuntimeError, AssertionError):
            pass


class DevicePanelInfo:
    """Helper class to store device panel information."""
    
    def __init__(self, panel: DevicePanel, container: ft.Container, collapse_button: ft.IconButton):
        self.panel = panel
        self.container = container
        self.collapse_button = collapse_button
        self.is_collapsed = False


class StreamPage(ft.Column):
    """Main stream page with multi-view layout for device communication."""
    
    def __init__(self, page: ft.Page):
        super().__init__(expand=True)
        self.page = page
        
        # Determine active theme
        self.active_theme = (
            page.dark_theme if page.theme_mode == ft.ThemeMode.DARK else page.theme
        )
        
        # Device panels storage
        self.device_panels = {}  # device_address -> DevicePanelInfo
        self.message_cutoff_times = {}  # device_address -> datetime
        
        # Container for all device panels (vertical stack)
        self.devices_container = ft.ListView(
            expand=True,
            spacing=16,
            padding=20,
            auto_scroll=False
        )
        
        # Page header
        self.header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.STREAM,
                        size=32,
                        color=self.active_theme.color_scheme.primary
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(
                                "Communication Stream",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=self.active_theme.color_scheme.on_surface
                            ),
                            ft.Text(
                                "Real-time device communication monitoring",
                                size=12,
                                color=self.active_theme.color_scheme.on_surface_variant
                            )
                        ],
                        spacing=2,
                        tight=True
                    ),
                    ft.Container(expand=True),
                    ft.Text(
                        f"Active Devices: {len(self.device_panels)}",
                        size=14,
                        color=self.active_theme.color_scheme.secondary,
                        weight=ft.FontWeight.W_500
                    )
                ],
                spacing=12,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=16,
            bgcolor=ft.Colors.with_opacity(0.03, self.active_theme.color_scheme.on_surface),
            border=_safe_border_all(1, self.active_theme.color_scheme.outline),
            border_radius=8,
            margin=_safe_margin_only(bottom=16)
        )
        
        # Empty state for no devices
        self.no_devices_state = EmptyState(
            theme=self.active_theme,
            message="No devices connected"
        )
        
        # Main content
        self.main_content = ft.Container(
            content=self.no_devices_state,
            expand=True
        )
        
        # Build page layout
        self.controls = [
            self.header,
            self.main_content
        ]
    
    def did_mount(self):
        """Called when the view is mounted."""
        self.page.pubsub.subscribe(self._on_messages_broadcast)
        self.page.run_task(self._initial_messages_fetch)
        log_info("StreamPage mounted and subscribed to updates")
        
        # Listen for theme changes
        def on_theme_change(e):
            new_theme = (
                self.page.dark_theme 
                if self.page.theme_mode == ft.ThemeMode.DARK 
                else self.page.theme
            )
            self._update_all_themes(new_theme)
        
        self.page.on_theme_change = on_theme_change
    
    def will_unmount(self):
        """Called when the view is unmounted."""
        try:
            self.page.pubsub.unsubscribe(self._on_messages_broadcast)
        except Exception:
            pass
        log_info("StreamPage unmounted and unsubscribed")
    
    async def _initial_messages_fetch(self):
        """Fetch initial messages."""
        messages = await fetch_communication_messages()
        if self._update_device_panels(messages):
            self.update()
    
    def _on_messages_broadcast(self, message):
        """Handle PubSub messages."""
        if self.page and message.get("type") == "messages":
            self.page.run_task(self._handle_messages_update, message.get("data"))
    
    async def _handle_messages_update(self, data):
        """Handle incoming message updates."""
        if self._update_device_panels(data):
            self.update()
    
    def _close_panel(self, device_address: str):
        """Close a device panel."""
        if device_address in self.device_panels:
            panel_info = self.device_panels.pop(device_address)
            
            # Remove from container
            if panel_info.container in self.devices_container.controls:
                self.devices_container.controls.remove(panel_info.container)
            
            # Record cutoff time
            self.message_cutoff_times[device_address] = datetime.now()
            
            # Update device count in header
            self._update_header()
            
            # Show empty state if no panels
            if not self.device_panels:
                self.main_content.content = self.no_devices_state
            
            self.update()
    
    def _get_device_panel(self, device_name: str, device_address: str) -> DevicePanelInfo:
        """Get or create a device panel."""
        if device_address not in self.device_panels:
            # Create new device panel
            device_panel = DevicePanel(
                device_name=device_name,
                device_address=device_address,
                page=self.page,
                theme=self.active_theme
            )
            
            # Create collapse toggle function
            def toggle_collapse(e, addr=device_address):
                if addr in self.device_panels:
                    panel_info = self.device_panels[addr]
                    panel_info.is_collapsed = not panel_info.is_collapsed
                    
                    # Toggle visibility of device panel
                    panel_column = panel_info.container.content
                    if panel_info.is_collapsed:
                        # Hide the panel, show only header
                        panel_column.controls = [panel_column.controls[0]]  # Keep header only
                        panel_info.collapse_button.icon = ft.Icons.EXPAND_MORE
                        panel_info.collapse_button.tooltip = "Expand"
                    else:
                        # Show full panel
                        panel_column.controls = [panel_column.controls[0], panel_info.panel]
                        panel_info.collapse_button.icon = ft.Icons.EXPAND_LESS
                        panel_info.collapse_button.tooltip = "Collapse"
                    
                    self.page.update()
            
            # Create collapse/expand button
            collapse_button = ft.IconButton(
                icon=ft.Icons.EXPAND_LESS,
                icon_size=20,
                on_click=toggle_collapse,
                tooltip="Collapse",
                icon_color=self.active_theme.color_scheme.primary
            )
            
            # Create panel header with collapsible section
            panel_header = ft.Container(
                content=ft.Row(
                    controls=[
                        collapse_button,
                        ft.Text(
                            f"{len(self.device_panels) + 1}. {device_name}",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=self.active_theme.color_scheme.on_surface
                        ),
                        ft.Text(
                            f"({device_address})",
                            size=12,
                            color=self.active_theme.color_scheme.on_surface_variant
                        ),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_size=18,
                            on_click=lambda _, addr=device_address: self._close_panel(addr),
                            tooltip="Hide device",
                            icon_color=self.active_theme.color_scheme.error
                        )
                    ],
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                bgcolor=ft.Colors.with_opacity(0.05, self.active_theme.color_scheme.primary),
                padding=ft.Padding(16, 12, 16, 12),
                border_radius=ft.border_radius.only(top_left=8, top_right=8)
            )
            
            # Wrap panel in container with header
            panel_container = ft.Container(
                content=ft.Column(
                    controls=[
                        panel_header,
                        device_panel
                    ],
                    spacing=0,
                    tight=True
                ),
                border=_safe_border_all(1, self.active_theme.color_scheme.outline),
                border_radius=8,
                animate=_safe_animation(300, getattr(ft, "AnimationCurve", None).EASE_OUT if hasattr(ft, "AnimationCurve") else None)
            )
            
            # Store panel info
            panel_info = DevicePanelInfo(panel=device_panel, container=panel_container, collapse_button=collapse_button)
            self.device_panels[device_address] = panel_info
            
            # Store device name for update tracking
            panel_info.device_name = device_name
            # Store reference to header text controls for updating
            panel_info.header_text = panel_header.content.controls[1]  # The device name text control
            
            # Add to devices container
            self.devices_container.controls.append(panel_container)
            
            # Update main content to show devices
            self.main_content.content = self.devices_container
            
            # Update header
            self._update_header()
            
            # Force update
            self.page.update()
        else:
            # Panel exists - check if device name has changed and update header if needed
            panel_info = self.device_panels[device_address]
            if hasattr(panel_info, 'device_name') and panel_info.device_name != device_name:
                # Device name changed - update header text
                panel_info.device_name = device_name
                panel_index = list(self.device_panels.keys()).index(device_address) + 1
                panel_info.header_text.value = f"{panel_index}. {device_name}"
                log_info(f"Updated device panel header for {device_address}: {device_name}")

        
        return self.device_panels[device_address]
    
    def _filter_new_messages(self, messages: list) -> dict:
        """Filter messages by cutoff time."""
        device_messages = defaultdict(list)
        for msg in messages:
            if client_address := msg.get("client_address"):
                msg_timestamp = datetime.fromisoformat(msg["timestamp"])
                cutoff_time = self.message_cutoff_times.get(client_address)
                
                if not cutoff_time or msg_timestamp > cutoff_time:
                    device_messages[client_address].append(msg)
        
        return device_messages
    
    def _update_device_panels(self, messages: list) -> bool:
        """Update device panels with new messages."""
        try:
            if not messages:
                return False
            
            device_messages = self._filter_new_messages(messages)
            updated = False
            
            for client_address, device_msgs in device_messages.items():
                if device_msgs:
                    device_name = device_msgs[-1]["client_name"]
                    panel_info = self._get_device_panel(device_name, client_address)
                    
                    # Only add truly new messages (composite key to avoid dropping subsecond messages like IN/OUT pairs)
                    existing_keys = set(
                        (msg.get("timestamp"), msg.get("direction"), msg.get("message"))
                        for msg in panel_info.panel.messages
                    )
                    new_msgs = [
                        msg for msg in device_msgs 
                        if (msg.get("timestamp"), msg.get("direction"), msg.get("message")) not in existing_keys
                    ]
                    
                    if new_msgs:
                        all_messages = panel_info.panel.messages + new_msgs
                        panel_info.panel.update_messages(all_messages)
                        updated = True
            
            return updated
        except Exception as e:
            log_error(f"Error updating device tabs: {e}")
            return False
    
    def _update_header(self):
        """Update the header with current device count."""
        device_count_text = self.header.content.controls[3]
        device_count_text.value = f"Active Devices: {len(self.device_panels)}"
    
    def _update_all_themes(self, new_theme: ft.Theme):
        """Update theme for all components."""
        self.active_theme = new_theme
        
        for panel_info in self.device_panels.values():
            panel_info.panel.update_theme(new_theme)
        
        self.update()


def stream_view(page: ft.Page):
    """Create and return the stream view."""
    return StreamPage(page)
