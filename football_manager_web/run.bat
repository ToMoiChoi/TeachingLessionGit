@echo off
setlocal
cd /d "%~dp0"
title Football Manager Web

echo ========================================================
echo   FOOTBALL MANAGER WEB - PHIEN BAN FC MOBILE 24/25
echo ========================================================
echo.

:: [1] Giai phong cong 5000 va dong cac tien trinh cu
echo [1/3] Dang kiem tra va giai phong cong 5000...
powershell -NoProfile -ExecutionPolicy Bypass -Command "try { Get-NetTCPConnection -LocalPort 5000 -State Listen -EA Stop | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -EA 0 } } catch {}; exit 0" >nul 2>&1
taskkill /f /im FootballManager.exe >nul 2>&1
taskkill /f /im run.exe >nul 2>&1

:: [2] Kiem tra thu vien can thiet
echo [2/3] Dang kiem tra thu vien...
python -c "import flask, flask_sqlalchemy" >nul 2>&1
if %errorlevel% neq 0 (
    echo Dang cai dat cac thu vien can thiet...
    python -m pip install -r requirements.txt --disable-pip-version-check
)

:: [3] Khoi chay Game Server (app.py se tu dong mo trinh duyet)
echo [3/3] Dang khoi dong Game Server...
echo.
echo ========================================================
echo   GAME DA SAN SANG TAI: http://127.0.0.1:5000
echo   Giao dien Doi Hinh:   http://127.0.0.1:5000/squad
echo   Vui long khong dong cua so nay trong khi choi game!
echo ========================================================
echo.

python app.py
if %errorlevel% neq 0 (
    echo.
    echo [LOI] Khong the khoi chay game!
    pause
)
