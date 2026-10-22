import pygame

from settings import (
    WIDTH,
    HEIGHT,
    WHITE,
    GREEN,
    YELLOW,
    RED
)


class HUD:

    def __init__(self):
        # Dùng Segoe UI / Tahoma có đầy đủ bộ glyph Tiếng Việt Unicode chuẩn trên Windows
        font_family = "segoeui,tahoma,arial"
        self.font_small = pygame.font.SysFont(font_family, 16, bold=True)
        self.font = pygame.font.SysFont(font_family, 20)
        self.mid_font = pygame.font.SysFont(font_family, 26, bold=True)
        self.big_font = pygame.font.SysFont(font_family, 34, bold=True)

    def draw_text(
        self,
        screen,
        text,
        x,
        y,
        color=WHITE,
        font=None
    ):
        if font is None:
            font = self.font

        image = font.render(
            text,
            True,
            color
        )

        screen.blit(
            image,
            (x, y)
        )

    def draw(
        self,
        screen,
        player,
        player_score,
        enemy_score,
        round_timer
    ):
        # =====================================================
        # 1. THANH MÁU (HP) & GIÁP (ARMOR) GÓC DƯỚI TRÁI
        # =====================================================
        hp_val = max(0, int(getattr(player, "hp", 100)))
        armor_val = max(0, int(getattr(player, "armor", 50)))

        bar_w = 170
        bx = 24

        # Nền panel cho HP/Armor
        panel_h = pygame.Surface((bar_w + 16, 62), pygame.SRCALPHA)
        panel_h.fill((16, 20, 26, 200))
        pygame.draw.rect(panel_h, (55, 65, 80, 220), (0, 0, bar_w + 16, 62), 1, border_radius=6)
        screen.blit(panel_h, (bx - 8, HEIGHT - 76))

        # Thanh máu HP
        hp_y = HEIGHT - 70
        pygame.draw.rect(screen, (30, 35, 42), (bx, hp_y, bar_w, 18), border_radius=4)
        hp_fill = int(bar_w * min(1.0, hp_val / 100.0))
        hp_col = (60, 220, 100) if hp_val > 30 else (240, 60, 70)
        if hp_fill > 0:
            pygame.draw.rect(screen, hp_col, (bx, hp_y, hp_fill, 18), border_radius=4)
        self.draw_text(screen, f"HP  {hp_val}", bx + 8, hp_y - 1, (255, 255, 255), self.font_small)

        # Thanh giáp Armor
        ar_y = HEIGHT - 46
        pygame.draw.rect(screen, (30, 35, 42), (bx, ar_y, bar_w, 18), border_radius=4)
        ar_fill = int(bar_w * min(1.0, armor_val / 50.0))
        if ar_fill > 0:
            pygame.draw.rect(screen, (70, 160, 245), (bx, ar_y, ar_fill, 18), border_radius=4)
        self.draw_text(screen, f"GIÁP  {armor_val}", bx + 8, ar_y - 1, (255, 255, 255), self.font_small)

        # =====================================================
        # 2. KHUNG ĐẠN & VŨ KHÍ GÓC DƯỚI PHẢI
        # =====================================================
        box_w, box_h = 165, 62
        rx = WIDTH - box_w - 20
        ry = HEIGHT - box_h - 15
        panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        panel.fill((16, 20, 26, 200))
        pygame.draw.rect(panel, (55, 65, 80, 220), (0, 0, box_w, box_h), 1, border_radius=6)
        screen.blit(panel, (rx, ry))

        # Tên vũ khí đã có ở danh sách slot, ô này chỉ hiển thị đạn
        self.draw_text(
            screen,
            "ĐẠN",
            rx + 12,
            ry + 6,
            (205, 215, 230),
            self.font_small
        )

        mag = getattr(player, "magazine", 0)
        res = getattr(player, "reserve", 0)
        ammo_col = (255, 75, 75) if mag == 0 else WHITE
        self.draw_text(
            screen,
            f"{mag} / {res}",
            rx + 12,
            ry + 26,
            ammo_col,
            self.mid_font
        )

        # =====================================================
        # 3. TỶ SỐ & THỜI GIAN TRẬN ĐẤU Ở ĐỈNH GIỮA MÀN HÌNH
        # =====================================================
        cx = WIDTH // 2

        # Khung nền Header
        header_surf = pygame.Surface((180, 68), pygame.SRCALPHA)
        header_surf.fill((14, 18, 24, 210))
        pygame.draw.rect(header_surf, (55, 65, 80, 220), (0, 0, 180, 68), 1, border_radius=8)
        screen.blit(header_surf, (cx - 90, 8))

        # Tỷ số 0 - 0
        score_text = f"{player_score}  -  {enemy_score}"
        s_img = self.big_font.render(score_text, True, (255, 255, 255))
        screen.blit(s_img, (cx - s_img.get_width() // 2, 12))

        # Thời gian đếm ngược
        sec = max(0, int(round_timer))
        t_col = (255, 90, 90) if sec <= 10 else (225, 230, 240)
        t_img = self.font_small.render(f"{sec}s", True, t_col)
        screen.blit(t_img, (cx - t_img.get_width() // 2, 48))

    def crosshair(self, screen):
        cx = WIDTH // 2
        cy = HEIGHT // 2
        gap = 7
        length = 8

        pygame.draw.line(screen, WHITE, (cx - gap - length, cy), (cx - gap, cy), 2)
        pygame.draw.line(screen, WHITE, (cx + gap, cy), (cx + gap + length, cy), 2)
        pygame.draw.line(screen, WHITE, (cx, cy - gap - length), (cx, cy - gap), 2)
        pygame.draw.line(screen, WHITE, (cx, cy + gap), (cx, cy + gap + length), 2)