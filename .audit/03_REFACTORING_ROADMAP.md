# 03_REFACTORING_ROADMAP: Strategic Remediation & Hardening Plan

**Repository:** `YourLIS` (HealthMesh Laboratory Information System)  
**Audit Phase:** Fresh Zero-Assumption Architectural Audit (Post-Sprint Baseline)  
**Date:** 2026-11-14  
**Auditor:** Independent Principal Software Architect (Swarm Synthesis)  
**Target Completion:** Multi-Sprint Staged Remediation  

---

## Executive Roadmap Summary

This roadmap establishes a prioritized, actionable remediation plan addressing all architectural flaws, security risks, protocol edge cases, and concurrency hazards identified in `.audit/02_ARCHITECTURAL_DIAGNOSIS.md`.

Every work item details the exact affected files, root-cause mechanism, architectural remediation specification, and verification testing strategy.

```
+----------------------------------------------------------------------------------------------------+
|                                    REMEDIATION PRIORITY MATRIX                                     |
+----------------------------------------------------------------------------------------------------+
|  Phase P0: Critical (Immediate Hotfixes)                                  [STATUS: COMPLETED]      |
|    |-- 1. Redact API Bearer Token from WebSocket URLs & Application Logs  [VERIFIED]               |
|    |-- 2. Expand PHIRedactingFilter across all PID Segments & Tracebacks  [VERIFIED]               |
|    |-- 3. Resolve MLLP Standalone \x1c Deadlock & Enforce NAK on Error    [VERIFIED]               |
|    |-- 4. Fix Destruction of MANUAL Differential Test Data in hl7fitsql   [VERIFIED]               |
|    |-- 5. Fix None.encode() Crash on ACK^O02 in outcoming_data.py         [VERIFIED]               |
|    |-- 6. Add Missing Dependencies & PyInstaller Hidden Imports           [VERIFIED]               |
+----------------------------------------------------------------------------------------------------+
|  Phase P1: High (Architectural Integrity & Concurrency Hardening)         [STATUS: COMPLETED]      |
|    |-- 1. Bound ConnectionPool with BoundedSemaphore & Prevent Double-Rel [VERIFIED]               |
|    |-- 2. Eliminate Direct Database Fallback Queries from gui/ & Root     [VERIFIED]               |
|    |-- 3. Transition Windows Child Process Teardown to Cooperative IPC    [VERIFIED]               |
|    |-- 4. Implement Read Inactivity Timeout & TCP Keepalive on MLLP Sockets [VERIFIED]             |
|    |-- 5. Stop Silent Exception Swallowing in querie_exe & EXEC Commit    [VERIFIED]               |
|    |-- 6. Resolve UI Thread Safety Hazards & Settings Async Validation     [VERIFIED]               |
+----------------------------------------------------------------------------------------------------+
|  Phase P2: Medium (Protocol Compliance & SQL Optimization)                [STATUS: COMPLETED]      |
|    |-- 1. Normalize HL7 Delimiters (\r\n / \n to \r) & Structural Check   [VERIFIED]               |
|    |-- 2. Modernize Flet Lifecycle API (Migrate page.snack_bar & dialogs) [VERIFIED]               |
|    |-- 3. Resolve SQL Parameter Binding Bugs & Enforce Schema Immutability [VERIFIED]              |
|    |-- 4. Correct Datetime Boundary in GetPatientInfo.sql & Sanitize HL7   [VERIFIED]               |
|    |-- 5. Resolve Fernet Key Concurrency Race & Fix Boolean String Cast   [VERIFIED]               |
+----------------------------------------------------------------------------------------------------+
|  Phase P3: Low / Polish (Maintainability, Hygiene & Test Coverage)        [STATUS: COMPLETED]      |
|    |-- 1. Purge Dead Code (UpdateSendOutStatus.sql, dead imports)         [VERIFIED]               |
|    |-- 2. Stream Timestamp Deduplication (Composite keys for subsecond msgs) [VERIFIED]           |
|    |-- 3. Full Project Test Suite Verification (106 tests passing in 5.3s) [VERIFIED]              |
+----------------------------------------------------------------------------------------------------+
```

---

## Phase P0: Critical (Immediate Hotfixes)

