import pygame
from settings import MAP_W, MAP_H

walls = [
    pygame.Rect(0, 0, MAP_W, 35),
    pygame.Rect(0, MAP_H - 35, MAP_W, 35),
    pygame.Rect(0, 0, 35, MAP_H),
    pygame.Rect(MAP_W - 35, 0, 35, MAP_H),

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

    # C
    pygame.Rect(1030, 700, 35, 270),
    pygame.Rect(1030, 935, 400, 35),
    pygame.Rect(1395, 700, 35, 270),

    # Cover
    pygame.Rect(700, 590, 150, 35),
    pygame.Rect(950, 590, 150, 35),
]


site_A = pygame.Rect(300, 220, 320, 170)
site_B = pygame.Rect(1200, 220, 250, 170)
site_C = pygame.Rect(1080, 750, 280, 150)


def is_blocked(rect):
    return any(rect.colliderect(wall) for wall in walls)


def line_blocked(x1, y1, x2, y2):
    distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    steps = max(1, int(distance / 16))
    dx = (x2 - x1) / steps
    dy = (y2 - y1) / steps

    x = x1
    y = y1

    for _ in range(steps):
        x += dx
        y += dy
        for wall in walls:
            if wall.collidepoint(x, y):
                return True

    return False


def seg_dist(px, py, x1, y1, x2, y2):
    """Tính khoảng cách ngắn nhất từ điểm (px, py) tới đoạn thẳng nối (x1, y1) và (x2, y2)."""
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / l2))
    return ((px - (x1 + t * dx)) ** 2 + (py - (y1 + t * dy)) ** 2) ** 0.5


def check_smoke_blocks(x1, y1, x2, y2, smokes):
    """
    Kiểm tra xem tia nhìn (Line of Sight) giữa (x1, y1) và (x2, y2) có bị làn khói che khuất không.
    Trả về True nếu:
    - Khói nằm chắn giữa 2 điểm.
    - Điểm đầu hoặc điểm cuối nằm trong vùng khói.
    """
    if not smokes:
        return False
    for s in smokes:
        sr = s.get("r", s.get("radius", 130))
        # Bán kính khói che phủ tầm nhìn
        if seg_dist(s["x"], s["y"], x1, y1, x2, y2) <= sr * 0.95:
            return True
    return False
