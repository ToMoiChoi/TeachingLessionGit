import math

import pygame

from config import CYBER_BLUE, CYBER_PINK, CYBER_YELLOW, DARK_BG, GREEN, RED, WHITE
from font_vn import get_font
from weapon import SHOP_WEAPONS, WEAPON_LIST

GREY = (80, 80, 100)
ORANGE = (255, 140, 0)
PURPLE = (170, 120, 255)


def draw_star(screen, cx, cy, r, filled, color=CYBER_YELLOW):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
    if filled:
        pygame.draw.polygon(screen, color, pts)
    pygame.draw.polygon(screen, color if filled else (90, 90, 110), pts, 1 if filled else 2)


class Menu:
    # Nút menu chính: (mã, nhãn, y, màu)
    MAIN_BUTTONS = [
        ("start", "START GAME", 120, CYBER_BLUE),
        ("levels", "CHỌN MÀN", 170, CYBER_BLUE),
        ("endless", "CHẾ ĐỘ VÔ TẬN", 220, CYBER_PINK),
        ("shop", "SHOP & COSMETICS", 270, CYBER_YELLOW),
        ("missions", "NHIỆM VỤ & KỶ LỤC", 320, GREEN),
        ("difficulty", "ĐỘ KHÓ", 370, WHITE),
    ]
    TABS = [("UPGRADES", "NÂNG CẤP", 130), ("WEAPONS", "VŨ KHÍ", 315), ("COSMETICS", "COSMETICS", 500)]

    def __init__(self, screen):
        self.screen = screen
        self.title_font = get_font(32, bold=True)
        self.font = get_font(18, bold=True)
        self.small = get_font(15)
        self.tick = 0

    @staticmethod
    def _main_rect(y):
        return pygame.Rect(290, y, 220, 42)

    @staticmethod
    def _level_rect(i):
        col, row = (i - 1) % 4, (i - 1) // 4
        return pygame.Rect(180 + col * 120, 170 + row * 110, 100, 85)

    @staticmethod
    def _mission_claim_rect(idx):
        return pygame.Rect(370, 155 + idx * 80 + 36, 90, 28)

    BACK_RECT = pygame.Rect(300, 435, 200, 40)

    # ==================================================================
    # CLICK
    # ==================================================================
    def handle_click(self, pos, current_state, engine):
        x, y = pos

        if current_state == "MENU":
            for key, _, by, _ in self.MAIN_BUTTONS:
                if self._main_rect(by).collidepoint(pos):
                    if key == "start":
                        engine.start_level(engine.current_level if engine.mode == "STORY" else 1)
                        return "GAME"
                    if key == "levels":
                        return "LEVEL_SELECT"
                    if key == "endless":
                        engine.start_endless()
                        return "GAME"
                    if key == "shop":
                        engine.shop_tab = "UPGRADES"
                        return "SHOP"
                    if key == "missions":
                        engine.missions.ensure_today()
                        return "MISSIONS"
                    if key == "difficulty":
                        engine.cycle_difficulty()
                        return "MENU"

        elif current_state == "LEVEL_SELECT":
            if self.BACK_RECT.collidepoint(pos):
                return "MENU"
            for i in range(1, 9):
                if self._level_rect(i).collidepoint(pos) and i <= engine.max_unlocked_level:
                    engine.start_level(i)
                    return "GAME"

        elif current_state == "MISSIONS":
            if self.BACK_RECT.collidepoint(pos):
                return "MENU"
            for idx in range(len(engine.missions.missions)):
                if self._mission_claim_rect(idx).collidepoint(pos):
                    engine.claim_mission(idx)

        elif current_state == "SHOP":
            for key, _, tx in self.TABS:
                if pygame.Rect(tx, 80, 170, 40).collidepoint(pos):
                    engine.shop_tab = key
                    return "SHOP"
            if self.BACK_RECT.collidepoint(pos):
                return "MENU"

            if engine.shop_tab == "UPGRADES":
                if 150 <= x <= 270 and 320 <= y <= 360:
                    engine.buy_upgrade("HP")
                elif 340 <= x <= 460 and 320 <= y <= 360:
                    engine.buy_upgrade("DMG")
                elif 530 <= x <= 650 and 320 <= y <= 360:
                    engine.buy_upgrade("SPEED")
                elif 250 <= x <= 550 and 375 <= y <= 415:
                    engine.perform_rebirth()
            elif engine.shop_tab == "WEAPONS":
                for i, (wkey, (price, _)) in enumerate(SHOP_WEAPONS.items()):
                    if pygame.Rect(150 + i * 270, 340, 230, 40).collidepoint(pos):
                        engine.buy_weapon(wkey, price)
            elif engine.shop_tab == "COSMETICS":
                engine.cosmetic_mgr.handle_click(pos, engine)

        return current_state

    # ==================================================================
    # VẼ
    # ==================================================================
    def _button(self, rect, text, color, hover=False, fill=(30, 30, 50)):
        bg = (color[0] // 5 + 20, color[1] // 5 + 20, color[2] // 5 + 30) if hover else fill
        pygame.draw.rect(self.screen, bg, rect, border_radius=10)
        pygame.draw.rect(self.screen, color, rect, 2, border_radius=10)
        t = self.font.render(text, True, color)
        self.screen.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))

    def _title(self, text, color, y=40):
        t = self.title_font.render(text, True, color)
        self.screen.blit(t, (400 - t.get_width() // 2, y))

    def _background(self):
        self.screen.fill(DARK_BG)
        # lưới neon chạy chậm phía sau
        off = (self.tick // 2) % 40
        for x in range(-40, 840, 40):
            pygame.draw.line(self.screen, (25, 25, 45), (x + off, 0), (x + off, 500))
        for y in range(0, 500, 40):
            pygame.draw.line(self.screen, (25, 25, 45), (0, y), (800, y))

    def render(self, state, engine):
        self.tick += 1
        self._background()
        mouse = pygame.mouse.get_pos()

        if state == "MENU":
            glow = 0.5 + 0.5 * math.sin(self.tick * 0.05)
            col = (int(0 + 120 * glow), 220, 255)
            self._title("CYBER ESCAPE", col, 40)
            coins = self.small.render(f"Coins: {engine.coins}", True, CYBER_YELLOW)
            self.screen.blit(coins, (790 - coins.get_width(), 10))
            for key, label, by, color in self.MAIN_BUTTONS:
                rect = self._main_rect(by)
                if key == "difficulty":
                    d = engine.diff
                    label, color = f"ĐỘ KHÓ: {d['name']}", d["color"]
                self._button(rect, label, color, rect.collidepoint(mouse))
                if key == "missions" and engine.missions.claimable_count():
                    pygame.draw.circle(self.screen, RED, (rect.right - 6, rect.top + 6), 10)
                    n = self.small.render(str(engine.missions.claimable_count()), True, WHITE)
                    self.screen.blit(n, (rect.right - 6 - n.get_width() // 2, rect.top + 6 - n.get_height() // 2))
            hint = self.small.render("A/D: chạy  W: nhảy  Chuột: bắn  J/Chuột phải: chém  Q: lướt  "
                                     "E: khiên  F: làm chậm  1-5: đổi súng  ESC: tạm dừng", True, (150, 150, 175))
            self.screen.blit(hint, (400 - hint.get_width() // 2, 440))
            if engine.difficulty != "NORMAL":
                d = engine.diff
                info = self.small.render(f"Máu quái x{d['enemy_hp']}  |  Sát thương nhận x{d['enemy_dmg']}  |  "
                                         f"Coins x{d['coins']}", True, d["color"])
                self.screen.blit(info, (400 - info.get_width() // 2, 418))

        elif state == "LEVEL_SELECT":
            self._title("CHỌN MÀN CHƠI", CYBER_BLUE, 60)
            total = sum(int(v) for v in engine.stars.values())
            st = self.small.render(f"Tổng sao: {total}/24", True, CYBER_YELLOW)
            self.screen.blit(st, (400 - st.get_width() // 2, 110))
            for i in range(1, 9):
                rect = self._level_rect(i)
                unlocked = i <= engine.max_unlocked_level
                color = (CYBER_PINK if i in (4, 6, 8) else CYBER_BLUE) if unlocked else GREY
                hover = unlocked and rect.collidepoint(mouse)
                pygame.draw.rect(self.screen, (45, 45, 75) if hover else (30, 30, 50), rect, border_radius=8)
                pygame.draw.rect(self.screen, color, rect, 2, border_radius=8)
                label = f"LV {i}" if unlocked else "KHÓA"
                t = self.font.render(label, True, color)
                self.screen.blit(t, (rect.centerx - t.get_width() // 2, rect.top + 12))
                if i in (4, 6, 8) and unlocked:
                    b = self.small.render("BOSS", True, CYBER_PINK)
                    self.screen.blit(b, (rect.centerx - b.get_width() // 2, rect.top + 34))
                got = int(engine.stars.get(str(i), 0))
                for s in range(3):
                    draw_star(self.screen, rect.centerx - 22 + s * 22, rect.bottom - 16, 8, s < got)
            self._button(self.BACK_RECT, "QUAY LẠI", RED, self.BACK_RECT.collidepoint(mouse))

        elif state == "MISSIONS":
            self._title("NHIỆM VỤ & KỶ LỤC", GREEN, 30)
            sub = self.small.render(f"Nhiệm vụ hôm nay ({engine.missions.date}) - làm mới mỗi ngày", True, (170, 170, 190))
            self.screen.blit(sub, (40, 125))
            for idx, m in enumerate(engine.missions.missions):
                box = pygame.Rect(40, 155 + idx * 80, 430, 72)
                pygame.draw.rect(self.screen, (30, 30, 50), box, border_radius=8)
                done = m["progress"] >= m["target"]
                pygame.draw.rect(self.screen, GREEN if done else GREY, box, 2, border_radius=8)
                self.screen.blit(self.font.render(m["text"], True, WHITE), (box.x + 12, box.y + 6))
                bar = pygame.Rect(box.x + 12, box.y + 46, 300, 10)
                pygame.draw.rect(self.screen, (20, 20, 35), bar, border_radius=4)
                pygame.draw.rect(self.screen, GREEN if done else CYBER_BLUE,
                                 (bar.x, bar.y, int(bar.w * m["progress"] / m["target"]), bar.h), border_radius=4)
                pr = self.small.render(f"{m['progress']}/{m['target']}   +{m['reward']} coins", True, CYBER_YELLOW)
                self.screen.blit(pr, (box.x + 12, box.y + 26))
                btn = self._mission_claim_rect(idx)
                if m["claimed"]:
                    self._button(btn, "ĐÃ NHẬN", GREY)
                elif done:
                    self._button(btn, "NHẬN", GREEN, btn.collidepoint(mouse))
                else:
                    self._button(btn, "...", GREY)

            board = pygame.Rect(495, 125, 265, 285)
            pygame.draw.rect(self.screen, (30, 30, 50), board, border_radius=8)
            pygame.draw.rect(self.screen, CYBER_PINK, board, 2, border_radius=8)
            t = self.font.render("TOP 5 VÔ TẬN", True, CYBER_PINK)
            self.screen.blit(t, (board.centerx - t.get_width() // 2, board.y + 10))
            if not engine.endless_scores:
                e = self.small.render("Chưa có lượt chơi nào", True, (150, 150, 170))
                self.screen.blit(e, (board.centerx - e.get_width() // 2, board.y + 60))
            for r, s in enumerate(engine.endless_scores[:5]):
                y = board.y + 50 + r * 44
                col = [CYBER_YELLOW, (200, 200, 220), (205, 127, 50)][r] if r < 3 else WHITE
                self.screen.blit(self.font.render(f"#{r + 1}", True, col), (board.x + 14, y))
                self.screen.blit(self.font.render(f"{s['score']} điểm", True, WHITE), (board.x + 60, y))
                w = self.small.render(f"Wave {s['wave']}  -  {s.get('date', '')}", True, (150, 150, 170))
                self.screen.blit(w, (board.x + 60, y + 20))
            self._button(self.BACK_RECT, "QUAY LẠI", RED, self.BACK_RECT.collidepoint(mouse))

        elif state == "SHOP":
            self._title("CỬA HÀNG", CYBER_YELLOW, 25)
            coins_txt = self.font.render(f"Coins: {engine.coins}", True, CYBER_YELLOW)
            self.screen.blit(coins_txt, (650, 35))

            tab_colors = {"UPGRADES": CYBER_YELLOW, "WEAPONS": ORANGE, "COSMETICS": CYBER_PINK}
            for key, label, tx in self.TABS:
                rect = pygame.Rect(tx, 80, 170, 40)
                active = engine.shop_tab == key
                col = tab_colors[key] if active else (70, 70, 90)
                pygame.draw.rect(self.screen, (40, 50, 80) if active else (25, 25, 40), rect, border_radius=8)
                pygame.draw.rect(self.screen, col, rect, 2, border_radius=8)
                t = self.font.render(label, True, tab_colors[key] if active else WHITE)
                self.screen.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))

            if engine.shop_tab == "UPGRADES":
                upgrades = [
                    ("HP (+10)", f"Lv: {engine.hp_lvl}", f"Giá: {engine.hp_cost}", 150),
                    ("DMG (+4)", f"Lv: {engine.dmg_lvl}", f"Giá: {engine.dmg_cost}", 340),
                    ("SPEED", f"Lv: {engine.speed_lvl}", f"Giá: {engine.speed_cost}", 530),
                ]
                for name, lvl, cost, x in upgrades:
                    card = pygame.Rect(x, 155, 120, 150)
                    pygame.draw.rect(self.screen, (30, 30, 50), card, border_radius=10)
                    pygame.draw.rect(self.screen, CYBER_BLUE, card, 2, border_radius=10)
                    for text, color, ty in ((name, WHITE, 175), (lvl, CYBER_BLUE, 215), (cost, CYBER_YELLOW, 255)):
                        t = self.font.render(text, True, color)
                        self.screen.blit(t, (card.centerx - t.get_width() // 2, ty))
                    btn = pygame.Rect(x, 320, 120, 40)
                    pygame.draw.rect(self.screen, GREEN, btn, border_radius=8)
                    bt = self.font.render("MUA", True, DARK_BG)
                    self.screen.blit(bt, (btn.centerx - bt.get_width() // 2, btn.centery - bt.get_height() // 2))

                rebirth_rect = pygame.Rect(250, 375, 300, 40)
                can_rb = engine.can_rebirth()
                pygame.draw.rect(self.screen, (50, 20, 60) if can_rb else (25, 25, 35), rebirth_rect, border_radius=8)
                pygame.draw.rect(self.screen, CYBER_PINK if can_rb else (70, 70, 90), rebirth_rect, 2, border_radius=8)
                rb = (f"REBIRTH ({engine.rebirths}) | x{1 + engine.rebirths * 0.5:.1f} Coins | "
                      f"{engine.get_rebirth_cost()} Coins")
                rs = self.font.render(rb, True, CYBER_PINK if can_rb else (120, 120, 140))
                self.screen.blit(rs, (rebirth_rect.centerx - rs.get_width() // 2, rebirth_rect.centery - rs.get_height() // 2))

            elif engine.shop_tab == "WEAPONS":
                for i, (wkey, (price, desc)) in enumerate(SHOP_WEAPONS.items()):
                    w = WEAPON_LIST[wkey]
                    card = pygame.Rect(150 + i * 270, 140, 230, 245)
                    pygame.draw.rect(self.screen, (30, 30, 50), card, border_radius=10)
                    pygame.draw.rect(self.screen, ORANGE, card, 2, border_radius=10)
                    name = self.font.render(w.name, True, WHITE)
                    self.screen.blit(name, (card.centerx - name.get_width() // 2, card.y + 12))
                    img = pygame.transform.scale(w.image, (w.image.get_width() * 2, w.image.get_height() * 2))
                    self.screen.blit(img, (card.centerx - img.get_width() // 2, card.y + 45))
                    stats = [f"Sát thương: {w.damage}", f"Băng đạn: {w.max_ammo}",
                             f"Phím: {['1', '2', '3', '4', '5'][['Blaster', 'Shotgun', 'Rifle', 'Laser', 'Grenade'].index(wkey)]}"]
                    for j, s in enumerate(stats):
                        t = self.small.render(s, True, CYBER_BLUE)
                        self.screen.blit(t, (card.x + 16, card.y + 100 + j * 20))
                    d = self.small.render(desc, True, (190, 190, 210))
                    if d.get_width() > card.w - 20:
                        d = pygame.transform.smoothscale(d, (card.w - 20, d.get_height()))
                    self.screen.blit(d, (card.centerx - d.get_width() // 2, card.y + 165))
                    btn = pygame.Rect(150 + i * 270, 340, 230, 40)
                    if wkey in engine.weapons_owned:
                        self._button(btn, "ĐÃ SỞ HỮU", GREEN)
                    else:
                        can = engine.coins >= price
                        self._button(btn, f"MUA {price} C", CYBER_YELLOW if can else GREY,
                                     can and btn.collidepoint(mouse))

            elif engine.shop_tab == "COSMETICS":
                engine.cosmetic_mgr.render(self.screen)

            self._button(self.BACK_RECT, "QUAY LẠI", RED, self.BACK_RECT.collidepoint(mouse))

