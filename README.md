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

## 🚀 Getting Started

### Prerequisites
- Python 3.7+
- SQL Server (or compatible database for the schema)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/moazmaksod/YourLis
   cd YourLis
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv lis_env
   # On Windows:
   lis_env\Scripts\activate
   # On macOS/Linux:
   source lis_env/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

To start the full system (GUI, API, and Device Server):
```bash
python main.py
```

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

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the [MIT](LICENSE) License.
