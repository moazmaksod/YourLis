import unittest
from unittest.mock import patch, MagicMock, ANY
import queue # For queue.Empty
from threading import Thread # To check Thread.is_alive()

# Function to be tested
from server.incoming_data import handle_incoming_data

# Adapters that will be mocked (interfaces)
from database.database_adapter import DatabaseAdapter
from hl7msghandel.device_adapter import DeviceAdapter


class TestHandleIncomingData(unittest.TestCase):

    def setUp(self):
        self.mock_db_adapter = MagicMock(spec=DatabaseAdapter)
        self.mock_device_adapter = MagicMock(spec=DeviceAdapter)
        self.sample_message_bytes = b"MSH|^~\\&|APP|FAC|||Time||ORU^R01|MSGID001|P|2.3.1"
        self.decoded_sample_message = self.sample_message_bytes.decode(errors='ignore')

    @patch('server.incoming_data.Thread') # Patch Thread to control its execution
    @patch('server.incoming_data.generate_response_message') # Mock the function called within the thread
    def test_successful_message_processing(self, mock_generate_response, mock_thread_constructor):
        mock_parsed_msg = MagicMock(name="ParsedHL7Message")
        self.mock_device_adapter.parse_message.side_effect = [
            mock_parsed_msg, # First call for incoming message
            MagicMock(name="ParsedOutgoingHL7Message") # Second call for outgoing response validation
        ]
        
        # Mock the response payload from generate_response_message
        response_payload = {'response': 'HL7_RESPONSE_STR', 'sender': 'TestSender'}
        mock_generate_response.return_value = response_payload

        # Mock the queue to immediately put the response when the target function is called
        mock_queue_instance = MagicMock(spec=queue.Queue)
        
        # Simulate thread execution: when Thread is created, its target will be called.
        # We need to capture the target and its args to call it directly.
        def side_effect_thread_constructor(target, args):
            # args = (queue_instance, message_bytes, db_adapter, dev_adapter)
            # Call the target function (threaded_response_generation) directly
            # The first argument to target is the queue, which we've mocked.
            args[0].put(target(*args)) # Simulate putting result in queue
            
            # Return a mock thread that has join and is_alive methods
            mock_thread = MagicMock(spec=Thread)
            mock_thread.is_alive.return_value = False # Simulate thread finished
            return mock_thread
        
        mock_thread_constructor.side_effect = side_effect_thread_constructor
        
        # Call the function under test
        result_tuple = handle_incoming_data(self.sample_message_bytes, self.mock_db_adapter, self.mock_device_adapter)

        # Assertions
        self.assertIsNotNone(result_tuple)
        self.assertEqual(result_tuple[0], 'HL7_RESPONSE_STR')
        self.assertEqual(result_tuple[1], 'TestSender')

        # Check that device_adapter.parse_message was called for incoming message
        self.mock_device_adapter.parse_message.assert_any_call(self.decoded_sample_message, "Incoming")
        
        # Check that generate_response_message was called correctly by the thread's target
        mock_generate_response.assert_called_once_with(mock_parsed_msg, self.mock_db_adapter, self.mock_device_adapter)
        
        # Check that device_adapter.parse_message was called for outgoing response validation
        self.mock_device_adapter.parse_message.assert_any_call('HL7_RESPONSE_STR', "Outgoing")
        
        # Check Thread constructor calls
        mock_thread_constructor.assert_called_once()
        # Check that join was called on the thread mock
        mock_thread_constructor.return_value.join.assert_called_once_with(timeout=10)


    @patch('server.incoming_data.Thread')
    @patch('server.incoming_data.generate_response_message')
    def test_parsing_fails(self, mock_generate_response, mock_thread_constructor):
        self.mock_device_adapter.parse_message.return_value = None # Simulate parsing failure

        def side_effect_thread_constructor(target, args):
            args[0].put(target(*args))
            mock_thread = MagicMock(spec=Thread)
            mock_thread.is_alive.return_value = False
            return mock_thread
        mock_thread_constructor.side_effect = side_effect_thread_constructor
        
        result_tuple = handle_incoming_data(self.sample_message_bytes, self.mock_db_adapter, self.mock_device_adapter)

        self.assertIsNone(result_tuple)
        self.mock_device_adapter.parse_message.assert_called_once_with(self.decoded_sample_message, "Incoming")
        # generate_response_message should not be called if parsing fails within the thread's target
        mock_generate_response.assert_not_called() 

    @patch('server.incoming_data.Thread')
    @patch('server.incoming_data.generate_response_message')
    def test_generate_response_message_returns_none(self, mock_generate_response, mock_thread_constructor):
        mock_parsed_msg = MagicMock(name="ParsedHL7Message")
        self.mock_device_adapter.parse_message.return_value = mock_parsed_msg
        mock_generate_response.return_value = None # Simulate generate_response_message returning None

        def side_effect_thread_constructor(target, args):
            args[0].put(target(*args))
            mock_thread = MagicMock(spec=Thread)
            mock_thread.is_alive.return_value = False
            return mock_thread
        mock_thread_constructor.side_effect = side_effect_thread_constructor

        result_tuple = handle_incoming_data(self.sample_message_bytes, self.mock_db_adapter, self.mock_device_adapter)

        self.assertIsNone(result_tuple)
        mock_generate_response.assert_called_once_with(mock_parsed_msg, self.mock_db_adapter, self.mock_device_adapter)

    @patch('server.incoming_data.Thread')
    @patch('server.incoming_data.generate_response_message')
    def test_threaded_response_generation_exception(self, mock_generate_response, mock_thread_constructor):
        mock_parsed_msg = MagicMock(name="ParsedHL7Message")
        self.mock_device_adapter.parse_message.return_value = mock_parsed_msg
        mock_generate_response.side_effect = Exception("Simulated error in generate_response_message")

        def side_effect_thread_constructor(target, args):
            args[0].put(target(*args)) # This will effectively put the result of target (which includes exception handling)
            mock_thread = MagicMock(spec=Thread)
            mock_thread.is_alive.return_value = False
            return mock_thread
        mock_thread_constructor.side_effect = side_effect_thread_constructor

        result_tuple = handle_incoming_data(self.sample_message_bytes, self.mock_db_adapter, self.mock_device_adapter)
        
        self.assertIsNone(result_tuple) # Expect None because the thread's target function catches exceptions and puts None
        mock_generate_response.assert_called_once()

    @patch('server.incoming_data.Thread')
    def test_thread_join_timeout(self, mock_thread_constructor):
        # Simulate thread still being alive after join timeout
        mock_thread_instance = MagicMock(spec=Thread)
        mock_thread_instance.is_alive.return_value = True # Thread is still alive after join
        mock_thread_constructor.return_value = mock_thread_instance
        
        # Mock queue.get_nowait to raise Empty because the thread didn't put anything due to timeout (conceptually)
        # However, the code checks is_alive() first.
        
        result_tuple = handle_incoming_data(self.sample_message_bytes, self.mock_db_adapter, self.mock_device_adapter)
        
        self.assertIsNone(result_tuple)
        mock_thread_instance.join.assert_called_once_with(timeout=10)
        # queue.get_nowait() would not be called if is_alive is true after join.

    @patch('server.incoming_data.Thread')
    @patch('server.incoming_data.queue.Queue') # Mock the Queue class itself
    @patch('server.incoming_data.generate_response_message')
    def test_queue_empty_after_thread_finishes(self, mock_generate_response, mock_queue_class, mock_thread_constructor):
        # This tests the unlikely scenario where the thread finishes, but the queue is empty
        # which might indicate an issue with how the result is put into the queue.
        mock_parsed_msg = MagicMock(name="ParsedHL7Message")
        self.mock_device_adapter.parse_message.return_value = mock_parsed_msg
        
        # generate_response_message will be called, but we simulate its result not making it to the queue's get_nowait
        mock_generate_response.return_value = {'response': 'some_data', 'sender': 'some_sender'}

        mock_queue_instance = MagicMock(spec=queue.Queue)
        mock_queue_instance.get_nowait.side_effect = queue.Empty # Simulate queue being empty
        mock_queue_class.return_value = mock_queue_instance # Queue() call returns our mock instance

        def side_effect_thread_constructor(target, args):
            # Simulate target running but not successfully putting (or get_nowait is called too soon)
            # For this test, target *does* run and *does* put. The error is simulated at get_nowait.
            target_result = target(*args[1:]) # Call threaded_response_generation, excluding queue from its direct args
            # args[0].put(target_result) # Simulate the put
            mock_thread = MagicMock(spec=Thread)
            mock_thread.is_alive.return_value = False # Thread finished
            return mock_thread
        
        mock_thread_constructor.side_effect = side_effect_thread_constructor
        
        result_tuple = handle_incoming_data(self.sample_message_bytes, self.mock_db_adapter, self.mock_device_adapter)
        
        self.assertIsNone(result_tuple)
        mock_queue_instance.get_nowait.assert_called_once()


if __name__ == '__main__':
    unittest.main()
