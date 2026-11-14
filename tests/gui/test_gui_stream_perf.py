import pytest
import time
from unittest.mock import MagicMock
import flet as ft
from gui.views.stream import DevicePanel, MAX_STREAM_MESSAGES
from gui.views.stream_controls import SearchBar


def test_device_panel_bounds_messages_to_max():
    mock_page = MagicMock()
    mock_theme = MagicMock()
    mock_theme.color_scheme.outline = "grey"
    mock_theme.color_scheme.on_surface = "black"

    panel = DevicePanel("TestDevice", "127.0.0.1", mock_page, mock_theme)

    # Generate 250 test messages
    messages = [
        {
            "timestamp": f"2026-01-01T{i // 3600:02d}:{(i % 3600) // 60:02d}:{i % 60:02d}",
            "client_name": "TestDevice",
            "client_address": "127.0.0.1",
            "message": f"MSH|^~\\&|Analyzer||||20260101||ORU^R01|{i}|P|2.3.1\r",
            "direction": "device",
        }
        for i in range(250)
    ]

    panel.update_messages(messages)

    # Ensure buffer is strictly bounded to MAX_STREAM_MESSAGES (200)
    assert len(panel.messages) == MAX_STREAM_MESSAGES
    # Ensure it keeps the latest messages (index 50 through 249)
    last_expected_ts = f"2026-01-01T{249 // 3600:02d}:{(249 % 3600) // 60:02d}:{249 % 60:02d}"
    assert panel.messages[-1]["timestamp"] == last_expected_ts


def test_device_panel_incremental_card_updates():
    mock_page = MagicMock()
    mock_theme = MagicMock()
    mock_theme.color_scheme.outline = "grey"
    mock_theme.color_scheme.on_surface = "black"

    panel = DevicePanel("TestDevice", "127.0.0.1", mock_page, mock_theme)

    # Initial 5 messages
    initial_msgs = [
        {
            "timestamp": f"2026-01-01T12:00:0{i}",
            "client_name": "TestDevice",
            "client_address": "127.0.0.1",
            "message": f"Message {i}",
            "direction": "device",
        }
        for i in range(5)
    ]
    panel.update_messages(initial_msgs)
    assert len(panel.message_list.controls) == 5

    # Incremental append of 1 new message
    updated_msgs = list(initial_msgs) + [
        {
            "timestamp": "2026-01-01T12:00:10",
            "client_name": "TestDevice",
            "client_address": "127.0.0.1",
            "message": "Message 5 (New)",
            "direction": "device",
        }
    ]
    result = panel.update_messages(updated_msgs)
    assert result is True
    assert len(panel.message_list.controls) == 6


def test_search_bar_debounce():
    mock_theme = MagicMock()
    callback_calls = []

    def on_search(query):
        callback_calls.append(query)

    search_bar = SearchBar(mock_theme, on_search_change=on_search, debounce_ms=50)

    # Simulate rapid typing: "a", "ab", "abc" within 20ms
    search_bar.search_field.value = "a"
    search_bar._on_search_change(None)

    search_bar.search_field.value = "ab"
    search_bar._on_search_change(None)

    search_bar.search_field.value = "abc"
    search_bar._on_search_change(None)

    # Immediately, callback should NOT have fired yet
    assert len(callback_calls) == 0

    # Wait for debounce duration
    time.sleep(0.08)

    # Debounce fired exactly once with final value
    assert len(callback_calls) == 1
    assert callback_calls[0] == "abc"


def test_overlay_dialog_cleanup():
    mock_page = MagicMock()
    mock_page.overlay = []

    from gui.views.stream_controls import StreamToolbar

    mock_theme = MagicMock()
    toolbar = StreamToolbar(mock_page, mock_theme, on_clear_messages=lambda: None)

    # Trigger clear messages confirmation dialog
    toolbar._on_clear_messages(None)
    mock_page.open.assert_called_once()
    dialog = mock_page.open.call_args[0][0]
    assert dialog.title.value == "Clear Messages"

    # Click Cancel on the dialog
    cancel_button = dialog.actions[0]
    cancel_button.on_click(None)

    # Dialog should be closed via page.close
    mock_page.close.assert_called_once_with(dialog)


def test_overlay_dialog_cleanup_fallback():
    # Legacy fallback: page without open/close methods
    mock_page = MagicMock(spec=["overlay", "update"])
    mock_page.overlay = []

    from gui.views.stream_controls import StreamToolbar

    mock_theme = MagicMock()
    toolbar = StreamToolbar(mock_page, mock_theme, on_clear_messages=lambda: None)

    toolbar._on_clear_messages(None)
    assert len(mock_page.overlay) == 1
    dialog = mock_page.overlay[0]

    cancel_button = dialog.actions[0]
    cancel_button.on_click(None)

    assert len(mock_page.overlay) == 0
