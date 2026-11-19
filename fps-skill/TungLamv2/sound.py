import pygame
import os

try:
    pygame.mixer.init()
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_sound_cache = {}

def play(file_name):
    try:
        if file_name not in _sound_cache:
            path = os.path.join(BASE_DIR, 'sounds', file_name)
            if not os.path.exists(path):
                path = file_name
            if os.path.exists(path):
                _sound_cache[file_name] = pygame.mixer.Sound(path)
        if file_name in _sound_cache:
            _sound_cache[file_name].play()
    except Exception:
        pass
