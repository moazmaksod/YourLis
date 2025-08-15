# PowerShell script to build YourLIS as a standalone EXE
# 1. Ensure required folders exist
$folders = @('assets', 'logs', 'setting', 'Sql_reqirement_querys')
foreach ($folder in $folders) {
    if (-not (Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder | Out-Null
    }
}

# 2. Install dependencies
if (Test-Path "requirements.txt") {
    python -m pip install --upgrade pip
    pip install -r requirements.txt
}

# 3. Build with PyInstaller using the updated spec file
pyinstaller --clean --noconfirm main.spec

Write-Host "Build complete. The EXE is in the 'dist' folder."