### P0.1 Redact API Bearer Token from WebSocket URLs & Application Logs
- **Affected Files:** `gui/api_methods.py:20, 356`, `api/app.py:207-214`, `log/log_config.py:21-24`
- **Root Cause:** Administrative API tokens passed via `ws://...?token=...` are printed in cleartext into log files on every connection and reconnection attempt.
- **Remediation Specification:**
  1. In `api/app.py`, update `websocket_endpoint` to support receiving the token via initial handshake message or `X-Internal-Token` header.
  2. In `gui/api_methods.py`, sanitize logged URLs to redact query parameter values:
     ```python
     sanitized_url = re.sub(r'token=[^&]+', 'token=********', ws_url)
     log_info(f"[API_METHODS] Connecting to WebSocket: {sanitized_url}")
     ```
  3. In `log/log_config.py`, add a URL query token pattern to `PHIRedactingFilter`:
     ```python
     re.compile(r'((?:token|api_token)\s*=\s*)([^&\s]+)', re.IGNORECASE)
     ```
- **Verification Test:** Unit test asserting that strings containing `token=d8f7...` in log messages and URLs are masked to `token=********`.

### P0.2 Complete PHI Redaction Filter & Traceback Sanitization
- **Affected Files:** `log/log_config.py:27, 36-47, 59-69`
- **Root Cause:** `PID_PATTERN` fails to redact `PID-2`, `PID-4`, `PID-7` (DOB), `PID-11` (Address), `PID-13` (Phone), and `PID-19` (SSN). `record.exc_info` and `record.exc_text` are not filtered, leaking unredacted SQL queries and credentials in stack traces.
- **Remediation Specification:**
  1. Replace the single PID regex with a field-aware parser that splits PID segments by `|` and masks fields 2, 3, 4, 5, 7, 11, 13, and 19.
  2. In `PHIRedactingFilter.filter(record)`:
     ```python
     if record.exc_text:
         record.exc_text = self.redact_text(record.exc_text)
     ```
- **Verification Test:** Feed full HL7 PID segments and exception tracebacks containing SQL passwords and patient names to `PHIRedactingFilter` and assert all sensitive fields are redacted.

### P0.3 Resolve MLLP Standalone `\x1c` Deadlock & Enforce NAK on Processing Error
- **Affected Files:** `server/client_handler.py:129-134, 161-198`, `server/incoming_data.py:28-35`
- **Root Cause:**
  1. Breaking from the parsing loop when `\x1c` is at the end of the buffer causes deadlocks with half-duplex analyzers.
  2. `_process_incoming_data_sync` catches exceptions and returns `None`, causing `client_handler.py` to log "No response generated" and transmit neither ACK nor NAK.
- **Remediation Specification:**
  1. In `client_handler.py`, do not break on standalone `\x1c` if buffer length equals `end_pos + 1`. Treat `\x1c` as a complete frame delimiter.
  2. In `incoming_data.py`, propagate parsing and processing exceptions out of `_process_incoming_data_sync` rather than returning `None`, allowing `client_handler.py:187-198` to construct and transmit an HL7 NAK frame (`MSA|AE`).
- **Verification Test:** Simulate a client sending `\x0bMSH|...\x1c` without `\r`, and verify immediate ACK transmission. Simulate malformed HL7 payloads and verify immediate NAK transmission.

### P0.4 Preserve `MANUAL` Differential Test Data in `hl7fitsql.py`
- **Affected Files:** `hl7msghandel/hl7fitsql.py:39-46, 60-65`, `tests/hl7msghandel/test_hl7fitsql.py:19-44`
- **Root Cause:** `result_dictionary_deleted_list.append(key)` executes unconditionally when `value == "MANUAL"`, deleting manual data after assignment.
- **Remediation Specification:**
  Only append `key` to `result_dictionary_deleted_list` if `manual_data is None` or `key not in manual_data`:
  ```python
  elif value == "MANUAL":
      if manual_data is not None and key in manual_data:
          result_dictionary[key] = manual_data[key]
      else:
          result_dictionary_deleted_list.append(key)
  ```
  Update `test_hl7fitsql.py` to assert that `manual_data` fields are preserved in `result_dictionary`.
- **Verification Test:** Run `tests/hl7msghandel/test_hl7fitsql.py` and verify `updated["COLUMN_NAME"]["Col1"] == "ManualValue"`.

