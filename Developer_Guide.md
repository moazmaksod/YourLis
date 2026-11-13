# YourLIS Developer Guide

This guide provides technical information for developers looking to understand, maintain, or extend the **YourLIS** (HealthMesh) clinical laboratory information system.

---

## 1. System Architecture

YourLIS follows an asynchronous, decoupled multi-service architecture designed for clinical reliability, real-time medical device ingestion, and data security:

- **GUI Process (Flet)**: Handles all clinical user interactions, test order visualization, and real-time analyzer monitoring. Decoupled from direct database access.
- **Backend Service (FastAPI)**: Provides internal and external REST API endpoints (`/api/v1/...`) for patient management, test requests, send-out tracking, and server orchestration.
- **Async TCP Server Process**: An asynchronous `asyncio` TCP server that implements the Minimal Lower Layer Protocol (MLLP) to communicate with laboratory analyzers (e.g., CBC hematology instruments).
- **Database Layer (SQL Server / PyODBC)**: Centralized connection pooling and DAO layer managing relational schema storage with full schema immutability.

```
+--------------------------------------------------------------+
|                    Clinical User Interface                   |
|                   (Flet Desktop Application)                 |
+------------------------------+-------------------------------+
                               | HTTP / REST (gui/api_methods)
                               v
+--------------------------------------------------------------+
|                     FastAPI Backend Layer                    |
|          /api/v1/patients | /api/v1/send-out | /server       |
+------------------------------+-------------------------------+
                               | DAO / Async Offload
                               v
+--------------------------------------------------------------+
|               Centralized PyODBC ConnectionPool              |
|        (Native Pooling, Health Check SELECT 1, Recycling)    |
+------------------------------+-------------------------------+
                               |
                               v
+--------------------------------------------------------------+
|                    Microsoft SQL Server                      |
+--------------------------------------------------------------+
                               ^
                               | Async Execution / Thread Offload
+------------------------------+-------------------------------+
|                      HL7 Responder / Parser                  |
+------------------------------+-------------------------------+
                               ^ MLLP Frames
                               |
+--------------------------------------------------------------+
|                   Async MLLP TCP Server                      |
|         (Port 5600, Framed Buffer, 5MB Max Capacity)         |
+------------------------------+-------------------------------+
                               ^
                               | TCP / MLLP (0x0B ... 0x1C 0x0D)
+------------------------------+-------------------------------+
|                  Lab Analyzers (e.g., Genrui CBC)            |
+--------------------------------------------------------------+
```

---

## 2. Project Structure

- `main.py`: Application entry point orchestrating the startup of GUI, API, and Server processes with clean lifecycle management.
- `gui/`: Flet-based UI components and views.
  - `views/`: Dedicated clinical views (Dashboard, Patient, CBC Report, Send Out, Device Stream, Settings).
  - `api_methods.py`: Service client isolating GUI views from raw SQL; handles all HTTP requests to FastAPI endpoints.
  - `components.py`: Shared UI elements (Navigation side menu, status headers, footers).
- `api/`: FastAPI application defining clinical REST endpoints and lifespan handlers.
  - `app.py`: Route definitions, CORS middleware, and server state management.
- `server/`: Asynchronous TCP server and transport logic.
  - `server.py`: Async server lifecycle, client tracking, and background task management.
  - `client_handler.py`: MLLP frame boundary parsing, buffer protection, and analyzer dispatching.
- `hl7msghandel/`: Parsing, validating, and generating HL7 messages.
  - `hl7parser.py`: Parses raw HL7 segments into structured objects.
  - `hl7responder.py`: Generates MLLP-framed ACK (`ACK^R01`), ORR (`ORR^O02`), and NAK (`MSA|AE`/`MSA|AR`) responses.
  - `hl7fitsql.py`: Maps clinical HL7 fields to database records with schema immutability.
- `database/`: Database connectivity and queries.
  - `sqlconnection.py`: Thread-safe `ConnectionPool` with native PyODBC pooling and connection validation.
  - `sqlqueries.py`: SQL templates and parameterized query execution with schema immutability.
  - `sqlqueriesExe.py`: Database execution wrapper with PHI masking.
- `setting/`: Configuration security and persistence.
  - `config.py`: Fernet encryption key isolation, environment variable support, and atomic file persistence.
- `log/`: Logging infrastructure.
  - `log_config.py`: Structured logging with automated `PHIRedactingFilter`.
- `.antigravity/rules.md`: Architectural invariants and permanent engineering guardrails.

---

## 3. Core Architectural Subsystems

