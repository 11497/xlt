@echo off
setlocal

rem 始终在项目目录运行，即使是双击启动。
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

rem 文档索引/删除 Worker：必须启动，否则上传文档会一直停留在 pending。
start "XLT Worker" cmd /k "cd /d ""%PROJECT_DIR%"" && uv run python -m ai.indexing_worker"

rem 可选对账服务：恢复卡死任务、核对索引，不删除 OSS 对象。取消下一行注释即可启用。
rem start "XLT Reconcile" cmd /k "cd /d ""%PROJECT_DIR%"" && uv run python -m ai.reconciliation_service"

start "XLT Frontend" cmd /k "cd /d ""%PROJECT_DIR%frontend"" && npm run dev -- --host"

echo Backend, Worker and frontend startup windows have been opened.
exit /b 0