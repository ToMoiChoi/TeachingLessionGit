"""Lưu / nạp tiến trình.

- Chạy trên máy: ghi file save_data.json cạnh game.
- Chạy trên web (pygbag): ghi vào localStorage của trình duyệt, nên tải lại trang
  vẫn còn coins, màn đã mở, đồ đã mua...
"""
import copy
import json
import os
import sys

SAVE_FILE = "save_data.json"
WEB_KEY = "cyberesc_save_v1"
IS_WEB = sys.platform == "emscripten"

DEFAULT_DATA = {
    "coins": 300,
    "max_unlocked_level": 1,
    "hp_lvl": 1,
    "hp_cost": 500,
    "dmg_lvl": 1,
    "dmg_cost": 600,
    "speed_lvl": 1,
    "speed_cost": 400,
    "rebirths": 0,
    "stars": {},                      # {"1": 3, "2": 1, ...}
    "weapons_owned": ["Blaster", "Shotgun", "Rifle"],
    "cosmetics": {},                  # do CosmeticManager.export_state() tạo ra
    "difficulty": "NORMAL",
    "endless_scores": [],             # top 5: [{"score", "wave", "date"}]
    "missions": {},                   # do MissionManager.export_state() tạo ra
}


def _read_raw():
    if IS_WEB:
        try:
            import platform
            return platform.window.localStorage.getItem(WEB_KEY)
        except Exception as e:
            print(f"[SaveManager] Không đọc được localStorage: {e}")
            return None
    if not os.path.exists(SAVE_FILE):
        return None
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        return f.read()


def _write_raw(text):
    if IS_WEB:
        import platform
        platform.window.localStorage.setItem(WEB_KEY, text)
        return
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        f.write(text)


def load_game_data():
    data = copy.deepcopy(DEFAULT_DATA)
    try:
        raw = _read_raw()
        if raw:
            saved = json.loads(raw)
            if isinstance(saved, dict):
                data.update(saved)
    except Exception as e:
        print(f"[Warning] Không thể đọc dữ liệu save: {e}")
    for key, val in DEFAULT_DATA.items():
        data.setdefault(key, copy.deepcopy(val))
    return data


def save_game_data(data):
    try:
        _write_raw(json.dumps(data, ensure_ascii=False))
    except Exception as e:
        print(f"[Error] Lỗi khi lưu dữ liệu: {e}")
