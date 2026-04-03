# Run Parvarish backend with Uvicorn
Set-Location "$PSScriptRoot"

if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Error "Virtual environment not found at .\venv. Create it first with: python -m venv venv"
    exit 1
}

# Activate venv
. .\venv\Scripts\Activate.ps1

# Start FastAPI server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
