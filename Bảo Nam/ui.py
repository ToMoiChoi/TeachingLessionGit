"""Giao diện người dùng (UI) Chú Thuật Hồi Chiến: Menu, Chọn 8 Chú Thuật Sư, Bản Đồ, Kho Chú Cụ, Sổ Tay & HUD."""

import pygame
from config import (
    WIDTH, HEIGHT, WHITE, BLACK, DARK, DARK_CARD, GRAY, MUTED,
    RED, CRIMSON, GREEN, RCT_GREEN, BLUE, LAPSE_BLUE, REVERSAL_RED,
    HOLLOW_PURPLE, CYAN, YELLOW, GOLD, PURPLE, PINK, ORANGE,
    FONT_TITLE, FONT_BIG, FONT_MED, FONT, FONT_SMALL, FONT_TINY,
    draw_text, draw_bar, wrap_text
)


def _draw_button(screen, rect, label, border_color, bg_color=(28, 36, 56), text_color=WHITE, font=FONT_SMALL):
    pygame.draw.rect(screen, bg_color, rect, border_radius=9)
    pygame.draw.rect(screen, border_color, rect, 2, border_radius=9)
    draw_text(screen, label, rect.centerx, rect.centery, text_color, font, center=True)


# ============================================================
# 1. MÀN HÌNH MENU CHÍNH
# ============================================================

