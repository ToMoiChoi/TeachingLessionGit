"""Giữ tương thích với code cũ: Sounds.play("ten_file.wav") -> dùng bộ phát có bộ nhớ đệm."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sfx  # noqa: E402


def play(file_name):
    sfx.play(file_name)
