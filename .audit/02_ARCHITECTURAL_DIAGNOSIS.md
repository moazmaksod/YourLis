# 02_ARCHITECTURAL_DIAGNOSIS: Root Flaws, Vulnerabilities & Anti-Patterns

**Repository:** `YourLIS` (HealthMesh Laboratory Information System)  
**Audit Phase:** Fresh Zero-Assumption Architectural Audit (Post-Sprint Baseline)  
**Date:** 2026-11-14  
**Auditor:** Independent Principal Software Architect (Swarm Synthesis)  
**Status:** Comprehensive Diagnostic Assessment  

---

## Executive Summary & Threat Model

This diagnosis synthesizes the empirical, line-by-line findings of four specialized Goldfish subagents auditing the YourLIS codebase across:
1. TCP/MLLP Transport & HL7 Parsing Engine
2. Database, Connection Pooling & SQL Persistence
3. Process Orchestration, REST API, Security & Logging
4. Desktop Presentation Tier (Flet) & Build Pipeline

While recent refactoring sprints successfully introduced non-blocking async offloading (`asyncio.to_thread`), bounded buffer limits (5 MB), and deepcopy schema guards in `data_insert_for`, the audit revealed **critical protocol deadlocks**, **credential leakage in log files**, **PHI exposure in exception tracebacks**, **unconstrained database connection creation**, and **abrupt process termination on Windows**.

---

## Category 1: Architectural Drift & Layer Violations (Rule 4)

### 1.1 Direct Database Connection and Execution in GUI Root
- **Citations:** `gui/main_flet.py:97`, `gui/main_flet.py:118`
- **Mechanism:** In the presentation root `main_flet.py`:
  ```python
  97: from database.sqlconnection import get_db_connection_context
  ...
  118: with get_db_connection_context():
  119:     pass
  ```
  The presentation tier directly imports the persistence layer and opens a raw database connection during UI startup.
- **Architectural Impact:** Violates Rule 4 (Strict n-Tier Decoupling). If the database server is offline or unreachable, the synchronous PyODBC connection timeout (15–30 seconds) freezes the Flet desktop window during application launch before the main view is mounted.

### 1.2 Pervasive Direct Database Fallbacks in Presentation API Client
- **Citations:** `gui/api_methods.py:27`, `gui/api_methods.py:169-179`, `gui/api_methods.py:195-199`, `gui/api_methods.py:236-247`, `gui/api_methods.py:263-266`, `gui/api_methods.py:300-312`, `gui/api_methods.py:335-343`
- **Mechanism:** While `gui/views/` modules route calls through `gui/api_methods.py`, all data retrieval and modification functions in `api_methods.py` catch HTTP errors and silently fall back to importing `database.sqlqueries`:
  ```python
  # gui/api_methods.py:168-179
  # Graceful fallback to direct DB execution
  from database.sqlqueries import exec_procedure_for
  from database.sqldbdictionary import PATIENT_SEARCH_SQL
  ...
  return await exec_procedure_for(PATIENT_SEARCH_SQL, db_params) or []
  ```
- **Architectural Impact:** 
  1. The presentation layer retains compile-time and runtime coupling to the database schema, ODBC drivers, and SQL Server network credentials.
  2. Bypasses backend REST authentication, authorization, and audit logging when the API server is busy or restarting.
  3. Precludes deploying the Flet GUI on remote client workstations across a hospital subnet without opening direct SQL Server port 1433 to all endpoints.

### 1.3 Wildcard Persistence Coupling in HL7 Message Handler
- **Citations:** `hl7msghandel/hl7responder.py:3-5`
- **Mechanism:**
  ```python
  from database.sqlqueries import *
  from database.sqldbdictionary import *
  from hl7msghandel.hl7dictionary import *
  ```
- **Architectural Impact:** The HL7 domain responder pollutes its module namespace with wildcard imports from the persistence layer, tightly coupling messaging logic to database schema dictionaries and preventing independent unit testing.

### 1.4 Hardcoded 3-Part Database Name in SQL Scripts
- **Citations:** `Sql_reqirement_querys/Reallab/GetDestinationLabs.sql:11-13`
- **Mechanism:**
  ```sql
  SELECT [gehahid], [gehahname]
  FROM [Patients].[dbo].[Gehats]
  WHERE morsel != 0;
  ```
