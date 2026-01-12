# YourLIS Developer Guide

This guide provides technical information for developers looking to understand, maintain, or extend the YourLIS project.

## 1. System Architecture

YourLIS follows a multi-process architecture to ensure stability and responsiveness:

- **GUI Process (Flet)**: Handles all user interactions and data visualization.
- **Backend Process (FastAPI)**: Provides a REST API for internal communication and external integrations.
- **TCP Server Process**: An asynchronous server that handles TCP connections from medical laboratory devices (e.g., CBC analyzers).

### Data Flow
1. **Device** sends HL7 message via TCP to the **TCP Server**.
2. **HL7 Handler** parses the message and stores results in the **SQL Database**.
3. **GUI** fetches data from the database or via the **FastAPI** endpoints to update the display in real-time.

## 2. Project Structure

- `main.py`: The entry point that orchestrates the startup of GUI, API, and Server processes.
- `gui/`: Contains Flet-based UI components and views.
    - `views/`: Individual pages like Dashboard, Patient, Send Out, etc.
    - `components.py`: Reusable UI elements (Side Menu, Footer, etc.).
- `api/`: FastAPI application defining internal REST endpoints.
- `server/`: TCP Server logic and client handling.
- `hl7msghandel/`: Specific logic for parsing, validating, and responding to HL7 messages.
- `database/`: Database schema definitions, connection logic, and SQL requirements.
- `setting/`: Configuration management (`config.py`).
- `log/`: Logging utilities.

## 3. API Reference

The FastAPI server runs locally (usually on a dynamic port) to facilitate communication between the GUI and the background server tasks.

### Endpoints:
- `GET /server/status`: Returns current server state and connected clients.
- `GET /server/messages`: Retrieves recent communication logs for the Stream view.
- `POST /server/start`: Triggers the device server to start listening.
- `POST /server/stop`: Gracefully shuts down the device server.

## 4. HL7 Integration

The `hl7msghandel` module is critical for device communication. It includes:
- `hl7parser.py`: Breaks down raw HL7 strings into segments and fields.
- `hl7responder.py`: Generates ACK (Acknowledgement) messages to signal successful receipt to devices.
- `hl7fitsql.py`: Maps HL7 fields to database columns for automated result entry.

## 5. Database Setup

YourLIS uses a relational database (SQL Server) to store all laboratory data. 
- **Schema**: Defined in `database/db_schema.py`.
- **Startup Check**: `main.py` performs a `database_startup_check` to ensure all tables and stored procedures exist before launching the GUI.

## 6. Development Workflow

### Adding a New View
1. Create a new file in `gui/views/`.
2. Define a function that returns a Flet component.
3. Register the view in `gui/main_flet.py` within the `on_side_menu_change` handler and `side_menu` component.

### Modifying HL7 Logic
1. Update `hl7dictionary.py` if adding support for new HL7 segments.
2. Adjust `hl7parser.py` or specific device handlers to process new data types.

---
*Maintained by the YourLIS Development Team.*
