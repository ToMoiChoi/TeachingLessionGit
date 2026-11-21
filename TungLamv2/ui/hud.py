"""ui/hud.py - Thanh giao diện Máu, Giáp, Đạn, Tỉ số / Đợt Zombie (tối ưu cache Surface & font tiếng Việt)."""
import pygame

from settings import WIDTH, HEIGHT, WHITE
from font_vn import get_font


class HUD:
    def __init__(self):
        self.font_small = get_font(16, bold=True)
        self.font = get_font(20)
        self.mid_font = get_font(26, bold=True)
        self.big_font = get_font(32, bold=True)

        # Cache sẵn 3 tấm nền bán trong suốt để không cấp phát Surface mỗi frame
        self.bar_w = 170
        self._hp_panel = pygame.Surface((self.bar_w + 16, 62), pygame.SRCALPHA)
        self._hp_panel.fill((16, 20, 26, 200))
        pygame.draw.rect(self._hp_panel, (55, 65, 80, 220), (0, 0, self.bar_w + 16, 62), 1, border_radius=6)

        self.ammo_w, self.ammo_h = 172, 62
        self._ammo_panel = pygame.Surface((self.ammo_w, self.ammo_h), pygame.SRCALPHA)
        self._ammo_panel.fill((16, 20, 26, 200))
        pygame.draw.rect(self._ammo_panel, (55, 65, 80, 220), (0, 0, self.ammo_w, self.ammo_h), 1, border_radius=6)
        ammo_lbl = self.font_small.render("ĐẠN / AMMO", True, (205, 215, 230))
        self._ammo_panel.blit(ammo_lbl, (12, 6))

        self.header_w, self.header_h = 250, 72
        self._header_panel = pygame.Surface((self.header_w, self.header_h), pygame.SRCALPHA)
        self._header_panel.fill((14, 18, 24, 215))
        pygame.draw.rect(self._header_panel, (55, 65, 80, 225), (0, 0, self.header_w, self.header_h), 1, border_radius=8)
        self._text_cache = {}

    def _render_cached(self, font, text, color):
        key = (id(font), text, color)
        img = self._text_cache.get(key)
        if img is None:
            if len(self._text_cache) > 192:
                self._text_cache.clear()
            img = font.render(text, True, color)
            self._text_cache[key] = img
        return img

    def draw_text(self, screen, text, x, y, color=WHITE, font=None):
        if font is None:
            font = self.font
        screen.blit(self._render_cached(font, text, color), (x, y))

    def draw(
        self,
        screen,
        player,
        player_score,
        enemy_score,
        round_timer,
        header_title=None,
        header_sub=None,
    ):
        # 1. Máu & Giáp (Góc trái dưới)
        hp_val = max(0, int(getattr(player, "hp", 100)))
        armor_val = max(0, int(getattr(player, "armor", 50)))
        bx = 24
        screen.blit(self._hp_panel, (bx - 8, HEIGHT - 76))

        hp_y = HEIGHT - 70
        pygame.draw.rect(screen, (30, 35, 42), (bx, hp_y, self.bar_w, 18), border_radius=4)
        hp_fill = int(self.bar_w * min(1.0, hp_val / 100.0))
        hp_col = (60, 220, 100) if hp_val > 30 else (240, 60, 70)
        if hp_fill > 0:
            pygame.draw.rect(screen, hp_col, (bx, hp_y, hp_fill, 18), border_radius=4)
        self.draw_text(screen, f"HP  {hp_val}", bx + 8, hp_y, (255, 255, 255), self.font_small)

        ar_y = HEIGHT - 46
        pygame.draw.rect(screen, (30, 35, 42), (bx, ar_y, self.bar_w, 18), border_radius=4)
        ar_fill = int(self.bar_w * min(1.0, armor_val / 50.0))
        if ar_fill > 0:
            pygame.draw.rect(screen, (70, 160, 245), (bx, ar_y, ar_fill, 18), border_radius=4)
        self.draw_text(screen, f"GIÁP  {armor_val}", bx + 8, ar_y, (255, 255, 255), self.font_small)

        # 2. Hộp đạn (Góc phải dưới)
        rx = WIDTH - self.ammo_w - 20
        ry = HEIGHT - self.ammo_h - 15
        screen.blit(self._ammo_panel, (rx, ry))

        cur_w = getattr(player, "weapon", "")
        if cur_w == "KNIFE":
            self.draw_text(screen, "DAO CẬN CHIẾN", rx + 12, ry + 28, (220, 225, 235), self.font)
        else:
            mag = getattr(player, "magazine", 0)
            res = getattr(player, "reserve", 0)
            ammo_col = (255, 75, 75) if mag == 0 else WHITE
            self.draw_text(screen, f"{mag} / {res}", rx + 12, ry + 26, ammo_col, self.mid_font)

        # 3. Tỉ số / Đợt Zombie & Đồng hồ (Chính giữa trên)
        cx = WIDTH // 2
        screen.blit(self._header_panel, (cx - self.header_w // 2, 8))

        if header_title:
            s_img = self._render_cached(self.mid_font, header_title, (130, 250, 140))
            screen.blit(s_img, (cx - s_img.get_width() // 2, 13))
        else:
            score_text = f"{player_score}  -  {enemy_score}"
            s_img = self._render_cached(self.big_font, score_text, (255, 255, 255))
            screen.blit(s_img, (cx - s_img.get_width() // 2, 11))

        if header_sub:
            t_img = self._render_cached(self.font_small, header_sub, (245, 215, 90))
        else:
            sec = max(0, int(round_timer))
            t_col = (255, 90, 90) if sec <= 10 else (225, 230, 240)
            t_img = self._render_cached(self.font_small, f"{sec}s", t_col)
        screen.blit(t_img, (cx - t_img.get_width() // 2, 50))
