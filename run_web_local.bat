@echo off
cd /d "%~dp0"
echo ========================================================
echo   KHOI DONG BAN WEB LOCAL - TRANG TONG HOP GAME
echo ========================================================
rem Dung 127.0.0.1 chu KHONG dung localhost: pygbag gap "localhost" se tuong
rem la server dev cua no va tai pygame tu /cdn/ local -> loi 404.
echo Dang mo trinh duyet tai http://127.0.0.1:8000 ...
start http://127.0.0.1:8000
python -m http.server 8000 --bind 127.0.0.1
