#!/bin/bash
# Ban Mac cua run_web_local.bat - bam dup chuot de chay (Ctrl+C de tat server)
cd "$(dirname "$0")"
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python

echo "========================================================"
echo "  KHOI DONG BAN WEB LOCAL CHO GAME TUNG LAM V2"
echo "========================================================"
echo "Dang mo trinh duyet tai http://localhost:8000 ..."
(sleep 1; open http://localhost:8000) &
$PY -m http.server 8000
