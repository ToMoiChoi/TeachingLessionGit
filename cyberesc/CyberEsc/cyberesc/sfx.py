"""Phát hiệu ứng âm thanh có bộ nhớ đệm (mỗi file chỉ nạp 1 lần, lỗi thì im lặng)."""
import os
import pygame

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Sounds", "sounds")
_cache = {}
muted = False


def play(name, volume=0.7):
    if muted:
        return
    if name not in _cache:
        try:
            _cache[name] = pygame.mixer.Sound(os.path.join(_DIR, name))
        except Exception:
            _cache[name] = None
    snd = _cache[name]
    if snd is not None:
        try:
            snd.set_volume(volume)
            snd.play()
        except Exception:
            pass
