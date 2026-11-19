@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
cd /d "%~dp0"

rem ---- Configure PATH for Python on Windows ----
if exist "%LOCALAPPDATA%\Python\bin" set "PATH=%LOCALAPPDATA%\Python\bin;!PATH!"
if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64" set "PATH=%LOCALAPPDATA%\Python\pythoncore-3.14-64;%LOCALAPPDATA%\Python\pythoncore-3.14-64\Scripts;!PATH!"
if exist "%LOCALAPPDATA%\Programs\Python\Python314" set "PATH=%LOCALAPPDATA%\Programs\Python\Python314;%LOCALAPPDATA%\Programs\Python\Python314\Scripts;!PATH!"
if exist "%LOCALAPPDATA%\Programs\Python\Python313" set "PATH=%LOCALAPPDATA%\Programs\Python\Python313;%LOCALAPPDATA%\Programs\Python\Python313\Scripts;!PATH!"
if exist "%LOCALAPPDATA%\Programs\Python\Python312" set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;!PATH!"
if exist "%LOCALAPPDATA%\Programs\Python\Python311" set "PATH=%LOCALAPPDATA%\Programs\Python\Python311;%LOCALAPPDATA%\Programs\Python\Python311\Scripts;!PATH!"

set "PYTHONUTF8=1"

echo ========================================================
echo   AUTO-BUILD WEB (APK + TAR.GZ + INDEX)
echo   AND PUSH TO GIT
echo ========================================================
echo.

rem ---- Find valid Python command ----
set "PY_CMD="
python -c "import sys; sys.exit(0)" >nul 2>&1
if !ERRORLEVEL! EQU 0 (
    set "PY_CMD=python"
) else (
    py -c "import sys; sys.exit(0)" >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set "PY_CMD=py"
    ) else if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
        set "PY_CMD=%LOCALAPPDATA%\Python\bin\python.exe"
    ) else if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
        set "PY_CMD=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
    )
)

if "!PY_CMD!"=="" (
    echo [ERROR] Python not found! Please install Python or disable App execution aliases.
    pause
    exit /b 1
)

rem ---- Find Git Root ----
set "GIT_ROOT="
for /f "delims=" %%g in ('git rev-parse --show-toplevel 2^>nul') do set "GIT_ROOT=%%g"
if defined GIT_ROOT (
    set "GIT_ROOT=!GIT_ROOT:/=\!"
) else (
    set "GIT_ROOT=%~dp0"
    if "!GIT_ROOT:~-1!"=="\" set "GIT_ROOT=!GIT_ROOT:~0,-1!"
)

rem ---- Find Game Directory ----
if exist "%~dp0main.py" (
    for %%I in ("%~dp0.") do set "GAME=%%~nxI"
    set "GAME_DIR=%~dp0"
    if "!GAME_DIR:~-1!"=="\" set "GAME_DIR=!GAME_DIR:~0,-1!"
    echo   [+] Detected game in current directory: !GAME!
) else (
    cd /d "!GIT_ROOT!"
    set COUNT=0
    for /d %%D in (*) do (
        if exist "%%D\main.py" (
            set /a COUNT+=1
            set "GAME!COUNT!=%%D"
            echo   [!COUNT!] %%D
        )
    )

    if !COUNT! EQU 0 (
        echo [ERROR] No game directory containing main.py found!
        pause
        exit /b 1
    )

    if !COUNT! EQU 1 (
        echo   [+] Detected 1 game: !GAME1!
        set "GAME=!GAME1!"
    ) else (
        echo.
        set /p CHOICE=Enter the game number and press Enter: 
        set "GAME=!GAME%CHOICE%!"
        if "!GAME!"=="" (
            echo [ERROR] Invalid selection!
            pause
            exit /b 1
        )
    )
    set "GAME_DIR=!GIT_ROOT!\!GAME!"
)

echo.
set /p MAKEHOME=Set this game as homepage (index.html at root)? (y/n): 

echo.
echo [1/5] Checking pygbag...
!PY_CMD! -m pip show pygbag >nul 2>&1
if !ERRORLEVEL! NEQ 0 (
    echo Installing pygbag...
    !PY_CMD! -m pip install pygbag
)

echo [2/5] Building game "!GAME!" with pygbag...
!PY_CMD! -X utf8 -m pygbag --build --disable-sound-format-error "!GAME_DIR!\main.py"
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Build failed! Check the error above.
    pause
    exit /b 1
)

echo [3/5] Copying web files to game directory...
copy /Y "!GAME_DIR!\build\web\*" "!GAME_DIR!\" >nul
if /i "!MAKEHOME!"=="y" (
    echo       Copying to root directory as homepage...
    copy /Y "!GAME_DIR!\build\web\*" "!GIT_ROOT!\" >nul
)
dir /b "!GAME_DIR!\build\web"

echo [4/5] Committing to Git...
cd /d "!GIT_ROOT!"
git add .
git commit -m "Update game to English and new slots layout: %date% %time%" 2>nul || (
    echo       No changes to commit.
)

echo [5/5] Pulling latest changes and pushing to GitHub...
git pull --rebase origin main
if !ERRORLEVEL! NEQ 0 (
    echo [ERROR] Conflict occurred while pulling latest changes.
    pause
    exit /b 1
)
git push origin main

if !ERRORLEVEL! EQU 0 (
    echo ========================================================
    echo   PUSHED TO GIT SUCCESSFULLY! Vercel will auto-update.
    echo   Your game: /!GAME!/index.html
    echo ========================================================
) else (
    echo [ERROR] Failed to push to Git. Check network or credentials.
)

pause
