# YourLIS

YourLIS is a modern Laboratory Information System (LIS) built with Python, Flet, and FastAPI. It streamlines laboratory workflows by providing a powerful GUI for managing patients, tests, and reports, while maintaining a robust backend for device communication (HL7).

## ✨ Features

- **📊 Dashboard**: Real-time overview of system status and connected devices.
- **📁 Patient Management**: Comprehensive tools for patient registration and search.
- **🔬 CBC Reports**: Specialized handling for Complete Blood Count (CBC) results and reporting.
- **📤 Send Out Management**: Track and manage tests sent to external laboratories.
- **📡 Device Integration**: Live HL7 data stream monitoring and communication.
- **⚙️ Configurable**: Flexible settings for server, database, and appearance.
- **🛡️ Secure**: Built-in authentication and role management.

---

## 🚀 Getting Started

### Prerequisites
- **Database**: SQL Server (or compatible database schema configured in `setting/config.json`)
- **Package Manager**: [uv](https://docs.astral.sh/uv/) (recommended) or Python 3.10+

---

### Quick Start with `uv` (Recommended)

`uv` handles Python runtimes, virtual environments, and dependencies automatically without path corruption or slow installs.

#### 1. Clone the repository
```bash
git clone https://github.com/moazmaksod/YourLis.git
cd YourLis
```

#### 2. Install `uv` (one-time setup if not already installed)
- **Windows (PowerShell)**:
  ```powershell
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
- **macOS / Linux**:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **Via pip** (if you already have Python):
  ```bash
  pip install uv
  ```

#### 3. Run the Application
You don't even need to manually create or activate a virtual environment. Simply execute:
```bash
uv run main.py
```
> **What happens automatically?**
> - `uv` downloads and pins the appropriate Python version if missing.
> - Creates a local `.venv` inside the project folder.
> - Installs all dependencies in seconds.
> - Starts the full system (GUI, API, and HL7 Device Server).

#### 4. (Optional) Sync or Activate Environment Manually
If you want to sync the virtual environment for your IDE (such as VS Code or PyCharm):
```bash
uv sync
```
To activate the virtual environment manually in your shell:
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

If you prefer standard Python tools without `uv`:

1. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   
   # Windows:
   .venv\Scripts\activate
   
   # macOS/Linux:
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

---

## 🧪 Testing & Building

### Running Tests
Using `uv`:
```bash
uv run pytest
```
Or with an activated virtual environment:
```bash
pytest
```

### Building Executable (PyInstaller)
To package the application into a standalone executable:
```bash
uv run python build.py
```
The output executable will be generated inside the `dist/` directory.

---

## 📖 Documentation

For more detailed information, please refer to:
- [**User Guide**](User_Guide.md) - How to use the application.
- [**Developer Guide**](Developer_Guide.md) - Technical details and architecture.

## 🛠️ Tech Stack

- **GUI**: [Flet](https://flet.dev/) (Flutter for Python)
- **API**: [FastAPI](https://fastapi.tiangolo.com/)
- **Server**: Asynchronous TCP Server (`asyncio`)
- **Protocol**: HL7 (Health Level Seven)
- **Database**: SQL Server (via `pyodbc`)
- **Environment & Tooling**: [uv](https://docs.astral.sh/uv/)

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the [MIT](LICENSE) License.
