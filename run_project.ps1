$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Advanced Hiring System - Combined Launcher  " -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

$root = $PSScriptRoot

# Phase 2 Backend (Port 8000)
Write-Host "[1/3] Starting Phase 2 Backend (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$root\backend'; ..\.venv\Scripts\python.exe seed_data.py; ..\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload"
)

Start-Sleep -Seconds 3

# Phase 1 Backend (Port 8001)
Write-Host "[2/3] Starting Phase 1 Backend (Port 8001)..." -ForegroundColor Yellow
$p1back = "$root\hiring agent\backend"

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$p1back'; if (-not (Test-Path 'venv')) { python -m venv venv; .\venv\Scripts\pip install -r requirements.txt }; .\venv\Scripts\python.exe -m uvicorn app.main:app --port 8001 --reload"
)

Start-Sleep -Seconds 3

# Phase 1 Frontend (Vite Port 5173)
Write-Host "[3/3] Starting Phase 1 Frontend (Vite - Port 5173)..." -ForegroundColor Yellow
$p1front = "$root\hiring agent\frontend"

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$p1front'; if (-not (Test-Path 'node_modules')) { npm install }; npm run dev"
)

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  All 3 services are starting in separate windows!" -ForegroundColor Green
Write-Host "============================================================"
Write-Host ""
Write-Host "  PHASE 1 - Technical Assessment" -ForegroundColor Cyan
Write-Host "    Candidate Portal   :  http://localhost:5173"
Write-Host "    API Docs           :  http://localhost:8001/docs"
Write-Host ""
Write-Host "  PHASE 2 - Interview Management" -ForegroundColor Cyan
Write-Host "    Admin / Recruiter  :  Open phase-2\index.html in browser"
Write-Host "    Interviewer Portal :  Open phase-2\interviewer_profile.html"
Write-Host "    API Docs           :  http://localhost:8000/docs"
Write-Host ""
Write-Host "  CREDENTIALS (all accounts, password: password123)" -ForegroundColor Yellow
Write-Host "    Admin Recruiter    :  recruiter@hiringco.com"
Write-Host "    Rahul Sharma       :  rahul.sharma@hiringco.com"
Write-Host "    Priya Patel        :  priya.patel@hiringco.com"
Write-Host "    Arun Kumar         :  arun.kumar@hiringco.com"
Write-Host "    Divya Menon        :  divya.menon@hiringco.com"
Write-Host ""
Write-Host "  INTEGRATION - When a Phase 1 assessment completes," -ForegroundColor Magenta
Write-Host "  the candidate is automatically pushed to Phase 2 via webhook."
Write-Host ""
Write-Host "  Close the separate terminal windows to stop all services." -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Green
