import flet as ft
import csv
from datetime import datetime
from pathlib import Path
import os


class SearchBar(ft.Container):
    """Search bar for filtering messages."""
    
    def __init__(self, theme: ft.Theme, on_search_change=None):
        super().__init__()
        self.theme = theme
        self.on_search_change_callback = on_search_change
        
        self.search_field = ft.TextField(
            hint_text="Search messages...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=8,
            filled=True,
            dense=True,
            on_change=self._on_search_change,
            on_submit=self._on_search_change,
            text_size=14,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8),
        )
        
        self.clear_button = ft.IconButton(
            icon=ft.Icons.CLEAR,
            icon_size=18,
            tooltip="Clear search",
            on_click=self._on_clear,
            visible=False,
            style=ft.ButtonStyle(
                color=theme.color_scheme.on_surface_variant,
                padding=4
            )
        )
        
        self.content = ft.Row(
            controls=[
                ft.Container(
                    content=self.search_field,
                    expand=True
                ),
                self.clear_button
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.START
        )
        self.expand = True
    
    def _on_search_change(self, e):
        """Handle search text change."""
        query = self.search_field.value.strip()
        self.clear_button.visible = bool(query)
        self.update()
        
        if self.on_search_change_callback:
            self.on_search_change_callback(query)
    
    def _on_clear(self, e):
        """Clear the search field."""
        self.search_field.value = ""
        self.clear_button.visible = False
        self.update()
        
        if self.on_search_change_callback:
            self.on_search_change_callback("")
    
    def get_query(self) -> str:
        """Get current search query."""
        return self.search_field.value.strip()


class ExportButton(ft.Container):
    """Button with dropdown for exporting messages."""
    
    def __init__(self, theme: ft.Theme, on_export=None):
        super().__init__()
        self.theme = theme
        self.on_export_callback = on_export
        
        self.export_button = ft.IconButton(
            icon=ft.Icons.DOWNLOAD,
            tooltip="Export messages to CSV",
            on_click=self._on_export_click,
            icon_color=theme.color_scheme.primary,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, theme.color_scheme.primary)
                },
                padding=8
            )
        )
        
        self.content = self.export_button
    
    def _on_export_click(self, e):
        """Handle export button click."""
        if self.on_export_callback:
            self.on_export_callback()
    
    @staticmethod
    def export_to_csv(messages: list, device_name: str, save_path: str = None) -> str:
        """
        Export messages to CSV file.
        
        Args:
            messages: List of message dictionaries
            device_name: Name of the device for filename
            save_path: Optional custom save path
            
        Returns:
            Path to the exported file
        """
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"messages_{device_name.replace(' ', '_')}_{timestamp}.csv"
        
        # Use provided path or default to desktop
        if save_path:
            filepath = Path(save_path) / filename
        else:
            desktop = Path.home() / "Desktop"
            filepath = desktop / filename
        
        # Prepare CSV data
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Timestamp',
                'Direction',
                'Client Name',
                'Client Address',
                'Message Type',
                'Patient ID',
                'Patient Name',
                'Test Results',
                'Raw Message'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for msg in messages:
                # Parse HL7 for structured data
                from gui.views.message_components import HL7MessageParser
                parsed = HL7MessageParser.parse_hl7(msg['message'])
                
                # Format test results
                test_results = '; '.join([
                    f"{t.get('name', 'Unknown')}: {t.get('value', '')} {t.get('unit', '')}".strip()
                    for t in parsed['test_results']
                ])
                
                writer.writerow({
                    'Timestamp': msg['timestamp'],
                    'Direction': msg['direction'],
                    'Client Name': msg['client_name'],
                    'Client Address': msg['client_address'],
                    'Message Type': parsed['message_type'],
                    'Patient ID': parsed['patient_id'] or '',
                    'Patient Name': parsed['patient_name'] or '',
                    'Test Results': test_results,
                    'Raw Message': msg['message'].replace('\n', ' | ')
                })
        
        return str(filepath)


