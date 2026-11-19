"""Font tiếng Việt dùng chung cho bản chạy trên máy và bản web (pygbag).

Trên trình duyệt KHÔNG có font hệ thống: pygame.font.SysFont("arial") sẽ rơi về
font mặc định, font này thiếu phần lớn chữ có dấu (ạ, ế, ồ, ữ...) nên hiện ô vuông.
Vì vậy game mang theo file font riêng trong thư mục fonts/ (giấy phép OFL, miễn phí).

Cách dùng:  from font_vn import get_font
            font = get_font(20)              # chữ thường
            font = get_font(30, bold=True)   # chữ đậm
"""
import os
import pygame

_FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
_REGULAR = "RobotoCondensed-Regular.ttf"
_BOLD = "RobotoCondensed-Bold.ttf"
_SCALE = 0.94  # chỉnh cỡ chữ cho bằng font cũ (Arial Narrow) để không tràn khung

_cache = {}


def get_font(size, bold=False):
    """Trả về pygame.font.Font có đủ chữ tiếng Việt (đã lưu sẵn, gọi nhiều lần không tốn)."""
    key = (size, bold)
    if key not in _cache:
        path = os.path.join(_FONT_DIR, _BOLD if bold else _REGULAR)
        try:
            _cache[key] = pygame.font.Font(path, max(8, round(size * _SCALE)))
        except (OSError, FileNotFoundError):
            _cache[key] = pygame.font.SysFont("arial", size, bold=bold)
    return _cache[key]