### 3.1 Database Connection Pooling & Schema Immutability
- **Connection Pooling**: Implemented via `database/sqlconnection.py:ConnectionPool`. Native PyODBC pooling is enabled (`pyodbc.pooling = True`), and connections are checked via a lightweight `SELECT 1` ping before being handed to callers. Corrupted connections are automatically evicted.
- **Schema Immutability**: All SQL mapping functions in `database/sqlqueries.py` (`data_insert_for`, `data_update_for`) enforce deep copying of schema dictionaries:
  ```python
  column_name = copy.deepcopy(db_schema["COLUMN_NAME"])
  ```
  This guarantees that partial HL7 messages never permanently delete column definitions from global runtime state.

### 3.2 MLLP Framing & TCP Resilience
- **Framing Specification**: Conforms to standard HL7 MLLP:
  - Start Byte: `0x0B` (`\x0b`)
  - End Bytes: `0x1C 0x0D` (`\x1c\r` or `\x1c\x0d`)
- **Stream Reassembly**: Buffers partial TCP chunks until a complete MLLP frame is received. Supports multiple coalesced HL7 messages received in a single TCP packet.
- **Memory Protection**: Enforces `MAX_BUFFER_SIZE = 5 * 1024 * 1024` (5MB). If an instrument transmits un-framed data exceeding 5MB, the buffer is purged and the connection is safely reset.
- **Non-Fatal Error Handling**: On parse or database errors, the server replies with an HL7 NAK (`MSA|AE` or `MSA|AR`) retaining the message control ID (`MSH-10`), keeping the TCP connection active so instruments do not disconnect.

### 3.3 PHI/PII & Credential Log Sanitization
- All log records pass through `log/log_config.py:PHIRedactingFilter`.
- Patient identifiers (names, national IDs, medical record numbers) and database passwords in query strings or payloads are masked (e.g. `J***E`, `********`).
- Clinical traceability identifiers—specifically `MSH-10` message control IDs—are explicitly preserved in logs to allow auditing and regulatory traceability.

### 3.4 Service Boundary & GUI Decoupling
- GUI views in `gui/views/` (such as `patient.py`, `cbc_report.py`, and `send_out.py`) communicate exclusively through `gui/api_methods.py`.
- No direct SQL queries are executed from the presentation layer.
- If the backend service is temporarily unavailable, GUI components display structured error snackbars or dialogs rather than throwing uncaught exceptions.

### 3.5 Secure Configuration & Atomic Persistence
- Encryption keys are decoupled from configuration ciphertext. The system checks the `HEALTHMESH_SECRET_KEY` environment variable first before falling back to isolated key storage.
- All configuration file writes (`setting/config.py:save_config`) use atomic file replacement (`tempfile` + `os.replace`) guarded by a `threading.Lock()`.
- API and GUI configuration views return masked credentials (`********`) to prevent over-the-shoulder leaks.

### 3.6 UI Performance & Memory Management
- **Bounded Stream State**: The device message stream (`gui/views/stream.py`) enforces a strict buffer limit (`MAX_STREAM_MESSAGES = 200`). When exceeded, the oldest messages are pruned to prevent memory bloat.
- **Incremental Updates**: Incoming messages are prepended to the UI container directly without rebuilding the entire message list control tree.
- **Debounced Search**: Search filtering is debounced by 300ms to eliminate UI stuttering during typing.
- **Overlay Cleanup**: Dialogs and snackbars are explicitly evicted from `page.overlay` upon dismissal to eliminate memory leaks.

---

## 4. REST API Reference

The FastAPI service runs on a configurable port (default dynamic or 8000):

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/server/status` | Returns TCP server run state and connected clients |
| `GET` | `/server/messages` | Retrieves recent communication events for stream display |
| `POST` | `/server/start` | Starts the async MLLP device ingestion server |
| `POST` | `/server/stop` | Gracefully shuts down the MLLP device server |
| `GET` | `/api/v1/patients` | Search and filter registered laboratory patients |
| `GET` | `/api/v1/patients/{id}/cbc` | Retrieve CBC laboratory results for a given patient |
| `GET` | `/api/v1/send-out` | List external send-out tests with status filters |
| `GET` | `/api/v1/send-out/destinations` | List registered reference laboratories |
| `POST` | `/api/v1/send-out/{id}/financials` | Update financial charges and cost for send-outs |
| `POST` | `/api/v1/send-out/{id}/mark-sent` | Mark test as sent to reference laboratory |
| `GET` | `/config` | Retrieve non-sensitive system configuration |
| `POST` | `/config` | Atomically update system configuration |

---

## 5. Testing & Verification

The test suite covers unit, contract, and integration tests across all architectural layers.

```bash
# Run the entire automated test suite
uv run pytest -v

# Or with virtual environment activated:
pytest -v
```

All 86 test cases must pass before any pull request or code change is merged.

---

## 6. Architectural Rules

Refer to [`.antigravity/rules.md`](file:///.antigravity/rules.md) for the mandatory architectural invariants.
