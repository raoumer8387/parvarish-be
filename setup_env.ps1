# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Error "Python is not installed or not in PATH. Please install Python first."
    exit 1
}

# Create virtual environment if it doesn't exist
$venvPath = "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..." -ForegroundColor Cyan
    python -m venv $venvPath
    Write-Host "Virtual environment created at ./$venvPath" -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Yellow
}

# Activate virtual environment and install requirements
Write-Host "Installing requirements..." -ForegroundColor Cyan
& ".\$venvPath\Scripts\python.exe" -m pip install --upgrade pip
& ".\$venvPath\Scripts\pip.exe" install -r requirements.txt

if ($?) {
    Write-Host "Requirements installed successfully!" -ForegroundColor Green
    Write-Host "`nTo activate the virtual environment, run:" -ForegroundColor Cyan
    Write-Host ".\venv\Scripts\Activate.ps1" -ForegroundColor White
} else {
    Write-Error "Failed to install requirements."
}
