import flet as ft
from datetime import datetime
from hl7msghandel.hl7parser import parse_hl7_message
from hl7msghandel.hl7dictionary import CBC_RESULT_HL7, HGB_RESULT_HL7
from log.logger import log_error


def _safe_border_all(width: float, color: str):
    """Safely construct a border across Flet versions."""
    if hasattr(ft, "Border") and hasattr(ft.Border, "all"):
        return ft.Border.all(width, color)
    if hasattr(ft, "border") and hasattr(ft.border, "all"):
        return ft.border.all(width, color)
    return None


def _safe_animation(duration: int, curve=None):
    """Safely construct an Animation across Flet versions."""
    anim_cls = getattr(ft, "Animation", getattr(ft, "animation", None))
    if hasattr(anim_cls, "Animation"):
        anim_cls = anim_cls.Animation
    if anim_cls:
        return anim_cls(duration, curve) if curve else anim_cls(duration)
    return duration


def _safe_margin_only(left=0, top=0, right=0, bottom=0):
    """Safely construct margin across Flet versions."""
    if hasattr(ft, "Margin"):
        return ft.Margin(left=left, top=top, right=right, bottom=bottom)
    if hasattr(ft, "margin") and hasattr(ft.margin, "only"):
        return ft.margin.only(left=left, top=top, right=right, bottom=bottom)
    return None


