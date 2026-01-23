# Launch Script for Adaptive Persuasion System
# This script helps you start both backend and frontend servers

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "   Adaptive Persuasion System - Launch Helper" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if venv is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  Virtual environment not activated!" -ForegroundColor Yellow
    Write-Host "Activating venv..." -ForegroundColor Yellow
    & .\venv\Scripts\Activate.ps1
}

# Check for HF_TOKEN
if (-not $env:HF_TOKEN) {
    # Try to load from User environment variables
    $userToken = [System.Environment]::GetEnvironmentVariable('HF_TOKEN', 'User')
    if ($userToken) {
        $env:HF_TOKEN = $userToken
        Write-Host "✅ Loaded HF_TOKEN from User environment variables" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "⚠️  HF_TOKEN environment variable not set!" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please set your HuggingFace token:" -ForegroundColor Yellow
        Write-Host '  $env:HF_TOKEN="your_token_here"' -ForegroundColor Green
        Write-Host ""
        Write-Host "Or set it permanently:" -ForegroundColor Yellow
        Write-Host '  [System.Environment]::SetEnvironmentVariable("HF_TOKEN", "your_token_here", "User")' -ForegroundColor Green
        Write-Host ""
        Write-Host "Then run this script again." -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
} else {
    Write-Host "✅ HF_TOKEN already set in current session" -ForegroundColor Green
}

Write-Host "✅ Environment ready!" -ForegroundColor Green
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Starting Backend and Frontend Servers" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend will run on:  http://localhost:8000" -ForegroundColor Green
Write-Host "Frontend will run on: http://localhost:8080" -ForegroundColor Green
Write-Host ""
Write-Host "Opening in separate windows..." -ForegroundColor Yellow
Write-Host ""

# Start backend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; python start_backend.py"

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Start frontend in new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; python start_frontend.py"

Write-Host "✅ Servers launched in separate windows!" -ForegroundColor Green
Write-Host ""
Write-Host "To stop the servers, close the PowerShell windows or press Ctrl+C in each." -ForegroundColor Yellow
Write-Host ""