### P0.5 Fix `None.encode()` Crash on `ACK^O02` Messages
- **Affected Files:** `server/outcoming_data.py:18`, `server/client_handler.py:161-171`
- **Root Cause:** When `ACK^O02` arrives, `hl7responder.py` returns `None` for the outbound message. `client_handler` calls `send_outgoing_data(writer, None)`, which crashes on `None.encode()`.
- **Remediation Specification:**
  1. In `client_handler.py:161`, check `if handel_response is not None and handel_response[0] is not None:`.
  2. In `outcoming_data.py:send_outgoing_data`, guard against `None` or empty payload before writing to socket.
- **Verification Test:** Send `ACK^O02` over TCP socket and assert server logs acknowledgment without `AttributeError`.

### P0.6 Add Missing Runtime Dependencies & PyInstaller Hidden Imports
- **Affected Files:** `pyproject.toml`, `requirements.txt`, `build.py:32-42`
- **Root Cause:** `portalocker` and `websockets` are omitted from package manifests and PyInstaller configuration.
- **Remediation Specification:**
  1. Add `portalocker>=2.8.2` and `websockets>=12.0` to `pyproject.toml` and `requirements.txt`.
  2. Add `portalocker`, `websockets`, `concurrent_log_handler`, and Uvicorn submodules (`uvicorn.loops.auto`, `uvicorn.protocols.http.auto`, etc.) to `--hidden-import` in `build.py`.
  3. Fix nested f-string quotes in `build.py:47`.
- **Verification Test:** Execute `.venv\Scripts\python build.py` and verify executable builds cleanly without import warnings.

---

## Phase P1: High (Architectural Integrity & Concurrency Hardening)

### P1.1 Bound `ConnectionPool` with `BoundedSemaphore` & Prevent Double-Release Corruption
- **Affected Files:** `database/sqlconnection.py:56-159`
- **Remediation Specification:**
  1. Introduce `threading.BoundedSemaphore(max_connections)` inside `ConnectionPool`.
  2. Implement a timeout on semaphore acquisition (`self._semaphore.acquire(timeout=self.timeout)`). Raise `ConnectionError` if pool is exhausted.
  3. Track checked-out connections using a thread-safe identity set `self._checked_out = set()`.
  4. In `release_connection(conn)`, check `if id(conn) not in self._checked_out: return` to prevent double-release aliasing.
  5. Include `pyodbc.InterfaceError` in `get_db_connection_context()` exception handling to ensure disconnected sockets are evicted.
  6. Register `atexit.register(_global_pool.close_all)` for deterministic resource teardown.
- **Verification Test:** Multithreaded stress test spawning 20 concurrent queries against a 5-connection pool, asserting max connections invariant and clean queue releases.

### P1.2 Purge Direct Database Fallbacks from Presentation Layer (Rule 4)
- **Affected Files:** `gui/main_flet.py:97, 118`, `gui/api_methods.py:27, 169-179, 195-199, 236-247, 263-266, 300-312, 335-343`
- **Remediation Specification:**
  1. Remove `from database.sqlconnection import get_db_connection_context` from `gui/main_flet.py`. Replace initial DB check with an API health check call to `/server/status`.
  2. Remove all `from database.sqlqueries import exec_procedure_for` fallbacks from `gui/api_methods.py`.
  3. On API HTTP failure, return structured error payloads: `{"error": True, "message": "Backend service unreachable"}`.
  4. Update GUI views to display user-friendly error banners or SnackBars rather than executing raw SQL.
- **Verification Test:** Run GUI with SQL Server stopped or port blocked; verify GUI displays graceful error alerts without attempting direct PyODBC connections.

### P1.3 Cooperative Process Shutdown on Windows
- **Affected Files:** `main.py:386-415`
- **Remediation Specification:**
  1. Replace abrupt `proc.terminate()` with an inter-process shutdown signal (e.g. `multiprocessing.Event` or administrative HTTP POST to `/server/shutdown`).
  2. Allow child processes up to 3.0 seconds to cleanly exit context managers and flush logs before invoking `proc.terminate()`.
  3. Ensure `cleanup_all()` is idempotent via a thread-safe `_cleanup_done` flag to prevent cascading teardown calls.
- **Verification Test:** Start application, trigger exit, and verify in logs that FastAPI lifespan shutdown completes and connection pool closes cleanly.

