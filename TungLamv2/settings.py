import sys

IS_WEB = sys.platform == "emscripten"

# Bản Web dùng khung 16:9 chuẩn (1024x576) để pygbag phóng toàn màn bằng GPU và giữ vững 60 FPS;
# Bản Desktop giữ nguyên Full HD+ (1600x900) 120 FPS.
WIDTH = 1024 if IS_WEB else 1600
HEIGHT = 576 if IS_WEB else 900
FPS = 60 if IS_WEB else 120

MAP_W = 1800
MAP_H = 1200

FOV = 90

PLAYER_SPEED = 260
PLAYER_RADIUS = 18

MAX_HP = 100
MAX_ARMOR = 50

ROUND_TIME = 100
BUY_TIME = 30

WHITE = (245, 245, 245)
BLACK = (5, 5, 8)
RED = (220, 60, 70)
GREEN = (60, 220, 130)
BLUE = (70, 150, 240)
YELLOW = (240, 210, 70)
GRAY = (90, 90, 100)
DARK = (25, 27, 32)
WALL = (75, 80, 88)