- **Architectural Impact:** The database name `[Patients]` is hardcoded in the query. If the database is renamed (e.g. `YourLIS_DB`, `RealLabDB`), or if user logins lack cross-database permissions, queries fail with `Cannot open database "Patients" requested by the login`.

---

## Category 2: Security, Credentials & PHI Leakage (Rules 3 & 6)

### 2.1 API Bearer Token Transmitted in URL Query and Logged in Cleartext (CWE-598)
- **Citations:** `gui/api_methods.py:20`, `gui/api_methods.py:356`, `api/app.py:207-214`
- **Mechanism:**
  1. `get_ws_base_url()` formats: `url = f"ws://{api_ip}:{api_port}/ws?token={token}"`.
  2. `gui/api_methods.py:356` logs:
     ```python
     log_info(f"[API_METHODS] Connecting to WebSocket: {ws_url}")
     ```
  3. `PHIRedactingFilter` in `log/log_config.py` contains no regex targeting URL query parameters (`token=...`).
- **Architectural Impact:** The administrative API bearer token is logged in cleartext into `HealthMesh_log_<date>.log` and printed to console on every connection attempt and every 5-second reconnection loop, violating Rule 3 and Rule 6.

### 2.2 Incomplete PHI Redaction in HL7 Log Records
- **Citations:** `log/log_config.py:27`, `log/log_config.py:59-69`
- **Mechanism:** The PID redaction regular expression:
  ```python
  PID_PATTERN = re.compile(r'(PID\|[^|\r\n]*\|[^|\r\n]*\|)([^|\r\n]*)(\|[^|\r\n]*\|)([^|\r\n]*)')
  ```
  captures:
  - Group 1: `PID-1` (Set ID) and `PID-2` (External Patient ID). **`PID-2` is left unredacted.**
  - Group 2: `PID-3` (Internal Patient ID - redacted).
  - Group 3: `PID-4` (Alternate Patient ID). **`PID-4` is left unredacted.**
  - Group 4: `PID-5` (Patient Name - redacted).
  - Crucial identifiers: `PID-7` (Date of Birth), `PID-11` (Patient Address), `PID-13` (Phone Number), and `PID-19` (SSN/National ID) are completely unmatched and left in cleartext.
- **Architectural Impact:** Clinical instruments outputting national IDs in `PID-2` or `PID-4`, or transmitting birthdates in `PID-7`, have protected health information written directly into application log files and in-memory communication message deques.

### 2.3 Exception Traceback PHI & Password Leakage (`exc_info`)
- **Citations:** `log/log_config.py:36-47`
- **Mechanism:** `PHIRedactingFilter.filter` inspects only `record.msg` and `record.message`. It does not sanitize `record.exc_info` or `record.exc_text`.
- **Architectural Impact:** Whenever an exception is logged with `exc_info=True` or via `log_error` in an exception block, Python's `logging.Formatter` serializes the traceback. Any local variables, cleartext SQL connection strings with passwords (`PWD=...`), or unredacted patient payloads in the traceback lines bypass `PHIRedactingFilter` completely and leak to disk and stdout.

### 2.4 Unauthenticated Information Disclosure Endpoint `/server/status`
- **Citations:** `api/app.py:185-191`
- **Mechanism:**
  ```python
  @app.get("/server/status", response_model=ServerStatus)
  async def get_server_status():
      ...
      clients = clients_with_names
      return ServerStatus(state=state, text=text, clients=clients)
  ```
  The endpoint lacks `dependencies=[Depends(verify_token)]`.
- **Architectural Impact:** Any client on the local network can query this endpoint without credentials, enumerating all connected analyzers, their IP addresses, assigned identifiers, and operational states.

### 2.5 False HTTP 200 Success on Server Startup Failure
- **Citations:** `api/app.py:231-242`
- **Mechanism:** When `/server/start` encounters an error during `start_server()`:
  ```python
  except Exception as e:
      log_error(f"[API] Exception in /server/start: {e}")
      return {"message": f"Failed to start server: {e}"}
  ```
