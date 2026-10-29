@echo off
chcp 65001 >nul
echo ========================================================
echo   DANG DONG GOI VA TU DONG DAY LEN GIT & VERCEL
echo ========================================================

set PYTHONUTF8=1

echo [1/4] Build ban web bang pygbag...
python -m pygbag --build --disable-sound-format-error TungLamv2/main.py

if %ERRORLEVEL% NEQ 0 (
    echo [LOI] Build pygbag that bai!
    pause
    exit /b %ERRORLEVEL%
)

echo [2/4] Sao chep file web ra thu muc goc...
copy /Y TungLamv2\build\web\* . >nul
copy /Y TungLamv2\build\web\* TungLamv2\ >nul

echo [3/4] Commit cac thay doi vao Git...
git add .

set COMMIT_MSG=Cap nhat code va build web moi: %date% %time%
git commit -m "%COMMIT_MSG%"

echo [4/4] Day len GitHub (origin main)...
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo ========================================================
    echo   DA DAY LEN GIT THANH CONG! Vercel se tu dong cap nhat.
    echo ========================================================
) else (
    echo [LOI] Khong the push len Git. Vui long kiem tra mang hoac xung dot Git.
)

pause

