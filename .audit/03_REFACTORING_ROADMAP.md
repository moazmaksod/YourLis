# 03_REFACTORING_ROADMAP: Action Plan & Implementation Blueprint

**Repository:** `YourLIS` (HealthMesh Laboratory Information System)  
**Auditor:** Lead Software Architect  
**Date:** 2026-11-13  
**Status:** Implementation-Ready Execution Blueprint  

---

## Refactoring Overview & Phasing Strategy

This roadmap details the prioritized, step-by-step implementation tasks required to stabilize the codebase, eliminate clinical data corruption, restore runtime reliability, and position the architecture for feature scalability in Phase 2.

```
+-----------------------------------------------------------------------------------------------+
|                                  REFACTORING PHASING ROADMAP                                  |
+-----------------------------------------------------------------------------------------------+
|                                                                                               |
|  [PHASE 0: EMERGENCY STABILITY & DATA INTEGRITY] (P0)                                        |
|    |-- [DONE] Task 0.1: Prevent Global Schema Dictionary Mutation (Stop Clinical Data Loss)    |
|    |-- [DONE] Task 0.2: Eliminate Event-Loop Freeze in TCP Ingestion Pipeline                  |
|    |-- [DONE] Task 0.3: Resolve Fatal Startup NameError (`db_conn_fail_dialog`)                |
|    |-- [DONE] Task 0.4: Fix Fatal ImportError in Live Stream CSV Export                        |
|    +-- [DONE] Task 0.5: Redact PHI / PII from Application Logs (HIPAA / GDPR Compliance)       |
|                                                                                               |
|  [PHASE 1: PERSISTENCE, CONCURRENCY & CONNECTION RESILIENCE] (P1)                             |
|    |-- [DONE] Task 1.1: Implement Centralized Connection Pooling for PyODBC                    |
|    |-- [DONE] Task 1.2: Eliminate Async/Sync Fake Coroutines & Unblock GUI Event Loop         |
|    |-- [DONE] Task 1.3: Fix Corrupted String Fallback on Missing HL7 Segments                  |
|    |-- [DONE] Task 1.4: Resolve Server Shutdown Task Mutation & Socket Leak                   |
|    +-- [DONE] Task 1.5: Fix TOCTOU Port Allocation Race Condition                              |
|                                                                                               |
|  [PHASE 2: PROTOCOL RIGOR, SECURITY & SERVICE BOUNDARIES] (P2)                                |
|    |-- [DONE] Task 2.1: Enforce Strict MLLP Framing (`0x1C 0x0D`) & Bounded Ingestion Buffer    |
|    |-- [DONE] Task 2.2: Implement Resilient Connection Handling (NAK on Error, Keep Socket Alive)   |
|    |-- [DONE] Task 2.3: Unify Presentation Layer Behind Service / API Layer                          |
|    |-- [DONE] Task 2.4: Secure Secrets, Fernet Keys, & File I/O Concurrency                           |
|    +-- [DONE] Task 2.5: Modernize FastAPI Lifespan & Add API Security Middleware                     |
|                                                                                               |
|  [PHASE 3: UI PERFORMANCE, TEST HARNESS & CODE CLEANUP] (P3)                                  |
|    |-- [DONE] Task 3.1: Virtualize & Debounce Live Stream Rendering                                  |
|    |-- [DONE] Task 3.2: Clean Up Overlay Memory Leaks in Dialogs                                     |
|    |-- [DONE] Task 3.3: Remove Dead Files & Deprecated Attributes                                    |
|    +-- [DONE] Task 3.4: Construct Automated End-to-End GUI & HL7 Pipeline Test Suite                 |
|                                                                                               |
+-----------------------------------------------------------------------------------------------+
```

---

## Phase 0: Emergency Stability & Data Integrity (P0 - Immediate Action)

