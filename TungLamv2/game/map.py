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

    # clipline cắt đoạn thẳng với hình chữ nhật (chạy bằng C) -> nhanh hơn
    # nhiều so với nhích từng 16px và dò mọi bức tường.
    # Bỏ qua tường mà điểm đầu đang đứng sát/trong (giống bản cũ chỉ xét từ bước đầu).
    for wall in walls:
        if wall.clipline(x1, y1, x2, y2):
            if not wall.collidepoint(x1, y1):
                return True

    return False