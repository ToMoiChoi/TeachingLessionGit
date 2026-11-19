import math
import random
import pygame
from font_vn import get_font
from config import CYBER_BLUE, CYBER_PINK, CYBER_YELLOW, DARK_BG, GREEN, RED, WHITE

ORANGE = (255, 140, 0)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width=120, height=15):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, screen, camera_x=0):
        render_rect = self.rect.move(-camera_x, 0)
        pygame.draw.rect(screen, (40, 50, 80), render_rect, border_radius=5)
        pygame.draw.rect(screen, CYBER_BLUE, render_rect, 2, border_radius=5)


class LayoutRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = get_font(18, bold=True)
        self.title_font = get_font(36, bold=True)

    def render(self, gameplay):
        if gameplay.current_level == 8 and gameplay.state in ["GAME", "LEVEL_CLEAR", "GAME_OVER"]:
            self.screen.fill((200, 10, 30))
        else:
            self.screen.fill(DARK_BG)

        if gameplay.state in ["GAME", "LEVEL_CLEAR", "GAME_OVER"]:
            cam_x = gameplay.camera_x

            pygame.draw.rect(self.screen, (40, 40, 60), (-cam_x, 380, gameplay.level_width, 200))
            pygame.draw.line(self.screen, CYBER_BLUE, (-cam_x, 380), (gameplay.level_width - cam_x, 380), 2)

            for plat in gameplay.platforms:
                plat.draw(self.screen, cam_x)

            for p in gameplay.powerups:
                ren_rect = p.rect.move(-cam_x, 0)
                if hasattr(p, 'draw'):
                    orig_rect = p.rect
                    p.rect = ren_rect
                    p.draw(self.screen)
                    p.rect = orig_rect

            for enemy in gameplay.enemies:
                if hasattr(enemy, 'draw'):
                    enemy.draw(self.screen, cam_x)
                else:
                    ren_rect = enemy.rect.move(-cam_x, 0)
                    if hasattr(enemy, 'image') and enemy.image:
                        self.screen.blit(enemy.image, ren_rect)
                    else:
                        pygame.draw.rect(self.screen, RED, ren_rect, border_radius=4)
                    hp_ratio = max(0, enemy.hp / getattr(enemy, 'max_hp', 50))
                    pygame.draw.rect(self.screen, RED, (ren_rect.x, ren_rect.top - 8, 35, 4))
                    pygame.draw.rect(self.screen, GREEN, (ren_rect.x, ren_rect.top - 8, int(35 * hp_ratio), 4))

            boss = gameplay.boss_group.sprite
            if boss:
                ren_rect = boss.rect.move(-cam_x, 0)
                if hasattr(boss, 'image') and boss.image:
                    self.screen.blit(boss.image, ren_rect)
                else:
                    boss_color = (255, 60, 0) if getattr(boss, 'phase', 1) == 2 else CYBER_PINK
                    pygame.draw.rect(self.screen, boss_color, ren_rect, border_radius=6)
                if hasattr(boss, 'draw_health_bar'):
                    boss.draw_health_bar(self.screen, gameplay.player)

            for b in gameplay.player_bullets:
                ren_rect = b.rect.move(-cam_x, 0)
                if hasattr(b, 'image') and b.image:
                    self.screen.blit(b.image, ren_rect)
                else:
                    pygame.draw.rect(self.screen, getattr(b, 'color', CYBER_YELLOW), ren_rect)

            for b in gameplay.enemy_bullets:
                ren_rect = b.rect.move(-cam_x, 0)
                if hasattr(b, 'image') and b.image:
                    self.screen.blit(b.image, ren_rect)
                else:
                    pygame.draw.rect(self.screen, RED, ren_rect)

            if gameplay.state != "GAME_OVER":   # đã nổ tung thì không vẽ nhân vật
                gameplay.player.draw(self.screen, cam_x)

            for pt in gameplay.particle_mgr.particles:
                if isinstance(pt, dict):
                    px, py = int(pt['x'] - cam_x), int(pt['y'])
                    col = pt.get('color', WHITE)
                    sz = int(pt.get('size', 3))
                elif isinstance(pt, (list, tuple)) and len(pt) >= 7:
                    px, py = int(pt[0] - cam_x), int(pt[1])
                    col = pt[6]
                    sz = int(pt[4])
                elif isinstance(pt, (list, tuple)):
                    px, py = int(pt[0] - cam_x), int(pt[1])
                    col = pt[2] if len(pt) > 2 and isinstance(pt[2], (tuple, list)) else WHITE
                    sz = int(pt[3]) if len(pt) > 3 and isinstance(pt[3], (int, float)) else 3
                elif hasattr(pt, 'x') and hasattr(pt, 'y'):
                    px, py = int(pt.x - cam_x), int(pt.y)
                    col = getattr(pt, 'color', WHITE)
                    sz = int(getattr(pt, 'size', 3))
                else:
                    continue
                pygame.draw.circle(self.screen, col, (px, py), max(1, sz))

            # UI BẢNG THÔNG TIN
            hp_txt = self.font.render(f"HP: {max(0, gameplay.player.hp)}/{gameplay.player.max_hp}", True, WHITE)
            ammo_txt = self.font.render(f"AMMO: {gameplay.current_weapon.ammo}/{gameplay.current_weapon.max_ammo}", True, ORANGE)
            gun_label = self.font.render("GUN [1,2,3]:", True, CYBER_YELLOW)
            coin_txt = self.font.render(f"Coins: {gameplay.coins}", True, CYBER_YELLOW)
            disp_lvl = gameplay.current_level - 1 if gameplay.state == 'LEVEL_CLEAR' else gameplay.current_level
            lvl_txt = self.font.render(f"Level: {disp_lvl}", True, CYBER_BLUE)

            self.screen.blit(hp_txt, (10, 10))
            self.screen.blit(ammo_txt, (10, 32))
            self.screen.blit(gun_label, (10, 54))

            # HIỂN THỊ HÌNH ẢNH SÚNG TRỰC TIẾP
            gun_obj = gameplay.current_weapon
            gun_img = getattr(gun_obj, 'image', getattr(gun_obj, 'surface', None))
            if gun_img:
                gun_icon = pygame.transform.scale(gun_img, (40, 20))
                self.screen.blit(gun_icon, (125, 52))
            else:
                gun_name_txt = self.font.render(gun_obj.name, True, CYBER_YELLOW)
                self.screen.blit(gun_name_txt, (125, 54))

            self.screen.blit(coin_txt, (10, 76))
            self.screen.blit(lvl_txt, (10, 98))

            pygame.draw.rect(self.screen, (30, 30, 50), (10, 124, 100, 12), border_radius=3)
            slash_ratio = 1 - (gameplay.player.slash_cooldown / gameplay.player.slash_delay)
            pygame.draw.rect(self.screen, CYBER_BLUE, (10, 124, int(100 * max(0, slash_ratio)), 12), border_radius=3)
            self.screen.blit(self.font.render("SWORD", True, WHITE), (115, 120))

            buff_y = 10
            for buff in gameplay.active_buffs:
                box_rect = pygame.Rect(620, buff_y, 170, 30)
                bg_surf = pygame.Surface((170, 30), pygame.SRCALPHA)
                bg_surf.fill((20, 20, 35, 210))
                self.screen.blit(bg_surf, (620, buff_y))
                pygame.draw.rect(self.screen, buff["color"], box_rect, 2, border_radius=6)
                txt_surf = self.font.render(buff["text"], True, buff["color"])
                self.screen.blit(txt_surf, (box_rect.centerx - txt_surf.get_width() // 2, box_rect.centery - txt_surf.get_height() // 2))
                ratio = buff["timer"] / buff["max_timer"]
                pygame.draw.line(self.screen, buff["color"], (box_rect.left + 4, box_rect.bottom - 3), (box_rect.left + int(162 * ratio), box_rect.bottom - 3), 2)
                buff_y += 36

            if gameplay.state == "LEVEL_CLEAR":
                overlay = pygame.Surface((800, 500), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (0, 0))
                box_rect = pygame.Rect(200, 120, 400, 260)
                pygame.draw.rect(self.screen, (20, 20, 35), box_rect, border_radius=15)
                pygame.draw.rect(self.screen, CYBER_BLUE, box_rect, 3, border_radius=15)
                win_title = self.title_font.render("VICTORY!", True, CYBER_YELLOW)
                self.screen.blit(win_title, (box_rect.centerx - win_title.get_width() // 2, 140))
                info_txt = self.font.render(f"Màn chơi {gameplay.current_level - 1} Hoàn Thành!", True, WHITE)
                self.screen.blit(info_txt, (box_rect.centerx - info_txt.get_width() // 2, 200))
                sec_left = max(1, gameplay.clear_timer // 60 + 1)
                time_txt = self.font.render(f"Tự động về Menu sau {sec_left}s...", True, CYBER_BLUE)
                self.screen.blit(time_txt, (box_rect.centerx - time_txt.get_width() // 2, 250))
            if gameplay.state == "GAME_OVER":
                self.draw_game_over(gameplay)
        else:
            gameplay.menu.render(gameplay.state, gameplay)

        pygame.display.flip()

    # ==================================================================
    # MÀN HÌNH "BẠN ĐÃ CHẾT"
    # ==================================================================
    def draw_game_over(self, gameplay):
        sw, sh = self.screen.get_size()
        t = gameplay.death_timer
        fade = min(1.0, t / 40.0)

        # Lớp phủ đỏ sẫm mờ dần + vệt quét ngang kiểu màn hình hỏng
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((40, 0, 8, int(200 * fade)))
        for y in range(0, sh, 4):
            pygame.draw.line(overlay, (0, 0, 0, int(60 * fade)), (0, y), (sw, y))
        self.screen.blit(overlay, (0, 0))

        # Viền đỏ nhấp nháy quanh màn hình
        pulse = 0.5 + 0.5 * math.sin(t * 0.15)
        edge = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for i in range(12):
            a = int((90 - i * 7) * fade * (0.6 + 0.4 * pulse))
            if a > 0:
                pygame.draw.rect(edge, (255, 30, 50, a), (i, i, sw - 2 * i, sh - 2 * i), 1)
        self.screen.blit(edge, (0, 0))

        if t < 12:
            return  # khoảnh khắc nổ: chỉ thấy màn hình đỏ dần

        # Tiêu đề rơi xuống + hiệu ứng nhiễu (glitch) màu xanh/hồng
        if not hasattr(self, "death_font"):
            self.death_font = get_font(64, bold=True)
            self.sub_font = get_font(20)
        drop = max(0.0, 1.0 - (t - 12) / 20.0)
        title_y = int(95 - 60 * drop * drop)
        title = "BẠN ĐÃ CHẾT"
        jitter = 6 if (t < 40 or random.random() < 0.06) else 0
        cx = sw // 2
        for color, ox in ((CYBER_BLUE, -3), (CYBER_PINK, 3)):
            g = self.death_font.render(title, True, color)
            dx = ox + (random.randint(-jitter, jitter) if jitter else 0)
            self.screen.blit(g, (cx - g.get_width() // 2 + dx, title_y))
        main = self.death_font.render(title, True, (255, 60, 70))
        self.screen.blit(main, (cx - main.get_width() // 2, title_y))

        sub = self.sub_font.render("Kết nối thần kinh bị cắt đứt... Hệ thống đang khởi động lại", True, (255, 170, 175))
        self.screen.blit(sub, (cx - sub.get_width() // 2, title_y + 78))

        if t < 30:
            return

        # Bảng thống kê
        st = gameplay.death_stats
        box = pygame.Rect(cx - 210, 215, 420, 160)
        bg = pygame.Surface(box.size, pygame.SRCALPHA)
        bg.fill((15, 10, 25, 220))
        self.screen.blit(bg, box.topleft)
        pygame.draw.rect(self.screen, (255, 60, 70), box, 2, border_radius=10)
        mins, secs = divmod(st.get("seconds", 0), 60)
        rows = [
            ("Màn chơi", f"{st.get('level', 1)}", CYBER_BLUE),
            ("Quái đã hạ", f"{st.get('kills', 0)}", GREEN),
            ("Coins kiếm được", f"+{st.get('coins', 0)}", CYBER_YELLOW),
            ("Thời gian sống", f"{mins:02d}:{secs:02d}", WHITE),
        ]
        if st.get("boss_hp"):
            hp, mx = st["boss_hp"]
            rows.append(("Boss còn lại", f"{int(100 * hp / max(1, mx))}% máu", CYBER_PINK))
        row_h = (box.height - 20) // len(rows)
        for i, (label, value, col) in enumerate(rows):
            y = box.top + 10 + i * row_h
            self.screen.blit(self.font.render(label, True, (200, 200, 215)), (box.left + 24, y))
            v = self.font.render(value, True, col)
            self.screen.blit(v, (box.right - 24 - v.get_width(), y))

        # Nút bấm
        ready = t >= gameplay.GAMEOVER_INPUT_DELAY
        mouse = pygame.mouse.get_pos()
        for rect, text, col in ((gameplay.RETRY_RECT, "[R] CHƠI LẠI", GREEN),
                                (gameplay.MENU_RECT, "[M] VỀ MENU", CYBER_BLUE)):
            hover = ready and rect.collidepoint(mouse)
            fill = (col[0] // 4, col[1] // 4, col[2] // 4) if hover else (20, 20, 35)
            pygame.draw.rect(self.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.screen, col if ready else (90, 90, 100), rect, 2, border_radius=8)
            lbl = self.font.render(text, True, col if ready else (110, 110, 120))
            self.screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))

        if ready and (t // 30) % 2 == 0:
            hint = self.sub_font.render("Nhấn R hoặc Enter để thử lại", True, (200, 200, 210))
            self.screen.blit(hint, (cx - hint.get_width() // 2, 455))