### [DONE] Task 0.1: Prevent Global Schema Dictionary In-Place Mutation
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `database/sqlqueries.py:38-43`, `database/sqlqueries.py:84-96`
- **Root Cause:** Direct in-place deletion (`del column_name[key]`) alters shared global schema references in `sqldbdictionary.py`, causing permanent data loss for subsequent patients.
- **Implementation Notes:**
  1. Deep-copied `column_name` and `condition` in both `data_insert_for` and `data_update_for`.
  2. Employed non-mutating dictionary comprehensions to isolate columns present in incoming HL7 payloads without modifying the caller's schema definitions.
  3. Added regression tests in `tests/database/test_sqlqueries.py` (`test_data_insert_for_schema_immutability` and `test_data_update_for_schema_immutability`) verifying that partial HL7 messages leave schemas intact for subsequent full-field insertions.

### [DONE] Task 0.2: Eliminate Event-Loop Freeze in TCP Ingestion Pipeline
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `server/client_handler.py:123`, `server/incoming_data.py:10-63`, `hl7msghandel/hl7responder.py`
- **Root Cause:** `response_queue.get(timeout=10)` blocks the main asyncio thread for up to 10 seconds per incoming frame. Spawning raw unmanaged `threading.Thread` adds overhead without providing async concurrency.
- **Implementation Notes:**
  1. Converted `handle_incoming_data(message, timeout=10.0)` into an async coroutine delegating parsing and DB execution to `asyncio.to_thread(_process_incoming_data_sync, message)`.
  2. Guarded thread execution with non-blocking `await asyncio.wait_for(..., timeout=timeout)`.
  3. Awaited `handle_incoming_data` in `server/client_handler.py:123`.
  4. Fixed `"respose"` typo with backward-compatible dict aliases in `hl7responder.py`.
  5. Added concurrency and timeout unit tests in `tests/server/test_async_ingestion.py` proving that event loop ticks and concurrent client connections proceed uninterrupted during slow HL7 processing.

### [DONE] Task 0.3: Resolve Fatal Startup NameError (`db_conn_fail_dialog`)
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `gui/main_flet.py:95-122`, `gui/components.py`
- **Root Cause:** Line 118 calls `dialog = db_conn_fail_dialog(...)`, which is never imported or defined, crashing the GUI instantly if the database is unreachable on startup.
- **Implementation Notes:**
  1. Implemented `db_conn_fail_dialog(page, on_settings)` in `gui/components.py` returning an `ft.AlertDialog` with "Open Settings" and "Exit" actions.
  2. Imported `db_conn_fail_dialog` in `gui/main_flet.py`.
  3. Added unit tests in `tests/gui/test_gui_fixes.py` verifying dialog structure, callbacks, and import integrity.

### [DONE] Task 0.4: Fix Fatal ImportError in Live Stream CSV Export
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `gui/views/stream_controls.py:147-148`, `gui/views/message_components.py`
- **Root Cause:** `ExportButton.export_to_csv` imports non-existent class `from gui.views.message_components import HL7MessageParser`.
- **Implementation Notes:**
  1. Replaced broken import with `from gui.views.message_components import MessageDataExtractor` in `gui/views/stream_controls.py`.
  2. Added `HL7MessageParser = MessageDataExtractor` alias and `parse_hl7` classmethod adapter in `gui/views/message_components.py` for backward compatibility.
  3. Hardened string/bytes decoding and OBX/PID KeyError handling.
  4. Added unit tests in `tests/gui/test_gui_fixes.py` verifying clean CSV generation and parser compatibility.

### [DONE] Task 0.5: Redact Protected Health Information (PHI) from Application Logs
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `log/log_config.py`, `log/logger.py`, `database/sqlqueriesExe.py`, `hl7msghandel/hl7responder.py`, `server/client_handler.py`
- **Root Cause:** Plaintext patient names, national IDs, and raw HL7 frames were logged to persistent files, violating HIPAA § 164.312 and GDPR Art. 9.
- **Implementation Notes:**
  1. Implemented `PHIRedactingFilter` in `log/log_config.py` attached to both file and console log handlers.
  2. Redacts raw HL7 `PID` segment fields (patient name, patient ID) while preserving `MSH-10` correlation IDs.
  3. Redacts passwords in connection strings and JSON configurations (`PWD=********`).
  4. Injected default `source="General"` when missing on log records, eliminating third-party logger format crashes (`KeyError: 'source'`).
  5. Implemented `mask_identifier` and `sanitize_parameters` in `log/logger.py` and sanitized parameter logging in `database/sqlqueriesExe.py`.
  6. Masked patient names in `hl7msghandel/hl7responder.py` log statements.
  7. Added test coverage in `tests/test_phi_redaction.py`.