- **Architectural Impact:** Returns HTTP 200 OK. Clients inspecting `response.status_code == 200` assume the TCP server is running when it failed to bind or crashed. Furthermore, the unredacted raw exception `str(e)` is leaked to the client.

### 2.6 Fernet Key Concurrency Race Condition & Permissive ACLs
- **Citations:** `setting/config.py:248-256`
- **Mechanism:** `get_encryption_key()` checks `if os.path.exists(target_key_url):` without cross-process locking. If multiple processes launch concurrently on a clean system, both observe that `key.key` is missing, both generate distinct keys, and race to write `setting\key.key`. The second write overwrites the first, causing `InvalidToken` decryption crashes. Furthermore, `key.key` is created with default OS permissions rather than restricted user-only ACLs (`0o600`).

### 2.7 Silent Lock Failure on `portalocker.Lock` Timeout
- **Citations:** `setting/config.py:54-62`
- **Mechanism:**
  ```python
  try:
      lock = portalocker.Lock(path, timeout=timeout)
      lock.acquire()
  except Exception:
      lock = None
  try:
      yield
  ```
  If lock acquisition times out after 5.0 seconds due to file contention, the exception is caught, `lock` is set to `None`, and the function **silently executes the critical section without holding the file lock**.
- **Architectural Impact:** Completely breaks cross-process mutual exclusion guarantees. Multiple processes simultaneously read and write `config.json`, causing configuration corruption.

### 2.8 Config Wipeout on Transient Read Error
- **Citations:** `setting/config.py:333-335`
- **Mechanism:**
  ```python
  existing_config = _load_config(config_url, encrypt_list, key_url)
  if not existing_config:
      existing_config = default_config_data.copy()
  ```
  If `_load_config()` fails due to transient file locking or a partial read, it returns `{}`. `save_config()` replaces it with `default_config_data.copy()`, permanently overwriting custom passwords, ports, and analyzer configurations with default factory values.

### 2.9 Boolean String Casting Bug in `save_config`
- **Citations:** `setting/config.py:346-347`
- **Mechanism:**
  ```python
  config_data_to_save[key] = bool(value)
  ```
  In Python, `bool("False")` and `bool("0")` evaluate to `True`.
- **Architectural Impact:** Passing `"AUTO_START_CBC_SERVER": "False"` or `"DARK_MODE": "False"` from configuration views or API endpoints sets the configuration values to `True`.

---

## Category 3: Protocol Edge Cases & Data Integrity (Rules 1 & 5)

### 3.1 MLLP Standalone `\x1c` Deadlock on Live Sockets
- **Citations:** `server/client_handler.py:129-134`
- **Mechanism:**
  ```python
  # If 0x1C is the very last byte in buffer, await next TCP chunk to determine
  # if trailing \r (0x0D) is arriving, avoiding orphaned delimiter split (unless EOF reached)
  if len(buffer) == end_pos + 1:
      if not is_eof:
          break
  ```
  When an analyzer transmits a message ending in standalone `\x1c` (or if `\x1c` arrives at the end of a TCP packet while `\r` is delayed), the handler breaks out of the framing loop to wait for more data from `reader.read()`.
- **Architectural Impact:** Half-duplex lab analyzers transmit the full message and immediately stop sending bytes, waiting for the server's ACK. Because the server is waiting for more bytes from the analyzer and the analyzer is waiting for the server's ACK, both endpoints enter an **unrecoverable protocol deadlock**.

### 3.2 Outgoing Data Crash on `ACK^O02` (`None.encode()`)
- **Citations:** `server/outcoming_data.py:18`, `server/client_handler.py:161-171`
- **Mechanism:** When an analyzer acknowledges a patient demographic query, it sends `ACK^O02`. `hl7responder.py:89` processes this and returns `None` as the response string. In `client_handler.py:169`, `send_outgoing_data(writer, response)` is called with `response = None`.
  In `server/outcoming_data.py:18`:
  ```python
  writer.write(response.encode())
  ```
- **Architectural Impact:** Calling `None.encode()` raises `AttributeError: 'NoneType' object has no attribute 'encode'`, crashing the connection handler and abruptly closing the TCP socket.

