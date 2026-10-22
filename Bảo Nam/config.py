import pygame
import os

pygame.init()
pygame.mixer.init()

# ============================================================
# AUDIO
# ============================================================

SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
SOUND_CACHE = {}
AUDIO_ENABLED = True

def load_sound(file_name):
    if not AUDIO_ENABLED:
        return None
    if file_name in SOUND_CACHE:
        return SOUND_CACHE[file_name]

    path = os.path.join(SOUND_DIR, file_name)
    if not os.path.exists(path):
        return None

    try:
        sound = pygame.mixer.Sound(path)
        SOUND_CACHE[file_name] = sound
        return sound
    except (pygame.error, OSError):
        return None

def play_sound(file_name):
    sound = load_sound(file_name)
    if sound is not None:
        try:
            sound.play()
        except pygame.error:
            pass

SOUND_FILES = {
    "light": "sword_slash.wav",
    "heavy": "sword_heavy.wav",
    "skill": "sword_skill.wav",
    "hit": "hit.wav",
    "parry": "parry.wav",
    "dodge": "dodge.wav",
    "counter": "counter.wav",
    "victory": "victory.wav",
    "defeat": "defeat.wav",
}

# ============================================================
# CONFIG
# ============================================================

WIDTH = 1100
HEIGHT = 650
FPS = 60

GROUND_Y = 500
ARENA_LEFT = 70
ARENA_RIGHT = WIDTH - 70

PLAYER_HP = 1000
START_GOLD = 10000

LIGHT_DAMAGE = 25
HEAVY_DAMAGE = 65
SKILL_DAMAGE = 120
COUNTER_DAMAGE = 60

WHITE = (245, 245, 245)
BLACK = (8, 10, 18)

BG_TOP = (12, 18, 35)
BG_BOTTOM = (25, 32, 52)

RED = (239, 68, 68)
GREEN = (34, 197, 94)
BLUE = (59, 130, 246)
CYAN = (6, 182, 212)
YELLOW = (245, 158, 11)
PURPLE = (168, 85, 247)
GRAY = (100, 116, 139)
DARK = (25, 34, 52)

# ============================================================
# LEVELS SYSTEM (THÊM MỚI)
# ============================================================

LEVELS = [
    {
        "id": 1,
        "name": "Màn 1: Kẻ Lót Đường",
        "boss_name": "RONIN",
        "boss_color": (150, 150, 150),
        "boss_hp": 1200,
        "boss_speed": 130,
        "reward_gold": 1500,
        "description": "Kiếm sĩ lang thang canh giữ cửa thành."
    },
    {
        "id": 2,
        "name": "Màn 2: Cuồng Long",
        "boss_name": "RYU - HẮC KIẾM SĨ",
        "boss_color": (239, 68, 68),
        "boss_hp": 2000,
        "boss_speed": 160,
        "reward_gold": 2500,
        "description": "Sở hữu thanh hắc kiếm với tốc độ chớp nhoáng."
    },
    {
        "id": 3,
        "name": "Màn 3: Vô Diện Ảnh Sát",
        "boss_name": "SHADOW BLADE",
        "boss_color": (168, 85, 247),
        "boss_hp": 3000,
        "boss_speed": 200,
        "reward_gold": 4000,
        "description": "Tốc độ cao, tỷ lệ né đòn và parry rất khó chịu."
    },
    {
        "id": 4,
        "name": "Màn 4: Trùm Cuối",
        "boss_name": "GENERAL GAIA",
        "boss_color": (245, 158, 11),
        "boss_hp": 5000,
        "boss_speed": 120,
        "reward_gold": 10000,
        "description": "Trùm cuối với lớp giáp dày và sức mạnh hủy diệt."
    }
]

# ============================================================
# FONTS
# ============================================================

FONT_TITLE = pygame.font.SysFont("arial", 42, bold=True)
FONT_BIG = pygame.font.SysFont("arial", 30, bold=True)
FONT_MED = pygame.font.SysFont("arial", 21, bold=True)
FONT = pygame.font.SysFont("arial", 17)
FONT_SMALL = pygame.font.SysFont("arial", 13)

# ============================================================
# HELPERS
# ============================================================

def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))

def draw_text(surface, text, x, y, color=WHITE, font=FONT, center=False):
    img = font.render(str(text), True, color)
    if center:
        rect = img.get_rect(center=(x, y))
    else:
        rect = img.get_rect(topleft=(x, y))
    surface.blit(img, rect)

def draw_bar(surface, x, y, width, height, value, maximum, color):
    pygame.draw.rect(surface, (45, 50, 65), (x, y, width, height), border_radius=6)
    if maximum > 0:
        ratio = clamp(value / maximum, 0, 1)
        pygame.draw.rect(surface, color, (x, y, int(width * ratio), height), border_radius=6)