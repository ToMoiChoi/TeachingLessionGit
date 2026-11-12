"""API online dùng chung cho cả lớp (Buổi 13): bảng xếp hạng + lưu tiến trình lên mạng.

Chạy trên Vercel ở đường dẫn /api/online/ (xem vercel.json). Mọi game của lớp gọi chung 1 API,
học viên KHÔNG phải tự deploy server riêng.

Cách gọi (tham số để trên URL, dữ liệu gửi đi dạng JSON):
    GET  /api/online/                                    -> kiểm tra API, cho biết đang lưu ở đâu
    GET  /api/online/?action=top&game=cyberesc&limit=10  -> Top điểm cao
    POST /api/online/?action=score   {"game", "player", "score", "extra": {...}}
    GET  /api/online/?action=load&game=cyberesc&player=Nam
    POST /api/online/?action=save    {"game", "player", "data": {...}}

Nơi lưu dữ liệu:
    - Có biến môi trường KV_REST_API_URL + KV_REST_API_TOKEN (hoặc UPSTASH_REDIS_REST_URL +
      UPSTASH_REDIS_REST_TOKEN) -> lưu vào Upstash Redis, dữ liệu giữ lâu dài.
      Trên Vercel: Project -> Storage -> thêm "Upstash for Redis" là biến tự có.
    - Không có -> lưu file JSON trong /tmp (dữ liệu TẠM, mất khi server khởi động lại).
"""
import json
import os
import re
import tempfile
import threading
import time
import urllib.request

from flask import Flask, jsonify, request

app = Flask(__name__)

MAX_DATA_BYTES = 20_000      # 1 bản lưu tối đa ~20 KB
MAX_SCORE = 10**9
GAME_RE = re.compile(r"^[a-z0-9_-]{1,32}$")

REDIS_URL = os.environ.get("KV_REST_API_URL") or os.environ.get("UPSTASH_REDIS_REST_URL")
REDIS_TOKEN = os.environ.get("KV_REST_API_TOKEN") or os.environ.get("UPSTASH_REDIS_REST_TOKEN")