### 3.3 Silent Exception Suppression in Incoming Data Pipeline (Rule 5 Violation)
- **Citations:** `server/incoming_data.py:28-35`, `server/client_handler.py:161, 172-176`
- **Mechanism:** In `server/incoming_data.py`:
  ```python
  def _process_incoming_data_sync(message):
      try:
          ...
      except Exception as e:
          log_error(f"Error processing incoming data: {e}", source=SOURCE)
          return None
  ```
  When parsing, validation, or database execution fails, `_process_incoming_data_sync` catches the exception and returns `None`.
  In `client_handler.py:161`:
  ```python
  if handel_response is not None:
      ...
  else:
      log_info(f"No response generated for {client_address}", source=SOURCE)
  ```
- **Architectural Impact:** No exception is raised in `client_handler.py`, so the NAK generation block (`client_handler.py:187-198`) is never reached. The server sends **neither ACK nor NAK**, violating Rule 5. The analyzer hangs until its internal timeout expires and disconnects.

### 3.4 Unconditional Destruction of `MANUAL` Data (Silent Clinical Data Loss)
- **Citations:** `hl7msghandel/hl7fitsql.py:39-46`, `hl7msghandel/hl7fitsql.py:60-65`
- **Mechanism:**
  ```python
  elif value == "MANUAL":
      try:
          if manual_data is not None:
              result_dictionary[key] = manual_data[key]
          result_dictionary_deleted_list.append(key) # UNCONDITIONAL DELETION
      except Exception as e:
          ...
  for result in result_dictionary_deleted_list:
      del result_dictionary[result]
  ```
- **Architectural Impact:** When manual test entries (e.g. manual leukocyte differentials: `EOSINOPHIL`, `BASOPHIL`, `BAND`, `BLAST`) are supplied via `manual_data`, they are assigned to `result_dictionary` and then **immediately deleted**. Manual test results can never be persisted to the database.

### 3.5 Missing SQL Keys Insert Literal `"SQL"` String into Database
- **Citations:** `hl7msghandel/hl7fitsql.py:31-38`
- **Mechanism:**
  ```python
  if value == "SQL":
      try:
          if sql_data is not None:
              result_dictionary[key] = sql_data[key]
      except Exception as e:
          log_error(f"Error updating sql dictionary: {e}", source=SOURCE)
  ```
  If `sql_data` is `None` or missing the key, the key is left with its initial dictionary value: the literal string `"SQL"`.
- **Architectural Impact:** In `database/sqlqueries.py`, the literal string `"SQL"` is bound as an SQL parameter and inserted into SQL Server datetime or integer columns, causing query execution failures.

### 3.6 HL7 Segment Separator Normalization Failure
- **Citations:** `hl7msghandel/hl7parser.py:23`
- **Mechanism:** `python-hl7` splits segments strictly on `\r`. If an instrument or gateway sends `\r\n` (CRLF), the `\n` is prepended to subsequent segment tags (e.g. `\nPID`). Segment queries (`msg.segments("PID")`) fail with `KeyError`. If the message uses Unix `\n` (LF), the entire message collapses into a single segment.
- **Architectural Impact:** Analyzers transmitting standard network CRLF or Unix LF segments fail parsing.

### 3.7 Ignored HL7 Validation Results
- **Citations:** `hl7msghandel/hl7parser.py:29-33`
- **Mechanism:**
  ```python
  validate_hl7_message(hl7_message, message_direction)
  return hl7_message
  ```
  The boolean return value of `validate_hl7_message` is discarded. Corrupt or malformed messages are returned as valid.

### 3.8 Missing Bounds Checks and Crash Vectors in Responder
- **Citations:** `hl7msghandel/hl7responder.py:43, 63`, `hl7msghandel/hl7responder.py:225`
- **Mechanism:**
  1. `if len(hl7_msh) <= 8: raise ValueError(...)`: If MSH has 9 or 10 fields, accessing `hl7_msh[9]` or `hl7_msh[10]` crashes with `IndexError`.
  2. `patient_id = hl7_message.segments("ORC")[0][3]`: Crashes with `KeyError` if `ORC` is missing, or `IndexError` if fewer than 4 fields exist.