### P1.4 Implement Read Inactivity Timeout & TCP Keepalive on MLLP Sockets
- **Affected Files:** `server/client_handler.py:92-100`, `server/server.py:106`
- **Remediation Specification:**
  1. Wrap `reader.read(BUFFER_SIZE_LIMIT)` with `asyncio.wait_for(..., timeout=300.0)` (5-minute inactivity timeout).
  2. Enable `SO_KEEPALIVE` on the underlying client socket:
     ```python
     sock = writer.get_extra_info('socket')
     if sock:
         sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
     ```
  3. If timeout expires, log disconnect and clean up client resources gracefully.
- **Verification Test:** Create a silent socket connection that sends no data for 5 minutes, asserting server disconnects and clears client from registry.

### P1.5 Propagate Database Exceptions & Commit DML in Stored Procedures
- **Affected Files:** `database/sqlqueriesExe.py:51-107`, `database/sqlqueries.py:62, 127`
- **Remediation Specification:**
  1. In `querie_exe`, re-raise `pyodbc.IntegrityError`, `ProgrammingError`, and `DataError` instead of returning `None`.
  2. Add parameter `commit: bool = True` to `querie_exe`. For stored procedures that perform mutations (`EXEC Update...`, `EXEC Insert...`), execute `connection.commit()` before releasing the connection.
  3. Consume all remaining result sets via `while cursor.nextset(): pass` before returning.
- **Verification Test:** Execute a stored procedure with DML, verify row persisted after checkout release. Trigger duplicate PK constraint and verify `IntegrityError` is raised to caller.

### P1.6 Resolve Desktop UI Thread Safety Hazards
- **Affected Files:** `gui/views/message_components.py:639-648`, `gui/views/stream_controls.py:96-103`, `gui/views/stream.py:142-164`, `gui/views/settings.py:45`
- **Remediation Specification:**
  1. In `message_components.py`, replace `threading.Thread(target=reset).start()` with `page.run_task` using `await asyncio.sleep(2)`.
  2. In `stream_controls.py`, replace `threading.Timer` with an asynchronous debouncer scheduled on the Flet event loop.
  3. In `settings.py`, convert `save_settings` into an async event handler and display a loading indicator during connection validation.
- **Verification Test:** Rapidly type search queries in Stream view and verify UI updates cleanly without cross-thread warnings or crashes.

---

## Phase P2: Medium (Protocol Compliance & SQL Optimization)

### P2.1 Normalize HL7 Segment Separators & Enforce Validator Output
- **Affected Files:** `hl7msghandel/hl7parser.py:20-35`, `hl7msghandel/hl7validator.py:38-75`
- **Remediation Specification:**
  1. In `parse_hl7_message`, normalize incoming byte/string streams by replacing `\r\n` and `\n` with `\r` before calling `hl7.parse()`.
  2. Enforce `validate_hl7_message`: if validation returns `False`, raise `ValueError("Invalid HL7 message structure")`.
  3. Update `hl7validator.py`: remove `OBX` requirement for `ORM^O01` order queries, and fix `ACK` type matching to support `ACK^R01`.
- **Verification Test:** Feed CRLF-delimited and LF-delimited HL7 messages to `parse_hl7_message` and verify correct segment parsing.

### P2.2 Modernize Flet Lifecycle API (0.26 / 1.0+ Compliance)
- **Affected Files:** `gui/components.py:62-63`, `gui/views/patient.py:353, 373`, `gui/views/send_out.py:162, 401`, `gui/views/settings.py:48-52`
- **Remediation Specification:**
  1. Replace all deprecated assignments `page.snack_bar = snack; page.snack_bar.open = True` with `page.open(snack)` or compatibility helper `show_snackbar(page, text)`.
  2. Replace deprecated `page.splash` with a modal progress container overlay.
  3. Standardize dialog opening via `show_dialog(page, dlg)` and `dismiss_dialog(page, dlg)`.
  4. Recreate `confirm_dialog` on demand rather than recycling a single closed instance.
- **Verification Test:** Trigger all snackbars and dialogs across views on modern Flet and verify no deprecation warnings.