class MessageDataExtractor:
    """Extract human-readable data from HL7 messages using project's parser."""
    
    # CBC and HGB test name labels for display
    TEST_LABELS = {
        'WBC': 'White Blood Cell',
        'RBC': 'Red Blood Cell',
        'HGB': 'Hemoglobin',
        'HCT': 'Hematocrit',
        'PLT': 'Platelet',
        'MCV': 'Mean Corpuscular Volume',
        'MCH': 'Mean Corpuscular Hemoglobin',
        'MCHC': 'Mean Corpuscular Hgb Conc.',
        'RDW': 'Red Cell Distribution Width',
        'MPV': 'Mean Platelet Volume',
        'PCT': 'Plateletcrit',
        'PDW': 'Platelet Distribution Width',
        'NEUTROPHIL': 'Neutrophil',
        'LYMPHOCYTE': 'Lymphocyte',
        'MONOCYTE': 'Monocyte'
    }
    
    # Common units for CBC tests
    TEST_UNITS = {
        'WBC': '10^3/uL',
        'RBC': '10^6/uL',
        'HGB': 'g/dL',
        'HCT': '%',
        'PLT': '10^3/uL',
        'MCV': 'fL',
        'MCH': 'pg',
        'MCHC': 'g/dL',
        'RDW': '%',
        'MPV': 'fL',
        'PCT': '%',
        'PDW': 'fL',
        'NEUTROPHIL': '%',
        'LYMPHOCYTE': '%',
        'MONOCYTE': '%'
    }
    
    @staticmethod
    def extract_display_data(raw_message) -> dict:
        """
        Parse HL7 message and extract data for display.
        
        Returns:
            dict with keys: message_type, patient_id, patient_name, test_results
        """
        try:
            if isinstance(raw_message, bytes):
                raw_message_str = raw_message.decode('utf-8', errors='replace')
            else:
                raw_message_str = str(raw_message) if raw_message is not None else ""

            # Parse using project's HL7 parser
            hl7_msg = parse_hl7_message(raw_message_str, "Display")
            
            if not hl7_msg:
                return {
                    'message_type': 'Parse Error',
                    'patient_id': None,
                    'patient_name': None,
                    'test_results': []
                }
            
            # Extract basic info
            message_type = MessageDataExtractor._extract_message_type(hl7_msg)
            patient_id = MessageDataExtractor._extract_patient_id(hl7_msg)
            patient_name = MessageDataExtractor._extract_patient_name(hl7_msg)
            
            # Extract test results (CBC and HGB)
            test_results = []
            test_results.extend(MessageDataExtractor._extract_cbc_results(hl7_msg))
            test_results.extend(MessageDataExtractor._extract_hgb_results(hl7_msg))
            
            return {
                'message_type': message_type,
                'patient_id': patient_id,
                'patient_name': patient_name,
                'test_results': test_results
            }
            
        except Exception as e:
            log_error(f"Error extracting display data: {e}", source="MessageDataExtractor")
            return {
                'message_type': 'Error',
                'patient_id': None,
                'patient_name': None,
                'test_results': []
            }
    
    @staticmethod
    def _extract_message_type(hl7_msg) -> str:
        """Extract message type from MSH segment."""
        try:
            msh = hl7_msg.segment('MSH')
            if msh:
                # In python-hl7, msh[9] is MSH-9 (Message Type); fallback to index 8 if needed
                if len(msh) > 9 and str(msh[9]).strip():
                    return str(msh[9]).strip()
                elif len(msh) > 8 and str(msh[8]).strip():
                    return str(msh[8]).strip()
            return 'Unknown'
        except Exception:
            return 'Unknown'
    
    @staticmethod
    def _extract_patient_id(hl7_msg) -> str:
        """Extract patient ID from PID segment."""
        try:
            try:
                pid_segments = hl7_msg.segments('PID')
            except KeyError:
                return None
            if pid_segments and len(pid_segments) > 0:
                pid = pid_segments[0]
                if len(pid) >= 4:
                    return str(pid[3])
            return None
        except Exception:
            return None
    
    @staticmethod
    def _extract_patient_name(hl7_msg) -> str:
        """Extract patient name from PID segment."""
        try:
            try:
                pid_segments = hl7_msg.segments('PID')
            except KeyError:
                return None
            if pid_segments and len(pid_segments) > 0:
                pid = pid_segments[0]
                if len(pid) >= 6:
                    name = str(pid[5])
                    # Replace ^ with space for readability
                    return name.replace('^', ' ')
            return None
        except Exception:
            return None
    
    @staticmethod
    def _extract_cbc_results(hl7_msg) -> list:
        """Extract CBC test results using CBC_RESULT_HL7 dictionary."""
        results = []
        try:
            try:
                obx_segments = hl7_msg.segments('OBX')
            except KeyError:
                return results
            if not obx_segments:
                return results
            
            # Iterate through CBC dictionary to extract values
            for test_key, test_config in CBC_RESULT_HL7['COLUMN_NAME'].items():
                # Skip SQL, MANUAL entries, and non-test fields
                if test_config in ['SQL', 'MANUAL']:
                    continue
                
                # Skip metadata fields that aren't actual test results
                if test_key in ['PATIENT_ID', 'REQ_DATE']:
                    continue
                
                try:
                    segment_type = test_config['S']
                    segment_number = int(test_config['N'])
                    field_number = int(test_config['F'])
                    
                    # Get the specific OBX segment
                    if segment_number < len(obx_segments):
                        obx = obx_segments[segment_number]
                        if len(obx) > field_number:
                            value = str(obx[field_number]).strip()
                            
                            # Only add if value is not empty
                            if value:
                                # Get unit from OBX field 6 if available
                                unit = ''
                                if len(obx) > 6:
                                    unit = str(obx[6]).strip()
                                
                                # Fallback to default unit if not in message
                                if not unit:
                                    unit = MessageDataExtractor.TEST_UNITS.get(test_key, '')
                                
                                # Get human-readable label
                                label = MessageDataExtractor.TEST_LABELS.get(test_key, test_key)
                                
                                results.append({
                                    'key': test_key,
                                    'label': label,
                                    'value': value,
                                    'unit': unit
                                })
                except Exception as e:
                    # Skip this test if extraction fails
                    continue
            
        except Exception as e:
            log_error(f"Error extracting CBC results: {e}", source="MessageDataExtractor")
        
        return results
    
    @staticmethod
    def _extract_hgb_results(hl7_msg) -> list:
        """Extract HGB test results using HGB_RESULT_HL7 dictionary."""
        results = []
        try:
            try:
                obx_segments = hl7_msg.segments('OBX')
            except KeyError:
                return results
            if not obx_segments:
                return results
            
            # Iterate through HGB dictionary to extract values
            for test_key, test_config in HGB_RESULT_HL7['COLUMN_NAME'].items():
                # Skip SQL, MANUAL entries, and non-test fields
                if test_config in ['SQL', 'MANUAL']:
                    continue
                
                # Skip metadata fields that aren't actual test results
                if test_key in ['PATIENT_ID', 'REQ_DATE']:
                    continue
                
                try:
                    segment_type = test_config['S']
                    segment_number = int(test_config['N'])
                    field_number = int(test_config['F'])
                    
                    # Get the specific OBX segment
                    if segment_number < len(obx_segments):
                        obx = obx_segments[segment_number]
                        if len(obx) > field_number:
                            value = str(obx[field_number]).strip()
                            
                            # Only add if value is not empty and not duplicate
                            if value:
                                # Get unit from OBX field 6 if available
                                unit = ''
                                if len(obx) > 6:
                                    unit = str(obx[6]).strip()
                                
                                # Fallback to default unit
                                if not unit:
                                    unit = MessageDataExtractor.TEST_UNITS.get(test_key, '')
                                
                                # Get human-readable label
                                label = MessageDataExtractor.TEST_LABELS.get(test_key, test_key)
                                
                                # Check if not already in results (avoid duplicates from CBC)
                                if not any(r['key'] == test_key for r in results):
                                    results.append({
                                        'key': test_key,
                                        'label': label,
                                        'value': value,
                                        'unit': unit
                                    })
                except Exception:
                    # Skip this test if extraction fails
                    continue
            
        except Exception as e:
            log_error(f"Error extracting HGB results: {e}", source="MessageDataExtractor")
        
        return results

    @classmethod
    def parse_hl7(cls, raw_message) -> dict:
        """Alias for extract_display_data for backward compatibility."""
        return cls.extract_display_data(raw_message)


