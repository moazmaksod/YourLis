# 01_SYSTEM_MAP: System Topology, Process Boundaries & Architectural Map

**Repository:** `YourLIS` (HealthMesh Laboratory Information System)  
**Audit Phase:** Fresh Zero-Assumption Architectural Audit (Post-Sprint Baseline)  
**Date:** 2026-11-14  
**Auditor:** Independent Principal Software Architect (Swarm Synthesis)  
**Baseline Status:** Tests Passing (96 passed, 2 warnings)  

---

## 1. High-Level Executive Overview

YourLIS (internally branded as *HealthMesh*) is a hybrid clinical desktop Laboratory Information System (LIS) engineered for medical diagnostic automation, Complete Blood Count (CBC) hematology analyzers, patient reporting, and reference laboratory ("Send Out") logistics.

The system is organized around four core pillars:
1. **Desktop Presentation Layer**: A graphical interface built on [Flet](https://flet.dev/) (Flutter runtime for Python) providing responsive clinical operator dashboards, real-time device telemetry streaming, patient lookup, send-out logistics, and settings.
2. **REST & Push Telemetry Layer**: A local [FastAPI](https://fastapi.tiangolo.com/) service running on Uvicorn with WebSocket broadcasting, providing administrative, operational, and clinical data endpoints.
3. **Medical Device Connectivity**: An asynchronous TCP server implementing the Minimal Lower Layer Protocol (MLLP) framing standard (`\x0b`...`\x1c\x0d`) to ingest bidirectional HL7 v2.x clinical streams (e.g. `ORU^R01` observation results, `ORM^O01` test orders, and `ACK^O02` / `ACK^R01` acknowledgments) from automated hematology analyzers (e.g., Genrui KT-60).
4. **Relational Persistence**: Microsoft SQL Server accessed via `pyodbc` executing both dynamic SQL queries and vendor stored procedures through a thread-safe connection pool.

---

## 2. Process Architecture & Runtime Topology

The application operates as a multi-process desktop system on Windows (x86_64) using Python's `multiprocessing` module with `freeze_support()`.

```
+-------------------------------------------------------------------------------------------------------+
|                                      OPERATING SYSTEM HOST PROCESS                                    |
+-------------------------------------------------------------------------------------------------------+
|                                                                                                       |
|  [PARENT PROCESS: main.py]                                                                            |
|    |-- Working Directory Initialization: logs/, setting/, assets/                                     |
|    |-- Configuration Pre-Check & Fernet Crypto Key Validation: setting/config.py                      |
|    |-- Database Schema Validation & Migration: database/db_schema.py                                   |
|    |-- Dynamic Ephemeral Port Binding: main.py:generate_dynamic_port()                                |
|    |-- Configuration State Persistence: setting/config.json (Stores API_PORT)                         |
|    |-- Child Process Spawning via multiprocessing.Process:                                            |
|    |                                                                                                  |
|    +---> [CHILD PROCESS 1: Flet Desktop GUI (gui/main_flet.py)]                                       |
|    |       |-- Native Flutter/Flet UI Window (Dashboard, Stream, Patient, Send Out, CBC, Settings)   |
|    |       |-- WebSocket Telemetry Client -> ws://127.0.0.1:{API_PORT}/ws?token={API_TOKEN}          |
|    |       +-- REST Service Client (gui/api_methods.py) -> http://127.0.0.1:{API_PORT}/api/v1         |
|    |             * Architectural Debt: Direct DB queries executed as implicit fallback on API failure|
|    |                                                                                                  |
|    +---> [CHILD PROCESS 2: FastAPI & MLLP Device Server (api/app.py & server/server.py)]              |
|            |-- Uvicorn ASGI Server (127.0.0.1:{API_PORT})                                             |
|            |     |-- Lifespan Monitor: Background asyncio task (monitor_changes) polling state (1 Hz) |
|            |     |-- Protected Administrative Endpoints (/server/start, /server/stop, /server/messages)|
|            |     |-- Unauthenticated Status Endpoint (/server/status)                                 |
|            |     |-- Domain Clinical Endpoints (/api/v1/patients, /api/v1/cbc, /api/v1/send-out)       |
|            |     +-- WebSocket Telemetry Endpoint (/ws) with ConnectionManager broadcast loop         |
|            +-- In-Process Async TCP Socket Server (server/server.py)                                   |
|                  |-- Listening on SERVER_HOST:SERVER_PORT (e.g. 0.0.0.0:4000)                         |
|                  |-- MLLP Packet Slicer & Framer (\x0b...\x1c\x0d) in client_handler.py              |
|                  |-- Offloaded Worker Execution: asyncio.to_thread(_process_incoming_data_sync)       |
|                  |     |-- HL7 Parser & Validator (hl7msghandel/hl7parser.py)                         |
|                  |     |-- HL7-to-SQL Field Transformation (hl7msghandel/hl7fitsql.py)                |
|                  |     |-- Response / ACK Generator (hl7msghandel/hl7responder.py)                   |
|                  |     +-- Database Execution (database/sqlqueries.py via ConnectionPool)             |
|                  +-- In-Memory Circular Buffers: clients dict, communication_messages (maxlen=100)    |
|                                                                                                       |
+-------------------------------------------------------------------------------------------------------+
```

---

## 3. Subsystem Inventory & Responsibilities

| Subsystem | Directory / Module | Core Responsibilities | Key Dependencies |
| :--- | :--- | :--- | :--- |
| **Process Orchestration** | `main.py`, `build.py` | Multi-process bootstrapping, DB migration check, port allocation, Windows process supervision, PyInstaller build. | `multiprocessing`, `uvicorn`, `flet`, `httpx` |
| **Backend REST & WS** | `api/app.py` | HTTP REST API, token verification (`verify_token`), WebSocket streaming (`ConnectionManager`), background state monitor. | `fastapi`, `uvicorn`, `pydantic`, `starlette` |
| **TCP / MLLP Transport** | `server/server.py`, `server/client_handler.py`, `server/incoming_data.py`, `server/outcoming_data.py` | TCP socket server, MLLP framing state machine, packet reassembly, bounded buffer defense, ACK/NAK socket replies. | `asyncio`, `socket`, `threading` |
| **HL7 Processing Engine** | `hl7msghandel/hl7parser.py`, `hl7validator.py`, `hl7responder.py`, `hl7fitsql.py`, `hl7dictionary.py` | HL7 2.x parsing, segment validation, ACK/NAK generation, clinical order response generation, schema dictionary mapping. | `python-hl7`, `copy` |
| **Database & Pooling** | `database/sqlconnection.py`, `database/sqlqueries.py`, `database/sqlqueriesExe.py`, `database/db_schema.py`, `database/sqldbdictionary.py` | PyODBC connection pool (`ConnectionPool`), dynamic query builders (`INSERT`, `UPDATE`, `DELETE`), stored procedure executors, T-SQL migration runner. | `pyodbc` |
| **Configuration & Crypto** | `setting/config.py`, `setting/config.json`, `setting/key.key` | Configuration file I/O, cross-process file locking (`portalocker`), PBKDF2 HMAC SHA-256 key generation, Fernet password encryption. | `cryptography.fernet`, `portalocker`, `json` |
| **Logging & Redaction** | `log/logger.py`, `log/log_config.py` | Concurrent rotating file handler (`ConcurrentRotatingFileHandler`), clinical PHI redaction filter (`PHIRedactingFilter`), console output formatting. | `concurrent_log_handler`, `logging` |
| **Presentation Tier** | `gui/main_flet.py`, `gui/api_methods.py`, `gui/gui_methods.py`, `gui/components.py`, `gui/theme.py`, `gui/views/*` | Flet desktop application window, UI navigation, real-time telemetry rendering, patient search, CBC report preview/export, send-out logistics. | `flet`, `httpx`, `websockets` |
| **T-SQL Schemas** | `Sql_reqirement_querys/Reallab/*.sql` | MSSQL stored procedures and table definitions for patient info, CBC results, send-out logs, and destination reference laboratories. | Microsoft SQL Server (T-SQL) |
| **Automated Tests** | `tests/` (16 test files) | 96 unit and integration test cases covering API, DB connection pool, query builders, HL7 parsing/framing, server async pipeline, config, and GUI. | `pytest`, `pytest-asyncio`, `pytest-mock` |

---

## 4. End-to-End Clinical Data Flows

### 4.1 HL7 Observation Result Ingestion (`ORU^R01`)
```
[Analyzer: Genrui KT-60]
       |
       | 1. TCP Socket Stream (MLLP Enveloped: \x0bMSH|^~\&|...\x1c\x0d)
       v
[server/client_handler.py:handle_client_connection]
       |
       | 2. Reassemble TCP chunks in buffer; strip \x0b and locate \x1c\x0d
       | 3. Buffer threshold guard (len(buffer) <= 5 MB)
       v
[server/incoming_data.py:handle_incoming_data]
       |
       | 4. Offload to worker thread via asyncio.to_thread(_process_incoming_data_sync)
       v
[hl7msghandel/hl7parser.py:parse_hl7_message]
       |
       | 5. Parse segments via python-hl7; validate segment presence
       v
[hl7msghandel/hl7responder.py:handel_result_message]
       |
       | 6. Check if patient exists (PATIENT_EXIST_SQL) via exec_procedure_for
       | 7. If missing, insert patient metadata (PATIENT_INFO_SQL)
       | 8. Check if CBC result exists (RESULT_EXIST_SQL)
       | 9. Transform HL7 OBX fields via hl7fitsql.py:update_hl7_dictionary
       | 10. Execute data_insert_for(CBC_RESULT_SQL) or data_update_for
       v
[database/sqlconnection.py:ConnectionPool]
       |
       | 11. Acquire pooled PyODBC connection (get_db_connection_context)
       | 12. Execute parameterized query; commit transaction
       v
[hl7msghandel/hl7responder.py:generate_ack_message]
       |
       | 13. Construct MLLP ACK frame (\x0bMSH|...MSA|AA|{msg_id}...\x1c\r)
       v
[server/outcoming_data.py:send_outgoing_data]
       |
       | 14. Transmit ACK frame back over active TCP StreamWriter socket
       v
[Analyzer: Genrui KT-60 receives ACK]
```

### 4.2 Presentation & REST Service Data Flow
```
[User Action in Flet UI (e.g. Patient Search in gui/views/patient.py)]
       |
       | 1. User inputs search parameters and triggers search_handler()
       v
[gui/api_methods.py:fetch_patients_api]
       |
       | 2. Prepares HTTP GET request with query params
       | 3. Injects X-Internal-Token header (get_api_token())
       | 4. Dispatches via httpx.AsyncClient -> http://127.0.0.1:{API_PORT}/api/v1/patients
       v
[api/app.py:get_patients]
       |
       | 5. Validates authentication token via verify_token dependency
       | 6. Invokes database/sqlqueries.py:exec_procedure_for(PATIENT_SEARCH_SQL, params)
       v
[database/sqlqueries.py:exec_procedure_for -> exec_procedure_sync]
       |
       | 7. Offloaded to worker thread via asyncio.to_thread
       | 8. Formats parameters: EXEC GetPatientInfo @PATIENT_ID=?, @PATIENT_NAME=?, ...
       v
[database/sqlconnection.py:ConnectionPool]
       |
       | 9. Acquires pooled PyODBC connection; executes cursor.execute()
       | 10. Fetches results, serializes rows to list[dict], returns to FastAPI
       v
[HTTP 200 JSON Response -> gui/api_methods.py -> patient.py:PaginatedDataTable]
       |
       | 11. Table updates controls and invokes page.update()
```

### 4.3 Real-Time Telemetry & Status Streaming
```
[TCP Analyzer Connects / Frame Arrives]
       |
       | 1. client_handler.py updates clients_with_names dict & communication_messages deque
       v
[api/app.py:monitor_changes (Background Lifespan Task)]
       |
       | 2. Polls internal state every 1.0 second
       | 3. Detects state delta (server running state, connected clients, new message count)
       | 4. Broadcasts JSON payload to all active WebSocket connections in manager.active_connections
       v
[gui/api_methods.py:listen_to_updates (WebSocket Client)]
       |
       | 5. Receives JSON packet over ws://127.0.0.1:{API_PORT}/ws?token={token}
       | 6. Dispatches to page.pubsub.send_all(data)
       v
[gui/main_flet.py & gui/views/stream.py]
       |
       | 7. PubSub subscribers trigger UI card updates & server status indicator badge
```

---

## 5. Architectural Boundaries & Cross-Cutting Invariants

1. **Security & Cryptography**:
   - `HEALTHMESH_SECRET_KEY` environment variable takes precedence for Fernet key derivation; falls back to `setting/key.key`.
   - Sensitive database credentials (`DB_USER`, `DB_PASSWORD`, `API_TOKEN`) stored encrypted in `setting/config.json`.
   - HTTP endpoints requiring clinical data or device control protected by bearer token matching via `secrets.compare_digest`.
2. **Concurrency & Thread Safety**:
   - MLLP socket connections run on the `asyncio` event loop. All blocking PyODBC database I/O is offloaded to worker threads via `asyncio.to_thread`.
   - Configuration read/write synchronization utilizes cross-process file locking via `portalocker.Lock` alongside in-process `threading.Lock`.
3. **Database Resource Pooling**:
   - PyODBC native pooling enabled (`pyodbc.pooling = True`).
   - Managed `ConnectionPool` provides pre-ping connection validation (`SELECT 1`) and automatic eviction of broken sockets.
