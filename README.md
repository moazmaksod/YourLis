# YourLIS

**YourLIS** (HealthMesh) is an enterprise-grade Laboratory Information System (LIS) built with Python, Flet, and FastAPI. It streamlines clinical laboratory operations with an intuitive desktop user interface for managing patients, test orders, and medical reports, while maintaining a hardened, high-throughput backend for medical device ingestion (HL7 / MLLP).

---

## ✨ Features

- **📊 Dashboard**: Real-time operational overview of clinical activity, daily test counts, and connected laboratory instruments.
- **📁 Patient Management**: Comprehensive patient registration, search, and medical history tracking.
- **🔬 CBC Reports**: Specialized hematology handling for Complete Blood Count (CBC) parameters, differential flags, and printable PDF reports.
- **📤 Send-Out Management**: Tracking and financial ledger for tests dispatched to external reference laboratories.
- **📡 Device Stream & MLLP Server**: Real-time HL7 analyzer ingestion stream with bounded incremental UI rendering and search debounce.
- **🛡️ Clinical Security & HIPAA Hardening**:
  - Automated PHI/PII log redaction filter preserving `MSH-10` audit traceability.
  - Decoupled Fernet encryption key storage supporting `HEALTHMESH_SECRET_KEY`.
  - Atomic configuration persistence with lock protection.
  - Centralized PyODBC connection pool with native pooling and health recycling.
- **⚙️ Multi-Tier Decoupling**: Complete service boundary isolation separating the Flet presentation layer from the database through FastAPI endpoints.

---

## 🏛️ Architecture Highlights

```
+---------------------+       HTTP (REST)       +---------------------+
|      Flet GUI       |  ====================>  |   FastAPI Service   |
| (Incremental Stream)|                         |   (/api/v1/...)     |
+---------------------+                         +----------+----------+
                                                           |
                                                ConnectionPool (SELECT 1)
                                                           v
+---------------------+                         +---------------------+
|    Lab Analyzers    |                         |  MS SQL Server DB   |
| (Genrui CBC, etc.)  |                         | (Schema Immutability|
+----------+----------+                         +----------+----------+
           |                                               ^
           | TCP / MLLP (0x0B ... 0x1C 0x0D)               | Thread Offload
           v                                               |
+---------------------+    Async Ingestion / NAK    +------+--------------+
|   Async TCP Server  |  ========================>  |    HL7 Responder    |
| (5MB Buffer Ceiling)|                             |  (ACK/ORR Generation)
+---------------------+                             +---------------------+
```

1. **Schema Immutability**: All SQL mapping dictionaries are deeply copied, ensuring partial incoming HL7 payloads never strip global schema definitions.
2. **Non-Blocking Ingestion**: Synchronous database queries and HL7 processing are offloaded to worker threads via `asyncio.to_thread()`, keeping TCP ingestion responsive during peak analyzer bursts.
3. **Resilient MLLP Framing**: Standard `\x0b` (VT) and `\x1c\x0d` (FS CR) frame boundary reassembly protects against TCP fragmentation and packet coalescing, bounded by a 5MB memory guard.
4. **Resilient Error Recovery**: Analyzers receive standard HL7 NAK frames (`MSA|AE` or `MSA|AR`) upon processing errors, maintaining persistent socket connections without disconnecting instruments.

---

## 🚀 Getting Started

### Prerequisites
- **Database**: Microsoft SQL Server (or compatible instance configured in `setting/config.json`)
- **Package Manager**: [uv](https://docs.astral.sh/uv/) (recommended) or Python 3.10+

---

### Quick Start with `uv` (Recommended)

`uv` automatically manages Python runtimes, virtual environments, and dependencies.

#### 1. Clone the repository
```bash
git clone https://github.com/moazmaksod/YourLis.git
cd YourLis
```

#### 2. Install `uv` (if not already installed)
- **Windows (PowerShell)**:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **macOS / Linux**:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

#### 3. Run the Application
```bash
uv run main.py
```
> **What happens automatically?**
> - `uv` provisions the pinned Python virtual environment.
> - Installs all dependencies in seconds.
> - Starts the FastAPI service, MLLP TCP Server, and Flet desktop GUI.

#### 4. (Optional) Sync or Activate Virtual Environment
```bash
uv sync
```
To activate the virtual environment manually:
- **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (CMD)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

---

### Alternative: Traditional Setup with `venv` & `pip`

```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

---

## 🔐 Security & Secret Key Configuration

To isolate sensitive credentials in production, configure the Fernet encryption key via environment variable:

```bash
# Windows PowerShell
$env:HEALTHMESH_SECRET_KEY="<base64-encoded-fernet-key>"

# Linux / macOS
export HEALTHMESH_SECRET_KEY="<base64-encoded-fernet-key>"
```

If not provided, the system will securely generate and persist a protected key file isolated from configuration data.

---

## 🧪 Testing & Verification

The test suite includes 86 automated unit, contract, and end-to-end integration tests covering database pooling, MLLP socket pipelines, PHI redaction, and UI stream performance.

```bash
# Run tests with uv
uv run pytest -v

# Or with activated virtual environment
pytest -v
```

---

## 📖 Documentation & Guidelines

- [**Developer Guide**](Developer_Guide.md) - Deep architectural breakdown, API endpoints, and subsystem documentation.
- [**User Guide**](User_Guide.md) - End-user manual for laboratory technicians.
- [**Architectural Invariants & Rules**](.antigravity/rules.md) - Mandatory non-negotiable coding guardrails.

---

## 🛠️ Tech Stack

- **GUI**: [Flet](https://flet.dev/) (Flutter for Python)
- **API**: [FastAPI](https://fastapi.tiangolo.com/) (Uvicorn)
- **Device Ingestion**: Asynchronous TCP Server (`asyncio`, MLLP standard)
- **Protocol**: HL7 v2.3.1 (Health Level Seven)
- **Database**: Microsoft SQL Server via `pyodbc` (with native pooling)
- **Security**: Cryptography (Fernet AES-CBC), PHI Redacting Logging Filter
- **Tooling**: [uv](https://docs.astral.sh/uv/), `pytest`

---

## 🤝 Contributing

Please ensure all changes comply with [`.antigravity/rules.md`](.antigravity/rules.md) and maintain 100% test coverage before submitting pull requests.

## 📄 License

This project is licensed under the [MIT](LICENSE) License.