---

## Phase 1: Persistence, Concurrency & Connection Resilience (P1 - High Priority)

### [DONE] Task 1.1: Implement Centralized Connection Pooling for PyODBC
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `database/sqlconnection.py`, `database/sqlqueriesExe.py`
- **Root Cause:** Opening and closing a brand new `pyodbc.connect` instance for every single SQL query caused socket thrashing, high latency, and ephemeral port exhaustion.
- **Implementation Notes:**
  1. Enabled driver-level pooling via `pyodbc.pooling = True`.
  2. Implemented thread-safe `ConnectionPool` with checkout/checkin queue, health pre-ping (`SELECT 1`), and stale connection eviction.
  3. Created context manager `get_db_connection_context()` automatically releasing healthy connections back to the pool and evicting broken ones on `OperationalError`.
  4. Refactored `database/sqlqueriesExe.py:querie_exe` to acquire connections via `with get_db_connection_context() as connection:` rather than tearing down sockets.
  5. Added unit tests in `tests/database/test_sqlconnection.py` verifying connection reuse across queries and automatic broken-connection eviction.

### [DONE] Task 1.2: Eliminate False Asynchronicity & Unblock GUI Event Loop
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `database/sqlqueries.py`, `gui/views/patient.py`, `gui/views/dashboard.py`
- **Root Cause:** Synchronous PyODBC calls wrapped in `async def` without `await` returned unawaited coroutines when passed to `asyncio.to_thread`, causing recursive await hacks and freezing the desktop UI.
- **Implementation Notes:**
  1. Separated pure synchronous DAO functions (`exec_procedure_sync`, `exec_procedure_no_return_sync`) in `database/sqlqueries.py`.
  2. Implemented genuine asynchronous wrappers (`exec_procedure_for`, `exec_procedure_no_return`) offloading to thread pool using `await asyncio.to_thread(...)`.
  3. Cleaned up coroutine unwrapping hacks in `gui/views/patient.py` and `gui/views/dashboard.py`.

### [DONE] Task 1.3: Fix Corrupted String Fallback on Missing HL7 Segments
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `hl7msghandel/hl7fitsql.py`, `database/sqlqueries.py`
- **Root Cause:** When an HL7 segment extraction threw an `IndexError`, mapping metadata (`{"S": ..., "N": ..., "F": ...}`) was left in `result_dictionary[key]`, formatting dictionary strings into SQL columns.
- **Implementation Notes:**
  1. Updated `update_hl7_dictionary` in `hl7msghandel/hl7fitsql.py` to set missing field values explicitly to `None` (SQL NULL) on extraction exceptions.
  2. Updated `data_insert_for` and `data_update_for` in `database/sqlqueries.py` to preserve `None` values as SQL `NULL` instead of formatting as string `"None"`.
  3. Added unit tests in `tests/hl7msghandel/test_hl7fitsql.py`.

### [DONE] Task 1.4: Resolve Server Shutdown Task Mutation Bug & Socket Leak
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `server/server.py`
- **Root Cause:** Mutating `server_tasks` in `client_connected.finally` while iterating over `server_tasks` in `run_server` skipped every second client task. Redundant `writer.close()` created socket leaks.
- **Implementation Notes:**
  1. Updated `server/server.py:run_server` to cancel tasks over a snapshot copy (`tasks_to_cancel = list(server_tasks)`) and await cancellation via `asyncio.gather(*tasks_to_cancel, return_exceptions=True)`.
  2. Unified socket teardown authority strictly in `handle_client_connection.finally`.
  3. Added unit test `test_server_shutdown_task_snapshot_cancellation` in `tests/server/test_mllp_framing.py`.

