import pygame
from config import WIDTH, HEIGHT, WHITE, RED, GREEN, YELLOW, CYAN, GRAY, DARK, FONT_TITLE, FONT_BIG, FONT_MED, FONT, FONT_SMALL, draw_text, draw_bar

def draw_menu(screen, game, lv_data, current_map, cls):
    # Vẽ nền
    game.draw_background()
    
    # Tiêu đề game
    draw_text(screen, "BLADE MASTER", WIDTH // 2 + 3, 33, (200, 100, 0), FONT_TITLE, True)
    draw_text(screen, "BLADE MASTER", WIDTH // 2, 30, (255, 215, 0), FONT_TITLE, True)
    
    draw_text(screen, f"Bản đồ: {current_map['name']} | Màn: {lv_data['name']}", WIDTH // 2, 85, CYAN, FONT_MED, True)

    # Character card
    pygame.draw.rect(screen, DARK, (100, 135, 420, 270), border_radius=15)
    pygame.draw.rect(screen, cls["color"], (100, 135, 420, 270), 2, border_radius=15)
    draw_text(screen, f"NV: {cls['name']}", 130, 165, cls["color"], FONT_BIG)
    draw_text(screen, cls["title"], 130, 205, WHITE)
    draw_text(screen, f"HP: {cls['hp']} | Tốc độ: {cls['speed']}", 130, 245, GREEN)
    draw_text(screen, f"Sát thương cộng thêm: +50", 130, 285, (255, 100, 100), FONT_SMALL)
    draw_text(screen, cls["desc"], 130, 325, GRAY)

    # Boss card
    pygame.draw.rect(screen, DARK, (580, 135, 420, 270), border_radius=15)
    pygame.draw.rect(screen, lv_data["boss_color"], (580, 135, 420, 270), 2, border_radius=15)
    draw_text(screen, lv_data["boss_name"], 610, 165, lv_data["boss_color"], FONT_BIG)
    draw_text(screen, f"Thử thách: {lv_data['name']}", 610, 205, WHITE)
    draw_text(screen, f"HP Boss: {lv_data['boss_hp']} (+2000 HP)", 610, 245, RED)
    draw_text(screen, lv_data["description"], 610, 305, GRAY, FONT_SMALL)

    # Vàng
    gold_surf = FONT_MED.render(f"Vàng: {game.gold} G", True, (255, 235, 59))
    gold_rect = gold_surf.get_rect(center=(WIDTH // 2, 430))
    pygame.draw.rect(screen, (40, 35, 10), gold_rect.inflate(20, 10), border_radius=8)
    pygame.draw.rect(screen, (255, 193, 7), gold_rect.inflate(20, 10), 2, border_radius=8)
    screen.blit(gold_surf, gold_rect)

    draw_text(screen, "[ENTER] Bắt đầu trận đấu", WIDTH // 2, 480, WHITE, FONT_MED, True)
    draw_text(screen, "[C] Chọn NV    [M] Đổi Bản Đồ    [L] Đổi Màn    [S] Shop    [Q] Thoát", WIDTH // 2, 530, GRAY, FONT, True)

def draw_map_select(screen, game, maps):
    game.draw_background()
    draw_text(screen, "CHỌN BẢN ĐỒ CHIẾN ĐẤU", WIDTH // 2, 60, (255, 215, 0), FONT_TITLE, True)
    draw_text(screen, "Sử dụng phím [1], [2], [3] để chọn bản đồ, [ESC] để quay lại", WIDTH // 2, 120, GRAY, FONT_MED, True)

    card_width = 300
    start_x = 85
    for i, m in enumerate(maps):
        x = start_x + i * 330
        y = 180
        is_selected = (i == game.selected_map_index)
        border_color = (255, 215, 0) if is_selected else m["accent"]
        bg_color = (45, 45, 30) if is_selected else DARK

        pygame.draw.rect(screen, bg_color, (x, y, card_width, 280), border_radius=15)
        pygame.draw.rect(screen, border_color, (x, y, card_width, 280), 3 if is_selected else 2, border_radius=15)

        draw_text(screen, f"[{i+1}] Đấu Trường", x + 25, y + 25, m["accent"], FONT_BIG)
        draw_text(screen, m["name"], x + 25, y + 75, WHITE, FONT_MED)
        draw_text(screen, "Khu vực thi đấu chuyên nghiệp", x + 25, y + 140, GRAY, FONT_SMALL)

        if is_selected:
            draw_text(screen, "ĐANG CHỌN", x + card_width // 2, y + 220, (255, 215, 0), FONT_MED, True)

def draw_character_select(screen, game, player_classes):
    game.draw_background()
    draw_text(screen, "CHỌN NHÂN VẬT", WIDTH // 2, 60, (255, 215, 0), FONT_TITLE, True)
    draw_text(screen, "Sử dụng phím [1], [2], [3] để chọn nhân vật, [ESC] để quay lại", WIDTH // 2, 120, GRAY, FONT_MED, True)

    card_width = 300
    start_x = 85
    for i, cls in enumerate(player_classes):
        x = start_x + i * 330
        y = 180
        is_selected = (i == game.selected_class_index)
        border_color = (255, 215, 0) if is_selected else cls["color"]
        bg_color = (45, 45, 30) if is_selected else DARK

        pygame.draw.rect(screen, bg_color, (x, y, card_width, 320), border_radius=15)
        pygame.draw.rect(screen, border_color, (x, y, card_width, 3 if is_selected else 2), border_radius=15)

        draw_text(screen, f"[{i+1}] {cls['name']}", x + 25, y + 25, cls["color"], FONT_BIG)
        draw_text(screen, cls["title"], x + 25, y + 75, WHITE, FONT)
        draw_text(screen, f"HP Gốc: {cls['hp']}", x + 25, y + 130, GREEN)
        draw_text(screen, f"Tốc độ: {cls['speed']}", x + 25, y + 170, CYAN)
        draw_text(screen, cls["desc"], x + 25, y + 220, GRAY, FONT_SMALL)

        if is_selected:
            draw_text(screen, "ĐANG CHỌN", x + card_width // 2, y + 280, (255, 215, 0), FONT_MED, True)

def draw_shop(screen, game):
    game.draw_background()
    draw_text(screen, "CHỢ RÈN", WIDTH // 2, 50, (255, 215, 0), FONT_TITLE, True)
    
    gold_surf = FONT_MED.render(f"Vàng hiện có: {game.gold} G", True, (255, 235, 59))
    gold_rect = gold_surf.get_rect(center=(WIDTH // 2, 105))
    screen.blit(gold_surf, gold_rect)

    pygame.draw.rect(screen, DARK, (130, 160, 360, 320), border_radius=15)
    pygame.draw.rect(screen, (255, 193, 7), (130, 160, 360, 320), 2, border_radius=15)
    draw_text(screen, "KIẾM", 170, 195, (255, 215, 0), FONT_BIG)
    draw_text(screen, f"Cấp: {game.weapon_level}", 170, 250, WHITE)
    draw_text(screen, "+10 sát thương (+50 gốc)", 170, 290, GRAY)
    draw_text(screen, "+20 sát thương đòn nặng", 170, 320, GRAY)
    draw_text(screen, "Giá: 1000 vàng", 170, 380, (255, 235, 59))
    draw_text(screen, "[1] Nâng cấp", 170, 425, GREEN)

    pygame.draw.rect(screen, DARK, (610, 160, 360, 320), border_radius=15)
    pygame.draw.rect(screen, CYAN, (610, 160, 360, 320), 2, border_radius=15)
    draw_text(screen, "GIÁP", 650, 195, CYAN, FONT_BIG)
    draw_text(screen, f"Cấp: {game.armor_level}", 650, 250, WHITE)
    draw_text(screen, "-5% sát thương nhận", 650, 290, GRAY)
    draw_text(screen, "Giá: 1000 vàng", 650, 380, (255, 235, 59))
    draw_text(screen, "[2] Nâng cấp", 650, 425, GREEN)

    draw_text(screen, "[ESC] Quay lại", WIDTH // 2, 545, GRAY, FONT_MED, True)

def draw_hud(screen, game, lv_data, current_accent):
    pygame.draw.rect(screen, DARK, (20, 20, 360, 100), border_radius=10)
    pygame.draw.rect(screen, current_accent, (20, 20, 360, 100), 1, border_radius=10)
    draw_text(screen, game.player.name, 35, 30, game.player.color, FONT_MED)
    draw_bar(screen, 35, 60, 220, 15, game.player.hp, game.player.max_hp, GREEN)
    draw_text(screen, f"{int(game.player.hp)}/{game.player.max_hp}", 265, 58, WHITE, FONT_SMALL)
    draw_bar(screen, 35, 82, 220, 10, game.player.stamina, game.player.max_stamina, (255, 193, 7))

    pygame.draw.rect(screen, DARK, (WIDTH - 380, 20, 360, 100), border_radius=10)
    pygame.draw.rect(screen, RED, (WIDTH - 380, 20, 360, 100), 1, border_radius=10)
    draw_text(screen, lv_data["boss_name"], WIDTH - 365, 30, lv_data["boss_color"], FONT_MED)
    draw_bar(screen, WIDTH - 365, 60, 220, 15, game.enemy.hp, game.enemy.max_hp, RED)
    draw_text(screen, f"{int(game.enemy.hp)}/{game.enemy.max_hp}", WIDTH - 135, 58, WHITE, FONT_SMALL)
    draw_bar(screen, WIDTH - 365, 82, 220, 10, game.enemy.stamina, game.enemy.max_stamina, (255, 193, 7))

    draw_text(screen, lv_data["name"], WIDTH // 2, 30, current_accent, FONT_MED, True)
    draw_text(screen, f"Vàng: {game.gold} G", WIDTH // 2, 65, (255, 235, 59), FONT_SMALL, True)

    controls = "A/D: Di chuyển | W: Nhảy (2 lần) | S: Ngồi | E: Đánh nhẹ | Y: Nặng | Z: Parry | X: Né | C: Skill"
    pygame.draw.rect(screen, DARK, (110, HEIGHT - 50, WIDTH - 220, 35), border_radius=8)
    pygame.draw.rect(screen, current_accent, (110, HEIGHT - 50, WIDTH - 220, 35), 1, border_radius=8)
    draw_text(screen, controls, WIDTH // 2, HEIGHT - 32, WHITE, FONT_SMALL, True)

def draw_gameover(screen, game):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 190))
    screen.blit(overlay, (0, 0))

    title = "CHIẾN THẮNG!" if game.winner else "THẤT BẠI!"
    color = GREEN if game.winner else RED

    draw_text(screen, title, WIDTH // 2, 230, color, FONT_TITLE, True)
    draw_text(screen, game.message, WIDTH // 2, 300, WHITE, FONT_BIG, True)
    draw_text(screen, f"Vàng hiện tại: {game.gold} G", WIDTH // 2, 350, (255, 215, 0), FONT_MED, True)
    draw_text(screen, "[ENTER] Về Menu", WIDTH // 2, 420, WHITE, FONT_MED, True)