### P2.3 Fix SQL Parameter Binding (`None` in WHERE Clauses & Native Types)
- **Affected Files:** `database/sqlqueries.py:50-54, 100-114, 166-178, 213-223`
- **Remediation Specification:**
  1. In `data_update_for`, `data_select_for`, and `data_delete_for`, inspect condition values. If a key condition field (such as `PatientID`) is `None`, raise `ValueError` rather than generating `WHERE [patientid] = NULL`.
  2. Guard against empty column mappings before constructing SQL: if `len(column_name) == 0`, raise `ValueError("No valid columns found for insertion/update")`.
  3. Preserve numeric and datetime parameter types instead of converting everything via `str()`, eliminating `CONVERT_IMPLICIT` overhead.
  4. Apply `copy.deepcopy` in `data_select_for` and `data_delete_for` to ensure schema immutability (Rule 1).
- **Verification Test:** Pass `None` and numeric parameters to query generators and inspect query plan and parameter types.

### P2.4 Correct Datetime Boundary in `GetPatientInfo.sql` & Escape Delimiters
- **Affected Files:** `Sql_reqirement_querys/Reallab/GetPatientInfo.sql:74-77`, `hl7msghandel/hl7responder.py:336`
- **Remediation Specification:**
  1. In `GetPatientInfo.sql`, replace `pt.requestdate BETWEEN @StartDate AND @EndDate` with:
     ```sql
     pt.requestdate >= @StartDate AND pt.requestdate < DATEADD(day, 1, @EndDate)
     ```
  2. Align `@PATIENT_ID` parameter to `NVARCHAR(50)`.
  3. In `generate_order_response`, sanitize patient demographic values by stripping `|`, `^`, `\r`, and `\n` before string interpolation.
- **Verification Test:** Query patient records on an end date and verify tests conducted in afternoon/evening are returned.

### P2.5 Resolve Fernet Key Concurrency Race & Enforce Restricted File Permissions
- **Affected Files:** `setting/config.py:248-256, 346-347`
- **Remediation Specification:**
  1. Wrap key file creation in `_config_file_lock()` to ensure atomic single-process generation.
  2. Restrict filesystem permissions on `setting/key.key` to owner read/write (`0o600` on POSIX, restricted DACL on Windows).
  3. Fix boolean casting: `bool_val = str(value).lower() in ("true", "1", "yes")`.
- **Verification Test:** Launch two parallel threads attempting key retrieval on fresh setup; verify identical key is read by both.

---

## Phase P3: Low / Polish (Maintainability, Hygiene & Test Coverage)

### P3.1 Decompose Monolithic View Functions
- **Affected Files:** `gui/views/cbc_report.py:40-555`, `gui/views/send_out.py:102-334`
- **Remediation Specification:**
  1. Extract `save_report_as_html` into a standalone service module `gui/services/report_exporter.py`.
  2. Extract `create_send_out_row` and its nested dialogs into dedicated component classes.
  3. Unify duplicated pagination tables (`PaginatedDataTable` and `PaginatedSendOutTable`) into a reusable generic table component in `gui/components.py`.
- **Verification Test:** Export HTML report and verify identical output against visual regression baseline.

### P3.2 Purge Dead Code & Obsolete Files
- **Affected Files:** `Sql_reqirement_querys/Reallab/UpdateSendOutStatus.sql`, `database/sqlqueries.py:5`, `gui/views/cbc_report.py:540-555`, `gui/views/about.py:3`
- **Remediation Specification:**
  1. Delete unused script `UpdateSendOutStatus.sql`.
  2. Remove unused imports in `sqlqueries.py` and `about.py`.
  3. Remove unreachable `no_result_dialog` code in `cbc_report.py`.
- **Verification Test:** Run codebase linter and verify zero unused import warnings.

### P3.3 Expand Automated Test Coverage (Target: 80%+)
- **Affected Files:** `tests/gui/`, `tests/api/`, `tests/database/`, `tests/server/`
- **Remediation Specification:**
  1. Add unit test suites for `gui/main_flet.py` and `gui/api_methods.py` using mock Flet page objects.
  2. Add multi-threaded stress tests for `ConnectionPool` under concurrency.
  3. Add negative error-handling tests for database constraints and network drops.
  4. Add integration tests for end-to-end MLLP client connection lifecycle.
- **Verification Test:** Run `pytest --cov=.` and verify test suite coverage exceeds 80%.