### [DONE] Task 1.5: Fix TOCTOU Dynamic Port Allocation Race Condition
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `main.py`, `server/server.py`
- **Root Cause:** Sockets closed immediately after inspecting port created a collision window before Uvicorn or the TCP server started.
- **Implementation Notes:**
  1. Added retry with backoff and automatic port re-allocation on `OSError` (`WSAEADDRINUSE`) in `main.py:run_fastapi`.
  2. Enabled `socket.SO_REUSEADDR` in `server/server.py:check_server_start_capability` so pre-flight port checks do not leave sockets in `TIME_WAIT`.

---

## Phase 2: Protocol Rigor, Security & Service Boundaries (P2 - Medium Priority)

### [DONE] Task 2.1: Enforce Strict MLLP Framing & Bounded Ingestion Buffer
- **Status:** `[DONE]` (Implemented in Phase 1)
- **Affected Files:** `server/client_handler.py`
- **Root Cause:** MLLP end marker slicing at `\x1c` left orphaned `\r` bytes; buffer grew without bounds, enabling DoS attacks.
- **Implementation Notes:**
  1. Enforced standard MLLP framing: start marker `\x0b`, end delimiter `\x1c\r` (with optional `\n` consumption and fallback for standalone `\x1c`).
  2. Implemented leading noise and orphaned byte discarding before `\x0b`.
  3. Added TCP fragmentation assembly and multi-message coalescing burst processing in `handle_client_connection`.
  4. Enforced strict 5 MB buffer ceiling (`MAX_BUFFER_LIMIT`) with automatic client disconnect on overflow.
  5. Added comprehensive async tests in `tests/server/test_mllp_framing.py`.

### [DONE] Task 2.2: Implement Resilient Connection Handling (NAK on Error, Keep Socket Alive)
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `server/client_handler.py`, `hl7msghandel/hl7responder.py`, `tests/server/test_client_handler.py`, `tests/hl7msghandel/test_hl7responder.py`
- **Root Cause:** Any frame parsing or DB error closed the entire TCP connection, locking out clinical analyzers; non-responses caused analyzer timeouts.
- **Implementation Notes:**
  1. Wrapped message frame processing in `server/client_handler.py` in an inner `try...except Exception as frame_err:` block. Socket reading loop persists across frame errors.
  2. Implemented `generate_nak_response(hl7_message, error_msg, ack_code="AE", msg_id=None)` in `hl7msghandel/hl7responder.py`, creating compliant MLLP-framed HL7 NAK messages (`MSA|AE|...` / `MSA|AR|...`).
  3. Sanitized error messages to avoid delimiter collisions (`|`, `\r`, `\n`) while preserving correlation ID (`MSH-10`).
  4. Transmit NAK response immediately to client writer upon frame failure so analyzers never hang or time out.
  5. Added unit tests verifying NAK transmission and persistent socket connection across erroneous frames.

### [DONE] Task 2.3: Unify Presentation Layer Behind Service / API Layer
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `api/app.py`, `gui/api_methods.py`, `gui/views/patient.py`, `gui/views/cbc_report.py`, `gui/views/send_out.py`, `tests/api/test_app.py`
- **Root Cause:** Direct database access in UI views violated n-tier architecture and prevented distributed deployments.
- **Implementation Notes:**
  1. Expanded FastAPI router with domain REST endpoints:
     - `GET /api/v1/patients`: Patient search with query parameters (`id`, `name`, `start_date`, `end_date`, `status`, `result_finished`).
     - `GET /api/v1/patients/{patient_id}/cbc`: CBC report details for patient.
     - `GET /api/v1/send-out`: Send-out sample listings with filters.
     - `GET /api/v1/send-out/destinations`: List of destination labs.
     - `POST /api/v1/send-out/financials`: Send-out pricing and status update endpoint.
     - `POST /api/v1/send-out/sent`: Mark sample as sent endpoint.
  2. Implemented client methods in `gui/api_methods.py` (`fetch_patients_api`, `fetch_patient_cbc_api`, `fetch_send_out_api`, `fetch_destination_labs_api`, `update_send_out_financials_api`, `mark_send_out_sent_api`) with automatic fallback to local DAO layer if API is offline.
  3. Decoupled Flet UI views (`patient.py`, `cbc_report.py`, `send_out.py`), removing direct `database.sqlqueries` and `database.sqldbdictionary` imports.
  4. Added endpoint unit tests in `tests/api/test_app.py`.