# Backward-compatibility alias
HL7MessageParser = MessageDataExtractor


class MessageCard(ft.Container):
    """Modern message card with human-readable HL7 display."""
    
    def __init__(self, message: dict, theme: ft.Theme, on_copy=None):
        super().__init__()
        self.message = message
        self.theme = theme
        self.timestamp = datetime.fromisoformat(message["timestamp"])
        self.on_copy_callback = on_copy
        self.is_expanded = False
        
        # Determine message direction and styling
        is_server = self.message["direction"] == "server"
        is_info = self.message["direction"] == "info"
        is_error = self.message["direction"] == "error"
        
        # Set colors based on message type
        if is_info:
            self.bg_color = ft.Colors.with_opacity(0.05, ft.Colors.GREY_700)
            self.text_color = ft.Colors.GREY_700
            self.icon = ft.Icons.INFO_OUTLINE
            self.icon_color = ft.Colors.GREY_700
        elif is_error:
            self.bg_color = ft.Colors.with_opacity(0.1, ft.Colors.RED_600)
            self.text_color = ft.Colors.RED_800
            self.icon = ft.Icons.ERROR_OUTLINE
            self.icon_color = ft.Colors.RED_600
        else:
            if is_server:
                self.bg_color = ft.Colors.with_opacity(0.08, self.theme.color_scheme.primary)
                self.text_color = self.theme.color_scheme.on_surface
                self.icon = ft.Icons.ARROW_DOWNWARD
                self.icon_color = self.theme.color_scheme.primary
            else:
                self.bg_color = ft.Colors.with_opacity(0.08, self.theme.color_scheme.secondary)
                self.text_color = self.theme.color_scheme.on_surface
                self.icon = ft.Icons.ARROW_UPWARD
                self.icon_color = self.theme.color_scheme.secondary
        
        # Parse HL7 message using project's parser
        self.parsed_hl7 = MessageDataExtractor.extract_display_data(self.message["message"])
        
        # Build the card UI
        self._build_card()
    
    def _build_card(self):
        """Build the message card UI."""
        
        # Header with direction icon and type
        header = ft.Row(
            controls=[
                ft.Icon(
                    self.icon,
                    size=16,
                    color=self.icon_color
                ),
                ft.Text(
                    f"{self.message['direction'].upper()}",
                    weight=ft.FontWeight.BOLD,
                    color=self.icon_color,
                    size=12
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.CONTENT_COPY,
                    icon_size=14,
                    tooltip="Copy message",
                    on_click=self._on_copy_click,
                    icon_color=self.theme.color_scheme.on_surface_variant
                ),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.START,
        )
        
        # Build human-readable content
        content_controls = []
        
        # Message type
        if self.parsed_hl7['message_type'] != 'Unknown':
            content_controls.append(
                ft.Row([
                    ft.Text("Type:", weight=ft.FontWeight.BOLD, size=13),
                    ft.Text(self.parsed_hl7['message_type'], size=13),
                ], spacing=8)
            )
        
        # Patient info
        if self.parsed_hl7['patient_id']:
            content_controls.append(
                ft.Row([
                    ft.Text("Patient ID:", weight=ft.FontWeight.BOLD, size=13),
                    ft.Text(self.parsed_hl7['patient_id'], size=13),
                ], spacing=8)
            )
        
        if self.parsed_hl7['patient_name']:
            content_controls.append(
                ft.Row([
                    ft.Text("Patient:", weight=ft.FontWeight.BOLD, size=13),
                    ft.Text(self.parsed_hl7['patient_name'], size=13),
                ], spacing=8)
            )
        
        # Test results (CBC/HGB)
        if self.parsed_hl7['test_results']:
            content_controls.append(
                ft.Text("Test Results:", weight=ft.FontWeight.BOLD, size=13, color=self.theme.color_scheme.primary)
            )
            
            # Show up to 5 test results
            for test in self.parsed_hl7['test_results'][:5]:
                # Format: Label (Key): Value Unit
                test_label = test.get('label', test.get('key', 'Unknown'))
                test_value = test.get('value', '')
                test_unit = test.get('unit', '')
                
                # Build the display text
                test_text = f"• {test_label}: {test_value}"
                if test_unit:
                    test_text += f" {test_unit}"
                
                content_controls.append(
                    ft.Text(test_text, size=12, color=self.text_color)
                )
            
            # Show count if more than 5 results
            if len(self.parsed_hl7['test_results']) > 5:
                content_controls.append(
                    ft.Text(
                        f"... and {len(self.parsed_hl7['test_results']) - 5} more",
                        size=11,
                        italic=True,
                        color=self.theme.color_scheme.on_surface_variant
                    )
                )
        
        # If no parsed data, show raw message preview
        if not content_controls:
            preview = self.message["message"][:100]
            if len(self.message["message"]) > 100:
                preview += "..."
            content_controls.append(
                ft.Text(
                    preview,
                    size=12,
                    color=self.text_color,
                    no_wrap=False,
                    max_lines=3
                )
            )
        
        message_content = ft.Column(
            controls=content_controls,
            spacing=4,
            tight=True
        )
        
        # Footer with timestamp
        footer = ft.Row(
            controls=[
                ft.Icon(
                    ft.Icons.ACCESS_TIME,
                    size=12,
                    color=self.theme.color_scheme.on_surface_variant
                ),
                ft.Text(
                    self.timestamp.strftime("%H:%M:%S"),
                    size=11,
                    color=self.theme.color_scheme.on_surface_variant,
                ),
                ft.Container(expand=True),
                ft.TextButton(
                    "View Raw",
                    icon=ft.Icons.CODE,
                    on_click=self._toggle_raw_view,
                    style=ft.ButtonStyle(
                        color=self.theme.color_scheme.primary,
                        padding=ft.Padding(8, 4, 8, 4)
                    )
                )
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.START,
        )
        
        # Main card container
        self.content = ft.Container(
            content=ft.Column(
                controls=[header, message_content, footer],
                spacing=12,
                tight=True
            ),
            bgcolor=self.bg_color,
            border=_safe_border_all(1, ft.Colors.with_opacity(0.1, self.icon_color)),
            border_radius=12,
            padding=16,
            animate=_safe_animation(200, getattr(ft, "AnimationCurve", None).EASE_OUT if hasattr(ft, "AnimationCurve") else None),
        )
        
        # Hover effect
        self.on_hover = self._on_hover
    
    def _on_hover(self, e):
        """Handle hover effect."""
        if e.data == "true":
            self.content.shadow = ft.BoxShadow(
                spread_radius=1,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                offset=ft.Offset(0, 2)
            )
        else:
            self.content.shadow = None
        self.update()
    
    def _on_copy_click(self, e):
        """Handle copy button click."""
        if self.on_copy_callback:
            self.on_copy_callback(self.message["message"])
    
    def _toggle_raw_view(self, e):
        """Show a dialog with the raw HL7 message."""
        # Get the page reference from the control hierarchy
        page = self.page
        if not page:
            # Try to get page from parent chain
            control = self
            while control and not page:
                control = getattr(control, 'parent', None)
                if control:
                    page = getattr(control, 'page', None)
        
        if not page:
            return
        
        # Create dialog content with formatted HL7 message
        raw_message_lines = self.message["message"].split('\n')
        
        # Create a column of text controls for each line with segment highlighting
        message_lines = []
        for line in raw_message_lines:
            if not line.strip():
                continue
            
            # Highlight segment type (first 3 characters before |)
            segment_type = line.split('|')[0] if '|' in line else line[:3]
            
            # Color code by segment type
            if segment_type == 'MSH':
                color = self.theme.color_scheme.primary
            elif segment_type == 'PID':
                color = self.theme.color_scheme.secondary
            elif segment_type in ['OBR', 'OBX']:
                color = ft.Colors.AMBER_700
            else:
                color = self.theme.color_scheme.on_surface
            
            message_lines.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(
                            segment_type,
                            weight=ft.FontWeight.BOLD,
                            color=color,
                            size=12,
                            font_family="Courier New"
                        ),
                        ft.Text(
                            line[len(segment_type):] if len(segment_type) < len(line) else '',
                            size=12,
                            color=self.theme.color_scheme.on_surface,
                            selectable=True,
                            font_family="Courier New"
                        )
                    ], spacing=0),
                    bgcolor=ft.Colors.with_opacity(0.03, self.theme.color_scheme.on_surface),
                    padding=ft.Padding(8, 4, 8, 4),
                    border_radius=4,
                    margin=_safe_margin_only(bottom=2)
                )
            )
        
        # Message metadata
        metadata = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("Direction:", weight=ft.FontWeight.BOLD, size=12),
                    ft.Text(self.message["direction"].upper(), size=12, color=self.icon_color),
                ], spacing=8),
                ft.Row([
                    ft.Text("Client:", weight=ft.FontWeight.BOLD, size=12),
                    ft.Text(f"{self.message['client_name']} ({self.message['client_address']})", size=12),
                ], spacing=8),
                ft.Row([
                    ft.Text("Timestamp:", weight=ft.FontWeight.BOLD, size=12),
                    ft.Text(self.timestamp.strftime("%Y-%m-%d %H:%M:%S"), size=12),
                ], spacing=8),
            ], spacing=6),
            bgcolor=ft.Colors.with_opacity(0.05, self.theme.color_scheme.on_surface),
            padding=12,
            border_radius=8,
            margin=ft.margin.only(bottom=12)
        )
        
        # Scrollable message content
        message_content = ft.Container(
            content=ft.ListView(
                controls=message_lines,
                spacing=0,
                height=400,
            ),
            border=_safe_border_all(1, self.theme.color_scheme.outline),
            border_radius=8,
            padding=8,
            bgcolor=ft.Colors.with_opacity(0.02, self.theme.color_scheme.on_surface)
        )
        
        # Copy button
        def copy_raw(e):
            page.set_clipboard(self.message["message"])
            # Update button text temporarily
            copy_btn.text = "Copied!"
            copy_btn.icon = ft.Icons.CHECK
            page.update()
            # Reset after 2 seconds safely on event loop
            async def reset_task():
                import asyncio
                await asyncio.sleep(2)
                copy_btn.text = "Copy All"
                copy_btn.icon = ft.Icons.CONTENT_COPY
                if getattr(dialog, "open", False):
                    try:
                        page.update()
                    except Exception:
                        pass

            if hasattr(page, "run_task"):
                page.run_task(reset_task)
            else:
                import asyncio
                try:
                    asyncio.create_task(reset_task())
                except RuntimeError:
                    pass
        
        copy_btn = ft.ElevatedButton(
            "Copy All",
            icon=ft.Icons.CONTENT_COPY,
            on_click=copy_raw,
            style=ft.ButtonStyle(
                bgcolor=self.theme.color_scheme.primary,
                color=ft.Colors.WHITE
            )
        )
        
        from gui.components import show_dialog, dismiss_dialog

        # Close button
        def close_dialog(e):
            dismiss_dialog(page, dialog)
        
        close_btn = ft.TextButton(
            "Close",
            on_click=close_dialog
        )
        
        # Create dialog
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.Icons.CODE, color=self.theme.color_scheme.primary),
                ft.Text("Raw HL7 Message", weight=ft.FontWeight.BOLD),
            ], spacing=8),
            content=ft.Container(
                content=ft.Column([
                    metadata,
                    message_content,
                ], spacing=0, tight=True),
                width=700,
            ),
            actions=[
                copy_btn,
                close_btn,
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        
        # Show dialog
        show_dialog(page, dialog)



class MessageTimestamp(ft.Container):
    """Display message timestamp with relative time."""
    
    def __init__(self, timestamp: datetime, theme: ft.Theme):
        super().__init__()
        self.timestamp = timestamp
        self.theme = theme
        
        # Calculate relative time
        now = datetime.now()
        diff = now - timestamp
        
        if diff.days > 0:
            relative = f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            relative = f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            relative = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            relative = "Just now"
        
        self.content = ft.Row(
            controls=[
                ft.Icon(
                    ft.Icons.SCHEDULE,
                    size=14,
                    color=theme.color_scheme.on_surface_variant
                ),
                ft.Text(
                    relative,
                    size=12,
                    color=theme.color_scheme.on_surface_variant
                ),
                ft.Text(
                    f"({timestamp.strftime('%H:%M:%S')})",
                    size=11,
                    color=theme.color_scheme.on_surface_variant,
                    italic=True
                )
            ],
            spacing=4
        )
        self.padding = ft.Padding(0, 8, 0, 8)


class DeviceConnectionBadge(ft.Container):
    """Status badge for device connection."""
    
    def __init__(self, device_name: str, device_address: str, is_connected: bool, theme: ft.Theme):
        super().__init__()
        self.device_name = device_name
        self.device_address = device_address
        self.is_connected = is_connected
        self.theme = theme
        
        # Status indicator
        status_color = theme.color_scheme.secondary if is_connected else ft.Colors.GREY_500
        status_text = "Connected" if is_connected else "Disconnected"
        
        self.content = ft.Row(
            controls=[
                ft.Container(
                    width=8,
                    height=8,
                    border_radius=4,
                    bgcolor=status_color,
                    animate=_safe_animation(300, getattr(ft, "AnimationCurve", None).EASE_IN_OUT if hasattr(ft, "AnimationCurve") else None)
                ),
                ft.Column(
                    controls=[
                        ft.Text(
                            device_name,
                            weight=ft.FontWeight.BOLD,
                            size=14,
                            color=theme.color_scheme.on_surface
                        ),
                        ft.Text(
                            f"{device_address} • {status_text}",
                            size=11,
                            color=theme.color_scheme.on_surface_variant
                        )
                    ],
                    spacing=2,
                    tight=True
                )
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.START
        )
        self.padding = 12
        self.border_radius = 8
        self.bgcolor = ft.Colors.with_opacity(0.05, theme.color_scheme.on_surface)
