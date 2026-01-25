# LUMA Installer for Windows
# Run with: irm https://mc095.github.io/LUMA/install.ps1 | iex

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  _    _   _ __  __    _    " -ForegroundColor Cyan
Write-Host " | |  | | | |  \/  |  / \   " -ForegroundColor Cyan
Write-Host " | |  | | | | |\/| | / _ \  " -ForegroundColor Cyan
Write-Host " | |__| |_| | |  | |/ ___ \ " -ForegroundColor Cyan
Write-Host " |_____\___/|_|  |_/_/   \_\" -ForegroundColor Cyan
Write-Host ""
Write-Host " Personal Voice AI Installer" -ForegroundColor Gray
Write-Host " ───────────────────────────" -ForegroundColor Gray
Write-Host ""

# Check for Python
Write-Host "[1/4] Checking Python..." -ForegroundColor Yellow
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "  X Python not found. Please install Python 3.11+ from python.org" -ForegroundColor Red
    exit 1
}
$version = python --version 2>&1
Write-Host "  OK $version" -ForegroundColor Green

# Install uv if not present
Write-Host "[2/4] Checking uv package manager..." -ForegroundColor Yellow
$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    Write-Host "  -> Installing uv..." -ForegroundColor Gray
    irm https://astral.sh/uv/install.ps1 | iex
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}
Write-Host "  OK uv installed" -ForegroundColor Green

# Clone repository
Write-Host "[3/4] Cloning LUMA repository..." -ForegroundColor Yellow
$installDir = "$env:USERPROFILE\LUMA"
if (Test-Path $installDir) {
    Write-Host "  -> Updating existing installation..." -ForegroundColor Gray
    Push-Location $installDir
    git pull --quiet
    Pop-Location
} else {
    git clone --quiet https://github.com/mc095/LUMA.git $installDir
}
Write-Host "  OK Installed to $installDir" -ForegroundColor Green

# Install dependencies
Write-Host "[4/4] Installing dependencies..." -ForegroundColor Yellow
Push-Location $installDir
uv sync --quiet 2>$null
Pop-Location
Write-Host "  OK Dependencies installed" -ForegroundColor Green

Write-Host ""
Write-Host "───────────────────────────────────────" -ForegroundColor Gray
Write-Host " Installation complete!" -ForegroundColor Green
Write-Host "───────────────────────────────────────" -ForegroundColor Gray
Write-Host ""
Write-Host " To start LUMA:" -ForegroundColor White
Write-Host "   cd $installDir" -ForegroundColor Cyan
Write-Host "   uv run python main.py" -ForegroundColor Cyan
Write-Host ""
Write-Host " On first run, you'll need your Groq API key." -ForegroundColor Gray
Write-Host " Get one free at: https://console.groq.com/keys" -ForegroundColor Gray
Write-Host ""