# ---------------------------------------------------------------- nơi lưu dữ liệu
class RedisStore:
    """Upstash Redis qua REST (chỉ dùng urllib, không cần cài thêm thư viện)."""
    kind = "redis"

    def _cmd(self, *args):
        req = urllib.request.Request(
            REDIS_URL.rstrip("/"),
            data=json.dumps([str(a) for a in args]).encode(),
            headers={"Authorization": f"Bearer {REDIS_TOKEN}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode())["result"]

    def hgetall(self, key):
        flat = self._cmd("HGETALL", key) or []
        return {flat[i]: flat[i + 1] for i in range(0, len(flat), 2)}

    def hget(self, key, field):
        return self._cmd("HGET", key, field)

    def hset(self, key, field, value):
        self._cmd("HSET", key, field, value)


class FileStore:
    """File JSON trong /tmp (Vercel) hoặc thư mục tạm của máy. Chỉ để thử, dữ liệu có thể mất."""
    kind = "file_tam"
    _lock = threading.Lock()

    def __init__(self):
        base = "/tmp" if os.path.isdir("/tmp") else tempfile.gettempdir()
        self.path = os.path.join(base, "online_lop_hoc.json")

    def _read(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def hgetall(self, key):
        return dict(self._read().get(key, {}))

    def hget(self, key, field):
        return self._read().get(key, {}).get(field)

    def hset(self, key, field, value):
        with self._lock:
            db = self._read()
            db.setdefault(key, {})[field] = value
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(db, f, ensure_ascii=False)
            os.replace(tmp, self.path)


store = RedisStore() if (REDIS_URL and REDIS_TOKEN) else FileStore()


# ---------------------------------------------------------------- tiện ích
def loi(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code


def lay_game(value):
    game = str(value or "").strip().lower()
    return game if GAME_RE.match(game) else None


def lay_player(value):
    name = " ".join(str(value or "").split())[:20]
    return name or None


def du_lieu_gui_len():
    return request.get_json(silent=True, force=True) or {}


@app.after_request
def cho_phep_cors(resp):
    # Game chạy cùng tên miền Vercel thì không cần, nhưng bật để bản desktop / trang khác gọi được.
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Cache-Control"] = "no-store"
    return resp


# ---------------------------------------------------------------- các chức năng
def kiem_tra():
    return jsonify({
        "ok": True,
        "api": "Online lớp học - Buổi 13",
        "storage": store.kind,
        "note": "" if store.kind == "redis" else "Dữ liệu TẠM: có thể mất khi server khởi động lại.",
        "actions": ["top", "score", "load", "save"],
    })


def top():
    game = lay_game(request.args.get("game"))
    if not game:
        return loi("Thiếu hoặc sai 'game' (chỉ chữ thường, số, - và _)")
    try:
        limit = max(1, min(int(request.args.get("limit", 10)), 50))
    except ValueError:
        limit = 10
    rows = []
    for raw in store.hgetall(f"lb:{game}").values():
        try:
            rows.append(json.loads(raw))
        except ValueError:
            pass
    rows.sort(key=lambda r: (-r.get("score", 0), r.get("time", 0)))
    return jsonify({"ok": True, "game": game, "top": rows[:limit]})


def score():
    body = du_lieu_gui_len()
    game, player = lay_game(body.get("game")), lay_player(body.get("player"))
    if not game or not player:
        return loi("Cần có 'game' và 'player'")
    try:
        diem = int(body.get("score"))
    except (TypeError, ValueError):
        return loi("'score' phải là số nguyên")
    if not 0 <= diem <= MAX_SCORE:
        return loi("'score' không hợp lệ")
    extra = body.get("extra") if isinstance(body.get("extra"), dict) else {}
    if len(json.dumps(extra)) > 1000:
        return loi("'extra' quá lớn")

    key = f"lb:{game}"
    cu = store.hget(key, player.lower())
    diem_cu = json.loads(cu).get("score", -1) if cu else -1
    ky_luc_moi = diem > diem_cu
    if ky_luc_moi:   # mỗi người chỉ giữ điểm cao nhất
        store.hset(key, player.lower(), json.dumps(
            {"player": player, "score": diem, "extra": extra, "time": int(time.time())},
            ensure_ascii=False))
    return jsonify({"ok": True, "new_record": ky_luc_moi, "best": max(diem, diem_cu)})


def load():
    game, player = lay_game(request.args.get("game")), lay_player(request.args.get("player"))
    if not game or not player:
        return loi("Cần có 'game' và 'player'")
    raw = store.hget(f"save:{game}", player.lower())
    data = json.loads(raw)["data"] if raw else None
    return jsonify({"ok": True, "found": raw is not None, "data": data})


def save():
    body = du_lieu_gui_len()
    game, player = lay_game(body.get("game")), lay_player(body.get("player"))
    if not game or not player:
        return loi("Cần có 'game' và 'player'")
    data = body.get("data")
    if not isinstance(data, dict):
        return loi("'data' phải là một dict (JSON object)")
    text = json.dumps({"player": player, "data": data, "time": int(time.time())}, ensure_ascii=False)
    if len(text.encode()) > MAX_DATA_BYTES:
        return loi("Bản lưu quá lớn (tối đa 20 KB)")
    store.hset(f"save:{game}", player.lower(), text)
    return jsonify({"ok": True})


ACTIONS = {
    ("GET", None): kiem_tra,
    ("GET", "top"): top,
    ("POST", "score"): score,
    ("GET", "load"): load,
    ("POST", "save"): save,
}


@app.route("/", defaults={"_path": ""}, methods=["GET", "POST", "OPTIONS"])
@app.route("/<path:_path>", methods=["GET", "POST", "OPTIONS"])
def xu_ly(_path):
    # Đường dẫn nào cũng được (Vercel có thể thêm /api/online/ hoặc dấu / cuối); chỉ xét 'action'.
    if request.method == "OPTIONS":
        return "", 204
    action = request.args.get("action") or None
    fn = ACTIONS.get((request.method, action))
    if fn is None:
        return loi(f"Không có chức năng {request.method} action={action}", 404)
    try:
        return fn()
    except Exception as e:  # lỗi nơi lưu (mạng tới Redis...) -> báo rõ, không sập
        return loi(f"Lỗi server: {type(e).__name__}", 500)


if __name__ == "__main__":
    # Chạy thử trên máy: py api/online/index.py  ->  http://127.0.0.1:5001/
    app.run(host="127.0.0.1", port=5001, debug=True)