def draw_menu(screen, game, lv_data, current_map, cls):
    game.draw_background()
    game.ui_buttons = []

    # Lớp phủ mờ giúp chữ nổi bật tuyệt đối
    overlay = game.dim_surface
    overlay.fill((6, 9, 18, 135))
    screen.blit(overlay, (0, 0))

    draw_text(screen, "CHÚ THUẬT HỒI CHIẾN: ĐẠI CHIẾN CHÚ THUẬT", WIDTH // 2, 34, GOLD, FONT_TITLE, center=True, shadow=True)
    draw_text(
        screen,
        f"Chiến trường: {current_map['name']}   |   {lv_data['name']}",
        WIDTH // 2, 74, CYAN, FONT_MED, center=True, shadow=True
    )

    # --- Thẻ Chú Thuật Sư (Bên trái) ---
    p_card = pygame.Rect(55, 105, 475, 315)
    pygame.draw.rect(screen, DARK_CARD, p_card, border_radius=14)
    pygame.draw.rect(screen, cls["color"], p_card, 2, border_radius=14)

    draw_text(screen, "CHÚ THUẬT SƯ CỦA BẠN", p_card.x + 22, p_card.y + 16, MUTED, FONT_TINY)
    draw_text(screen, cls["name"], p_card.x + 22, p_card.y + 36, cls["color"], FONT_BIG)
    draw_text(screen, f"Thuật thức: {cls['technique']}", p_card.x + 22, p_card.y + 72, WHITE, FONT_MED)

    bonus_hp = (game.armor_level - 1) * 150
    draw_text(
        screen,
        f"HP: {cls['hp'] + bonus_hp}   |   Tốc độ: {cls['speed']}   |   Chú Lực: {cls['max_ce']}",
        p_card.x + 22, p_card.y + 104, GREEN, FONT_SMALL
    )

    draw_text(screen, f"[E] Thể thuật/Chú cụ: {cls['basic_name']} (Nổ Hắc Thiểm!)", p_card.x + 22, p_card.y + 136, WHITE, FONT_SMALL)
    draw_text(screen, f"[Y] Chiêu 1: {cls['skill1_name']}", p_card.x + 22, p_card.y + 162, CYAN, FONT_SMALL)
    draw_text(screen, f"[C] Tuyệt kỹ: {cls['skill2_name']}", p_card.x + 22, p_card.y + 188, PINK, FONT_SMALL)
    draw_text(screen, f"[F] Hỗ trợ: {cls['shiki_name']}", p_card.x + 22, p_card.y + 214, YELLOW, FONT_SMALL)
    draw_text(screen, f"[R] Lãnh Địa: {cls['domain_name']}", p_card.x + 22, p_card.y + 240, GOLD, FONT_MED)
    draw_text(screen, f"Nội tại: {cls['passive']}", p_card.x + 22, p_card.y + 276, GRAY, FONT_TINY)

    # --- Thẻ Đặc Cấp Đối Thủ (Bên phải) ---
    b_card = pygame.Rect(570, 105, 475, 315)
    pygame.draw.rect(screen, DARK_CARD, b_card, border_radius=14)
    pygame.draw.rect(screen, lv_data["boss_color"], b_card, 2, border_radius=14)

    draw_text(screen, f"ĐỐI THỦ MÀN {lv_data['id']}/{len(game.levels)}", b_card.x + 22, b_card.y + 16, MUTED, FONT_TINY)
    draw_text(screen, lv_data["boss_name"], b_card.x + 22, b_card.y + 36, lv_data["boss_color"], FONT_BIG)
    draw_text(screen, f"Thuật thức: {lv_data['boss_tech']}", b_card.x + 22, b_card.y + 72, WHITE, FONT_MED)
    draw_text(screen, f"HP Đối Thủ: {lv_data['boss_hp']}   |   Thưởng: +{lv_data['reward_gold']} Điểm", b_card.x + 22, b_card.y + 104, RED, FONT_SMALL)
    draw_text(screen, f"Lãnh Địa Boss: {lv_data['boss_domain']}", b_card.x + 22, b_card.y + 136, PURPLE, FONT_MED)

    desc_lines = wrap_text(lv_data["description"], FONT_SMALL, 430)
    for idx, line in enumerate(desc_lines[:3]):
        draw_text(screen, line, b_card.x + 22, b_card.y + 174 + idx * 22, GRAY, FONT_SMALL)

    draw_text(
        screen,
        "Mẹo: Nhấn [Z] mở Giản Dị Lãnh Địa để chặn đòn Trúng Đích Tuyệt Đối khi Boss mở Lãnh Địa!",
        b_card.x + 22, b_card.y + 252, CYAN, FONT_TINY
    )
    draw_text(
        screen,
        f"Chú Cụ: Du Vân Cấp {game.weapon_level} | Thiên Nghịch Mâu Cấp {game.crit_level} | Chú Giáp Cấp {game.armor_level}",
        b_card.x + 22, b_card.y + 278, GOLD, FONT_TINY
    )

    # --- Điểm Chú Thuật (Vàng) ---
    gold_rect = pygame.Rect(WIDTH // 2 - 155, 436, 310, 38)
    pygame.draw.rect(screen, (38, 32, 14), gold_rect, border_radius=10)
    pygame.draw.rect(screen, GOLD, gold_rect, 2, border_radius=10)
    draw_text(screen, f"Điểm Chú Thuật: {game.gold} P", gold_rect.centerx, gold_rect.centery, YELLOW, FONT_MED, center=True)

    # --- Hàng Nút Bấm Tương Tác ---
    start_btn = pygame.Rect(WIDTH // 2 - 175, 488, 350, 48)
    _draw_button(screen, start_btn, "[ENTER] KHAI CHIẾN NGAY!", GOLD, (58, 24, 38), WHITE, FONT_BIG)
    game.ui_buttons.append((start_btn, "START"))

    nav_specs = [
        ("[C] 8 Chú Thuật Sư", "CHAR_SELECT", LAPSE_BLUE),
        ("[M] Đổi Bản Đồ", "MAP_SELECT", CYAN),
        ("[L] Đổi Màn Boss", "NEXT_LEVEL", REVERSAL_RED),
        ("[S] Kho Chú Cụ", "SHOP", GOLD),
        ("[H] Sổ Tay JJK", "GUIDE", PURPLE),
    ]
    btn_w = 186
    gap = 14
    total_w = len(nav_specs) * btn_w + (len(nav_specs) - 1) * gap
    sx = (WIDTH - total_w) // 2
    for i, (label, act, col) in enumerate(nav_specs):
        r = pygame.Rect(sx + i * (btn_w + gap), 554, btn_w, 42)
        _draw_button(screen, r, label, col)
        game.ui_buttons.append((r, act))

    draw_text(
        screen,
        "Điều khiển trong trận: A/D Di chuyển | W Nhảy | E Đánh/Hắc Thiểm | Y Chiêu 1 | C Tuyệt Kỹ | F Thức Thần | Z Giản Dị LĐ | X Nghịch Chuyển | R Lãnh Địa",
        WIDTH // 2, 622, GRAY, FONT_TINY, center=True
    )


# ============================================================
# 2. MÀN HÌNH CHỌN 8 CHÚ THUẬT SƯ (LƯỚI 4x2)
# ============================================================

def draw_character_select(screen, game, characters):
    game.draw_background()
    game.ui_buttons = []

    overlay = game.dim_surface
    overlay.fill((6, 9, 18, 175))
    screen.blit(overlay, (0, 0))

    draw_text(screen, "CHỌN CHÚ THUẬT SƯ & THUẬT THỨC (1 - 8)", WIDTH // 2, 30, GOLD, FONT_TITLE, center=True, shadow=True)
    draw_text(screen, "Bấm phím [1] - [8] hoặc Click chuột vào thẻ nhân vật | [ENTER] Xác nhận | [ESC] Quay lại", WIDTH // 2, 64, GRAY, FONT_SMALL, center=True)

    card_w = 242
    card_h = 168
    gap_x = 18
    gap_y = 14
    start_x = (WIDTH - (4 * card_w + 3 * gap_x)) // 2
    start_y = 88

    for i, c in enumerate(characters):
        col_idx = i % 4
        row_idx = i // 4
        x = start_x + col_idx * (card_w + gap_x)
        y = start_y + row_idx * (card_h + gap_y)
        rect = pygame.Rect(x, y, card_w, card_h)

        selected = (i == game.selected_class_index)
        bg = (38, 44, 68) if selected else DARK_CARD
        border = GOLD if selected else c["color"]

        pygame.draw.rect(screen, bg, rect, border_radius=12)
        pygame.draw.rect(screen, border, rect, 3 if selected else 2, border_radius=12)

        draw_text(screen, f"[{i + 1}] {c['name']}", x + 12, y + 10, c["color"], FONT_MED)
        draw_text(screen, c["technique"], x + 12, y + 36, WHITE, FONT_SMALL)
        draw_text(screen, f"HP: {c['hp']} | Tốc: {c['speed']} | CL: {c['max_ce']}", x + 12, y + 60, GREEN, FONT_TINY)
        draw_text(screen, f"[Y] {c['skill1_name']}", x + 12, y + 84, CYAN, FONT_TINY)
        draw_text(screen, f"[C] {c['skill2_name']}", x + 12, y + 104, PINK, FONT_TINY)
        draw_text(screen, f"[R] {c['domain_name']}", x + 12, y + 124, GOLD, FONT_TINY)

        if selected:
            draw_text(screen, "ĐANG CHỌN", x + card_w - 12, y + 146, YELLOW, FONT_TINY, right=True)

        game.ui_buttons.append((rect, f"PICK_CHAR_{i}"))

    # Khung chi tiết thuật thức của nhân vật đang chọn ở bên dưới
    sel = characters[game.selected_class_index]
    info_rect = pygame.Rect(start_x, 452, 4 * card_w + 3 * gap_x, 132)
    pygame.draw.rect(screen, (18, 24, 40), info_rect, border_radius=12)
    pygame.draw.rect(screen, sel["color"], info_rect, 2, border_radius=12)

    draw_text(screen, f"{sel['name']}  —  {sel['technique']}", info_rect.x + 18, info_rect.y + 12, sel["color"], FONT_BIG)
    draw_text(screen, f"Nội tại: {sel['passive']}", info_rect.right - 18, info_rect.y + 18, YELLOW, FONT_SMALL, right=True)
    draw_text(screen, f"Chiêu [Y] {sel['skill1_name']}: {sel['skill1_desc']}", info_rect.x + 18, info_rect.y + 48, CYAN, FONT_SMALL)
    draw_text(screen, f"Tuyệt kỹ [C] {sel['skill2_name']}: {sel['skill2_desc']}", info_rect.x + 18, info_rect.y + 74, PINK, FONT_SMALL)
    draw_text(screen, f"Bành Trướng Lãnh Địa [R] {sel['domain_name']}: {sel['domain_effect']}", info_rect.x + 18, info_rect.y + 100, GOLD, FONT_SMALL)

    ok_btn = pygame.Rect(WIDTH // 2 - 140, 596, 280, 40)
    _draw_button(screen, ok_btn, "[ENTER / ESC] XÁC NHẬN & VỀ MENU", GOLD, (45, 36, 18), WHITE, FONT_MED)
    game.ui_buttons.append((ok_btn, "BACK_MENU"))


# ============================================================
# 3. MÀN HÌNH CHỌN BẢN ĐỒ
# ============================================================

def draw_map_select(screen, game, maps):
    game.draw_background()
    game.ui_buttons = []

    overlay = game.dim_surface
    overlay.fill((6, 9, 18, 165))
    screen.blit(overlay, (0, 0))

    draw_text(screen, "CHỌN CHIẾN TRƯỜNG KẾT GIỚI", WIDTH // 2, 55, GOLD, FONT_TITLE, center=True, shadow=True)
    draw_text(screen, "Nhấn phím [1], [2], [3] hoặc Click chuột vào bản đồ | [ESC] Quay lại", WIDTH // 2, 100, GRAY, FONT_MED, center=True)

    card_w = 310
    start_x = (WIDTH - (3 * card_w + 2 * 35)) // 2
    for i, m in enumerate(maps):
        x = start_x + i * (card_w + 35)
        y = 155
        rect = pygame.Rect(x, y, card_w, 320)
        is_sel = (i == game.selected_map_index)
        pygame.draw.rect(screen, (36, 42, 62) if is_sel else DARK_CARD, rect, border_radius=15)
        pygame.draw.rect(screen, GOLD if is_sel else m["accent"], rect, 3 if is_sel else 2, border_radius=15)

        # Khung xem trước màu bầu trời bản đồ
        prev = pygame.Rect(x + 20, y + 20, card_w - 40, 95)
        pygame.draw.rect(screen, m["bg_bottom"], prev, border_radius=8)
        pygame.draw.rect(screen, m["accent"], prev, 2, border_radius=8)
        pygame.draw.circle(screen, m["accent"], (prev.right - 35, prev.y + 30), 16)

        draw_text(screen, f"[{i + 1}] {m['name']}", x + 20, y + 135, m["accent"], FONT_MED)
        lines = wrap_text(m["subtitle"], FONT_SMALL, card_w - 40)
        for li, line in enumerate(lines):
            draw_text(screen, line, x + 20, y + 172 + li * 22, WHITE, FONT_SMALL)

        if is_sel:
            draw_text(screen, "ĐANG CHỌN", rect.centerx, y + 275, GOLD, FONT_MED, center=True)

        game.ui_buttons.append((rect, f"PICK_MAP_{i}"))

    back_btn = pygame.Rect(WIDTH // 2 - 120, 525, 240, 44)
    _draw_button(screen, back_btn, "[ESC] Quay lại Menu", CYAN)
    game.ui_buttons.append((back_btn, "BACK_MENU"))


# ============================================================
# 4. KHO VŨ KHÍ CHÚ CỤ ĐẶC CẤP (SHOP)
# ============================================================

def draw_shop(screen, game, shop_items):
    game.draw_background()
    game.ui_buttons = []

    overlay = game.dim_surface
    overlay.fill((6, 9, 18, 175))
    screen.blit(overlay, (0, 0))

    draw_text(screen, "KHO CHÚ CỤ ĐẶC CẤP CAO CHUYÊN", WIDTH // 2, 42, GOLD, FONT_TITLE, center=True, shadow=True)
    draw_text(screen, f"Điểm Chú Thuật hiện có: {game.gold} P", WIDTH // 2, 84, YELLOW, FONT_BIG, center=True)

    levels_map = {
        "weapon": game.weapon_level,
        "crit": game.crit_level,
        "armor": game.armor_level,
        "ce": game.ce_level,
    }

    card_w = 238
    gap = 20
    sx = (WIDTH - (4 * card_w + 3 * gap)) // 2

    for i, item in enumerate(shop_items):
        x = sx + i * (card_w + gap)
        y = 128
        rect = pygame.Rect(x, y, card_w, 365)
        cur_lv = levels_map[item["key"]]
        cost = item["cost"] + (cur_lv - 1) * 400

        pygame.draw.rect(screen, DARK_CARD, rect, border_radius=14)
        pygame.draw.rect(screen, item["color"], rect, 2, border_radius=14)

        draw_text(screen, f"[{i + 1}] {item['name']}", x + 16, y + 18, item["color"], FONT_MED)
        draw_text(screen, f"Cấp hiện tại: Lv.{cur_lv}", x + 16, y + 50, WHITE, FONT_MED)

        sub_lines = wrap_text(item["subtitle"], FONT_TINY, card_w - 32)
        for li, ln in enumerate(sub_lines[:2]):
            draw_text(screen, ln, x + 16, y + 84 + li * 18, GRAY, FONT_TINY)

        eff_lines = wrap_text(item["effect"], FONT_SMALL, card_w - 32)
        for li, ln in enumerate(eff_lines[:4]):
            draw_text(screen, ln, x + 16, y + 138 + li * 22, GREEN, FONT_SMALL)

        draw_text(screen, f"Giá nâng cấp: {cost} P", x + 16, y + 262, YELLOW, FONT_MED)

        buy_btn = pygame.Rect(x + 18, y + 304, card_w - 36, 42)
        _draw_button(screen, buy_btn, f"[{i + 1}] Cường Hóa", item["color"], (32, 42, 64), WHITE, FONT_MED)
        game.ui_buttons.append((buy_btn, f"BUY_{item['key']}"))

    if game.message:
        draw_text(screen, game.message, WIDTH // 2, 525, CYAN, FONT_MED, center=True)

    back_btn = pygame.Rect(WIDTH // 2 - 130, 565, 260, 44)
    _draw_button(screen, back_btn, "[ESC] Quay lại Menu", GRAY)
    game.ui_buttons.append((back_btn, "BACK_MENU"))


# ============================================================
# 5. SỔ TAY THUẬT THỨC & CƠ CHẾ CHÚ THUẬT HỒI CHIẾN
# ============================================================

def draw_guide(screen, game):
    game.draw_background()
    game.ui_buttons = []

    overlay = game.dim_surface
    overlay.fill((6, 9, 18, 205))
    screen.blit(overlay, (0, 0))

    draw_text(screen, "SỔ TAY THUẬT THỨC & CƠ CHẾ CHIẾN ĐẤU JJK", WIDTH // 2, 34, GOLD, FONT_TITLE, center=True)

    # Cột trái: 8 Nhóm thuật thức gia truyền & nổi bật
    left_box = pygame.Rect(40, 72, 500, 495)
    pygame.draw.rect(screen, DARK_CARD, left_box, border_radius=14)
    pygame.draw.rect(screen, LAPSE_BLUE, left_box, 2, border_radius=14)
    draw_text(screen, "1. NHÓM THUẬT THỨC GIA TRUYỀN & NỔI BẬT", left_box.x + 18, left_box.y + 14, CYAN, FONT_MED)

    clan_notes = [
        ("Gojo Satoru - Vô Hạ Hạn:", "Xanh (hút), Đỏ (đẩy nổ), Hư Thức Tím & Vô Lượng Không Xử."),
        ("Ryomen Sukuna - Ngự Trù Tử:", "Trảm kích Phân/Bổ, Thần Hỏa Fuga & Phục Ma Ngự Trù Tử."),
        ("Megumi - Thập Chủng Ảnh:", "Triệu hồi Ngọc Khuyển, Nue, Mãng Xà, Mahoraga từ bóng tối."),
        ("Yuta Okkotsu - Sao Chép:", "Chú lực khổng lồ, sao chép thuật thức & Thuần Ái Pháo Rika."),
        ("Inumaki Toge - Chú Ngôn:", "Lời nói mang chú lực: 'Đứng Im!' khóa cứng, 'Nổ Tung!' phá hủy."),
        ("Kamo - Xích Huyết Thao Thuật:", "Xích Lân tăng tốc, tia Xuyên Huyết siêu thanh & Siêu Tân Tinh."),
        ("Nobara - Sô Linh Chú Pháp:", "Búa đóng đinh chú lực, kích nổ Trâm & Cộng Hưởng Búp Bê Rơm."),
        ("Nanami - Thập Vạch (7:3):", "Tạo điểm yếu vạch 7/3 chí mạng & Khế ước Tăng Ca nổ Hắc Thiểm."),
    ]
    for idx, (title, body) in enumerate(clan_notes):
        yy = left_box.y + 50 + idx * 54
        draw_text(screen, title, left_box.x + 18, yy, GOLD, FONT_SMALL)
        draw_text(screen, body, left_box.x + 18, yy + 20, WHITE, FONT_TINY)

    # Cột phải: 5 Kỹ năng & cơ chế chiến đấu chung
    right_box = pygame.Rect(560, 72, 500, 495)
    pygame.draw.rect(screen, DARK_CARD, right_box, border_radius=14)
    pygame.draw.rect(screen, HOLLOW_PURPLE, right_box, 2, border_radius=14)
    draw_text(screen, "2. KỸ NĂNG & CƠ CHẾ CHIẾN ĐẤU CHUNG", right_box.x + 18, right_box.y + 14, PINK, FONT_MED)

    mech_notes = [
        (
            "Hắc Thiểm (Black Flash) - Phím [E]:",
            "Đòn vật lý bọc chú lực bùng nổ tia sét Đen-Đỏ, gây x2.5 sát thương, hồi Chú Lực và vào trạng thái Zone 120% tiềm năng!"
        ),
        (
            "Nghịch Chuyển Thuật Thức (RCT) - Phím [X]:",
            "Nhân đôi chú lực âm tạo năng lượng dương trắng-lục giúp chữa lành vết thương nhanh chóng và hóa giải choáng."
        ),
        (
            "Bành Trướng Lãnh Địa (Domain Expansion) - Phím [R]:",
            "Khi thanh Lãnh Địa đạt 100%, mở không gian thuật thức riêng giúp đòn đánh Trúng Đích Tuyệt Đối (Sure-Hit)!"
        ),
        (
            "Giản Dị Lãnh Địa (Simple Domain) - Phím [Z]:",
            "Rào chắn Tân Âm Lưu dưới chân: Phản đòn (Parry) đầu chiêu, giảm mạnh sát thương & VÔ HIỆU HÓA Trúng Đích Tuyệt Đối!"
        ),
        (
            "Thức Thần & Chú Cụ - Phím [F] & Shop [S]:",
            "Triệu hồi Thức Thần hỗ trợ chiến đấu [F] và cường hóa Chú Cụ Đặc Cấp (Du Vân, Thiên Nghịch Mâu) trong Kho Chú Cụ."
        ),
    ]
    cy = right_box.y + 52
    for title, body in mech_notes:
        draw_text(screen, title, right_box.x + 18, cy, YELLOW, FONT_SMALL)
        wrapped = wrap_text(body, FONT_TINY, 464)
        for li, ln in enumerate(wrapped):
            draw_text(screen, ln, right_box.x + 18, cy + 22 + li * 17, WHITE, FONT_TINY)
        cy += 88

    back_btn = pygame.Rect(WIDTH // 2 - 140, 584, 280, 44)
    _draw_button(screen, back_btn, "[ESC / H] Đóng Sổ Tay", GOLD)
    game.ui_buttons.append((back_btn, "CLOSE_GUIDE"))


# ============================================================
# 6. HUD TRONG TRẬN ĐẤU & THANH KỸ NĂNG COOLDOWN
# ============================================================

def draw_hud(screen, game, lv_data, current_accent):
    p = game.player
    e = game.enemy
    cls = game.characters[game.selected_class_index]

    # --- Khung Người Chơi (Góc trái trên) ---
    pygame.draw.rect(screen, DARK_CARD, (18, 14, 370, 114), border_radius=12)
    pygame.draw.rect(screen, p.color, (18, 14, 370, 114), 2, border_radius=12)

    draw_text(screen, f"{p.name} ({cls['technique']})", 30, 20, p.color, FONT_SMALL)
    draw_bar(screen, 30, 43, 245, 14, p.hp, p.max_hp, GREEN, border_color=(65, 80, 95))
    draw_text(screen, f"HP {int(p.hp)}/{int(p.max_hp)}", 283, 41, WHITE, FONT_TINY)

    draw_bar(screen, 30, 63, 245, 11, p.ce, p.max_ce, CYAN, border_color=(65, 80, 95))
    draw_text(screen, f"Chú Lực {int(p.ce)}", 283, 60, CYAN, FONT_TINY)

    dom_col = GOLD if p.domain_gauge >= 100 else HOLLOW_PURPLE
    draw_bar(screen, 30, 80, 245, 11, p.domain_gauge, 100, dom_col, border_color=(65, 80, 95))
    dom_txt = "SẴN SÀNG [R]!" if p.domain_gauge >= 100 else f"Lãnh Địa {int(p.domain_gauge)}%"
    draw_text(screen, dom_txt, 283, 77, dom_col, FONT_TINY)

    # Dòng trạng thái Buff
    status_parts = [f"RCT [X]: {p.rct_uses}"]
    if p.zone_timer > 0:
        status_parts.append(f"HẮC THIỂM 120% ({p.zone_timer:.1f}s)")
    if p.overtime_timer > 0:
        status_parts.append(f"TĂNG CA ({p.overtime_timer:.1f}s)")
    if p.simple_domain_timer > 0:
        status_parts.append(f"GIẢN DỊ LĐ ({p.simple_domain_timer:.1f}s)")
    if p.blue_combo_timer > 0 and p.char_id == "gojo":
        status_parts.append("CỘNG HƯỞNG TÍM!")
    draw_text(screen, " | ".join(status_parts[:3]), 30, 100, YELLOW, FONT_TINY)

    # --- Khung Boss (Góc phải trên) ---
    pygame.draw.rect(screen, DARK_CARD, (WIDTH - 388, 14, 370, 114), border_radius=12)
    pygame.draw.rect(screen, lv_data["boss_color"], (WIDTH - 388, 14, 370, 114), 2, border_radius=12)

    draw_text(screen, lv_data["boss_name"], WIDTH - 376, 20, lv_data["boss_color"], FONT_SMALL)
    draw_bar(screen, WIDTH - 376, 43, 245, 14, e.hp, e.max_hp, RED, border_color=(85, 65, 75))
    draw_text(screen, f"{int(e.hp)}/{int(e.max_hp)}", WIDTH - 122, 41, WHITE, FONT_TINY)

    draw_bar(screen, WIDTH - 376, 63, 245, 11, e.ce, e.max_ce, ORANGE, border_color=(85, 65, 75))
    draw_text(screen, f"CL {int(e.ce)}", WIDTH - 122, 60, ORANGE, FONT_TINY)

    draw_bar(screen, WIDTH - 376, 80, 245, 11, e.domain_gauge, 100, PURPLE, border_color=(85, 65, 75))
    draw_text(screen, f"LĐ {int(e.domain_gauge)}%", WIDTH - 122, 77, PURPLE, FONT_TINY)

    boss_tags = [f"RCT Boss: {e.rct_uses}"]
    if e.nail_stacks > 0:
        boss_tags.append(f"Đinh Sô Linh: {e.nail_stacks}/6")
    if e.simple_domain_timer > 0:
        boss_tags.append("Giản Dị LĐ")
    draw_text(screen, " | ".join(boss_tags), WIDTH - 376, 100, GRAY, FONT_TINY)

    # --- Khu vực Trung Tâm Trên Cùng & Thông Báo Bành Trướng Lãnh Địa ---
    draw_text(screen, lv_data["name"], WIDTH // 2, 24, current_accent, FONT_MED, center=True, shadow=True)
    draw_text(screen, f"Điểm Chú Thuật: {game.gold} P  |  [H] Sổ Tay  |  [ESC] Menu", WIDTH // 2, 48, GRAY, FONT_TINY, center=True)

    dom = game.domain_state
    if dom["active"]:
        banner = pygame.Rect(WIDTH // 2 - 215, 134, 430, 36)
        b_col = GOLD if dom["clash"] else (p.color if dom["owner"] is p else lv_data["boss_color"])
        pygame.draw.rect(screen, (15, 12, 28), banner, border_radius=10)
        pygame.draw.rect(screen, b_col, banner, 2, border_radius=10)
        title_str = "GIẰNG CO LÃNH ĐỊA!" if dom["clash"] else f"LÃNH ĐỊA: {dom['name'].upper()}"
        draw_text(screen, f"{title_str} ({dom['timer']:.1f}s)", banner.centerx, banner.centery, WHITE, FONT_MED, center=True)

    # --- Thanh Kỹ Năng & Cooldown Dưới Đáy Màn Hình ---
    gojo_y_label = "Đỏ (Reversal)" if (p.char_id == "gojo" and p.gojo_red_next) else cls["skill1_name"]
    slots = [
        ("E", "Hắc Thiểm/Đánh", p.light_cd, WHITE),
        ("Y", gojo_y_label[:20], p.skill1_cd, CYAN),
        ("C", cls["skill2_name"][:20], p.skill2_cd, PINK),
        ("F", cls["shiki_name"][:20], p.shiki_cd, YELLOW),
        ("Z", "Giản Dị Lãnh Địa", p.simple_cd, LAPSE_BLUE),
        ("X", f"Nghịch Chuyển ({p.rct_uses})", 0.0 if p.rct_uses > 0 else 9.9, RCT_GREEN),
        ("R", "Bành Trướng LĐ", 0.0 if p.domain_gauge >= 100 else -1.0, GOLD),
    ]

    slot_w = 142
    gap = 8
    total_w = len(slots) * slot_w + (len(slots) - 1) * gap
    sx = (WIDTH - total_w) // 2
    sy = HEIGHT - 58

    for i, (key_lbl, name_lbl, cd_val, col) in enumerate(slots):
        rx = sx + i * (slot_w + gap)
        box = pygame.Rect(rx, sy, slot_w, 48)
        ready = (cd_val == 0.0)
        bg = (22, 28, 46) if ready else (14, 16, 26)
        b_col = col if ready else (55, 62, 80)

        pygame.draw.rect(screen, bg, box, border_radius=8)
        pygame.draw.rect(screen, b_col, box, 2 if ready else 1, border_radius=8)

        draw_text(screen, f"[{key_lbl}]", rx + 8, sy + 6, col if ready else GRAY, FONT_TINY)
        if cd_val > 0 and cd_val < 9.0:
            draw_text(screen, f"{cd_val:.1f}s", rx + slot_w - 8, sy + 6, RED, FONT_TINY, right=True)
        elif cd_val == -1.0:
            draw_text(screen, f"{int(p.domain_gauge)}%", rx + slot_w - 8, sy + 6, PURPLE, FONT_TINY, right=True)
        elif ready:
            draw_text(screen, "OK", rx + slot_w - 8, sy + 6, GREEN, FONT_TINY, right=True)

        draw_text(screen, name_lbl, rx + 8, sy + 26, WHITE if ready else MUTED, FONT_TINY)


# ============================================================
# 7. MÀN HÌNH KẾT THÚC TRẬN ĐẤU
# ============================================================

def draw_gameover(screen, game):
    game.ui_buttons = []
    overlay = game.dim_surface
    overlay.fill((5, 8, 16, 195))
    screen.blit(overlay, (0, 0))

    title = "THANH TẨY HOÀN TẤT - CHIẾN THẮNG!" if game.winner else "BẠI TRẬN TRƯỚC LỜI NGUYỀN!"
    color = GOLD if game.winner else REVERSAL_RED

    card = pygame.Rect(WIDTH // 2 - 290, 155, 580, 340)
    pygame.draw.rect(screen, DARK_CARD, card, border_radius=16)
    pygame.draw.rect(screen, color, card, 3, border_radius=16)

    draw_text(screen, title, WIDTH // 2, 205, color, FONT_BIG, center=True, shadow=True)
    draw_text(screen, game.message, WIDTH // 2, 255, WHITE, FONT_BIG, center=True)

    draw_text(
        screen,
        f"Hắc Thiểm đã nổ: {game.match_black_flashes} lần   |   Bành Trướng Lãnh Địa: {game.match_domains} lần",
        WIDTH // 2, 305, CYAN, FONT_SMALL, center=True
    )
    draw_text(screen, f"Tổng Điểm Chú Thuật hiện có: {game.gold} P", WIDTH // 2, 345, YELLOW, FONT_MED, center=True)

    btn_menu = pygame.Rect(WIDTH // 2 - 145, 405, 290, 48)
    _draw_button(screen, btn_menu, "[ENTER / SPACE] Tiếp Tục", GOLD, (45, 36, 18), WHITE, FONT_MED)
    game.ui_buttons.append((btn_menu, "BACK_MENU"))
