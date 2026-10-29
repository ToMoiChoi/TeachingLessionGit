@echo off
echo ========================================================
echo   KHOI DONG GAME TUNG LAM V2 (BAN DESKTOP PYGAME)
echo ========================================================
cd TungLamv2
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Co loi xay ra khi chay game.
    pause
)

