#!/bin/bash
# Ban Mac cua run_game.bat - bam dup chuot de chay
cd "$(dirname "$0")/TungLamv2"
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python

echo "========================================================"
echo "  KHOI DONG GAME TUNG LAM V2 (BAN DESKTOP PYGAME)"
echo "========================================================"
if ! $PY main.py; then
    echo
    echo "Co loi xay ra khi chay game."
    read -r -p "Bam Enter de dong..."
fi
