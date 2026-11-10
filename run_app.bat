@echo off
chcp 65001 >nul
title AI Video Factory - Studio Dashboard

cd /d "%~dp0"

echo ======================================================================
echo           🎬 AI VIDEO FACTORY - STUDIO DASHBOARD
echo ======================================================================
echo.

:: 1. Kiểm tra môi trường ảo .venv
if not exist ".venv\Scripts\python.exe" (
    echo [!] Khong tim thay moi truong ao .venv tai thu muc nay!
    echo     Vui long kiem tra lai theo huong dan.
    pause
    exit /b 1
)

:: 2. Kiểm tra xem Ollama có đang chạy không
echo [*] Dang kiem tra ket noi Ollama (http://localhost:11434)...
curl -s -m 2 http://localhost:11434 >nul 2>&1
if %errorlevel% neq 0 (
    echo [CANH BAO] Ollama chua duoc bat hoac chua chay tai localhost:11434!
    echo           Hay mo Ollama tren Windows truoc khi tao video tu dong.
    echo.
) else (
    echo [OK] Ollama da san sang!
)

:: 3. Mở trình duyệt Web Frontend
echo [*] Dang khoi dong Giao Dien Web tai: http://localhost:8000
start "" "http://localhost:8000"

:: 4. Chạy Backend FastAPI Server
echo [*] Server dang lang nghe tren port 8000. Nhan Ctrl + C de dung server.
echo.
.\.venv\Scripts\python.exe server.py

pause

