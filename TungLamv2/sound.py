import pygame
import os

# 1. Khoi tao am thanh
try:
    pygame.mixer.init()
except Exception:
    pass

# Thu muc noi sound.py dang dung
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Ham phat am thanh tu file
def play(file_name):
    # Tim file trong thu muc sounds/
    path = os.path.join(BASE_DIR, "sounds", file_name)
    if not os.path.exists(path):
        path = file_name # Thu duong dan nguoi dung truyen

    if not os.path.exists(path):
        return

    # Phat am thanh
    try:
        sound = pygame.mixer.Sound(path)
        sound.play()
    except Exception as e:
        print(f">> Khong the phat am thanh: {file_name} ({e})")

# Chay thu truc tiep file nay
if __name__ == '__main__':
    play("pistol.wav")
    pygame.time.delay(600)
    print(">> Phat thanh cong!")
