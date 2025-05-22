<#
.SYNOPSIS
    Uploads the package to PyPI using the PyPI token from environment variables.
.DESCRIPTION
    This script builds the package and uploads it to PyPI using the PYPI_TOKEN environment variable.
    Make sure to set the PYPI_TOKEN environment variable in your .env file.
#>

# Stop on first error
$ErrorActionPreference = "Stop"

# Load environment variables from .env file
if (Test-Path "$PSScriptRoot\..\.env") {
    Get-Content "$PSScriptRoot\..\.env" | ForEach-Object {
        $name, $value = $_.Split('=', 2)
        if ($name -and $name[0] -ne '#') {
            [System.Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim())
        }
    }
}

# Check if PYPI_TOKEN is set
$pypiToken = [System.Environment]::GetEnvironmentVariable("PYPI_TOKEN")
if (-not $pypiToken) {
    Write-Error "PYPI_TOKEN environment variable is not set. Please add it to your .env file."
    exit 1
}

# Build the package
Write-Host "Building package..." -ForegroundColor Cyan
python -m build

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to build the package"
    exit $LASTEXITCODE
}

# Upload to PyPI
Write-Host "Uploading to PyPI..." -ForegroundColor Cyan
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = $pypiToken

twine upload dist/*

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to upload to PyPI"
    exit $LASTEXITCODE
}

Write-Host "Package successfully uploaded to PyPI!" -ForegroundColor Green
