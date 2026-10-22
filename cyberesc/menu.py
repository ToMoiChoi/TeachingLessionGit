import pygame
from config import CYBER_BLUE, CYBER_PINK, CYBER_YELLOW, DARK_BG, WHITE, RED, GREEN

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.title_font = pygame.font.SysFont("Arial", 32, bold=True)
        self.font = pygame.font.SysFont("Arial", 18, bold=True)

    def handle_click(self, pos, current_state, engine):
        x, y = pos

        if current_state == "MENU":
            if 300 <= x <= 500 and 160 <= y <= 205:
                engine.start_level(engine.current_level)
                return "GAME"
            elif 300 <= x <= 500 and 225 <= y <= 270:
                return "LEVEL_SELECT"
            elif 300 <= x <= 500 and 290 <= y <= 335:
                engine.shop_tab = "UPGRADES"
                return "SHOP"

        elif current_state == "LEVEL_SELECT":
            if 300 <= x <= 500 and 420 <= y <= 460:
                return "MENU"
            for i in range(1, 9):
                col = (i - 1) % 4
                row = (i - 1) // 4
                bx = 180 + col * 120
                by = 180 + row * 100
                if bx <= x <= bx + 100 and by <= y <= by + 70:
                    if i <= engine.max_unlocked_level:
                        engine.start_level(i)
                        return "GAME"

        elif current_state == "SHOP":
            # Switch Tabs
            if 220 <= x <= 390 and 80 <= y <= 120:
                engine.shop_tab = "UPGRADES"
                return "SHOP"
            elif 410 <= x <= 580 and 80 <= y <= 120:
                engine.shop_tab = "COSMETICS"
                return "SHOP"

            # Nút Back
            if 300 <= x <= 500 and 430 <= y <= 470:
                return "MENU"

            # Click nâng cấp cơ bản
            if engine.shop_tab == "UPGRADES":
                if 150 <= x <= 270 and 320 <= y <= 360:
                    engine.buy_upgrade("HP")
                elif 340 <= x <= 460 and 320 <= y <= 360:
                    engine.buy_upgrade("DMG")
                elif 530 <= x <= 650 and 320 <= y <= 360:
                    engine.buy_upgrade("SPEED")
                elif 250 <= x <= 550 and 375 <= y <= 415:
                    engine.perform_rebirth()

            # Gọi click xử lý riêng trong file cosmetics.py
            elif engine.shop_tab == "COSMETICS":
                engine.cosmetic_mgr.handle_click(pos, engine)

        return current_state

    def render(self, state, engine):
        self.screen.fill(DARK_BG)

        if state == "MENU":
            title = self.title_font.render("CYBER PLATFORMER", True, CYBER_BLUE)
            self.screen.blit(title, (400 - title.get_width() // 2, 70))

            buttons = [
                ("START GAME", 160, CYBER_BLUE),
                ("SELECT LEVEL", 225, CYBER_BLUE),
                ("SHOP & COSMETICS", 290, CYBER_YELLOW)
            ]

            for text, y, color in buttons:
                rect = pygame.Rect(300, y, 200, 45)
                pygame.draw.rect(self.screen, (30, 30, 50), rect, border_radius=10)
                pygame.draw.rect(self.screen, color, rect, 2, border_radius=10)
                txt_surf = self.font.render(text, True, color)
                self.screen.blit(txt_surf, (rect.centerx - txt_surf.get_width() // 2, rect.centery - txt_surf.get_height() // 2))

        elif state == "LEVEL_SELECT":
            title = self.title_font.render("CHỌN MÀN CHƠI", True, CYBER_BLUE)
            self.screen.blit(title, (400 - title.get_width() // 2, 70))

            for i in range(1, 9):
                col = (i - 1) % 4
                row = (i - 1) // 4
                bx = 180 + col * 120
                by = 180 + row * 100
                rect = pygame.Rect(bx, by, 100, 70)

                unlocked = i <= engine.max_unlocked_level
                color = CYBER_BLUE if unlocked else (80, 80, 100)
                
                pygame.draw.rect(self.screen, (30, 30, 50), rect, border_radius=8)
                pygame.draw.rect(self.screen, color, rect, 2, border_radius=8)

                lvl_txt = self.font.render(f"LV {i}", True, color)
                self.screen.blit(lvl_txt, (rect.centerx - lvl_txt.get_width() // 2, rect.centery - lvl_txt.get_height() // 2))

            back_rect = pygame.Rect(300, 420, 200, 40)
            pygame.draw.rect(self.screen, (30, 30, 50), back_rect, border_radius=8)
            pygame.draw.rect(self.screen, RED, back_rect, 2, border_radius=8)
            b_txt = self.font.render("QUAY LẠI", True, RED)
            self.screen.blit(b_txt, (back_rect.centerx - b_txt.get_width() // 2, back_rect.centery - b_txt.get_height() // 2))

        elif state == "SHOP":
            title = self.title_font.render("CỬA HÀNG", True, CYBER_YELLOW)
            self.screen.blit(title, (400 - title.get_width() // 2, 25))

            coins_txt = self.font.render(f"Coins: {engine.coins}", True, CYBER_YELLOW)
            self.screen.blit(coins_txt, (650, 35))

            # --- TAB BAR ---
            tab1_rect = pygame.Rect(220, 80, 170, 40)
            tab2_rect = pygame.Rect(410, 80, 170, 40)

            # Tab Nâng Cấp
            is_tab1 = engine.shop_tab == "UPGRADES"
            bg1 = (40, 50, 80) if is_tab1 else (25, 25, 40)
            border1 = CYBER_YELLOW if is_tab1 else (70, 70, 90)
            txt_c1 = CYBER_YELLOW if is_tab1 else WHITE
            pygame.draw.rect(self.screen, bg1, tab1_rect, border_radius=8)
            pygame.draw.rect(self.screen, border1, tab1_rect, 2, border_radius=8)
            t1_surf = self.font.render("NÂNG CẤP", True, txt_c1)
            self.screen.blit(t1_surf, (tab1_rect.centerx - t1_surf.get_width() // 2, tab1_rect.centery - t1_surf.get_height() // 2))

            # Tab Cosmetics
            is_tab2 = engine.shop_tab == "COSMETICS"
            bg2 = (50, 40, 70) if is_tab2 else (25, 25, 40)
            border2 = CYBER_PINK if is_tab2 else (70, 70, 90)
            txt_c2 = CYBER_PINK if is_tab2 else WHITE
            pygame.draw.rect(self.screen, bg2, tab2_rect, border_radius=8)
            pygame.draw.rect(self.screen, border2, tab2_rect, 2, border_radius=8)
            t2_surf = self.font.render("COSMETICS", True, txt_c2)
            self.screen.blit(t2_surf, (tab2_rect.centerx - t2_surf.get_width() // 2, tab2_rect.centery - t2_surf.get_height() // 2))

            # --- NỘI DUNG TAB ---
            if engine.shop_tab == "UPGRADES":
                upgrades = [
                    ("HP (+20)", f"Lv: {engine.hp_lvl}", f"Giá: {engine.hp_cost}", 150),
                    ("DMG (+10)", f"Lv: {engine.dmg_lvl}", f"Giá: {engine.dmg_cost}", 340),
                    ("SPEED (+1)", f"Lv: {engine.speed_lvl}", f"Giá: {engine.speed_cost}", 530)
                ]

                for name, lvl, cost, x in upgrades:
                    card = pygame.Rect(x, 155, 120, 150)
                    pygame.draw.rect(self.screen, (30, 30, 50), card, border_radius=10)
                    pygame.draw.rect(self.screen, CYBER_BLUE, card, 2, border_radius=10)

                    t1 = self.font.render(name, True, WHITE)
                    t2 = self.font.render(lvl, True, CYBER_BLUE)
                    t3 = self.font.render(cost, True, CYBER_YELLOW)
                    self.screen.blit(t1, (card.centerx - t1.get_width() // 2, 175))
                    self.screen.blit(t2, (card.centerx - t2.get_width() // 2, 215))
                    self.screen.blit(t3, (card.centerx - t3.get_width() // 2, 255))

                    btn = pygame.Rect(x, 320, 120, 40)
                    pygame.draw.rect(self.screen, GREEN, btn, border_radius=8)
                    btn_t = self.font.render("MUA", True, DARK_BG)
                    self.screen.blit(btn_t, (btn.centerx - btn_t.get_width() // 2, btn.centery - btn_t.get_height() // 2))

                # --- NÚT REBIRTH ---
                rebirth_rect = pygame.Rect(250, 375, 300, 40)
                can_rb = engine.can_rebirth()
                rb_cost = engine.get_rebirth_cost()
                rb_mult = engine.get_coin_multiplier()
                rb_count = engine.rebirths

                bg_rb = (50, 20, 60) if can_rb else (25, 25, 35)
                border_rb = CYBER_PINK if can_rb else (70, 70, 90)
                txt_c = CYBER_PINK if can_rb else (120, 120, 140)

                pygame.draw.rect(self.screen, bg_rb, rebirth_rect, border_radius=8)
                pygame.draw.rect(self.screen, border_rb, rebirth_rect, 2, border_radius=8)

                rb_text = f"REBIRTH ({rb_count}) | x{rb_mult:.1f} Coins | {rb_cost} Coins"
                rb_surf = self.font.render(rb_text, True, txt_c)
                self.screen.blit(rb_surf, (rebirth_rect.centerx - rb_surf.get_width() // 2, rebirth_rect.centery - rb_surf.get_height() // 2))

            elif engine.shop_tab == "COSMETICS":
                # Gọi hàm vẽ giao diện từ file cosmetics.py
                engine.cosmetic_mgr.render(self.screen)

            # Nút Quay lại Menu
            back_rect = pygame.Rect(300, 430, 200, 40)
            pygame.draw.rect(self.screen, (30, 30, 50), back_rect, border_radius=8)
            pygame.draw.rect(self.screen, RED, back_rect, 2, border_radius=8)
            b_txt = self.font.render("QUAY LẠI", True, RED)
            self.screen.blit(b_txt, (back_rect.centerx - b_txt.get_width() // 2, back_rect.centery - b_txt.get_height() // 2))