import os
import pygame
from font_vn import get_font

pygame.init()
try:
    pygame.mixer.init()
    AUDIO_ENABLED = True
except pygame.error:
    AUDIO_ENABLED = False

# ============================================================
# AUDIO SYSTEM (Tương thích cả Desktop và Web Pygbag)
# ============================================================

SOUND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
SOUND_CACHE = {}

SOUND_FILES = {
    "light": "sword_slash.wav",
    "heavy": "ball_kick.wav",
    "black_flash": "electric_zap.wav",
    "fire": "fireball.wav",
    "beam": "laser_pulse.wav",
    "blast": "shotgun.wav",
    "dash": "cyber_dash.wav",
    "parry": "post_clang.wav",
    "simple_domain": "shield_pickup.wav",
    "shield_hit": "shield_clank.wav",
    "rct": "potion_drink.wav",
    "nail": "ricochet.wav",
    "domain": "alarm_siren.wav",
    "roar": "zombie_roar.wav",
    "buy": "cash_transfer.wav",
    "victory": "crowd_cheer.wav",
    "defeat": "terminal_hack.wav",
    "hit": "ball_kick.wav",
}


def load_sound(file_name):
    if not AUDIO_ENABLED or not file_name:
        return None
    if file_name in SOUND_CACHE:
        return SOUND_CACHE[file_name]

    path = os.path.join(SOUND_DIR, file_name)
    if not os.path.exists(path):
        return None

    try:
        sound = pygame.mixer.Sound(path)
        sound.set_volume(0.55)
        SOUND_CACHE[file_name] = sound
        return sound
    except (pygame.error, OSError):
        return None


def play_sound(key_or_file):
    file_name = SOUND_FILES.get(key_or_file, key_or_file)
    sound = load_sound(file_name)
    if sound is not None:
        try:
            sound.play()
        except pygame.error:
            pass


# ============================================================
# CẤU HÌNH MÀN HÌNH & THÔNG SỐ CHUNG
# ============================================================

WIDTH = 1100
HEIGHT = 650
FPS = 60

GROUND_Y = 515
ARENA_LEFT = 65
ARENA_RIGHT = WIDTH - 65

START_GOLD = 3000

# Bảng màu Chú Thuật Hồi Chiến (Jujutsu Kaisen Palette)
WHITE = (245, 247, 252)
BLACK = (8, 10, 18)
DARK = (18, 22, 36)
DARK_CARD = (24, 30, 48)
GRAY = (140, 152, 175)
MUTED = (95, 108, 130)

RED = (239, 68, 68)
CRIMSON = (190, 18, 60)
GREEN = (34, 197, 94)
RCT_GREEN = (110, 255, 190)
BLUE = (59, 130, 246)
LAPSE_BLUE = (38, 170, 255)
REVERSAL_RED = (255, 50, 80)
HOLLOW_PURPLE = (185, 70, 255)
CYAN = (34, 211, 238)
YELLOW = (250, 204, 21)
GOLD = (245, 168, 28)
PURPLE = (168, 85, 247)
PINK = (244, 114, 182)
ORANGE = (251, 115, 24)
SHADOW_COL = (55, 65, 95)

# ============================================================
# HỆ THỐNG FONT TIẾNG VIỆT
# ============================================================

FONT_TITLE = get_font(38, bold=True)
FONT_BIG = get_font(26, bold=True)
FONT_MED = get_font(19, bold=True)
FONT = get_font(16)
FONT_SMALL = get_font(14)
FONT_TINY = get_font(12, bold=True)


# ============================================================
# HÀM TIỆN ÍCH VẼ GIAO DIỆN
# ============================================================

def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def draw_text(surface, text, x, y, color=WHITE, font=FONT, center=False, right=False, shadow=False):
    text_str = str(text)
    if shadow:
        sh_img = font.render(text_str, True, (5, 8, 15))
        if center:
            sh_rect = sh_img.get_rect(center=(int(x) + 2, int(y) + 2))
        elif right:
            sh_rect = sh_img.get_rect(topright=(int(x) + 2, int(y) + 2))
        else:
            sh_rect = sh_img.get_rect(topleft=(int(x) + 2, int(y) + 2))
        surface.blit(sh_img, sh_rect)

    img = font.render(text_str, True, color)
    if center:
        rect = img.get_rect(center=(int(x), int(y)))
    elif right:
        rect = img.get_rect(topright=(int(x), int(y)))
    else:
        rect = img.get_rect(topleft=(int(x), int(y)))
    surface.blit(img, rect)
    return rect


def draw_bar(surface, x, y, width, height, value, maximum, color, bg_color=(35, 42, 58), border_color=None):
    rect_bg = pygame.Rect(int(x), int(y), int(width), int(height))
    pygame.draw.rect(surface, bg_color, rect_bg, border_radius=6)
    if maximum > 0 and value > 0:
        ratio = clamp(value / maximum, 0.0, 1.0)
        fill_w = max(4, int(width * ratio))
        pygame.draw.rect(surface, color, (int(x), int(y), fill_w, int(height)), border_radius=6)
    if border_color is not None:
        pygame.draw.rect(surface, border_color, rect_bg, 1, border_radius=6)


def wrap_text(text, font, max_width):
    """Tự động xuống dòng tiếng Việt không tràn khung."""
    words = str(text).split(" ")
    lines = []
    current = ""
    for w in words:
        test = w if not current else current + " " + w
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines
