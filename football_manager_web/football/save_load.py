# -*- coding: utf-8 -*-
import json
import os
import hashlib

DATA_DIR = "data"

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def save_game(data, passcode):
    ensure_data_dir()
    hashed = hashlib.sha256(passcode.encode()).hexdigest()
    data["passcode_hash"] = hashed
    filename = f"save_{hashlib.md5(passcode.encode()).hexdigest()[:8]}.json"
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    return filepath

def load_game(passcode):
    ensure_data_dir()
    hashed = hashlib.sha256(passcode.encode()).hexdigest()
    for fname in os.listdir(DATA_DIR):
        if fname.startswith("save_") and fname.endswith(".json"):
            filepath = os.path.join(DATA_DIR, fname)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("passcode_hash") == hashed:
                return data
    return None

def auto_save(data, passcode):
    save_game(data, passcode)
    print("💾 Đã lưu tiến trình tự động.")