### [DONE] Task 2.4: Secure Secrets, Fernet Keys, & File I/O Concurrency
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `setting/config.py`, `gui/views/settings.py`, `main.py`, `tests/setting/test_config.py`
- **Root Cause:** Fernet key co-located with config, un-locked multi-process file writes to `config.json`, cleartext password reveal toggle in GUI.
- **Implementation Notes:**
  1. Implemented `get_encryption_key()` supporting `HEALTHMESH_SECRET_KEY` environment variable with fallback to file key path (`HEALTHMESH_KEY_PATH` or `setting/key.key`).
  2. Implemented thread-safe atomic configuration writes in `save_config` using module-level `threading.Lock()`, writing to temporary file via `tempfile.NamedTemporaryFile` and executing atomic `os.replace`.
  3. Added `mask_config_credentials(cfg)` utility masking sensitive credentials with `********` for external/API/GUI presentation.
  4. Removed `can_reveal_password=True` from `gui/views/settings.py` and `main.py:show_db_config_window`.
  5. Implemented password masking with placeholder in settings view, preserving existing decrypted credentials on save if unchanged.
  6. Added unit tests for atomic file writes, credential masking, and environment key isolation in `tests/setting/test_config.py`.

### [DONE] Task 2.5: Modernize FastAPI Lifespan & Add Security Middleware
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `api/app.py`, `tests/api/test_app.py`, `main.py`
- **Root Cause:** Deprecated `@app.on_event("startup")`, unmanaged background monitor task, zero CORS controls, child process leaks on exit.
- **Implementation Notes:**
  1. Replaced deprecated `@app.on_event("startup")` with `@asynccontextmanager async def lifespan(app: FastAPI):` managing background monitor task lifecycle.
  2. Added `CORSMiddleware` with allowed origins, methods, and credentials.
  3. Migrated Pydantic V1 `class Config:` to Pydantic V2 `model_config = ConfigDict(...)`.
  4. Hardened WebSocket `ConnectionManager.broadcast` with automatic dead connection removal.
  5. Added robust child process termination in `main.py` using `atexit.register` and `signal.signal(signal.SIGINT/SIGTERM)` handlers with kill escalation.
  6. Added tests in `tests/api/test_app.py` verifying CORS headers and lifespan cleanup.

---

## Phase 3: UI Performance, Test Harness & Code Cleanup (P3 - Polish & Quality)

### [DONE] Task 3.1: Virtualize & Debounce Live Stream Rendering
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `gui/views/stream.py:115-175`, `gui/views/stream_controls.py:22-65`
- **Root Cause:** Reconstructing all `MessageCard` controls on every incoming HL7 message caused severe UI lag and memory bloat under high analyzer throughput; un-debounced search triggered filtering on every keystroke.
- **Implementation Notes:**
  1. Implemented bounded message storage (`MAX_STREAM_MESSAGES = 200`) in `DevicePanel`:
     - Prunes oldest messages from `self.messages` and `self.message_list.controls` when capacity is exceeded.
  2. Implemented incremental card updates:
     - Directly prepends only newly received message cards to `self.message_list.controls` via `insert(0, card)`.
     - Full collection re-rendering is reserved exclusively for search/filter term mutations.
  3. Implemented a 300ms debounce timer (`self._debounce_timer`) in `SearchBar` before dispatching filtering callbacks.
  4. Added unit tests in `tests/gui/test_gui_stream_perf.py` (`test_device_panel_bounds_messages_to_max`, `test_device_panel_incremental_card_updates`, `test_search_bar_debounce`).

### [DONE] Task 3.2: Clean Up Overlay Memory Leaks in Dialogs
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `gui/views/cbc_report.py:537`, `gui/views/message_components.py:634`, `gui/views/stream_controls.py:298`, `gui/views/stream.py:145`
- **Root Cause:** Modal dialogs and snackbars were repeatedly appended to `page.overlay` without removal upon dismissal, creating accumulating control trees and memory leaks.
- **Implementation Notes:**
  1. Updated all dialog dismiss handlers to explicitly evict themselves from `page.overlay`:
     ```python
     if dialog in page.overlay:
         page.overlay.remove(dialog)
     dialog.open = False
     page.update()
     ```
  2. Applied clean overlay removal to CSV export snackbars, raw HL7 message modal dialogs, and clear-stream confirmation dialogs.
  3. Added unit tests in `tests/gui/test_gui_stream_perf.py` (`test_overlay_dialog_cleanup`).

