#!/bin/bash
# Ban Mac cua deploy_web.bat - bam dup chuot de chay
cd "$(dirname "$0")"
export PYTHONUTF8=1
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python

pause() { read -r -p "Bam Enter de dong..."; }

echo "========================================================"
echo "  DANG DONG GOI VA TU DONG DAY LEN GIT & VERCEL"
echo "========================================================"

echo "[1/4] Build ban web bang pygbag..."
if ! $PY -m pygbag --build --disable-sound-format-error TungLamv2/main.py; then
    echo "[LOI] Build pygbag that bai!"
    pause; exit 1
fi

echo "[2/4] Sao chep file web ra thu muc goc..."
cp -f TungLamv2/build/web/* .
cp -f TungLamv2/build/web/* TungLamv2/

echo "[3/4] Commit cac thay doi vao Git..."
git add .
git commit -m "Cap nhat code va build web moi: $(date '+%d/%m/%Y %H:%M:%S')"

echo "[4/4] Day len GitHub (origin main)..."
if git push origin main; then
    echo "========================================================"
    echo "  DA DAY LEN GIT THANH CONG! Vercel se tu dong cap nhat."
    echo "========================================================"
else
    echo "[LOI] Khong the push len Git. Vui long kiem tra mang hoac xung dot Git."
fi

pause