class StreamToolbar(ft.Container):
    """Top toolbar with search, export, and control buttons."""
    
    def __init__(
        self,
        page: ft.Page,
        theme: ft.Theme,
        on_search_change=None,
        on_export=None,
        on_auto_scroll_toggle=None,
        on_clear_messages=None
    ):
        super().__init__()
        self.page = page
        self.theme = theme
        self.on_search_change_callback = on_search_change
        self.on_export_callback = on_export
        self.on_auto_scroll_toggle_callback = on_auto_scroll_toggle
        self.on_clear_messages_callback = on_clear_messages
        
        # Auto-scroll state (enabled by default)
        self.auto_scroll_enabled = True
        
        # Search bar
        self.search_bar = SearchBar(theme, on_search_change=on_search_change)
        
        # Export button
        self.export_btn = ExportButton(theme, on_export=on_export)
        
        # Auto-scroll toggle
        self.auto_scroll_button = ft.IconButton(
            icon=ft.Icons.VERTICAL_ALIGN_BOTTOM,
            tooltip="Auto-scroll: ON",
            on_click=self._toggle_auto_scroll,
            icon_color=theme.color_scheme.secondary,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, theme.color_scheme.secondary)
                },
                padding=8
            )
        )
        
        # Clear messages button
        self.clear_button = ft.IconButton(
            icon=ft.Icons.DELETE_SWEEP,
            tooltip="Clear messages",
            on_click=self._on_clear_messages,
            icon_color=theme.color_scheme.error,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.1, theme.color_scheme.error)
                },
                padding=8
            )
        )
        
        # Build toolbar
        self.content = ft.Container(
            content=ft.Row(
                controls=[
                    self.search_bar,
                    ft.VerticalDivider(width=1, color=theme.color_scheme.outline),
                    self.auto_scroll_button,
                    self.export_btn,
                    self.clear_button,
                ],
                spacing=8,
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            bgcolor=ft.Colors.with_opacity(0.03, theme.color_scheme.on_surface),
            border=ft.border.all(1, theme.color_scheme.outline),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
        )
        self.margin = ft.margin.only(bottom=12)
    
    def _toggle_auto_scroll(self, e):
        """Toggle auto-scroll functionality."""
        self.auto_scroll_enabled = not self.auto_scroll_enabled
        
        # Update button appearance
        if self.auto_scroll_enabled:
            self.auto_scroll_button.icon = ft.Icons.VERTICAL_ALIGN_BOTTOM
            self.auto_scroll_button.icon_color = self.theme.color_scheme.secondary
            self.auto_scroll_button.tooltip = "Auto-scroll: ON"
        else:
            self.auto_scroll_button.icon = ft.Icons.VERTICAL_ALIGN_CENTER
            self.auto_scroll_button.icon_color = self.theme.color_scheme.on_surface_variant
            self.auto_scroll_button.tooltip = "Auto-scroll: OFF"
        
        self.update()
        
        if self.on_auto_scroll_toggle_callback:
            self.on_auto_scroll_toggle_callback(self.auto_scroll_enabled)
    
    def _on_clear_messages(self, e):
        """Handle clear messages button click."""
        if self.on_clear_messages_callback:
            # Show confirmation dialog
            def close_dialog(e):
                dialog.open = False
                self.page.update()
            
            def confirm_clear(e):
                dialog.open = False
                self.page.update()
                self.on_clear_messages_callback()
            
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Clear Messages"),
                content=ft.Text("Are you sure you want to clear all messages for this device?"),
                actions=[
                    ft.TextButton("Cancel", on_click=close_dialog),
                    ft.TextButton(
                        "Clear",
                        on_click=confirm_clear,
                        style=ft.ButtonStyle(
                            color=self.theme.color_scheme.error
                        )
                    ),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
    
    def get_search_query(self) -> str:
        """Get current search query."""
        return self.search_bar.get_query()
    
    def is_auto_scroll_enabled(self) -> bool:
        """Check if auto-scroll is enabled."""
        return self.auto_scroll_enabled


class LoadingSkeleton(ft.Container):
    """Loading skeleton for messages."""
    
    def __init__(self, theme: ft.Theme):
        super().__init__()
        self.theme = theme
        
        # Create shimmer effect containers
        skeletons = []
        for i in range(3):
            skeleton = ft.Container(
                content=ft.Column([
                    ft.Container(
                        width=200,
                        height=12,
                        bgcolor=ft.Colors.with_opacity(0.1, theme.color_scheme.on_surface),
                        border_radius=4
                    ),
                    ft.Container(
                        width=300,
                        height=40,
                        bgcolor=ft.Colors.with_opacity(0.05, theme.color_scheme.on_surface),
                        border_radius=8,
                        margin=ft.margin.only(top=8)
                    ),
                    ft.Container(
                        width=100,
                        height=10,
                        bgcolor=ft.Colors.with_opacity(0.08, theme.color_scheme.on_surface),
                        border_radius=4,
                        margin=ft.margin.only(top=4)
                    ),
                ], spacing=4),
                padding=16,
                margin=ft.margin.only(bottom=12)
            )
            skeletons.append(skeleton)
        
        self.content = ft.Column(
            controls=skeletons,
            spacing=8
        )
        self.animate_opacity = ft.animation.Animation(1000, ft.AnimationCurve.EASE_IN_OUT)


class EmptyState(ft.Container):
    """Empty state when no messages are available."""
    
    def __init__(self, theme: ft.Theme, message: str = "No messages yet"):
        super().__init__()
        self.theme = theme
        
        self.content = ft.Column(
            controls=[
                ft.Icon(
                    ft.Icons.MESSAGE_OUTLINED,
                    size=64,
                    color=theme.color_scheme.on_surface_variant,
                    opacity=0.5
                ),
                ft.Text(
                    message,
                    size=16,
                    color=theme.color_scheme.on_surface_variant,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Messages will appear here when devices connect",
                    size=12,
                    color=theme.color_scheme.on_surface_variant,
                    text_align=ft.TextAlign.CENTER,
                    opacity=0.7
                )
            ],
            spacing=12,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER
        )
        self.expand = True
        self.alignment = ft.alignment.center