### [DONE] Task 3.3: Remove Dead Files & Deprecated Syntax
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `gui/views/report.py` (deleted), `gui/views/settings.py`, `api/app.py`, `gui/views/`
- **Root Cause:** Obsolete placeholder files, unreferenced constants, and deprecated Flet / Pydantic V1 syntax.
- **Implementation Notes:**
  1. Deleted orphaned stub file `gui/views/report.py`.
  2. Removed dead global constants `changed_db_user` and `changed_db_password` from `gui/views/settings.py`.
  3. Migrated Pydantic V1 `class Config:` in `api/app.py` to Pydantic V2 `model_config = ConfigDict(...)`.
  4. Upgraded Flet control layout patterns across `gui/views/` (`stream.py`, `stream_controls.py`, `message_components.py`, `report_component.py`) with resilient compatibility helpers (`_safe_border_all`, `_safe_margin_only`, `_safe_animation`, and `_page_ref`) to resolve Flet 1.1.2 breaking changes.

### [DONE] Task 3.4: Construct Automated End-to-End GUI & HL7 Pipeline Test Suite
- **Status:** `[DONE]` (Implemented 2026-11-13)
- **Affected Files:** `tests/server/test_hl7_server_pipeline.py`, `tests/gui/test_gui_stream_perf.py`, `tests/gui/test_gui_fixes.py`
- **Root Cause:** Incomplete integration test coverage for TCP/MLLP socket conversations under live network conditions.
- **Implementation Notes:**
  1. Built comprehensive end-to-end TCP integration test in `tests/server/test_hl7_server_pipeline.py`:
     - Launches an in-process `asyncio.start_server` bound to an ephemeral port.
     - Connects client socket and sends an `ORU^R01` result frame; asserts valid MLLP-wrapped `ACK^R01` with `MSA|AA`.
     - Sends an `ORM^O01` clinical order query on the **same** persistent socket; asserts valid `ORR^O02` order response.
     - Sends an unsupported `ADT^A01` frame on the same socket; asserts proper MLLP-wrapped NAK `MSA|AR` response while maintaining persistent socket connectivity.
  2. Expanded GUI test harness in `tests/gui/test_gui_stream_perf.py` and `tests/gui/test_gui_fixes.py` covering message rendering, search debounce, overlay cleanup, and CSV export.
  3. Total test suite expanded to 86 automated tests across 12 modules with 100% pass rate.

---

## Refactoring Task Summary Matrix

