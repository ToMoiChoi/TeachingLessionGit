#!/bin/bash
# Ban Mac cua BAM_DE_BUILD_VA_DAY_GIT.bat - bam dup chuot de chay
cd "$(dirname "$0")"
export PYTHONUTF8=1
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python

pause() { read -r -p "Bam Enter de dong..."; }

echo "========================================================"
echo "  NUT BAM: TU DONG BUILD GAME (APK + TAR.GZ + INDEX)"
echo "  VA DAY LEN GIT"
echo "========================================================"
echo

# ---- Tim cac thu muc game (co file main.py) ----
GAMES=()
for d in */; do
    d="${d%/}"
    if [ -f "$d/main.py" ]; then
        GAMES+=("$d")
        echo "  [${#GAMES[@]}] $d"
    fi
done

if [ ${#GAMES[@]} -eq 0 ]; then
    echo "[LOI] Khong tim thay thu muc game nao co file main.py!"
    pause; exit 1
fi

echo
read -r -p "Chon so thu tu game cua ban roi bam Enter: " CHOICE
if ! [[ "$CHOICE" =~ ^[0-9]+$ ]] || [ "$CHOICE" -lt 1 ] || [ "$CHOICE" -gt ${#GAMES[@]} ]; then
    echo "[LOI] So ban chon khong hop le!"
    pause; exit 1
fi
GAME="${GAMES[$((CHOICE-1))]}"

echo
read -r -p "Dat game nay lam trang chu web (index.html o thu muc goc)? (y/n): " MAKEHOME

echo
echo "[1/5] Kiem tra pygbag..."
if ! $PY -m pip show pygbag >/dev/null 2>&1; then
    echo "Chua co pygbag, dang cai dat..."
    $PY -m pip install pygbag
fi

echo "[2/5] Dang build game \"$GAME\" bang pygbag (cho 1 chut nhe)..."
if ! $PY -m pygbag --build --disable-sound-format-error "$GAME/main.py"; then
    echo "[LOI] Build that bai! Xem loi o phia tren."
    pause; exit 1
fi

echo "[3/5] Sao chep file apk, tar.gz, index.html ra thu muc game..."
cp -f "$GAME"/build/web/* "$GAME"/
if [ "$MAKEHOME" = "y" ] || [ "$MAKEHOME" = "Y" ]; then
    echo "      Sao chep ra thu muc goc lam trang chu..."
    cp -f "$GAME"/build/web/* .
fi
ls "$GAME/build/web"

echo "[4/5] Commit vao Git..."
git add .
git commit -m "Build web moi cho $GAME: $(date '+%d/%m/%Y %H:%M:%S')"

echo "[5/5] Lay code moi nhat cua cac ban khac roi day len GitHub..."
if ! git pull --rebase origin main; then
    echo "[LOI] Bi xung dot khi lay code moi. Nho thay/co giup nhe!"
    pause; exit 1
fi

if git push origin main; then
    echo "========================================================"
    echo "  DA DAY LEN GIT THANH CONG! Vercel se tu dong cap nhat."
    echo "  Game cua ban: /$GAME/index.html"
    echo "========================================================"
else
    echo "[LOI] Khong the push len Git. Kiem tra mang hoac dang nhap Git."
fi

pause
