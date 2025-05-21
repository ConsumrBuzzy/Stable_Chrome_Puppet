<#
.SYNOPSIS
    Sets up the development environment for Chrome Puppet.
.DESCRIPTION
    This script creates a Python virtual environment and installs all required dependencies.
    It's designed to work on Windows, macOS, and Linux.
#>

param (
    [switch]$Dev = $false
)

$ErrorActionPreference = "Stop"

# Determine the Python command to use
$pythonCmd = if (Get-Command python -ErrorAction SilentlyContinue) {
    "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    "python3"
} else {
    Write-Error "Python is not found. Please install Python 3.8 or higher and try again."
    exit 1
}

# Check Python version
$pythonVersion = & $pythonCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
$pythonMajor = [int]($pythonVersion -split '\\.')[0]
$pythonMinor = [int]($pythonVersion -split '\\.')[1]

if ($pythonMajor -lt 3 -or ($pythonMajor -eq 3 -and $pythonMinor -lt 8)) {
    Write-Error "Python 3.8 or higher is required. Found Python $pythonVersion"
    exit 1
}

Write-Host "Using Python $pythonVersion" -ForegroundColor Green

# Create virtual environment
$venvDir = ".venv"

if (Test-Path $venvDir) {
    Write-Host "Virtual environment already exists at $venvDir" -ForegroundColor Yellow
} else {
    Write-Host "Creating virtual environment at $venvDir..." -ForegroundColor Cyan
    & $pythonCmd -m venv $venvDir
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
        exit 1
    }
}

# Activate virtual environment
$activateScript = if ($IsWindows) {
    ".\$venvDir\Scripts\Activate.ps1"
} else {
    "./$venvDir/bin/Activate.ps1"
}

if (-not (Test-Path $activateScript)) {
    Write-Error "Failed to find activation script at $activateScript"
    exit 1
}

# Activate the virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
. $activateScript

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Cyan
& $pythonCmd -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to upgrade pip"
    exit 1
}

# Install dependencies
$requirementsFile = "requirements.txt"
if ($Dev) {
    $requirementsFile = "requirements-dev.txt"
    Write-Host "Installing development dependencies..." -ForegroundColor Cyan
} else {
    Write-Host "Installing dependencies..." -ForegroundColor Cyan
}

& $pythonCmd -m pip install -r $requirementsFile
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install dependencies"
    exit 1
}

Write-Host ""
Write-Host "✅ Environment setup complete!" -ForegroundColor Green
Write-Host "To activate the virtual environment, run:"
if ($IsWindows) {
    Write-Host "    .\$venvDir\Scripts\Activate.ps1" -ForegroundColor Cyan
} else {
    Write-Host "    source $venvDir/bin/activate" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "To run Chrome Puppet:" -ForegroundColor Yellow
Write-Host "    python main.py --help" -ForegroundColor Cyan