| ID | Title | Target Subsystem | Priority | Complexity | Risk if Not Addressed |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **0.1** | [DONE] Prevent Schema In-Place Mutation | `database/sqlqueries.py` | **P0** | Low | **Permanent clinical data loss** |
| **0.2** | [DONE] Fix Ingestion Event Loop Freeze | `server/incoming_data.py` | **P0** | Medium | **10s backend freeze on every message** |
| **0.3** | [DONE] Fix `db_conn_fail_dialog` Crash | `gui/main_flet.py` | **P0** | Low | **Immediate app crash on DB drop** |
| **0.4** | [DONE] Fix CSV Export Import Crash | `gui/views/stream_controls.py` | **P0** | Low | **Crash on core export feature** |
| **0.5** | [DONE] Redact PHI/PII from Logs | `database/`, `hl7msghandel/` | **P0** | Low | **HIPAA/GDPR compliance violation** |
| **1.1** | [DONE] Connection Pooling (PyODBC) | `database/sqlconnection.py` | **P1** | High | **OS port exhaustion & latency** |
| **1.2** | [DONE] Fix False Async in Queries | `database/sqlqueries.py`, `gui/`| **P1** | Medium | **Desktop UI freezes during queries** |
| **1.3** | [DONE] Fix Missing Field String Bug | `hl7msghandel/hl7fitsql.py` | **P1** | Low | **Python dict strings saved to DB** |
| **1.4** | [DONE] Fix Server Shutdown Task Bug | `server/server.py` | **P1** | Low | **Orphaned sockets on shutdown** |
| **1.5** | [DONE] Fix Dynamic Port TOCTOU Race | `main.py`, `server/server.py` | **P1** | Medium | **Random startup crash with port conflict** |
| **2.1** | [DONE] Standard MLLP & Bounded Buffer | `server/client_handler.py` | **P2** | Medium | **Buffer overflow / Memory exhaustion** |
| **2.2** | [DONE] Resilient TCP Connection Loop | `server/client_handler.py` | **P2** | Medium | **Analyzers disconnected on errors** |
| **2.3** | [DONE] Unify Data Access via API/Service| `gui/views/`, `api/app.py` | **P2** | High | **Tightly coupled direct DB access in UI** |
| **2.4** | [DONE] Secure Secrets & Atomic Config | `setting/config.py` | **P2** | Medium | **Corrupted config files & leaked passwords** |
| **2.5** | [DONE] FastAPI Lifespan & Security | `api/app.py` | **P2** | Low | **Leaked WebSocket connections** |
| **3.1** | [DONE] Stream Virtualization & Debounce | `gui/views/stream.py` | **P3** | Medium | **UI lag with high message volume** |
| **3.2** | [DONE] Dialog Overlay Cleanup | `gui/views/*.py` | **P3** | Low | **Minor memory accumulation** |
| **3.3** | [DONE] Remove Dead Code & Stubs | `gui/views/report.py` | **P3** | Low | **Technical debt / confusion** |
| **3.4** | [DONE] Expand Automated Test Suite | `tests/` | **P3** | High | **Undetected regressions** |

---

## Phase 4: Pre-Merge Audit Remediation Sprint (B-1..B-3, M-1..M-7, Minors)

Following an adversarial independent pre-merge audit, all 3 Blockers (`B-1` to `B-3`), 7 Majors (`M-1` to `M-7`), and 4 Minor findings were remediated and verified with regression tests.

### [DONE] Task 4.1: Resolve GUI DataRow Crash, Thread-Safety & Button Compatibility (B-1, M-2, M-6, Minor #1, #4)
- **Status:** `[DONE]` (Remediated 2026-11-13)
- **Affected Files:** `gui/views/patient.py`, `gui/main_flet.py`, `gui/views/stream.py`, `gui/views/settings.py`, `gui/views/message_components.py`
- **Remediation Details:**
  1. **B-1 (`gui/views/patient.py:93-135`):** Updated `create_patient_row` to defensively parse `Requested Date` whether it arrives as a `datetime` object, an ISO string (`datetime.fromisoformat`), or missing/None. Wrapped button creation in a dual-compatible `ButtonClass` supporting Flet 1.1+ without keyword/positional mismatches.
  2. **M-2 (`gui/main_flet.py:116-118`):** Replaced bare `get_db_connection()` startup connection probe with `with get_db_connection_context(): pass` to guarantee immediate pool socket return.
  3. **M-6 (`gui/views/stream.py`):** Added `self._lock = threading.Lock()` and thread-safe synchronization around `self.messages`, `self.filtered_messages`, and `self.message_list.controls` to prevent race conditions between incoming WebSocket streams and SearchBar debounce filters.
  4. **Minor #1 & #4 (`gui/views/settings.py:3`, `gui/views/message_components.py:187-188`):** Routed DB connection test through `gui.api_methods.test_db_connection_api` to achieve 100% layer decoupling in GUI views; removed duplicate `return results` in `_extract_cbc_results`.

