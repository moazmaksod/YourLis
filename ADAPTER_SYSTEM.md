# Adapter System for Database and HL7 Device Integration

This document outlines the adapter-based architecture implemented to make the application more dynamic and extensible for various database backends and HL7-compliant medical devices.

## 1. Overview

The core idea is to decouple the main application logic from the specific implementations of database interactions and HL7 message processing. This is achieved through two primary abstract base classes (interfaces):

*   **`DatabaseAdapter` (`database.database_adapter.DatabaseAdapter`)**: Defines a standard interface for all database operations required by the application.
*   **`DeviceAdapter` (`hl7msghandel.device_adapter.DeviceAdapter`)**: Defines a standard interface for parsing HL7 messages from devices, extracting relevant data into a generic format, and creating HL7 response messages.

By coding to these interfaces, the application can easily switch between different database systems or support new medical devices by simply implementing a new concrete adapter and updating the configuration.

## 2. DatabaseAdapter

The `DatabaseAdapter` interface standardizes how the application interacts with databases.

### 2.1. Purpose
To provide a consistent set of methods for operations like connecting to a database, retrieving patient information, saving test results, etc., without exposing SQL or specific database schema details to the core application logic.

### 2.2. Creating a New DatabaseAdapter
To support a new database system (e.g., PostgreSQL, MySQL):

1.  **Create a new Python class** that inherits from `database.database_adapter.DatabaseAdapter`.
    ```python
    from database.database_adapter import DatabaseAdapter
    from typing import Dict, List, Any, Union # Ensure correct imports for type hints

    class MyNewDbAdapter(DatabaseAdapter):
        # ... implementation ...
        def connect(self, connection_params: Dict[str, Any]) -> None:
            # Implementation for connecting to the new database
            pass

        def disconnect(self) -> None:
            # Implementation for disconnecting
            pass

        def is_connected(self) -> bool:
            # Implementation for checking connection status
            return False # Placeholder

        def check_result_exists(self, patient_id: str) -> bool:
            # Implementation for checking if result exists
            return False # Placeholder

        def save_cbc_result(self, patient_id: str, result_data: Dict[str, Union[str, float, int]], request_date: str) -> None:
            # Implementation for saving CBC results
            pass

        def update_cbc_result(self, patient_id: str, result_data: Dict[str, Union[str, float, int]], request_date: str) -> None:
            # Implementation for updating CBC results
            pass

        def save_hgb_result(self, patient_id: str, result_data: Dict[str, Union[str, float, int]], request_date: str) -> None:
            # Implementation for saving HGB results
            pass

        def update_hgb_result(self, patient_id: str, result_data: Dict[str, Union[str, float, int]], request_date: str) -> None:
            # Implementation for updating HGB results
            pass

        def get_patient_info(self, patient_id: str) -> Union[Dict[str, Any], None]:
            # Implementation for fetching patient details
            return None # Placeholder

        def get_patient_test_request(self, patient_id: str) -> Union[Dict[str, Any], None]:
            # Implementation for fetching test request details
            return None # Placeholder

        def execute_procedure(self, procedure_name: str, params: Dict[str, Any]) -> Union[List[Dict[str, Any]], None]:
            # Implementation for executing a stored procedure
            return None # Placeholder
    ```
