"""game/map.py - Hệ thống đa bản đồ (5 bản đồ chiến thuật & sinh tồn) và kiểm tra va chạm tối ưu."""
import math
import pygame
from settings import MAP_W, MAP_H


def _border_walls(w=MAP_W, h=MAP_H, t=35):
    return [
        pygame.Rect(0, 0, w, t),
        pygame.Rect(0, h - t, w, t),
        pygame.Rect(0, 0, t, h),
        pygame.Rect(w - t, 0, t, h),
    ]


# ==============================================================================
# DANH SÁCH 5 BẢN ĐỒ (GỐC + 4 BẢN ĐỒ MỚI)
# Mọi tọa độ spawn đều đã được kiểm chứng không chạm bất kỳ khối tường nào.
# ==============================================================================
MAPS = {
    "lotus": {
        "id": "lotus",
        "name": "LOTUS RUINS",
        "subtitle": "Di tích cổ đại 3 khu A/B/C",
        "player_spawn": (880, 1050, -math.pi / 2),
        "enemy_spawns": [
            (400, 280), (540, 330), (1300, 280), (1400, 330),
            (1220, 820), (630, 820), (900, 220), (180, 620),
        ],
        "zombie_spawns": [
            (140, 140), (900, 120), (1660, 140), (1660, 620),
            (1640, 1080), (140, 1080), (140, 620), (430, 280),
        ],
        "sites": {
            "A": pygame.Rect(300, 220, 320, 170),
            "B": pygame.Rect(1200, 220, 250, 170),
            "C": pygame.Rect(1080, 750, 280, 150),
        },
        "theme": {
            "sky_top": (14, 18, 28),
            "sky_bot": (38, 48, 70),
            "floor_far": (32, 36, 44),
            "floor_near": (82, 82, 84),
            "wall_rgb": (75, 82, 98),
            "stripe_rgb": (30, 185, 225),
            "accent": (30, 185, 225),
        },
        "walls": _border_walls() + [
            # A SITE
            pygame.Rect(250, 160, 420, 35),
            pygame.Rect(250, 160, 35, 300),
            pygame.Rect(635, 160, 35, 300),
            pygame.Rect(250, 425, 180, 35),
            pygame.Rect(500, 425, 170, 35),
            # MID
            pygame.Rect(760, 285, 35, 260),
            pygame.Rect(760, 510, 300, 35),
            # B SITE
            pygame.Rect(1150, 160, 360, 35),
            pygame.Rect(1150, 160, 35, 300),
            pygame.Rect(1475, 160, 35, 300),
            pygame.Rect(1150, 425, 150, 35),
            pygame.Rect(1360, 425, 150, 35),
            # LOWER
            pygame.Rect(470, 700, 35, 260),
            pygame.Rect(470, 925, 360, 35),
            pygame.Rect(800, 700, 35, 260),
            # C SITE
            pygame.Rect(1030, 700, 35, 270),
            pygame.Rect(1030, 935, 400, 35),
            pygame.Rect(1395, 700, 35, 270),
            # Cover
            pygame.Rect(700, 590, 150, 35),
            pygame.Rect(950, 590, 150, 35),
        ],
    },
    "cyber_lab": {
        "id": "cyber_lab",
        "name": "CYBER LAB",
        "subtitle": "Phòng thí nghiệm lõi Neon",
        "player_spawn": (900, 1080, -math.pi / 2),
        "enemy_spawns": [
            (900, 160), (300, 220), (1500, 220), (320, 600),
            (1480, 600), (620, 340), (1180, 340), (900, 590),
        ],
        "zombie_spawns": [
            (130, 130), (900, 130), (1670, 130), (130, 600),
            (1670, 600), (130, 1070), (1670, 1070), (900, 360),
        ],
        "sites": {
            "A": pygame.Rect(210, 190, 260, 200),
            "B": pygame.Rect(770, 500, 260, 200),
            "C": pygame.Rect(1330, 190, 260, 200),
        },
        "theme": {
            "sky_top": (18, 10, 34),
            "sky_bot": (52, 24, 82),
            "floor_far": (28, 24, 44),
            "floor_near": (68, 62, 92),
            "wall_rgb": (68, 64, 96),
            "stripe_rgb": (215, 65, 255),
            "accent": (215, 65, 255),
        },
        "walls": _border_walls() + [
            # Phòng lõi trung tâm 4 cửa mở
            pygame.Rect(700, 430, 140, 32),
            pygame.Rect(960, 430, 140, 32),
            pygame.Rect(700, 740, 140, 32),
            pygame.Rect(960, 740, 140, 32),
            pygame.Rect(700, 430, 32, 110),
            pygame.Rect(700, 660, 32, 112),
            pygame.Rect(1068, 430, 32, 110),
            pygame.Rect(1068, 660, 32, 112),
            # Buồng thí nghiệm Tây (A)
            pygame.Rect(190, 160, 310, 32),
            pygame.Rect(190, 160, 32, 260),
            pygame.Rect(468, 160, 32, 160),
            pygame.Rect(190, 420, 170, 32),
            # Buồng thí nghiệm Đông (C)
            pygame.Rect(1300, 160, 310, 32),
            pygame.Rect(1578, 160, 32, 260),
            pygame.Rect(1300, 160, 32, 160),
            pygame.Rect(1440, 420, 170, 32),
            # Hành lang chắn dưới hai cánh
            pygame.Rect(240, 760, 250, 32),
            pygame.Rect(458, 760, 32, 190),
            pygame.Rect(1310, 760, 250, 32),
            pygame.Rect(1310, 760, 32, 190),
            # Trụ chắn bảo vệ Bắc & Nam
            pygame.Rect(790, 240, 220, 32),
            pygame.Rect(790, 920, 220, 32),
        ],
    },
    "desert_bazaar": {
        "id": "desert_bazaar",
        "name": "DESERT BAZAAR",
        "subtitle": "Phố chợ sa mạc & đại lộ ngắm",
        "player_spawn": (220, 1060, -math.pi / 4),
        "enemy_spawns": [
            (1560, 180), (1340, 260), (920, 200), (420, 220),
            (1520, 760), (1120, 620), (680, 520), (1560, 1020),
        ],
        "zombie_spawns": [
            (1580, 150), (920, 130), (200, 150), (1650, 580),
            (1620, 1060), (920, 1080), (680, 600), (1220, 380),
        ],
        "sites": {
            "A": pygame.Rect(240, 180, 260, 190),
            "B": pygame.Rect(800, 490, 240, 200),
            "C": pygame.Rect(1360, 740, 260, 200),
        },
        "theme": {
            "sky_top": (42, 24, 18),
            "sky_bot": (118, 68, 38),
            "floor_far": (64, 52, 38),
            "floor_near": (132, 110, 78),
            "wall_rgb": (122, 98, 70),
            "stripe_rgb": (255, 185, 55),
            "accent": (255, 185, 55),
        },
        "walls": _border_walls() + [
            # Khu đền Tây Bắc (Site A)
            pygame.Rect(210, 390, 220, 35),
            pygame.Rect(520, 150, 35, 275),
            # Các quầy chợ trung tâm (Mid)
            pygame.Rect(740, 260, 280, 35),
            pygame.Rect(740, 440, 35, 260),
            pygame.Rect(1040, 460, 35, 260),
            pygame.Rect(830, 720, 245, 35),
            # Ngõ hẹp Tây Nam
            pygame.Rect(380, 640, 230, 35),
            pygame.Rect(380, 640, 35, 260),
            pygame.Rect(580, 880, 180, 35),
            # Đại lộ Đông & Khu chợ C
            pygame.Rect(1240, 180, 35, 240),
            pygame.Rect(1240, 385, 230, 35),
            pygame.Rect(1310, 690, 310, 35),
            pygame.Rect(1310, 690, 35, 250),
            # Thùng gỗ chắn đạn
            pygame.Rect(900, 560, 70, 55),
            pygame.Rect(1500, 520, 90, 40),
        ],
    },
    "ice_outpost": {
        "id": "ice_outpost",
        "name": "ICE OUTPOST",
        "subtitle": "Trạm radar băng giá Bắc Cực",
        "player_spawn": (900, 1070, -math.pi / 2),
        "enemy_spawns": [
            (280, 210), (1520, 210), (900, 190), (560, 430),
            (1240, 430), (280, 760), (1520, 760), (900, 580),
        ],
        "zombie_spawns": [
            (140, 150), (900, 120), (1660, 150), (140, 580),
            (1660, 580), (140, 1050), (1660, 1050), (900, 380),
        ],
        "sites": {
            "A": pygame.Rect(190, 170, 260, 190),
            "B": pygame.Rect(770, 170, 260, 180),
            "C": pygame.Rect(1350, 170, 260, 190),
        },
        "theme": {
            "sky_top": (10, 26, 38),
            "sky_bot": (28, 78, 96),
            "floor_far": (38, 52, 66),
            "floor_near": (96, 118, 138),
            "wall_rgb": (88, 108, 128),
            "stripe_rgb": (90, 245, 200),
            "accent": (90, 245, 200),
        },
        "walls": _border_walls() + [
            # Lô-cốt chữ L Tây Bắc & Đông Bắc
            pygame.Rect(460, 150, 35, 230),
            pygame.Rect(220, 380, 275, 35),
            pygame.Rect(1305, 150, 35, 230),
            pygame.Rect(1305, 380, 275, 35),
            # Tường chắn trạm Radar Bắc (Site B)
            pygame.Rect(730, 350, 130, 35),
            pygame.Rect(940, 350, 130, 35),
            # Cầu băng trung tâm & hào chắn hai bên
            pygame.Rect(380, 560, 280, 35),
            pygame.Rect(625, 560, 35, 180),
            pygame.Rect(1140, 560, 280, 35),
            pygame.Rect(1140, 560, 35, 180),
            pygame.Rect(830, 640, 140, 45),
            # Kho tiếp vận phía Nam
            pygame.Rect(220, 840, 260, 35),
            pygame.Rect(220, 710, 35, 165),
            pygame.Rect(1320, 840, 260, 35),
            pygame.Rect(1545, 710, 35, 165),
            pygame.Rect(740, 900, 110, 35),
            pygame.Rect(950, 900, 110, 35),
        ],
    },
    "dead_bunker": {
        "id": "dead_bunker",
        "name": "DEAD BUNKER",
        "subtitle": "Pháo đài ngầm chống Zombie",
        "player_spawn": (900, 600, -math.pi / 2),
        "enemy_spawns": [
            (220, 200), (1580, 200), (220, 1000), (1580, 1000),
            (900, 160), (900, 1040), (200, 600), (1600, 600),
        ],
        "zombie_spawns": [
            (130, 130), (900, 120), (1670, 130), (1670, 600),
            (1670, 1070), (900, 1080), (130, 1070), (130, 600),
        ],
        "sites": {
            "A": pygame.Rect(170, 170, 230, 180),
            "B": pygame.Rect(780, 500, 240, 200),
            "C": pygame.Rect(1400, 850, 230, 180),
        },
        "theme": {
            "sky_top": (28, 12, 14),
            "sky_bot": (68, 24, 24),
            "floor_far": (36, 26, 26),
            "floor_near": (78, 60, 58),
            "wall_rgb": (86, 68, 66),
            "stripe_rgb": (245, 75, 55),
            "accent": (245, 75, 55),
        },
        "walls": _border_walls() + [
            # 4 góc pháo đài trung tâm (lối vào rộng cả 4 hướng cho người chơi cố thủ)
            pygame.Rect(680, 410, 130, 35),
            pygame.Rect(680, 410, 35, 110),
            pygame.Rect(990, 410, 130, 35),
            pygame.Rect(1085, 410, 35, 110),
            pygame.Rect(680, 755, 130, 35),
            pygame.Rect(680, 680, 35, 110),
            pygame.Rect(990, 755, 130, 35),
            pygame.Rect(1085, 680, 35, 110),
            # Các vách chắn hành lang vòng ngoài (4 góc hầm)
            pygame.Rect(330, 240, 210, 35),
            pygame.Rect(330, 240, 35, 190),
            pygame.Rect(1260, 240, 210, 35),
            pygame.Rect(1435, 240, 35, 190),
            pygame.Rect(330, 925, 210, 35),
            pygame.Rect(330, 770, 35, 190),
            pygame.Rect(1260, 925, 210, 35),
            pygame.Rect(1435, 770, 35, 190),
            # 4 trụ bê tông chắn tầm xa
            pygame.Rect(865, 230, 70, 55),
            pygame.Rect(865, 915, 70, 55),
            pygame.Rect(420, 565, 60, 70),
            pygame.Rect(1320, 565, 60, 70),
        ],
    },
}

