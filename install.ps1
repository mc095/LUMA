# Download and set up LUMA Voice Assistant
$ErrorActionPreference = "Stop"

Write-Host "🎙️ LUMA Voice Assistant - Installation Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# Create installation directory
$installDir = "LUMA"
if (!(Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir | Out-Null
}
Set-Location $installDir

# Download latest release
Write-Host "`n📦 Downloading LUMA..." -ForegroundColor Yellow
$releaseUrl = "https://github.com/mc095/LUMA/releases/latest/download/LUMA.exe"
Invoke-WebRequest -Uri $releaseUrl -OutFile "LUMA.exe"

# Create config file from user input
Write-Host "`n🔑 Setting up configuration..." -ForegroundColor Yellow
$groqKey = Read-Host "Enter your GROQ API key"
$geminiKey = Read-Host "Enter your Google (Gemini) API key (optional, press Enter to skip)"

$configContent = @"
"""Build configuration with embedded API keys."""

# API Keys
GROQ_API_KEY = "$groqKey"
GEMINI_API_KEY = "$geminiKey"
"@

$configContent | Out-File -FilePath "build_config.py" -Encoding UTF8

Write-Host "`n✅ Installation complete!" -ForegroundColor Green
Write-Host "To start LUMA, run:" -ForegroundColor Yellow
Write-Host "cd $installDir" -ForegroundColor White
Write-Host ".\LUMA.exe" -ForegroundColor White

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")