2.  **Implement all abstract methods** defined in `DatabaseAdapter`. These include:
    *   `connect(self, connection_params: Dict[str, Any]) -> None`: Establish connection.
    *   `disconnect(self) -> None`: Close connection.
    *   `is_connected(self) -> bool`: Check connection status.
    *   `check_result_exists(self, patient_id: str) -> bool`: Check if a result for a patient exists.
    *   `save_cbc_result(self, patient_id: str, result_data: Dict[str, Union[str, float, int]], request_date: str) -> None`: Save CBC results. (Corrected type hint from `Dict` to `Dict[str, Union[str, float, int]]`)
    *   `update_cbc_result(self, patient_id: str, result_data: Dict[str, Union[str, float, int]], request_date: str) -> None`: Update CBC results. (Corrected type hint)
    *   `save_hgb_result(self, patient_id: str, result_data: Dict[str, Union[str, float, int]], request_date: str) -> None`: Save HGB results. (Corrected type hint)
    *   `update_hgb_result(self, patient_id: str, result_data: Dict[str, Union[str, float, int]], request_date: str) -> None`: Update HGB results. (Corrected type hint)
    *   `get_patient_info(self, patient_id: str) -> Union[Dict[str, Any], None]`: Fetch patient details. (Corrected type hint from `Dict | None` to `Union[Dict[str, Any], None]`)
    *   `get_patient_test_request(self, patient_id: str) -> Union[Dict[str, Any], None]`: Fetch test request details. (Corrected type hint)
    *   `execute_procedure(self, procedure_name: str, params: Dict[str, Any]) -> Union[List[Dict[str, Any]], None]`: Execute a stored procedure. (Corrected type hint from `List | None` to `Union[List[Dict[str, Any]], None]` and params from `Dict` to `Dict[str, Any]`)
    *   *(Ensure method signatures and return types match the abstract definitions, using generic Python dictionaries for data exchange.)*
3.  **Internal Logic**: The adapter will be responsible for its own database connection management, SQL query construction (or ORM usage), and mapping between the generic data dictionaries and the specific database schema.

