# -*- coding: utf-8 -*-
import os
import random

_has_pygame = False
try:
    import pygame
    try:
        pygame.mixer.init()
    except Exception:
        pass
    _has_pygame = True
except Exception:
    _has_pygame = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SFX_DIR = os.path.join(BASE_DIR, "sounds", "sfx")
BGM_DIR = os.path.join(BASE_DIR, "sounds", "bgm")

# Danh sách các bài hát FIFA trong thư mục sounds/bgm
FIFA_TRACKS = [
    "Glass Animals - Heat Waves (Official Video).mp3",
    "John Newman - Love Me Again.mp3",
    "Joy Crookes - Feet Don t Fail Me Now (Official Video).mp3"
]

# Playlist ngẫu nhiên đang chạy
_shuffled_playlist = []
_current_track_index = 0

def get_shuffled_fifa_playlist():
    """Trả về danh sách bài hát FIFA đã được xáo trộn ngẫu nhiên."""
    playlist = list(FIFA_TRACKS)
    random.shuffle(playlist)
    return playlist

def play_sfx(filename, volume=0.7):
    """Phát âm thanh hiệu ứng (SFX)."""
    if not _has_pygame:
        return
    path = os.path.join(SFX_DIR, filename)
    if not os.path.exists(path):
        path = os.path.join(BASE_DIR, "sounds", filename)
    if os.path.exists(path):
        try:
            sound = pygame.mixer.Sound(path)
            if "goal" in filename.lower():
                sound.set_volume(1.0)
            else:
                sound.set_volume(volume)
            sound.play()
        except Exception:
            pass

def play_goal():
    """Phát âm thanh bàn thắng."""
    play_sfx("Goal.wav", volume=1.0)

def play_kick():
    """Phát tiếng sút bóng."""
    play_sfx("Kick.wav", volume=0.7)

def play_click():
    """Phát tiếng click chuột."""
    play_sfx("Click.wav", volume=0.5)

def play_crowd(volume=0.25):
    """Phát tiếng khán giả reo hò trong trận đấu."""
    if not _has_pygame:
        return
    path = os.path.join(BGM_DIR, "Fan cherring.mp3")
    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1)
        except Exception:
            pass

def play_next_fifa_bgm(volume=0.35):
    """Tự động xáo trộn và phát bài nhạc FIFA ngẫu nhiên tiếp theo."""
    if not _has_pygame:
        return
    global _shuffled_playlist, _current_track_index
    if not _shuffled_playlist or _current_track_index >= len(_shuffled_playlist):
        _shuffled_playlist = get_shuffled_fifa_playlist()
        _current_track_index = 0

    track_name = _shuffled_playlist[_current_track_index]
    _current_track_index += 1

    path = os.path.join(BGM_DIR, track_name)
    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play()
        except Exception:
            pass
