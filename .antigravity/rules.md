# YourLIS System Architectural Guardrails & Invariants

This document codifies the non-negotiable architectural rules and system invariants for the **YourLIS** (HealthMesh) clinical laboratory information system. Every engineer, subagent, and contributor must adhere strictly to these patterns.

---

## 1. Zero In-Place Schema Mutation (Immutability)
- **Invariant:** The global `db_schema` structures and SQL column mappings in `database/sqlqueries.py` and `hl7msghandel/hl7fitsql.py` must never be mutated in-place.
- **Rule:** Never execute `column_name = db_schema["COLUMN_NAME"]` followed by in-place mutations (e.g. `del column_name[...]` or `column_name.pop(...)`).
- **Enforcement:** Always create an isolated clone using `copy.deepcopy()` or immutable dictionary comprehensions:
  ```python
  column_name = copy.deepcopy(db_schema["COLUMN_NAME"])
  ```
- **Rationale:** In-place deletions permanently alter global dictionary references across the process lifecycle, causing subsequent HL7 transactions to silently omit valid clinical fields.

---

## 2. Non-Blocking Async Ingestion & Event Loop Purity
- **Invariant:** The `asyncio` event loop driving the MLLP TCP server must never be blocked by synchronous database I/O, file access, or blocking thread synchronizations.
- **Rule:** 
  - Never execute blocking PyODBC queries directly inside async functions or event loop tasks.
  - Never call synchronous `queue.Queue.get(timeout=...)` on the main loop.
- **Enforcement:**
  - Offload blocking operations using `asyncio.to_thread(...)` or asynchronous event bridges (`asyncio.Queue` / `asyncio.wait_for`):
  ```python
  response = await asyncio.wait_for(
      asyncio.to_thread(response_queue.get, True, timeout_sec),
      timeout=timeout_sec
  )
  ```
- **Rationale:** Blocking the event loop causes concurrent analyzer connections to stall, dropping packets and timing out hospital instrument feeds.

---

## 3. Strict PHI/PII & Secret Sanitization in Logs
- **Invariant:** Protected Health Information (PHI), Personally Identifiable Information (PII), and authentication credentials must never appear in cleartext in application logs or standard output.
- **Rule:**
  - Do not log raw PID/OBX segment payloads containing patient names, national IDs, or birthdates.
  - Do not log database connection strings containing cleartext passwords.
  - Redaction must preserve clinical traceability identifiers: message control IDs (`MSH-10`), timestamp headers, and status codes.
- **Enforcement:** All logger instances must utilize `log/log_config.py:PHIRedactingFilter`. Sensitive parameters passed to query executors must be masked via `mask_parameters()` prior to debug logging.
- **Rationale:** Compliance with HIPAA, GDPR, and medical device security standards.

---

## 4. Service Boundaries & n-Tier Decoupling
- **Invariant:** Presentation tier (Flet GUI views in `gui/views/`) must remain decoupled from database persistence layers (`database/sqlqueries.py`, `database/sqlconnection.py`).
- **Rule:** GUI view components must never import database query functions directly.
- **Enforcement:**
  - All data retrieval and mutations from the GUI must pass through the Service/API layer: `gui/api_methods.py` or FastAPI endpoints in `api/app.py`.
  - GUI state management must handle backend service timeouts and HTTP errors gracefully using alert dialogs or snackbars rather than unhandled exceptions.
- **Rationale:** Enables running the GUI on separate workstations from the central database server, supports headless/containerized deployments, and enforces authorization boundaries.

---

## 5. Resilient TCP Ingestion & Standard MLLP Framing
- **Invariant:** All TCP socket communications with lab analyzers must conform strictly to Minimal Lower Layer Protocol (MLLP) standards:
  - Start block: `\x0b` (VT)
  - End block: `\x1c\x0d` or `\x1c\r` (FS CR)
- **Rule:**
  - Incoming streams must reassemble fragmented TCP packets across multiple `recv()` calls and cleanly handle coalesced multi-message bursts.
  - The client buffer must enforce a strict ceiling (`MAX_BUFFER_SIZE = 5 * 1024 * 1024`, 5MB) to defend against memory exhaustion attacks or misbehaving instruments.
  - On processing errors or unsupported message types, the server must transmit a standard HL7 NAK (`MSA|AE` or `MSA|AR`) and **keep the socket open**.
- **Enforcement:** Never disconnect an analyzer socket merely because a single message failed parsing or validation.

---

## 6. Secure Configuration & Atomic File Writes
- **Invariant:** Secrets and configuration must follow defensive storage standards.
- **Rule:**
  - Encryption keys must never be stored alongside encrypted ciphertext in the same file or publicly accessible repository files.
  - Always check the `HEALTHMESH_SECRET_KEY` environment variable before falling back to local protected key storage.
  - All writes to configuration files (e.g. `setting/config.json`) must be atomic: write to a secure temporary file first, flush/sync to disk, and atomic-rename via `os.replace` within a `threading.Lock`.
  - Credentials returned by API endpoints or GUI configuration screens must be masked (`********`).
- **Rationale:** Prevents configuration file corruption during abrupt shutdowns or power losses and protects credentials from unauthorized exposure.

---

## 7. Connection Pooling & Resource Lifecycle Management
- **Invariant:** PyODBC database connections must be pooled and managed deterministically.
- **Rule:**
  - Never open unmanaged raw `pyodbc.connect()` calls that can exhaust ephemeral sockets (`TIME_WAIT`).
  - PyODBC native pooling must be enabled (`pyodbc.pooling = True`).
  - Use `ConnectionPool.get_connection()` context managers that automatically validate connection health (`SELECT 1`) and evict corrupted connections on failure.
  - Server shutdown routines must cleanly snapshot and cancel active client tasks, awaiting their termination within bounded timeouts.