### [DONE] Task 4.2: Implement Cross-Process Config Lock, Token Authentication & SQL PHI Masking (B-2, B-3, M-7)
- **Status:** `[DONE]` (Remediated 2026-11-13)
- **Affected Files:** `setting/config.py`, `api/app.py`, `gui/api_methods.py`, `log/log_config.py`
- **Remediation Details:**
  1. **B-2 (`setting/config.py`):** Implemented cross-process file locking via `portalocker.Lock` combined with an in-process thread lock for `get_config()` and `save_config()`. Implemented `_atomic_replace_with_retry` with exponential backoff on Windows `PermissionError` (`WinError 32`) and eliminated raw `open(..., "w")` truncation. Added `setting/*.lock` to `.gitignore`.
  2. **B-3 (`api/app.py`, `gui/api_methods.py`):** Replaced wild-card CORS with explicit allowed local origins (`http://localhost`, `127.0.0.1`, `3000`, `8000`). Enforced IPC bearer/API token authentication (`X-Internal-Token` / `get_api_token()`) on sensitive clinical endpoints and WebSocket connections while preserving unauthenticated access to `/server/status` for readiness probes.
  3. **M-7 (`log/log_config.py`):** Extended `PHIRedactingFilter` with `SQL_DUPLICATE_KEY_PATTERN` to redact patient names and medical record IDs embedded within SQL Server duplicate key exception strings.

### [DONE] Task 4.3: Enforce SQL Parameter Hygiene & Pool Connection Rollback (M-1, M-3, Minor #3)
- **Status:** `[DONE]` (Remediated 2026-11-13)
- **Affected Files:** `database/sqlqueries.py`, `database/sqlconnection.py`, `database/sqlqueriesExe.py`
- **Remediation Details:**
  1. **M-1 (`database/sqlqueries.py:166, 209`):** Explicitly converted `None` and `"None"` values to SQL `None` (NULL) in `data_select_for` and `data_delete_for` parameter lists instead of passing literal string `'None'`.
  2. **M-3 (`database/sqlconnection.py:78, 123`):** Added explicit `conn.rollback()` inside `ConnectionPool._is_alive()` after `SELECT 1` ping and inside `release_connection()` before returning sockets to the idle pool, preventing dangling transactions on PyODBC with `autocommit=False`.
  3. **Minor #3 (`database/sqlqueriesExe.py:53`):** Re-raised `(pyodbc.OperationalError, ConnectionError)` so `get_db_connection_context()` reliably triggers `discard = True` to evict terminated/broken sockets.

### [DONE] Task 4.4: MLLP Split Delimiter Chunk Reassembly & Dynamic Port Sync (M-4, M-5, Minor #2)
- **Status:** `[DONE]` (Remediated 2026-11-13)
- **Affected Files:** `server/client_handler.py`, `main.py`
- **Remediation Details:**
  1. **M-5 (`server/client_handler.py:130-145`):** When a TCP chunk ends precisely at `\x1c`, the handler checks `is_eof`: if not EOF, it defers message extraction to read the trailing `\r` (0x0D) cleanly, preventing orphaned byte corruption at the head of subsequent frames.
  2. **M-4 & Minor #2 (`main.py`):** Removed dead monkeypatching code (`patch_api_methods_base_url`), directly imported `start_server`, and synchronized dynamically re-allocated FastAPI ports via `get_config()` reload in `wait_for_fastapi_server`.

---

## Final Verification & Pre-Merge Audit Sign-Off
- **Automated Test Suite:** 95 passed out of 95 tests (100% pass rate).
- **Regression Tests Added:**
  - `test_create_patient_row_safe_date_and_age_formatting` (`tests/gui/test_gui_fixes.py`)
  - `test_atomic_replace_with_retry_recovers_from_transient_permission_error` (`tests/setting/test_config.py`)
  - `test_get_api_token_from_env_or_generated` (`tests/setting/test_config.py`)
  - `test_unauthenticated_protected_endpoint_returns_401` (`tests/api/test_app.py`)
  - `test_websocket_authentication` (`tests/api/test_app.py`)
  - `test_data_select_and_delete_none_parameter_binding` (`tests/database/test_sqlqueries.py`)
  - `test_connection_pool_rollback_on_release_and_is_alive` (`tests/database/test_sqlconnection.py`)
  - `test_mllp_split_delimiter_across_tcp_chunks` (`tests/server/test_mllp_framing.py`)
  - `test_phi_redacting_filter_sql_duplicate_key_exception` (`tests/test_phi_redaction.py`)
- **Verdict:** **`APPROVED FOR MERGE`**

