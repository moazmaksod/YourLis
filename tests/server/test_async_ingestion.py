import asyncio
import time
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from server.incoming_data import handle_incoming_data, _process_incoming_data_sync
from server.client_handler import handle_client_connection, MESSAGE_START_MARKER, MESSAGE_END_MARKER


@pytest.mark.asyncio
async def test_slow_hl7_handler_does_not_block_event_loop_ticks(mock_logger):
    """
    Verify that an HL7 handler undergoing slow synchronous processing
    (e.g. DB lookups, segment parsing) runs in a worker thread and
    does NOT block concurrent event loop ticks.
    """
    def slow_sync_processor(message):
        time.sleep(0.15)
        return ("ACK_RESPONSE", "Analyzer_KT60")

    ticks = 0

    async def tick_counter():
        nonlocal ticks
        for _ in range(5):
            await asyncio.sleep(0.02)
            ticks += 1

    with patch("server.incoming_data._process_incoming_data_sync", side_effect=slow_sync_processor):
        # Run the slow HL7 handler and the event loop tick counter concurrently
        ingestion_task = asyncio.create_task(handle_incoming_data(b"dummy_message", timeout=5.0))
        counter_task = asyncio.create_task(tick_counter())

        result, _ = await asyncio.gather(ingestion_task, counter_task)

        # Event loop ticked multiple times while the slow sync processor ran
        assert ticks >= 4
        assert result == ("ACK_RESPONSE", "Analyzer_KT60")


@pytest.mark.asyncio
async def test_slow_hl7_handler_timeout_non_blocking(mock_logger):
    """
    Verify that if HL7 processing exceeds timeout, it times out cleanly
    without blocking the loop or raising an unhandled exception.
    """
    def hanging_sync_processor(message):
        time.sleep(0.5)
        return ("ACK_RESPONSE", "Analyzer_KT60")

    with patch("server.incoming_data._process_incoming_data_sync", side_effect=hanging_sync_processor):
        start_time = time.time()
        result = await handle_incoming_data(b"dummy_message", timeout=0.08)
        elapsed = time.time() - start_time

        assert result is None
        # Should have timed out quickly around ~0.08s, well before the 0.5s sleep
        assert elapsed < 0.35


@pytest.mark.asyncio
async def test_concurrent_client_connections_non_blocking(mock_logger):
    """
    Verify that two concurrent TCP client connections can be processed concurrently
    without a slow client blocking subsequent clients.
    """
    async def mock_handle_incoming_data(message, timeout=10.0):
        if b"SLOW" in message:
            await asyncio.sleep(0.1)
            return ("ACK_SLOW", "Device1")
        else:
            await asyncio.sleep(0.01)
            return ("ACK_FAST", "Device2")

    completion_order = []

    async def simulate_client(client_id, message_content):
        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.get_extra_info.return_value = ("127.0.0.1", 10000 + client_id)
        mock_writer.wait_closed = AsyncMock()

        # Provide framed message then EOF
        raw_msg = MESSAGE_START_MARKER + message_content + MESSAGE_END_MARKER
        mock_reader.read = AsyncMock(side_effect=[raw_msg, b""])

        with patch("server.client_handler.handle_incoming_data", side_effect=mock_handle_incoming_data):
            with patch("server.client_handler.send_outgoing_data", return_value=None):
                await handle_client_connection(mock_reader, mock_writer)
                completion_order.append(client_id)

    # Launch slow client first, fast client second
    slow_task = asyncio.create_task(simulate_client(1, b"SLOW_MESSAGE"))
    fast_task = asyncio.create_task(simulate_client(2, b"FAST_MESSAGE"))

    await asyncio.gather(slow_task, fast_task)

    # Fast client must finish before slow client even though slow started first
    assert completion_order == [2, 1]