### 2.3. Configuration
To use your new adapter:
1.  Place your adapter class in an accessible Python module (e.g., `database.my_new_db_adapter.MyNewDbAdapter`).
2.  Update the `config.json` file (or use the application's settings UI if available) to set the `DATABASE_ADAPTER_CLASS` key:
    ```json
    {
        "DATABASE_ADAPTER_CLASS": "database.my_new_db_adapter.MyNewDbAdapter",
        // ... other settings ...
    }
    ```

## 3. DeviceAdapter

The `DeviceAdapter` interface standardizes how the application processes HL7 messages from different medical devices.

### 3.1. Purpose
To abstract the device-specific details of HL7 message structures (e.g., which segments/fields contain particular data, custom Z-segments, or specific HL7 versions/dialects) and provide a uniform way to parse messages and generate responses.

### 3.2. Creating a New DeviceAdapter
To support a new HL7-compliant device:

1.  **Create a new Python class** that inherits from `hl7msghandel.device_adapter.DeviceAdapter`.
    ```python
    from hl7msghandel.device_adapter import DeviceAdapter
    from typing import Any, Dict, Tuple, Union # Ensure correct imports

    class MyNewDeviceAdapter(DeviceAdapter):
        # ... implementation ...
        def parse_message(self, raw_hl7_message: str, direction: str = "incoming") -> Any:
            # Implementation for parsing raw HL7
            pass

        def get_message_type(self, parsed_hl7_message: Any) -> str:
            # Implementation for getting message type
            return "UNKNOWN" # Placeholder

        def get_patient_id_from_message(self, parsed_hl7_message: Any) -> Union[str, None]:
            # Implementation for extracting patient ID
            return None # Placeholder

        def extract_order_info(self, parsed_hl7_message: Any) -> Union[Dict[str, Any], None]:
            # Implementation for extracting order info
            return None # Placeholder

        def extract_result_data(self, parsed_hl7_message: Any) -> Tuple[Union[str, None], Union[str, None], Union[Dict[str, Any], None]]:
            # Implementation for extracting result data
            return None, None, None # Placeholder

        def create_ack_message(self, original_message_id: str, ack_code: str = "AA", error_message: Union[str, None] = None) -> str:
            # Implementation for creating ACK message
            return "" # Placeholder

        def create_order_response_message(self, original_message_id: str, patient_info: Dict[str, Any]) -> str:
            # Implementation for creating order response
            return "" # Placeholder
            
        def get_device_identifier(self, parsed_hl7_message: Any) -> Union[str, None]:
            # Implementation for extracting device identifier
            return None # Placeholder
    ```
2.  **Implement all abstract methods** defined in `DeviceAdapter`. Key methods include:
    *   `parse_message(self, raw_hl7_message: str, direction: str = "incoming") -> Any`: Parse raw HL7 string into a usable object (e.g., using the `python-hl7` library).
    *   `get_message_type(self, parsed_hl7_message: Any) -> str`: Extract message type (e.g., "ORU^R01").
    *   `get_patient_id_from_message(self, parsed_hl7_message: Any) -> Union[str, None]`: Extract patient ID. (Corrected type hint)
    *   `extract_order_info(self, parsed_hl7_message: Any) -> Union[Dict[str, Any], None]`: Extract data from order messages (e.g., ORM) into a generic dictionary. (Corrected type hint)
    *   `extract_result_data(self, parsed_hl7_message: Any) -> Tuple[Union[str, None], Union[str, None], Union[Dict[str, Any], None]]`: Extract test type, patient ID, and results from result messages (e.g., ORU) into a generic dictionary (e.g., `{'HGB': 12.3, 'WBC': 7.5}`). This is often the most complex method. (Corrected type hint)
    *   `create_ack_message(self, original_message_id: str, ack_code: str = "AA", error_message: Union[str, None] = None) -> str`: Generate an HL7 ACK message string. (Corrected type hint)
    *   `create_order_response_message(self, original_message_id: str, patient_info: Dict[str, Any]) -> str`: Generate an HL7 order response (e.g., ORR) from a generic `patient_info` dictionary. (Corrected type hint from `dict` to `Dict[str, Any]`)
    *   `get_device_identifier(self, parsed_hl7_message: Any) -> Union[str, None]`: Extract sending application/device name. (Corrected type hint)
    *   *(Ensure method signatures and return types match the abstract definitions.)*
3.  **Internal Logic**:
    *   The adapter will typically use an HL7 parsing library (like `python-hl7`).
    *   It will contain device-specific mapping logic, often as internal dictionaries, to translate HL7 field locations (e.g., OBX-3.1, OBX-5.1) to generic analyte names or data keys.
    *   It will handle the construction of HL7 message strings according to the device's expected format.

### 3.3. Configuration
To use your new device adapter:
1.  Place your adapter class in an accessible Python module (e.g., `hl7msghandel.my_new_device_adapter.MyNewDeviceAdapter`).
2.  Update the `config.json` file (or use the application's settings UI):
    *   Add a new entry to the `DEVICE_ADAPTER_CONFIG` dictionary. The key can be a unique name for your device.
        ```json
        {
            "DEVICE_ADAPTER_CONFIG": {
                "MyNewDevice": {
                    "class_path": "hl7msghandel.my_new_device_adapter.MyNewDeviceAdapter"
                    // Add any other device-specific config parameters here if needed
                },
                "Genrui_KT60": { // Existing example
                    "class_path": "hl7msghandel.genrui_kt60_adapter.GenruiKt60Adapter"
                }
            },
            "ACTIVE_DEVICE_ADAPTER_NAME": "MyNewDevice", // Set this to activate your new adapter
            // ... other settings ...
        }
        ```

## 4. Workflow Summary

1.  On startup, the application reads `DATABASE_ADAPTER_CLASS` and the active device adapter's `class_path` from the configuration.
2.  It uses `setting.config.load_adapter_class()` to dynamically load these adapter classes.
3.  Instances of the configured adapters are created. The `DatabaseAdapter` is connected.
4.  These adapter instances are passed to the core message handling logic (`server.incoming_data` and `hl7msghandel.hl7responder`).
5.  When an HL7 message is received:
    *   The active `DeviceAdapter` parses the message.
    *   The `DeviceAdapter` extracts data into generic Python dictionaries.
    *   The core logic uses the `DatabaseAdapter` to interact with the database using these generic dictionaries.
    *   The `DeviceAdapter` is used to create any necessary HL7 response messages.

This system allows for greater flexibility and easier integration of new technologies or device partners without requiring major changes to the core application code.
```