### 3.9 Delimiter Injection in Outbound Order Responses
- **Citations:** `hl7msghandel/hl7responder.py:336`
- **Mechanism:**
  ```python
  order_response = f"MSH|^~\\&|...PID|1||{patient_id}|{patient_name}|{patient_birth_date}|{patient_sex}..."
  ```
  Database variables (`patient_name`, `patient_id`) are interpolated directly into the HL7 message string without sanitizing or escaping delimiter characters (`|`, `^`, `~`, `\`, `&`).
- **Architectural Impact:** If a patient name contains a caret (e.g. `DOE^JOHN`) or pipe, the HL7 structure is corrupted, causing analyzer parsing errors.

---

## Category 4: Concurrency, Thread Safety & Resource Lifecycle (Rules 2 & 7)

### 4.1 Unconstrained Connection Creation in `ConnectionPool`
- **Citations:** `database/sqlconnection.py:63-68`, `database/sqlconnection.py:90-116`
- **Mechanism:** `ConnectionPool` configures `max_connections = 10`. However, in `get_connection()`:
  ```python
  while not self._pool.empty():
      # acquire idle connection...
  # Pool is empty or all checked connections were stale: create a new connection
  conn = self._create_raw_connection()
  ```
  There is **no check against `max_connections`**, **no semaphore**, and **no wait timeout**.
- **Architectural Impact:** Under concurrent load, the pool spawns unlimited physical ODBC connections to SQL Server, exhausting database worker threads and client ephemeral ports.

### 4.2 Desynchronized `_active_count` and Double-Release Aliasing
- **Citations:** `database/sqlconnection.py:99-100, 107-108, 129-130, 137-138, 154-155`
- **Mechanism:**
  1. Acquiring an existing connection from `_pool.get_nowait()` does not increment `_active_count`, while releasing a connection does not decrement it. `_active_count` fails to represent either checked-out connections or total connections.
  2. `release_connection(conn)` does not check if `conn` is already in `self._pool`. If released twice, the same connection instance is placed in the queue twice. Two concurrent worker threads receive the same `Connection` object, triggering fatal PyODBC concurrency errors (`HY000 Connection is busy with results for another command`).

### 4.3 Connection Leak via Raw `get_db_connection()`
- **Citations:** `database/sqlconnection.py:187-205`, `database/db_schema.py:27`, `database/db_schema.py:94-96`
- **Mechanism:** In `db_schema.py`:
  ```python
  connection = get_db_connection()
  ...
  finally:
      if connection:
          connection.close()
  ```
  `connection.close()` bypasses `_global_pool.release_connection()`. The pool is never notified that the connection was closed.

### 4.4 Missing `pyodbc.InterfaceError` Eviction
- **Citations:** `database/sqlconnection.py:179-184`
- **Mechanism:**
  ```python
  except (pyodbc.OperationalError, pyodbc.DatabaseError, ConnectionError):
      discard = True
      raise
  ```
  In PyODBC, `pyodbc.InterfaceError` inherits directly from `pyodbc.Error`, **not** from `pyodbc.DatabaseError`. When a TCP socket disconnects as an `InterfaceError`, `discard` remains `False`, and the broken connection is recycled into the pool.

### 4.5 Half-Open Socket Leak (Missing Read Inactivity Timeout)
- **Citations:** `server/client_handler.py:94`
- **Mechanism:** `data = await reader.read(BUFFER_SIZE_LIMIT)` has no `asyncio.wait_for` timeout and no `SO_KEEPALIVE` configured.
- **Architectural Impact:** When an analyzer loses power or disconnects silently, the coroutine hangs indefinitely. File descriptors and client entries in `clients` leak permanently.

### 4.6 Blocking Socket Bind/DNS Directly on Main Event Loop (Rule 2)
- **Citations:** `server/server.py:23-46, 164`
- **Mechanism:** `start_server()` invokes `check_server_start_capability()` directly on the active event loop without `asyncio.to_thread`. This performs synchronous socket creation, DNS resolution, and `bind()`, freezing the asyncio event loop during network latency.

### 4.7 Abrupt Child Process Force-Kill on Windows
- **Citations:** `main.py:386-398`, `main.py:400-403`
- **Mechanism:** On Windows, `proc.terminate()` executes the Win32 API `TerminateProcess(hProcess, 1)`.
- **Architectural Impact:** Child processes (`fastapi_process`, `flet_process`) are abruptly killed without executing `finally:` blocks, `atexit` handlers, Uvicorn lifespan shutdown, or database connection pool cleanups.

### 4.8 UI Thread Safety Violations in Desktop Views
- **Citations:**
  - `gui/views/message_components.py:639-648`: Spawns a raw OS `threading.Thread` that sleeps 2s and invokes `page.update()` directly outside the asyncio event loop.
  - `gui/views/stream_controls.py:96-103` & `gui/views/stream.py:142-164`: `SearchBar` starts a `threading.Timer(0.3, trigger)` which calls `self.update()` on the background timer thread.
  - `gui/views/settings.py:45`: Synchronous DB test blocks the UI thread for 15–30s on unreachable networks.

---

## Category 5: Database Transactions, SQL Binding & Server Compatibility

### 5.1 Stored Procedure DML Rollback with `expect_results=True`
- **Citations:** `database/sqlqueriesExe.py:51-74`, `database/sqlconnection.py:121-125`
- **Mechanism:** When executing stored procedures that return results (`expect_results=True`), `querie_exe` does not execute `connection.commit()`. When `get_db_connection_context()` releases the connection, `release_connection` executes `conn.rollback()`.
- **Architectural Impact:** If a stored procedure performs any INSERT/UPDATE/DELETE operations and also returns a result set, **all changes are unconditionally rolled back**.

### 5.2 Silent Exception Swallowing in `querie_exe`
- **Citations:** `database/sqlqueriesExe.py:93-107`, `database/sqlqueries.py:62, 127`
- **Mechanism:**
  ```python
  except Exception as e:
      ...
      if isinstance(e, (pyodbc.OperationalError, ConnectionError)):
          raise
      return None
  ```
  `pyodbc.IntegrityError`, `ProgrammingError`, and `DataError` are caught, rolled back, and swallowed, returning `None`.
- **Architectural Impact:** Callers cannot distinguish between successful queries and failed queries. In `hl7responder.py:164-167`, the server sends an ACK claiming success even when database insertion failed and clinical data was lost.

### 5.3 `None` Parameter Binding in WHERE Clauses Evaluates to UNKNOWN
- **Citations:** `database/sqlqueries.py:110-123`, `database/sqlqueries.py:166-178`, `database/sqlqueries.py:213-223`
- **Mechanism:** In `data_update_for`, `data_select_for`, and `data_delete_for`:
  ```python
  condition_strings = [f"{value} = ?" for key, value in condition.items()]
  ```
  When condition values are `None`, PyODBC executes `WHERE [patientid] = NULL`. In SQL Server (`ANSI_NULLS ON`), comparing `= NULL` evaluates to `UNKNOWN` (falsy), updating or deleting 0 rows silently.

### 5.4 Indiscriminate `str()` Conversion Forcing `CONVERT_IMPLICIT`
- **Citations:** `database/sqlqueries.py:50-54`, `database/sqlqueries.py:100-104`
- **Mechanism:** All parameter values are unconditionally coerced to strings (`str(hl7_column[value])`).
- **Architectural Impact:** PyODBC binds all parameters as `VARCHAR`/`NVARCHAR`. SQL Server is forced to apply `CONVERT_IMPLICIT` on integer and floating point columns, preventing index seeks and degrading query performance.

### 5.5 Empty Column Mapping Generates Invalid SQL Syntax
- **Citations:** `database/sqlqueries.py:40-59`, `database/sqlqueries.py:91-123`
- **Mechanism:** If an incoming HL7 message has no keys matching the schema, `column_name` is empty `{}`.
  Generated SQL: `INSERT INTO [dbo].[cbc] () VALUES ();`.

### 5.6 Datetime Truncation via `BETWEEN` in `GetPatientInfo.sql`
- **Citations:** `Sql_reqirement_querys/Reallab/GetPatientInfo.sql:74-77`
- **Mechanism:** `BETWEEN @StartDate AND @EndDate` truncates `@EndDate = '2026-11-14'` to `'2026-11-14 00:00:00'`, excluding all tests performed on the end date after midnight.

### 5.7 Missing Unique Constraint & Race Condition in `SendOutLog`
- **Citations:** `Sql_reqirement_querys/Reallab/InsertSendOutLog.sql:17-22`, `CreateSendOutLog.sql:1-14`
- **Mechanism:** `SendOutLog` has only a primary key on `LogID`. Concurrent queries pass `IF NOT EXISTS` and insert duplicate rows for `(PatientID, TestName)`.

---

## Category 6: Desktop Presentation & Flet Lifecycle

### 6.1 Deprecated Flet 0.26 / 1.0+ Properties
- **Citations:** `gui/components.py:62-63`, `gui/views/patient.py:353, 373`, `gui/views/send_out.py:162, 401`, `gui/views/settings.py:48`
- **Mechanism:** Views assign to deprecated properties: `page.snack_bar = ft.SnackBar(...)` and `page.splash = ft.ProgressBar(...)`. Modern Flet requires `page.open(snack)` and progress overlays.

### 6.2 Monolithic View Functions (>450 Lines)
- **Citations:** `gui/views/cbc_report.py:40-555` (`save_report_as_html` is 459 lines), `gui/views/send_out.py:102-334` (`create_send_out_row` is 232 lines).
- **Architectural Impact:** Deeply nested closures and mixed responsibilities (HTML generation, SVG file loading, CSS formatting, and DB mapping) make maintenance and testing impossible.

### 6.3 Message Deduplication Bug in Stream
- **Citations:** `gui/views/stream.py:592-598`
- **Mechanism:** Message uniqueness is verified solely against `msg["timestamp"]`. When analyzers send multiple messages within the same second, subsequent messages are silently dropped from the UI.

### 6.4 Client-Side Unpaged Table Memory Accumulation
- **Citations:** `gui/views/patient.py:207`, `gui/views/send_out.py:441`
- **Mechanism:** Searches pull the entire matching dataset into client RAM without database pagination (`OFFSET`/`FETCH`). Datasets with 50,000 records consume hundreds of megabytes in client memory.

---

## Category 7: Build, Packaging & Dependency Omissions

### 7.1 Missing Runtime Dependencies in Configuration Files
- **Citations:** `pyproject.toml`, `requirements.txt`
- **Omissions:** `portalocker` (imported in `setting/config.py:11`) and `websockets` (imported in `gui/api_methods.py:351`) are omitted from `requirements.txt` and `pyproject.toml`.

### 7.2 Missing PyInstaller Hidden Imports
- **Citations:** `build.py:32-42`
- **Omissions:** `portalocker`, `concurrent_log_handler`, and Uvicorn runtime submodules (`uvicorn.loops.auto`, `uvicorn.protocols.http.auto`, etc.) are missing from `--hidden-import`, causing PyInstaller standalone builds to crash on startup.

### 7.3 Relative Path Resolution Failure in PyInstaller Frozen Mode
- **Citations:** `main.py:76`, `setting/config.py:78-79`
- **Mechanism:** Bundled assets and keys are referenced as relative paths (`assets`, `setting\key.key`) instead of resolving against `sys._MEIPASS`.

---

## Category 8: Test Suite Blind Spots

1. **GUI Presentation Layer (0% Coverage on 14 of 16 modules):** Only 9 of 96 tests cover GUI code. `gui/main_flet.py`, `gui/api_methods.py`, `dashboard.py`, `send_out.py`, `settings.py`, and `cbc_report.py` have 0% automated test coverage.
2. **Process Lifecycle (0% Coverage on `main.py`):** Zero tests verify dynamic port allocation retry, process termination, signal handling, or database configuration modal loops.
3. **Connection Pooling & Concurrency:** Zero multi-threaded tests verify pool behavior under saturation, connection timeouts, or broken interface eviction.
4. **Asserting Buggy Behavior:** `tests/hl7msghandel/test_hl7fitsql.py:43` asserts that `MANUAL` fields are deleted from dictionary outputs rather than verifying retention.
