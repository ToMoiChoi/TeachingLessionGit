"""Copy a pygbag build into games/<id>/ and register it in games/games.json.

Usage: py tools/publish_game.py "<game folder>"
Called by BAM_DE_BUILD_VA_DAY_GIT.bat after `pygbag --build`.
"""
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAMES_DIR = ROOT / "games"
GAMES_JSON = GAMES_DIR / "games.json"


def slugify(name: str) -> str:
    """'Bảo Nam' -> 'baonam', 'TungLamv2' -> 'tunglamv2'."""
    name = name.replace("đ", "d").replace("Đ", "D")
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", name.lower()) or "game"


def ask(prompt: str, default: str) -> str:
    answer = input(f"{prompt} [{default}]: ").strip()
    return answer or default


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    game_dir = (ROOT / sys.argv[1]).resolve()
    build_web = game_dir / "build" / "web"
    if not (build_web / "index.html").exists():
        print(f"[LOI] Khong thay ban build: {build_web}")
        return 1

    games = json.loads(GAMES_JSON.read_text(encoding="utf-8")) if GAMES_JSON.exists() else []
    default_id = slugify(game_dir.name)
    entry = next((g for g in games if g["id"] == default_id), None)

    if entry is None:
        print(f"Game '{game_dir.name}' chua co tren trang chu, nhap thong tin (Enter = giu mac dinh):")
        entry = {
            "id": default_id,
            "title": ask("  Ten game", game_dir.name),
            "author": ask("  Tac gia", game_dir.name),
            "description": ask("  Mo ta ngan", ""),
            "tag": ask("  The loai", "Game"),
            "emoji": "🎮",
            "color": "#3b5bdb",
        }
        games.append(entry)
        GAMES_JSON.write_text(json.dumps(games, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Da them '{entry['title']}' vao games/games.json")

    target = GAMES_DIR / entry["id"]
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(build_web, target, ignore=shutil.ignore_patterns("web-cache"))
    print(f"Da chep ban build vao games/{entry['id']}/:")
    for f in sorted(target.iterdir()):
        print("   ", f.name)

    out = ROOT / ".last_game_id"
    out.write_text(entry["id"], encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
