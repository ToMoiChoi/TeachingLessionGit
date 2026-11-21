"""Hệ thống vẽ đồ họa Vector Chú Thuật Hồi Chiến: Bản đồ, Bành Trướng Lãnh Địa, Nhân Vật, Chú Cụ & Thức Thần."""

import math
import pygame
from config import (
    WIDTH, HEIGHT, GROUND_Y, WHITE, BLACK, DARK, GRAY,
    RED, CRIMSON, GREEN, RCT_GREEN, BLUE, LAPSE_BLUE, REVERSAL_RED,
    HOLLOW_PURPLE, CYAN, YELLOW, GOLD, PURPLE, PINK, ORANGE,
    FONT_SMALL, FONT_TINY, draw_text
)


# ============================================================
# 1. VẼ BẢN ĐỒ & KHÔNG GIAN BÀNH TRƯỚNG LÃNH ĐỊA
# ============================================================

def draw_arena_background(screen, current_map, domain_state, blood_stains, anim_time):
    dom_active = domain_state.get("active", False)
    dom_id = domain_state.get("char_id", "")
    is_clash = domain_state.get("clash", False)

    if dom_active:
        _draw_domain_space(screen, dom_id, is_clash, anim_time)
        return

    bg_top = current_map["bg_top"]
    bg_bottom = current_map["bg_bottom"]
    floor_color = current_map["floor"]
    accent = current_map["accent"]
    map_id = current_map["id"]

    # Gradient bầu trời (vẽ theo dải 4px để mượt 60FPS trên trình duyệt WebAssembly)
    for y in range(0, GROUND_Y, 4):
        ratio = y / GROUND_Y
        col = (
            int(bg_top[0] * (1 - ratio) + bg_bottom[0] * ratio),
            int(bg_top[1] * (1 - ratio) + bg_bottom[1] * ratio),
            int(bg_top[2] * (1 - ratio) + bg_bottom[2] * ratio),
        )
        pygame.draw.rect(screen, col, (0, y, WIDTH, 4))

    if map_id == "tokyo_high":
        # Trăng rằm vàng kim & Cổng Torii Cao Chuyên Tokyo
        pygame.draw.circle(screen, (255, 240, 185), (880, 115), 52)
        pygame.draw.circle(screen, accent, (880, 115), 56, 2)
        # Dãy núi mờ phía xa
        pts = [(0, GROUND_Y), (180, 340), (390, 420), (620, 320), (860, 400), (WIDTH, 330), (WIDTH, GROUND_Y)]
        pygame.draw.polygon(screen, (18, 26, 44), pts)
        # Cổng Torii truyền thống ở trung tâm
        tx = WIDTH // 2
        pygame.draw.rect(screen, (165, 35, 35), (tx - 110, GROUND_Y - 190, 18, 190))
        pygame.draw.rect(screen, (165, 35, 35), (tx + 92, GROUND_Y - 190, 18, 190))
        pygame.draw.rect(screen, (195, 45, 40), (tx - 145, GROUND_Y - 205, 290, 18), border_radius=4)
        pygame.draw.rect(screen, (145, 30, 30), (tx - 120, GROUND_Y - 165, 240, 12))
    elif map_id == "shibuya":
        # Màn Trướng (Curtain) bao phủ Shibuya + Tòa nhà đèn Neon
        for arc_r in (480, 560, 640):
            pygame.draw.circle(screen, (55, 35, 95), (WIDTH // 2, GROUND_Y + 80), arc_r, 1)
        for i in range(10):
            bx = 35 + i * 108
            bh = 130 + ((i * 53) % 160)
            pygame.draw.rect(screen, (18, 16, 32), (bx, GROUND_Y - bh, 86, bh))
            pygame.draw.rect(screen, (45, 40, 78), (bx, GROUND_Y - bh, 86, bh), 1)
            neon_col = CYAN if i % 2 == 0 else PINK
            pygame.draw.rect(screen, neon_col, (bx + 12, GROUND_Y - bh + 18, 62, 18), 2)
            for wy in range(GROUND_Y - bh + 50, GROUND_Y - 15, 26):
                pygame.draw.rect(screen, (70, 90, 140), (bx + 14, wy, 14, 10))
                pygame.draw.rect(screen, (70, 90, 140), (bx + 48, wy, 14, 10))
    else:
        # Kết Giới Tử Diệt Hồi Du (Huyết Nguyệt & Cột Đá Cổ)
        pygame.draw.circle(screen, (220, 40, 50), (550, 125), 58)
        pygame.draw.circle(screen, (35, 10, 15), (550, 125), 46)
        pygame.draw.circle(screen, GOLD, (550, 125), 60, 2)
        for i in range(7):
            px = 80 + i * 155
            ph = 120 + ((i * 41) % 130)
            pygame.draw.rect(screen, (38, 18, 24), (px, GROUND_Y - ph, 46, ph))
            pygame.draw.line(screen, accent, (px + 23, 0), (px + 23, GROUND_Y - ph), 1)

    # Sàn đấu
    pygame.draw.rect(screen, floor_color, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
    pygame.draw.line(screen, accent, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

    for stain in blood_stains:
        pygame.draw.ellipse(
            screen, stain["color"],
            (int(stain["x"] - stain["w"] // 2), GROUND_Y + 3, int(stain["w"]), int(stain["h"]))
        )

    for x in range(0, WIDTH + 100, 110):
        pygame.draw.line(screen, (55, 64, 82), (x, GROUND_Y), (x - 45, HEIGHT), 1)


def _draw_domain_space(screen, dom_id, is_clash, anim_time):
    """Biến đổi toàn bộ sân đấu khi kích hoạt Bành Trướng Lãnh Địa (Domain Expansion)."""
    cx, cy = WIDTH // 2, 250

    if is_clash:
        # Giằng co Lãnh Địa chia đôi không gian!
        pygame.draw.rect(screen, (15, 25, 65), (0, 0, cx, GROUND_Y))
        pygame.draw.rect(screen, (65, 12, 22), (cx, 0, WIDTH - cx, GROUND_Y))
        pygame.draw.rect(screen, (22, 24, 38), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        for i in range(8):
            ang = anim_time * 5 + i * 0.8
            ox = int(math.sin(ang * 3) * 18)
            pygame.draw.line(screen, GOLD, (cx + ox, i * 65), (cx - ox, (i + 1) * 65), 4)
        pygame.draw.line(screen, WHITE, (cx, 0), (cx, HEIGHT), 2)
        return

    if dom_id == "gojo":
        # VÔ LƯỢNG KHÔNG XỬ: Vũ trụ hố đen & vô tận thông tin
        screen.fill((6, 8, 20))
        for i in range(28):
            angle = i * (math.pi * 2 / 28) + anim_time * 0.4
            x2 = cx + math.cos(angle) * 650
            y2 = cy + math.sin(angle) * 420
            col = LAPSE_BLUE if i % 2 == 0 else (180, 220, 255)
            pygame.draw.line(screen, col, (cx, cy), (int(x2), int(y2)), 1)
        pygame.draw.circle(screen, WHITE, (cx, cy), 92, 4)
        pygame.draw.circle(screen, LAPSE_BLUE, (cx, cy), 102, 2)
        pygame.draw.circle(screen, (2, 3, 8), (cx, cy), 88)
        pygame.draw.rect(screen, (12, 18, 38), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.line(screen, WHITE, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

    elif dom_id in ("sukuna", "heian_sukuna"):
        # PHỤC MA NGỰ TRÙ TỬ: Bầu trời máu & Ngôi đền ma quái
        screen.fill((38, 6, 12))
        pygame.draw.rect(screen, (26, 8, 10), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        # Ngôi đền Ngự Trù Tử ở giữa sân
        pygame.draw.rect(screen, (20, 10, 14), (cx - 130, GROUND_Y - 210, 260, 210))
        pygame.draw.polygon(
            screen, (85, 14, 22),
            [(cx - 175, GROUND_Y - 205), (cx + 175, GROUND_Y - 205), (cx + 125, GROUND_Y - 265), (cx - 125, GROUND_Y - 265)]
        )
        pygame.draw.rect(screen, (140, 20, 30), (cx - 45, GROUND_Y - 140, 90, 140))
        # Các vệt chém Bổ & Phân chớp nhoáng khắp không gian
        for i in range(9):
            sx = (int(anim_time * 500) + i * 137) % WIDTH
            sy = (i * 63 + int(anim_time * 240)) % (GROUND_Y - 30)
            pygame.draw.line(screen, REVERSAL_RED, (sx - 45, sy - 20), (sx + 45, sy + 20), 2)
            pygame.draw.line(screen, WHITE, (sx - 30, sy + 18), (sx + 30, sy - 18), 1)
        pygame.draw.line(screen, REVERSAL_RED, (0, GROUND_Y), (WIDTH, GROUND_Y), 4)

    elif dom_id == "megumi":
        # KHẢM ÁM GIAO ĐÌNH: Biển bóng tối sâu thẳm
        screen.fill((8, 10, 18))
        for i in range(5):
            h_arc = 90 + i * 32
            pygame.draw.ellipse(screen, (24, 30, 52), (cx - 220 + i * 10, GROUND_Y - h_arc * 2, 440 - i * 20, h_arc), 3)
        pygame.draw.rect(screen, (4, 5, 10), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        for i in range(12):
            rx = int((i * 98 + anim_time * 90) % WIDTH)
            pygame.draw.ellipse(screen, (45, 70, 130), (rx - 40, GROUND_Y + 8 + (i % 3) * 28, 80, 16), 2)
        pygame.draw.line(screen, (90, 145, 255), (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

    elif dom_id == "yuta":
        # CHÂN NHÃ TƯƠNG ÁI: Cánh đồng vạn kiếm Katana
        screen.fill((34, 20, 44))
        pygame.draw.circle(screen, (75, 42, 95), (cx, 160), 120, 2)
        pygame.draw.rect(screen, (26, 18, 36), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        for kx in range(45, WIDTH, 68):
            kh = 48 + (kx % 25)
            pygame.draw.line(screen, (210, 225, 245), (kx, GROUND_Y), (kx + 6, GROUND_Y - kh), 3)
            pygame.draw.line(screen, PINK, (kx - 6, GROUND_Y - kh + 12), (kx + 14, GROUND_Y - kh + 10), 3)
        pygame.draw.line(screen, PINK, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

    elif dom_id == "nanami":
        # THẬP HOẠCH TUYỆT ĐIỂM GIỚI: Lưới tọa độ tỷ lệ 7:3
        screen.fill((22, 20, 14))
        for gx in range(0, WIDTH, 110):
            col = GOLD if (gx // 110) == 7 else (55, 50, 35)
            pygame.draw.line(screen, col, (gx, 0), (gx, GROUND_Y), 3 if col == GOLD else 1)
        for gy in range(60, GROUND_Y, 75):
            pygame.draw.line(screen, (55, 50, 35), (0, gy), (WIDTH, gy), 1)
        pygame.draw.rect(screen, (32, 28, 20), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.line(screen, GOLD, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

    else:
        # Lãnh địa đặc trưng cho Inumaki, Kamo, Nobara, Hanami, Jogo, Mahito
        palette = {
            "inumaki": ((28, 14, 48), PURPLE),
            "kamo": ((46, 8, 16), CRIMSON),
            "nobara": ((36, 16, 28), ORANGE),
            "hanami": ((12, 38, 22), GREEN),
            "jogo": ((52, 18, 8), ORANGE),
            "mahito": ((26, 12, 42), PURPLE),
        }
        bg_c, ring_c = palette.get(dom_id, ((20, 16, 40), CYAN))
        screen.fill(bg_c)
        for r in range(70, 420, 75):
            pulse = int((anim_time * 80 + r) % 360)
            pygame.draw.circle(screen, ring_c, (cx, cy), pulse + 40, 2)
        pygame.draw.rect(screen, (18, 16, 26), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.line(screen, ring_c, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)


# ============================================================
# 2. VẼ ĐẤU SĨ CHÚ THUẬT SƯ & HIỆU ỨNG TRẠNG THÁI
# ============================================================

def draw_jjk_fighter(screen, fighter, opponent, anim_time, show_ratio=False):
    fx = int(fighter.x)
    fy = int(fighter.y)
    cid = fighter.char_id
    facing = fighter.facing
    is_crouch = fighter.is_crouching
    color = WHITE if fighter.hit_flash > 0 else fighter.color

    cur_h = int(fighter.height * 0.65) if is_crouch else fighter.height
    top_y = fy - cur_h
    head_y = top_y + 16

    # --- A. GIẢN DỊ LÃNH ĐỊA (SIMPLE DOMAIN) DƯỚI CHÂN ---
    if fighter.simple_domain_timer > 0:
        sd_r = 78 + int(math.sin(anim_time * 12) * 5)
        pygame.draw.ellipse(screen, (20, 95, 135), (fx - sd_r, GROUND_Y - 18, sd_r * 2, 34))
        pygame.draw.ellipse(screen, CYAN, (fx - sd_r, GROUND_Y - 18, sd_r * 2, 34), 3)
        pygame.draw.ellipse(screen, WHITE, (fx - sd_r + 14, GROUND_Y - 13, (sd_r - 14) * 2, 24), 1)
        # Vòm chắn mờ xung quanh người
        pygame.draw.circle(screen, CYAN, (fx, fy - 56), 64, 2)

    # Bóng dưới đất (Megumi có đầm lầy bóng tối đặc trưng)
    if cid == "megumi":
        pygame.draw.ellipse(screen, (5, 7, 14), (fx - 52, GROUND_Y - 12, 104, 24))
        pygame.draw.ellipse(screen, (70, 110, 210), (fx - 52, GROUND_Y - 12, 104, 24), 2)
    else:
        pygame.draw.ellipse(screen, (12, 16, 26), (fx - 38, GROUND_Y - 9, 76, 18))

    # --- B. HÀO QUANG CHÚ LỰC (HẮC THIỂM ZONE / TĂNG CA / XÍCH LÂN / VÔ HẠ HẠN) ---
    if cid == "gojo":
        # Lớp rào chắn không gian Vô Hạ Hạn mỏng quanh người
        inf_r = 58 + int(math.sin(anim_time * 5) * 3)
        pygame.draw.circle(screen, (60, 165, 255), (fx, fy - 55), inf_r, 1)

    if fighter.zone_timer > 0:
        # Hào quang tia chớp Đen-Đỏ khi vào Zone 120% Hắc Thiểm!
        for i in range(4):
            ang = anim_time * 10 + i * 1.57
            ax = fx + int(math.cos(ang) * 42)
            ay = fy - 55 + int(math.sin(ang) * 48)
            pygame.draw.line(screen, REVERSAL_RED, (fx, fy - 55), (ax, ay), 3)
            pygame.draw.line(screen, BLACK, (fx, fy - 55), (ax, ay), 1)

    if fighter.overtime_timer > 0:
        pygame.draw.circle(screen, GOLD, (fx, fy - 55), 52 + int(math.sin(anim_time * 14) * 4), 2)

    if fighter.red_scale_timer > 0:
        pygame.draw.circle(screen, CRIMSON, (fx, fy - 55), 48, 2)

    if fighter.rct_heal_left > 0:
        # Năng lượng dương Nghịch Chuyển Thuật Thức bốc lên
        pygame.draw.circle(screen, RCT_GREEN, (fx, fy - 55), 50, 2)

    if fighter.shield_hp > 0:
        pygame.draw.circle(screen, PINK, (fx, fy - 55), 60, 2)

    # --- C. NỮ HOÀNG NGUYỀN RỦA RIKA LƠ LỬNG PHÍA SAU YUTA ---
    if cid == "yuta":
        rx = fx - facing * 42
        ry = top_y - 12 + int(math.sin(anim_time * 4) * 6)
        pygame.draw.circle(screen, (45, 25, 65), (rx, ry), 26)
        pygame.draw.circle(screen, PINK, (rx, ry), 26, 2)
        # Một con mắt xoáy đặc trưng của Rika
        pygame.draw.circle(screen, WHITE, (rx + facing * 6, ry - 2), 6)
        pygame.draw.circle(screen, CRIMSON, (rx + facing * 6, ry - 2), 3)

    # --- D. VẼ CƠ THỂ & TRANG PHỤC ĐẶC TRƯNG TỪNG NHÂN VẬT ---
    suit_col = (24, 28, 44)
    if cid in ("sukuna", "heian_sukuna"):
        suit_col = (225, 220, 215)  # Kimono trắng Sukuna
    elif cid == "yuta":
        suit_col = (235, 238, 245)  # Áo khoác trắng Yuta
    elif cid == "nanami":
        suit_col = (198, 178, 142)  # Bộ vest màu kem của Nanami
    elif cid == "toji":
        suit_col = (22, 24, 30)     # Áo đen bó sát của Toji

    # Chân
    if not is_crouch:
        leg_col = (25, 30, 45) if cid != "nanami" else (165, 145, 115)
        pygame.draw.line(screen, leg_col, (fx - 10, fy - 34), (fx - 15, fy), 11)
        pygame.draw.line(screen, leg_col, (fx + 10, fy - 34), (fx + 15, fy), 11)

    # Thân áo
    body_h = max(28, cur_h - 46)
    body_rect = pygame.Rect(fx - 20, top_y + 28, 40, body_h)
    pygame.draw.rect(screen, suit_col, body_rect, border_radius=8)
    pygame.draw.rect(screen, color, body_rect, 2, border_radius=8)

    # Chi tiết trang phục đặc trưng
    if cid in ("sukuna", "heian_sukuna"):
        # Đai lưng đen & Hình xăm nguyền chú của Sukuna
        pygame.draw.rect(screen, (30, 25, 32), (fx - 20, body_rect.bottom - 14, 40, 8))
        pygame.draw.line(screen, BLACK, (fx - 14, body_rect.top + 10), (fx + 14, body_rect.top + 10), 2)
        if cid == "heian_sukuna":
            # Cặp tay thứ 2 của Sukuna Nguyên Bản!
            pygame.draw.line(screen, (235, 190, 180), (fx - 18, body_rect.centery), (fx - 36, body_rect.centery + 8), 6)
            pygame.draw.line(screen, (235, 190, 180), (fx + 18, body_rect.centery), (fx + 36, body_rect.centery + 8), 6)
    elif cid == "nanami":
        # Cà vạt vàng chấm đen đặc trưng của Nanami
        pygame.draw.line(screen, GOLD, (fx, body_rect.top + 4), (fx, body_rect.bottom - 8), 5)
    elif cid == "inumaki":
        # Cổ áo cao che miệng Chú Ngôn
        pygame.draw.rect(screen, (32, 38, 58), (fx - 16, head_y + 3, 32, 16), border_radius=4)
        pygame.draw.circle(screen, PURPLE, (fx + facing * 7, head_y + 10), 3)
    elif cid == "toji":
        # Chú linh Kho Chứa Vũ Khí quấn ngang vai Toji
        pygame.draw.arc(screen, (145, 95, 175), (fx - 26, body_rect.top - 4, 52, 34), 0, 3.14, 7)
    elif cid == "kamo":
        # 3 Quả cầu máu xoay quanh Kamo Noritoshi
        for i in range(3):
            ba = anim_time * 4.5 + i * 2.09
            bx = fx + int(math.cos(ba) * 36)
            by = body_rect.centery + int(math.sin(ba) * 16)
            pygame.draw.circle(screen, CRIMSON, (bx, by), 6)
            pygame.draw.circle(screen, WHITE, (bx - 2, by - 2), 2)
    elif cid == "nobara":
        # Các đinh chú lực lơ lửng quanh Nobara
        for i in range(3):
            na = anim_time * 3.8 + i * 2.1
            nx = fx - facing * 28 + int(math.cos(na) * 10)
            ny = top_y + 15 + i * 16
            pygame.draw.line(screen, ORANGE, (nx - 5, ny), (nx + 5, ny - 4), 3)

    # Đầu & Tóc đặc trưng
    skin_col = (242, 216, 196)
    if cid == "hanami":
        skin_col = (225, 235, 220)
    elif cid == "jogo":
        skin_col = (195, 185, 165)
    elif cid == "mahito":
        skin_col = (205, 215, 230)

    pygame.draw.circle(screen, skin_col, (fx, head_y), 17)
    pygame.draw.circle(screen, color, (fx, head_y), 17, 2)

    # Tóc / Đầu riêng từng nhân vật
    if cid == "gojo":
        # Tóc trắng dựng + Băng bịt mắt đen ánh Lục Nhãn xanh sáng
        for dx in (-12, -5, 2, 9):
            pygame.draw.polygon(screen, WHITE, [(fx + dx - 5, head_y - 10), (fx + dx + 5, head_y - 10), (fx + dx, head_y - 26)])
        pygame.draw.rect(screen, (15, 18, 26), (fx - 16, head_y - 6, 32, 9), border_radius=2)
        pygame.draw.circle(screen, CYAN, (fx + facing * 6, head_y - 2), 3)
    elif cid in ("sukuna", "heian_sukuna"):
        # Tóc hồng dựng + 4 mắt đỏ rực
        for dx in (-11, -3, 4, 11):
            pygame.draw.polygon(screen, (245, 130, 155), [(fx + dx - 5, head_y - 11), (fx + dx + 5, head_y - 11), (fx + dx, head_y - 25)])
        pygame.draw.circle(screen, REVERSAL_RED, (fx + facing * 6, head_y - 3), 3)
        pygame.draw.circle(screen, REVERSAL_RED, (fx + facing * 4, head_y + 3), 2)
    elif cid == "megumi":
        # Tóc đen nhím biển đặc trưng của Megumi
        for ang_deg in (-150, -120, -90, -60, -30):
            rad = math.radians(ang_deg)
            tx = fx + int(math.cos(rad) * 28)
            ty = head_y + int(math.sin(rad) * 28)
            pygame.draw.polygon(screen, (20, 26, 40), [(fx - 6, head_y - 10), (fx + 6, head_y - 10), (tx, ty)])
        pygame.draw.circle(screen, (40, 90, 180), (fx + facing * 6, head_y - 1), 3)
    elif cid == "yuta":
        pygame.draw.arc(screen, (20, 22, 32), (fx - 18, head_y - 18, 36, 24), 0, 3.14, 8)
        pygame.draw.circle(screen, (60, 90, 140), (fx + facing * 6, head_y - 1), 3)
    elif cid == "inumaki":
        pygame.draw.arc(screen, (235, 228, 210), (fx - 18, head_y - 18, 36, 24), 0, 3.14, 8)
        pygame.draw.circle(screen, PURPLE, (fx + facing * 6, head_y - 3), 3)
    elif cid == "kamo":
        pygame.draw.arc(screen, (22, 20, 28), (fx - 18, head_y - 19, 36, 24), 0, 3.14, 9)
        pygame.draw.line(screen, CRIMSON, (fx + facing * 4, head_y - 2), (fx + facing * 10, head_y - 2), 2)
    elif cid == "nobara":
        pygame.draw.arc(screen, (195, 98, 45), (fx - 19, head_y - 18, 38, 28), -0.3, 3.4, 8)
        pygame.draw.circle(screen, ORANGE, (fx + facing * 6, head_y - 1), 3)
    elif cid == "nanami":
        pygame.draw.arc(screen, (235, 200, 115), (fx - 17, head_y - 18, 34, 20), 0.2, 3.0, 8)
        pygame.draw.rect(screen, (40, 170, 115), (fx + facing * 2, head_y - 5, 11, 6), border_radius=2)
    elif cid == "jogo":
        # Đỉnh núi lửa phun khói trên đầu Jogo + 1 mắt độc nhãn!
        pygame.draw.polygon(screen, (120, 65, 35), [(fx - 14, head_y - 10), (fx + 14, head_y - 10), (fx + 8, head_y - 28), (fx - 8, head_y - 28)])
        pygame.draw.circle(screen, ORANGE, (fx, head_y - 28), 6)
        pygame.draw.circle(screen, RED, (fx + facing * 5, head_y - 1), 5)
        pygame.draw.circle(screen, YELLOW, (fx + facing * 5, head_y - 1), 2)
    elif cid == "hanami":
        # Hai nhánh cây mọc từ hốc mắt Hanami
        pygame.draw.line(screen, (110, 65, 40), (fx - 4, head_y - 3), (fx - 18, head_y - 24), 4)
        pygame.draw.line(screen, (110, 65, 40), (fx + 5, head_y - 3), (fx + 18, head_y - 24), 4)
    elif cid == "mahito":
        # Tóc xanh bạc dài và vết khâu của Mahito
        pygame.draw.arc(screen, (135, 165, 215), (fx - 20, head_y - 19, 40, 32), -0.4, 3.5, 8)
        pygame.draw.line(screen, (50, 50, 65), (fx - 12, head_y + 4), (fx + 12, head_y + 4), 2)
    elif cid == "toji":
        pygame.draw.arc(screen, (18, 20, 26), (fx - 18, head_y - 18, 36, 22), 0, 3.14, 8)
        pygame.draw.circle(screen, GREEN, (fx + facing * 6, head_y - 1), 3)

    # --- E. VẼ CHÚ CỤ / VŨ KHÍ & ĐÒN TẤN CÔNG ---
    hand_x = fx + facing * 18
    hand_y = fy - 46 if is_crouch else fy - 58
    reach = 82 if fighter.attack_timer > 0 else 48

    if cid in ("yuta", "megumi"):
        # Thanh Katana / Ảnh Kiếm bọc chú lực
        end_x = hand_x + facing * reach
        end_y = hand_y - (10 if fighter.attack_timer > 0 else 24)
        glow = PINK if cid == "yuta" else (80, 130, 255)
        pygame.draw.line(screen, glow, (hand_x, hand_y), (end_x, end_y), 7)
        pygame.draw.line(screen, WHITE, (hand_x, hand_y), (end_x, end_y), 2)
    elif cid == "nanami":
        # Đoản đao quấn băng vải trắng chấm đen của Nanami
        end_x = hand_x + facing * int(reach * 0.85)
        end_y = hand_y - 14
        pygame.draw.line(screen, WHITE, (hand_x, hand_y), (end_x, end_y), 8)
        pygame.draw.line(screen, GOLD, (hand_x, hand_y), (end_x, end_y), 2)
    elif cid == "nobara":
        # Búa sắt Chú Cụ của Nobara
        end_x = hand_x + facing * 34
        end_y = hand_y - 16
        pygame.draw.line(screen, (140, 150, 170), (hand_x, hand_y), (end_x, end_y), 4)
        pygame.draw.rect(screen, (90, 100, 120), (end_x - 8, end_y - 8, 16, 14), border_radius=2)
    elif cid == "toji":
        # Thiên Nghịch Mâu chữ J đặc trưng của Toji
        end_x = hand_x + facing * int(reach * 0.9)
        end_y = hand_y - 12
        pygame.draw.line(screen, (215, 225, 240), (hand_x, hand_y), (end_x, end_y), 5)
        pygame.draw.line(screen, CYAN, (end_x - facing * 10, end_y), (end_x - facing * 10, end_y + 12), 4)
    else:
        # Nắm đấm bọc Chú Lực phát sáng (Gojo, Sukuna, Inumaki, Kamo, Bosses)
        fist_x = hand_x + (facing * 32 if fighter.attack_timer > 0 else facing * 8)
        pygame.draw.circle(screen, color, (fist_x, hand_y), 9 if fighter.attack_timer > 0 else 6)
        pygame.draw.circle(screen, WHITE, (fist_x, hand_y), 4)

    # Vòng cung chém khi đang tung đòn cận chiến
    if fighter.attack_timer > 0:
        arc_rect = (fx - 88, fy - 112, 176, 128)
        s_ang, e_ang = (-1.15, 1.15) if facing == 1 else (math.pi - 1.15, math.pi + 1.15)
        slash_col = REVERSAL_RED if fighter.attack_type == "black_flash" else color
        pygame.draw.arc(screen, slash_col, arc_rect, s_ang, e_ang, 8)
        pygame.draw.arc(screen, WHITE, arc_rect, s_ang, e_ang, 2)

    # Khiên Parry chớp nhoáng
    if fighter.parry_timer > 0:
        pygame.draw.circle(screen, WHITE, (fx, fy - 56), 58, 3)

    # --- F. ĐINH SÔ LINH CHÚ PHÁP GĂM TRÊN MỤC TIÊU ---
    if fighter.nail_stacks > 0:
        for n_idx in range(fighter.nail_stacks):
            nx = fx - 14 + (n_idx % 3) * 14
            ny = body_rect.top + 10 + (n_idx // 3) * 18
            pygame.draw.line(screen, PINK, (nx - 6, ny - 5), (nx + 4, ny + 4), 3)
            pygame.draw.circle(screen, ORANGE, (nx - 6, ny - 5), 3)
        draw_text(screen, f"Đinh: {fighter.nail_stacks}", fx, top_y - 44, ORANGE, FONT_TINY, center=True)

    # --- G. THƯỚC TỶ LỆ 7:3 CỦA NANAMI TRÊN MỤC TIÊU ---
    if show_ratio and fighter.alive:
        bar_w = 80
        bx = fx - bar_w // 2
        by = fy - cur_h - 32
        pygame.draw.line(screen, WHITE, (bx, by), (bx + bar_w, by), 2)
        for seg in range(11):
            sx = bx + int(bar_w * (seg / 10.0))
            pygame.draw.line(screen, GRAY, (sx, by - 4), (sx, by + 4), 1)
        # Vạch thứ 7 (tỷ lệ 7:3) phát sáng rực rỡ!
        x_73 = bx + int(bar_w * 0.7)
        pygame.draw.circle(screen, REVERSAL_RED, (x_73, by), 7)
        pygame.draw.circle(screen, GOLD, (x_73, by), 4)
        draw_text(screen, "7:3", x_73, by - 14, GOLD, FONT_TINY, center=True)

    # Nhãn tên nhân vật & trạng thái Choáng
    tag_text = "CHOÁNG!" if fighter.stun_timer > 0 else fighter.name.split(" - ")[0]
    tag_col = YELLOW if fighter.stun_timer > 0 else WHITE
    name_surf = FONT_TINY.render(tag_text, True, tag_col)
    name_rect = name_surf.get_rect(center=(fx, head_y - 28))
    pygame.draw.rect(screen, DARK, name_rect.inflate(10, 4), border_radius=5)
    pygame.draw.rect(screen, color, name_rect.inflate(10, 4), 1, border_radius=5)
    screen.blit(name_surf, name_rect)


# ============================================================
# 3. VẼ ĐẠN THUẬT THỨC (PROJECTILES) & THỨC THẦN (SHIKIGAMI)
# ============================================================

def draw_projectile(screen, proj):
    px, py = int(proj.x), int(proj.y)
    r = int(proj.radius)
    kind = proj.kind

    if kind == "blue_orb":
        # Thuận Chuyển: Xanh (vòng xoáy hút không gian)
        pygame.draw.circle(screen, (20, 90, 210), (px, py), r + 8, 2)
        pygame.draw.circle(screen, LAPSE_BLUE, (px, py), r)
        pygame.draw.circle(screen, WHITE, (px, py), max(5, r // 2))
        for i in range(4):
            a = proj.phase + i * 1.57
            pygame.draw.line(
                screen, CYAN,
                (px + int(math.cos(a) * (r + 14)), py + int(math.sin(a) * (r + 14))),
                (px + int(math.cos(a + 0.8) * (r - 4)), py + int(math.sin(a + 0.8) * (r - 4))),
                2,
            )

    elif kind == "red_orb":
        # Nghịch Chuyển: Đỏ (hạt nhân đỏ rực đẩy văng)
        pygame.draw.circle(screen, (150, 15, 35), (px, py), r + 10, 3)
        pygame.draw.circle(screen, REVERSAL_RED, (px, py), r)
        pygame.draw.circle(screen, WHITE, (px, py), max(4, r // 2))

    elif kind == "hollow_purple":
        # HƯ THỨC: TÍM (Hollow Purple khổng lồ!)
        pulse = int(math.sin(proj.phase * 2) * 6)
        pygame.draw.circle(screen, LAPSE_BLUE, (px - 8, py), r + 6, 3)
        pygame.draw.circle(screen, REVERSAL_RED, (px + 8, py), r + 6, 3)
        pygame.draw.circle(screen, (95, 25, 165), (px, py), r + pulse)
        pygame.draw.circle(screen, HOLLOW_PURPLE, (px, py), max(8, r - 8))
        pygame.draw.circle(screen, WHITE, (px, py), max(6, r // 3))

    elif kind in ("slash", "cleave_web"):
        # Nhát chém Phân / Bổ (Sukuna, Yuta, Nanami)
        dir_s = 1 if proj.vx >= 0 else -1
        pygame.draw.line(screen, proj.color, (px - dir_s * 22, py - r), (px + dir_s * 18, py + r), 6)
        pygame.draw.line(screen, WHITE, (px - dir_s * 18, py - r + 4), (px + dir_s * 16, py + r - 4), 2)
        if kind == "cleave_web":
            pygame.draw.line(screen, REVERSAL_RED, (px - 28, py + r - 6), (px + 28, py - r + 6), 4)
            pygame.draw.line(screen, BLACK, (px - 32, py), (px + 32, py), 3)

    elif kind == "fuga_arrow":
        # Thần Hỏa: Fuga (Mũi tên lửa địa ngục của Sukuna)
        dir_s = 1 if proj.vx >= 0 else -1
        pygame.draw.circle(screen, ORANGE, (px, py), r + 6)
        pygame.draw.polygon(
            screen, YELLOW,
            [(px + dir_s * (r + 24), py), (px - dir_s * r, py - 16), (px - dir_s * r, py + 16)]
        )
        pygame.draw.line(screen, WHITE, (px - dir_s * 30, py), (px + dir_s * 24, py), 4)

    elif kind == "speech_wave":
        # Sóng âm Chú Ngôn Inumaki
        pygame.draw.circle(screen, proj.color, (px, py), r, 4)
        pygame.draw.circle(screen, WHITE, (px, py), max(6, r - 10), 2)
        pygame.draw.circle(screen, PURPLE, (px, py), 6)

    elif kind == "piercing_blood":
        # Xuyên Huyết siêu thanh của Kamo (Tia laser máu ngang màn hình)
        dir_s = 1 if proj.vx >= 0 else -1
        tail_x = px - dir_s * 240
        pygame.draw.line(screen, CRIMSON, (tail_x, py), (px + dir_s * 35, py), 12)
        pygame.draw.line(screen, RED, (tail_x, py), (px + dir_s * 35, py), 6)
        pygame.draw.line(screen, WHITE, (tail_x + dir_s * 40, py), (px + dir_s * 35, py), 2)

    elif kind == "love_beam":
        # Thuần Ái Pháo của Rika & Yuta
        dir_s = 1 if proj.vx >= 0 else -1
        tail_x = px - dir_s * 280
        pygame.draw.line(screen, PURPLE, (tail_x, py), (px + dir_s * 45, py), 34)
        pygame.draw.line(screen, PINK, (tail_x, py), (px + dir_s * 45, py), 20)
        pygame.draw.line(screen, WHITE, (tail_x, py), (px + dir_s * 45, py), 8)

    elif kind == "nail":
        # Đinh Chú Lực của Nobara
        dir_s = 1 if proj.vx >= 0 else -1
        pygame.draw.line(screen, PINK, (px - dir_s * 16, py), (px + dir_s * 14, py), 5)
        pygame.draw.line(screen, WHITE, (px - dir_s * 12, py), (px + dir_s * 14, py), 2)

    elif kind == "resonance_spike":
        # Cọc Cộng Hưởng Búp Bê Rơm xuyên thẳng mục tiêu!
        pygame.draw.line(screen, ORANGE, (px, py - 95), (px, py + 45), 10)
        pygame.draw.line(screen, WHITE, (px, py - 90), (px, py + 40), 3)
        pygame.draw.circle(screen, PINK, (px, py - 15), r, 3)

    elif kind == "roots":
        # Rễ cây Mộc Độn của Boss Hanami
        pygame.draw.polygon(screen, (115, 70, 42), [(px - 22, GROUND_Y), (px + 22, GROUND_Y), (px, GROUND_Y - 95)])
        pygame.draw.polygon(screen, GREEN, [(px - 16, GROUND_Y), (px + 16, GROUND_Y), (px, GROUND_Y - 90)], 2)

    elif kind == "meteor":
        # Thiên Thạch Cực Phiên của Boss Jogo
        pygame.draw.circle(screen, ORANGE, (px, py), r + 8)
        pygame.draw.circle(screen, (95, 45, 25), (px, py), r)
        pygame.draw.circle(screen, YELLOW, (px - 6, py - 6), r // 3)

    else:
        pygame.draw.circle(screen, proj.color, (px, py), r)
        pygame.draw.circle(screen, WHITE, (px, py), max(3, r // 2), 2)


def draw_shikigami(screen, shiki):
    sx, sy = int(shiki.x), int(shiki.y)
    f = shiki.facing
    kind = shiki.kind

    if kind == "divine_dog":
        # Ngọc Khuyển: Hỗn (Sói bóng tối lao tới)
        pygame.draw.ellipse(screen, (15, 18, 28), (sx - 34, sy - 38, 68, 32))
        pygame.draw.ellipse(screen, (90, 145, 255), (sx - 34, sy - 38, 68, 32), 2)
        head_x = sx + f * 32
        pygame.draw.polygon(screen, (20, 24, 38), [(head_x, sy - 46), (head_x + f * 22, sy - 30), (head_x - f * 6, sy - 22)])
        pygame.draw.circle(screen, RED, (head_x + f * 6, sy - 34), 3)

    elif kind == "nue":
        # Chim ưng sấm sét Nue
        wing_y = int(math.sin(shiki.phase * 3) * 18)
        pygame.draw.polygon(screen, (175, 110, 55), [(sx - 42, sy - wing_y), (sx, sy + 10), (sx + 42, sy - wing_y), (sx, sy - 12)])
        pygame.draw.circle(screen, WHITE, (sx + f * 12, sy), 9)
        pygame.draw.circle(screen, PURPLE, (sx, sy), 34, 2)

    elif kind == "mahoraga":
        # Dị Giới Thần Tướng MAHORAGA + Pháp Luân 8 tay xoay tròn trên đỉnh đầu!
        wheel_y = sy - 158
        pygame.draw.circle(screen, GOLD, (sx, wheel_y), 24, 4)
        for i in range(8):
            a = shiki.phase * 0.6 + i * (math.pi / 4)
            pygame.draw.line(
                screen, GOLD,
                (sx + int(math.cos(a) * 14), wheel_y + int(math.sin(a) * 14)),
                (sx + int(math.cos(a) * 32), wheel_y + int(math.sin(a) * 32)),
                3,
            )
        # Thân hình khổng lồ trắng ngà của Mahoraga
        pygame.draw.rect(screen, (230, 232, 240), (sx - 32, sy - 125, 64, 95), border_radius=12)
        pygame.draw.rect(screen, PURPLE, (sx - 32, sy - 125, 64, 95), 2, border_radius=12)
        pygame.draw.circle(screen, (240, 240, 248), (sx, sy - 132), 18)
        # Kiếm Diệt Tà gắn trên tay phải
        pygame.draw.line(screen, WHITE, (sx + f * 28, sy - 85), (sx + f * 85, sy - 45), 7)

    elif kind == "orochi":
        # Mãng Xà Orochi trồi lên từ bóng tối
        pygame.draw.ellipse(screen, (10, 12, 22), (sx - 42, GROUND_Y - 10, 84, 20))
        pygame.draw.rect(screen, (32, 48, 72), (sx - 20, GROUND_Y - 115, 40, 115), border_radius=12)
        pygame.draw.rect(screen, CYAN, (sx - 20, GROUND_Y - 115, 40, 115), 2, border_radius=12)
        pygame.draw.circle(screen, YELLOW, (sx - 8, GROUND_Y - 98), 4)
        pygame.draw.circle(screen, YELLOW, (sx + 8, GROUND_Y - 98), 4)

    elif kind == "rika":
        # Nữ Hoàng Nguyền Rủa Rika hiện thân tấn công
        pygame.draw.circle(screen, (35, 18, 52), (sx, sy - 75), 42)
        pygame.draw.circle(screen, PINK, (sx, sy - 75), 42, 3)
        pygame.draw.circle(screen, WHITE, (sx + f * 12, sy - 78), 10)
        pygame.draw.circle(screen, CRIMSON, (sx + f * 12, sy - 78), 5)
        # Cánh tay khổng lồ vung ra phía trước
        pygame.draw.line(screen, (55, 28, 78), (sx, sy - 65), (sx + f * 58, sy - 50), 14)

    else:
        pygame.draw.circle(screen, shiki.color, (sx, sy - 45), 24)
        pygame.draw.circle(screen, WHITE, (sx, sy - 45), 24, 2)
