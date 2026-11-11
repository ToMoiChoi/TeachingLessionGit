"""Âm thanh phía máy chủ (chỉ dùng khi chạy trên máy tính bằng launcher.py).
Trên web (server không có loa, không có pygame) mọi hàm đều tự bỏ qua;
âm thanh trên trình duyệt do GLOBAL_AUDIO_SNIPPET trong app.py đảm nhận.
"""
import os
import random

try:
    import pygame
    pygame.mixer.init()
except Exception:  # không có pygame hoặc không có thiết bị âm thanh
    pygame = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SFX_DIR = os.path.join(BASE_DIR, 'sounds', 'sfx')
BGM_DIR = os.path.join(BASE_DIR, 'sounds', 'bgm')

FIFA_TRACKS = [
    'Glass Animals - Heat Waves (Official Video).mp3',
    'John Newman - Love Me Again.mp3',
    'Joy Crookes - Feet Don t Fail Me Now (Official Video).mp3',
]
_shuffled_playlist = []
_current_track_index = 0


def get_shuffled_fifa_playlist():
    playlist = list(FIFA_TRACKS)
    random.shuffle(playlist)
    return playlist


def play_sfx(filename, volume=0.5):
    if pygame is None:
        return
    try:
        path = os.path.join(SFX_DIR, filename)
        if not os.path.exists(path):
            path = os.path.join(BASE_DIR, 'sounds', filename)
        if os.path.exists(path):
            sound = pygame.mixer.Sound(path)
            sound.set_volume(1.0 if 'goal' in filename.lower() else volume)
            sound.play()
    except Exception as e:
        print(f'>> Lỗi phát âm thanh {filename}: {e}')


def play_goal():
    play_sfx('Goal.wav', volume=1.0)


def play_kick():
    play_sfx('Kick.wav', volume=0.7)


def play_click():
    play_sfx('Click.wav', volume=0.5)


def play_crowd(volume=0.4):
    if pygame is None:
        return
    try:
        path = os.path.join(BGM_DIR, 'Fan cherring.mp3')
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1)
    except Exception as e:
        print(f'>> Lỗi phát tiếng khán giả: {e}')


def play_next_fifa_bgm(volume=0.5):
    global _shuffled_playlist, _current_track_index
    if pygame is None:
        return
    try:
        if not _shuffled_playlist or _current_track_index >= len(_shuffled_playlist):
            _shuffled_playlist = get_shuffled_fifa_playlist()
            _current_track_index = 0
        track_name = _shuffled_playlist[_current_track_index]
        _current_track_index += 1
        path = os.path.join(BGM_DIR, track_name)
        if os.path.exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play()
            print(f'>> Đang phát bài FIFA: {track_name}')
    except Exception as e:
        print(f'>> Lỗi phát nhạc FIFA: {e}')


if __name__ == '__main__':
    print('>> Đang test âm thanh Goal (Max Volume)...')
    play_goal()
    if pygame:
        pygame.time.delay(1000)
    print('>> Đang phát ngẫu nhiên 1 bài FIFA...')
    play_next_fifa_bgm()
    if pygame:
        pygame.time.delay(2000)
