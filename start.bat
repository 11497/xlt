@echo off
setlocal

rem Always run from the project directory, even when started by double-click.
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

where uv >nul 2>&1
if errorlevel 1 (
    echo [ERROR] uv was not found. Install uv and make sure it is on PATH.
    pause
    exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm was not found. Install Node.js and make sure npm is on PATH.
    pause
    exit /b 1
)

if not exist "%PROJECT_DIR%frontend\package.json" (
    echo [ERROR] frontend\package.json was not found.
    pause
    exit /b 1
)

start "XLT Backend" cmd /k "cd /d ""%PROJECT_DIR%"" && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000"

rem Document indexing/delete Worker: REQUIRED, uploads stay "pending" without it.
start "XLT Worker" cmd /k "cd /d ""%PROJECT_DIR%"" && uv run python -m ai.indexing_worker"

rem Optional reconciliation service: recovers stuck tasks, verifies indexes and
rem cleans orphan OSS objects. Uncomment the next line to enable it.
rem start "XLT Reconcile" cmd /k "cd /d ""%PROJECT_DIR%"" && uv run python -m ai.reconciliation_service"

start "XLT Frontend" cmd /k "cd /d ""%PROJECT_DIR%frontend"" && npm run dev -- --host"

echo Backend, Worker and frontend startup windows have been opened.
exit /b 0
