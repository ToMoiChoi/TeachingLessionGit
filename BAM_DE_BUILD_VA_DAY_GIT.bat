@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
cd /d "%~dp0"
set PYTHONUTF8=1

echo ========================================================
echo   NUT BAM: TU DONG BUILD GAME (APK + TAR.GZ + INDEX)
echo   VA DAY LEN GIT
echo ========================================================
echo.

rem ---- Tim cac thu muc game (co file main.py) ----
set COUNT=0
for /d %%D in (*) do (
    if exist "%%D\main.py" (
        set /a COUNT+=1
        set "GAME!COUNT!=%%D"
        echo   [!COUNT!] %%D
    )
)

if %COUNT% EQU 0 (
    echo [LOI] Khong tim thay thu muc game nao co file main.py!
    pause
    exit /b 1
)

echo.
set /p CHOICE=Chon so thu tu game cua ban roi bam Enter:
set "GAME=!GAME%CHOICE%!"
if "%GAME%"=="" (
    echo [LOI] So ban chon khong hop le!
    pause
    exit /b 1
)

echo [1/5] Kiem tra pygbag...
py -m pip show pygbag >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Chua co pygbag, dang cai dat...
    py -m pip install pygbag
)

echo [2/5] Dang build game "%GAME%" bang pygbag (cho 1 chut nhe)...
py -m pygbag --build --disable-sound-format-error "%GAME%\main.py"
if %ERRORLEVEL% NEQ 0 (
    echo [LOI] Build that bai! Xem loi o phia tren.
    pause
    exit /b 1
)

echo [3/5] Chep ban build vao games\ va cap nhat danh sach game...
py tools\publish_game.py "%GAME%"
if %ERRORLEVEL% NEQ 0 (
    echo [LOI] Khong chep duoc ban build!
    pause
    exit /b 1
)
set /p GAMEID=<.last_game_id
del .last_game_id

echo [4/5] Commit vao Git...
git add games "%GAME%"
git commit -m "Build web moi cho %GAME%: %date% %time%"

echo [5/5] Lay code moi nhat cua cac ban khac roi day len GitHub...
git pull --rebase origin main
if %ERRORLEVEL% NEQ 0 (
    echo [LOI] Bi xung dot khi lay code moi. Nho thay/co giup nhe!
    pause
    exit /b 1
)
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo ========================================================
    echo   DA DAY LEN GIT THANH CONG! Vercel se tu dong cap nhat.
    echo   Game cua ban: /games/!GAMEID!/
    echo ========================================================
) else (
    echo [LOI] Khong the push len Git. Kiem tra mang hoac dang nhap Git.
)

pause
