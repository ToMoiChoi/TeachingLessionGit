"""luu_tru.py - lưu tiến trình game trên máy người chơi (Buổi 13). Chép file này vào thư mục game.

    import luu_tru
    data = luu_tru.doc("cyberesc_save", {"coins": 300, "level": 1})   # đọc (không có thì lấy mặc định)
    luu_tru.ghi("cyberesc_save", data)                                 # ghi

- Bản web (pygbag): lưu vào localStorage của trình duyệt -> bấm F5 không mất.
- Bản desktop: lưu ra file <ten>.json cạnh file game, như cũ.
Tên (ten) nên có tên game ở đầu để không trùng với game khác trên cùng trang web.
"""
import json
import os
import sys

LA_WEB = sys.platform == "emscripten"


def doc(ten, mac_dinh=None):
    """Đọc dữ liệu đã lưu. Lỗi hoặc chưa có thì trả về bản sao của mac_dinh."""
    mac_dinh = dict(mac_dinh or {})
    try:
        if LA_WEB:
            from platform import window
            raw = window.localStorage.getItem(ten)
            text = None if raw is None else str(raw)
            if text in (None, "", "null", "undefined"):
                return mac_dinh
        else:
            if not os.path.exists(ten + ".json"):
                return mac_dinh
            with open(ten + ".json", encoding="utf-8") as f:
                text = f.read()
        data = json.loads(text)
        for k, v in mac_dinh.items():   # bản lưu cũ thiếu khóa mới -> bổ sung giá trị mặc định
            data.setdefault(k, v)
        return data
    except Exception as e:
        print(f"[luu_tru] Không đọc được '{ten}': {e}")
        return mac_dinh


def ghi(ten, data):
    """Ghi dữ liệu (dict). Trả về True nếu thành công."""
    try:
        text = json.dumps(data, ensure_ascii=False)
        if LA_WEB:
            from platform import window
            window.localStorage.setItem(ten, text)
        else:
            with open(ten + ".json", "w", encoding="utf-8") as f:
                f.write(text)
        return True
    except Exception as e:
        print(f"[luu_tru] Không ghi được '{ten}': {e}")
        return False


def xoa(ten):
    """Xóa bản lưu (nút 'Chơi lại từ đầu')."""
    try:
        if LA_WEB:
            from platform import window
            window.localStorage.removeItem(ten)
        elif os.path.exists(ten + ".json"):
            os.remove(ten + ".json")
    except Exception as e:
        print(f"[luu_tru] Không xóa được '{ten}': {e}")
