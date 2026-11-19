import json
import os

SAVE_FILE = "save_data.json"

DEFAULT_DATA = {
    "coins": 300,
    "max_unlocked_level": 1,
    "hp_lvl": 1,
    "hp_cost": 500,
    "dmg_lvl": 1,
    "dmg_cost": 600,
    "speed_lvl": 1,
    "speed_cost": 400,
    "rebirths": 0
}

def load_game_data():
    if not os.path.exists(SAVE_FILE):
        return DEFAULT_DATA.copy()
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for key, val in DEFAULT_DATA.items():
                data.setdefault(key, val)
            return data
    except Exception as e:
        print(f"[Warning] Không thể đọc file save: {e}")
        return DEFAULT_DATA.copy()

def save_game_data(data):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("[SaveManager] Đã lưu dữ liệu thành công!")
    except Exception as e:
        print(f"[Error] Lỗi khi lưu dữ liệu: {e}")