MAP_ORDER = ["lotus", "cyber_lab", "desert_bazaar", "ice_outpost", "dead_bunker"]

# Biến toàn cục tương thích ngược: cập nhật tại chỗ (in-place) khi đổi map
_current_map_id = "lotus"
walls = list(MAPS["lotus"]["walls"])
site_A = MAPS["lotus"]["sites"]["A"].copy()
site_B = MAPS["lotus"]["sites"]["B"].copy()
site_C = MAPS["lotus"]["sites"]["C"].copy()


def set_active_map(map_id):
    """Đổi bản đồ đang chơi và cập nhật danh sách tường + site A/B/C tại chỗ."""
    global _current_map_id
    if map_id not in MAPS:
        map_id = "lotus"
    _current_map_id = map_id
    m = MAPS[map_id]
    walls[:] = m["walls"]
    site_A.update(m["sites"]["A"])
    site_B.update(m["sites"]["B"])
    site_C.update(m["sites"]["C"])
    return m


def get_active_map():
    return MAPS[_current_map_id]


def get_active_map_id():
    return _current_map_id


def is_blocked(rect, walls_list=None):
    target_walls = walls if walls_list is None else walls_list
    return rect.collidelist(target_walls) != -1


def find_clear_point(x, y, radius=20, walls_list=None):
    """Đảm bảo điểm xuất hiện không kẹt vào tường (dịch nhẹ ra vùng trống nếu cần)."""
    target_walls = walls if walls_list is None else walls_list
    x = max(55, min(MAP_W - 55, float(x)))
    y = max(55, min(MAP_H - 55, float(y)))
    r = pygame.Rect(int(x - radius), int(y - radius), radius * 2, radius * 2)
    if r.collidelist(target_walls) == -1:
        return x, y
    for dist in (28, 56, 88, 125):
        for step in range(8):
            ang = step * (math.tau / 8)
            nx = max(55, min(MAP_W - 55, x + math.cos(ang) * dist))
            ny = max(55, min(MAP_H - 55, y + math.sin(ang) * dist))
            nr = pygame.Rect(int(nx - radius), int(ny - radius), radius * 2, radius * 2)
            if nr.collidelist(target_walls) == -1:
                return nx, ny
    return x, y


def line_blocked(x1, y1, x2, y2, walls_list=None):
    """Kiểm tra đoạn thẳng nối (x1, y1)-(x2, y2) có cắt tường nào không (dùng C clipline siêu tốc)."""
    target_walls = walls if walls_list is None else walls_list
    p1 = (x1, y1)
    p2 = (x2, y2)
    for wall in target_walls:
        if wall.clipline(p1, p2):
            return True
    return False


def seg_dist(px, py, x1, y1, x2, y2):
    """Khoảng cách ngắn nhất từ điểm (px, py) tới đoạn thẳng (x1, y1)-(x2, y2)."""
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / l2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def check_smoke_blocks(x1, y1, x2, y2, smokes):
    """Kiểm tra tia nhìn có bị vùng khói che khuất không."""
    if not smokes:
        return False
    for s in smokes:
        sr = s.get("r", s.get("radius", 130))
        if seg_dist(s["x"], s["y"], x1, y1, x2, y2) <= sr * 0.95:
            return True
    return False
