@echo off
echo ========================================================
echo   KHOI DONG BAN WEB LOCAL CHO GAME TUNG LAM V2
echo ========================================================
echo Dang mo trinh duyet tai http://localhost:8000 ...
start http://localhost:8000
python -m http.server 8000
