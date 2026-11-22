import math

import pygame

from config import CYBER_BLUE, CYBER_PINK, CYBER_YELLOW, DARK_BG, GREEN, RED, WHITE
from font_vn import get_font
from game_engine_layout import get_map_theme
from weapon import SHOP_WEAPONS, WEAPON_KEYS, WEAPON_LIST

GREY = (80, 80, 100)
ORANGE = (255, 140, 0)
PURPLE = (170, 120, 255)
BOSS_LEVELS = {4, 6, 8, 10, 12, 14, 16}
MAX_LEVEL = 16


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
    # Nút trên Landing Screen (cột phải): (mã, nhãn, y, màu)
    MAIN_BUTTONS = [
        ("start", "START GAME", 104, CYBER_BLUE),
        ("levels", "CHỌN MÀN (16 MAP)", 158, CYBER_BLUE),
        ("endless", "CHẾ ĐỘ VÔ TẬN", 212, CYBER_PINK),
        ("shop", "CỬA HÀNG & TÙY BIẾN", 266, CYBER_YELLOW),
        ("missions", "NHIỆM VỤ & KỶ LỤC", 320, GREEN),
        ("difficulty", "ĐỘ KHÓ", 374, WHITE),
    ]
    TABS = [("UPGRADES", "NÂNG CẤP", 130), ("WEAPONS", "VŨ KHÍ", 315), ("COSMETICS", "COSTUME & ĐỒ", 500)]
    WEAPONS_PER_PAGE = 3

    def __init__(self, screen):
        self.screen = screen
        self.title_font = get_font(32, bold=True)
        self.hero_font = get_font(36, bold=True)
        self.font = get_font(18, bold=True)
        self.small = get_font(14)
        self.tiny = get_font(12)
        self.tick = 0
        self.level_page = 0   # 0: LV 1..8, 1: LV 9..16
        self.weapon_page = 0  # 0: 3 súng đầu, 1: các súng còn lại

    @staticmethod
    def _main_rect(y):
        return pygame.Rect(365, y, 390, 44)

    @staticmethod
    def _level_rect(slot):
        """slot: 0..7 trên mỗi trang chọn màn (lưới 4x2)."""
        col, row = slot % 4, slot // 4
        return pygame.Rect(92 + col * 158, 146 + row * 124, 142, 108)

    @staticmethod
    def _mission_claim_rect(idx):
        return pygame.Rect(370, 155 + idx * 80 + 36, 90, 28)

    BACK_RECT = pygame.Rect(300, 442, 200, 40)
    LVL_PREV_RECT = pygame.Rect(140, 442, 140, 40)
    LVL_NEXT_RECT = pygame.Rect(520, 442, 140, 40)
    WPN_PREV_RECT = pygame.Rect(150, 394, 110, 32)
    WPN_NEXT_RECT = pygame.Rect(540, 394, 110, 32)

    # ==================================================================
    # CLICK
    # ==================================================================
    def handle_click(self, pos, current_state, engine):
        x, y = pos

        if current_state == "MENU":
            for key, _, by, _ in self.MAIN_BUTTONS:
                if self._main_rect(by).collidepoint(pos):
                    if key == "start":
                        target = engine.current_level if engine.mode == "STORY" else 1
                        engine.start_level(min(MAX_LEVEL, max(1, target)))
                        return "GAME"
                    if key == "levels":
                        self.level_page = 0 if engine.max_unlocked_level <= 8 else 1
                        return "LEVEL_SELECT"
                    if key == "endless":
                        engine.start_endless()
                        return "GAME"
                    if key == "shop":
                        engine.shop_tab = "COSMETICS"
                        if hasattr(engine, "sync_player_cosmetics"):
                            engine.sync_player_cosmetics()
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
            if self.LVL_PREV_RECT.collidepoint(pos) and self.level_page > 0:
                self.level_page -= 1
                return "LEVEL_SELECT"
            if self.LVL_NEXT_RECT.collidepoint(pos) and self.level_page < 1:
                self.level_page += 1
                return "LEVEL_SELECT"
            base = self.level_page * 8
            for slot in range(8):
                lvl = base + slot + 1
                if self._level_rect(slot).collidepoint(pos) and lvl <= engine.max_unlocked_level:
                    engine.start_level(lvl)
                    return "GAME"

        elif current_state == "MISSIONS":
            if self.BACK_RECT.collidepoint(pos):
                return "MENU"
            for idx in range(len(engine.missions.missions)):
                if self._mission_claim_rect(idx).collidepoint(pos):
                    engine.claim_mission(idx)

        elif current_state == "SHOP":
            for key, _, tx in self.TABS:
                if pygame.Rect(tx, 76, 170, 38).collidepoint(pos):
                    engine.shop_tab = key
                    if key == "COSMETICS" and hasattr(engine, "sync_player_cosmetics"):
                        engine.sync_player_cosmetics()
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
                wpn_items = list(SHOP_WEAPONS.items())
                pages = max(1, (len(wpn_items) + self.WEAPONS_PER_PAGE - 1) // self.WEAPONS_PER_PAGE)
                if self.WPN_PREV_RECT.collidepoint(pos) and self.weapon_page > 0:
                    self.weapon_page -= 1
                    return "SHOP"
                if self.WPN_NEXT_RECT.collidepoint(pos) and self.weapon_page < pages - 1:
                    self.weapon_page += 1
                    return "SHOP"
                start = self.weapon_page * self.WEAPONS_PER_PAGE
                for i, (wkey, (price, _)) in enumerate(wpn_items[start:start + self.WEAPONS_PER_PAGE]):
                    if pygame.Rect(65 + i * 235, 342, 200, 36).collidepoint(pos):
                        engine.buy_weapon(wkey, price)
            elif engine.shop_tab == "COSMETICS":
                engine.cosmetic_mgr.handle_click(pos, engine)

        return current_state

    # ==================================================================
    # VẼ
    # ==================================================================
    def _button(self, rect, text, color, hover=False, fill=(28, 30, 52), font=None):
        bg = (min(255, color[0] // 4 + 22), min(255, color[1] // 4 + 22), min(255, color[2] // 4 + 34)) if hover else fill
        pygame.draw.rect(self.screen, bg, rect, border_radius=10)
        pygame.draw.rect(self.screen, color, rect, 2, border_radius=10)
        f = font or self.font
        t = f.render(text, True, color)
        self.screen.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))

    def _title(self, text, color, y=28):
        t = self.title_font.render(text, True, color)
        self.screen.blit(t, (400 - t.get_width() // 2, y))

    def _background(self):
        self.screen.fill(DARK_BG)
        # Lưới neon chuyển động mượt phía sau
        off = (self.tick // 2) % 40
        for x in range(-40, 840, 40):
            pygame.draw.line(self.screen, (22, 25, 46), (x + off, 0), (x + off, 500))
        for y in range(0, 500, 40):
            pygame.draw.line(self.screen, (22, 25, 46), (0, y), (800, y))
        # Đường chân trời neon nhẹ ở cuối màn hình
        pygame.draw.line(self.screen, (0, 110, 150), (0, 456), (800, 456), 1)

    def _render_landing(self, engine, mouse):
        """Màn hình Landing mới: Header neon + Cột trái Preview nhân vật + Cột phải Action Panel."""
        # --- HEADER ---
        glow = 0.5 + 0.5 * math.sin(self.tick * 0.05)
        col = (int(20 + 110 * glow), 230, 255)
        title = self.hero_font.render("CYBER ESCAPE", True, col)
        shadow = self.hero_font.render("CYBER ESCAPE", True, (90, 0, 110))
        self.screen.blit(shadow, (42, 20))
        self.screen.blit(title, (40, 18))

        sub = self.small.render("CYBERPUNK ACTION PLATFORMER  •  16 MAPS  •  CUSTOM HERO", True, (160, 175, 205))
        self.screen.blit(sub, (42, 62))

        # Thanh thông số góc phải trên (Coins + Sao)
        total_stars = sum(int(v) for v in engine.stars.values())
        pill = pygame.Rect(500, 22, 260, 36)
        pygame.draw.rect(self.screen, (24, 26, 46), pill, border_radius=10)
        pygame.draw.rect(self.screen, (60, 70, 105), pill, 1, border_radius=10)
        c_txt = self.font.render(f"{engine.coins} C", True, CYBER_YELLOW)
        s_txt = self.font.render(f"{total_stars}/{MAX_LEVEL * 3}", True, CYBER_BLUE)
        self.screen.blit(c_txt, (pill.x + 16, pill.centery - c_txt.get_height() // 2))
        draw_star(self.screen, pill.right - s_txt.get_width() - 28, pill.centery, 7, True, CYBER_YELLOW)
        self.screen.blit(s_txt, (pill.right - s_txt.get_width() - 14, pill.centery - s_txt.get_height() // 2))

        # --- CỘT TRÁI: HERO CARD (LIVE PREVIEW NHÂN VẬT) ---
        hero_card = pygame.Rect(40, 96, 295, 348)
        pygame.draw.rect(self.screen, (20, 22, 40), hero_card, border_radius=14)
        pygame.draw.rect(self.screen, CYBER_BLUE, hero_card, 2, border_radius=14)

        badge = self.small.render("CHIẾN BINH CỦA BẠN", True, CYBER_BLUE)
        self.screen.blit(badge, (hero_card.centerx - badge.get_width() // 2, hero_card.y + 10))

        # Sân khấu preview nhân vật
        stage = pygame.Rect(hero_card.x + 18, hero_card.y + 34, hero_card.w - 36, 175)
        pygame.draw.rect(self.screen, (12, 14, 28), stage, border_radius=10)
        pygame.draw.rect(self.screen, (45, 55, 90), stage, 1, border_radius=10)
        # Bệ hào quang neon
        pulse_r = int(58 + 4 * math.sin(self.tick * 0.08))
        pygame.draw.ellipse(self.screen, (0, 150, 200),
                            (stage.centerx - pulse_r, stage.bottom - 26, pulse_r * 2, 16), 2)
        pygame.draw.ellipse(self.screen, (140, 0, 120),
                            (stage.centerx - pulse_r + 12, stage.bottom - 23, (pulse_r - 12) * 2, 10), 1)

        if hasattr(engine, "sync_player_cosmetics"):
            engine.sync_player_cosmetics()
        engine.player.draw_preview(self.screen, stage.centerx, stage.bottom - 18, scale=2.3, tick=self.tick)

        # Thông tin nhân vật & tiến độ
        buffs = engine.cosmetic_mgr.get_total_buffs()
        max_hp = 100 + (engine.hp_lvl - 1) * 10 + buffs["hp"]
        dmg_b = (engine.dmg_lvl - 1) * 4 + buffs["dmg"]
        spd = 5.0 + (engine.speed_lvl - 1) * 0.3 + buffs["speed"]

        outfit = self.small.render(f"{buffs['body_name']}", True, CYBER_YELLOW)
        if outfit.get_width() > hero_card.w - 24:
            outfit = pygame.transform.smoothscale(outfit, (hero_card.w - 24, outfit.get_height()))
        self.screen.blit(outfit, (hero_card.centerx - outfit.get_width() // 2, stage.bottom + 8))

        stat_rows = [
            ("Máu tối đa", f"{max_hp} HP", GREEN),
            ("Sát thương cộng", f"+{dmg_b} DMG", ORANGE),
            ("Tốc độ di chuyển", f"{spd:.1f}", CYBER_BLUE),
            ("Vũ khí sở hữu", f"{len(engine.weapons_owned)}/{len(WEAPON_KEYS)}", CYBER_PINK),
            ("Tiến độ bản đồ", f"LV {engine.max_unlocked_level}/{MAX_LEVEL}", CYBER_YELLOW),
        ]
        for idx, (lbl, val, c) in enumerate(stat_rows):
            ry = stage.bottom + 32 + idx * 20
            self.screen.blit(self.small.render(lbl, True, (175, 180, 205)), (hero_card.x + 18, ry))
            vt = self.small.render(val, True, c)
            self.screen.blit(vt, (hero_card.right - 18 - vt.get_width(), ry))

        # --- CỘT PHẢI: ACTION PANEL ---
        for key, label, by, color in self.MAIN_BUTTONS:
            rect = self._main_rect(by)
            if key == "start":
                cur_lv = min(MAX_LEVEL, max(1, engine.current_level if engine.mode == "STORY" else 1))
                label = f"CHƠI NGAY  —  LV {cur_lv}"
            elif key == "difficulty":
                d = engine.diff
                label = f"ĐỘ KHÓ: {d['name']}  (Quái x{d['enemy_hp']} | Coin x{d['coins']})"
                color = d["color"]
            self._button(rect, label, color, rect.collidepoint(mouse),
                         fill=(32, 38, 66) if key == "start" else (26, 28, 48))
            if key == "missions" and engine.missions.claimable_count():
                pygame.draw.circle(self.screen, RED, (rect.right - 12, rect.top + 10), 10)
                n = self.small.render(str(engine.missions.claimable_count()), True, WHITE)
                self.screen.blit(n, (rect.right - 12 - n.get_width() // 2, rect.top + 10 - n.get_height() // 2))

        # --- FOOTER HƯỚNG DẪN ---
        hint = self.small.render(
            "A/D: chạy  •  W/Space: nhảy  •  Chuột trái: bắn  •  J/Chuột phải: chém  •  Q/E/F: kỹ năng  •  1-8: đổi súng",
            True, (150, 155, 185)
        )
        self.screen.blit(hint, (400 - hint.get_width() // 2, 466))

    def render(self, state, engine):
        self.tick += 1
        self._background()
        mouse = pygame.mouse.get_pos()

        if state == "MENU":
            self._render_landing(engine, mouse)

        elif state == "LEVEL_SELECT":
            self._title("CHỌN MÀN CHƠI", CYBER_BLUE, 26)
            total = sum(int(v) for v in engine.stars.values())
            page_name = "CHƯƠNG I: THÀNH PHỐ NEON (LV 1 – 8)" if self.level_page == 0 else "CHƯƠNG II: VÙNG CẤM OMEGA (LV 9 – 16)"
            st = self.small.render(f"{page_name}   |   Tổng sao: {total}/{MAX_LEVEL * 3}   |   Trang {self.level_page + 1}/2",
                                   True, CYBER_YELLOW)
            self.screen.blit(st, (400 - st.get_width() // 2, 74))

            base = self.level_page * 8
            for slot in range(8):
                lvl = base + slot + 1
                rect = self._level_rect(slot)
                unlocked = lvl <= engine.max_unlocked_level
                theme = get_map_theme(lvl, "STORY")
                is_boss = lvl in BOSS_LEVELS
                color = (CYBER_PINK if is_boss else theme["accent"]) if unlocked else GREY
                hover = unlocked and rect.collidepoint(mouse)
                fill = (42, 46, 74) if hover else (26, 28, 48)
                pygame.draw.rect(self.screen, fill, rect, border_radius=10)
                pygame.draw.rect(self.screen, color, rect, 2, border_radius=10)

                label = f"LV {lvl}" if unlocked else f"LV {lvl} (KHÓA)"
                t = self.font.render(label, True, color)
                self.screen.blit(t, (rect.centerx - t.get_width() // 2, rect.top + 10))

                zone = self.tiny.render(theme["name"], True, (180, 185, 210) if unlocked else (100, 100, 120))
                if zone.get_width() > rect.w - 12:
                    zone = pygame.transform.smoothscale(zone, (rect.w - 12, zone.get_height()))
                self.screen.blit(zone, (rect.centerx - zone.get_width() // 2, rect.top + 36))

                if is_boss and unlocked:
                    b = self.tiny.render("[ BOSS ]", True, CYBER_PINK)
                    self.screen.blit(b, (rect.centerx - b.get_width() // 2, rect.top + 54))

                got = int(engine.stars.get(str(lvl), 0))
                for s in range(3):
                    draw_star(self.screen, rect.centerx - 24 + s * 24, rect.bottom - 18, 8, s < got)

            # Nút chuyển trang & Quay lại
            self._button(self.LVL_PREV_RECT, "< TRANG 1", CYBER_BLUE if self.level_page > 0 else GREY,
                         self.level_page > 0 and self.LVL_PREV_RECT.collidepoint(mouse), font=self.small)
            self._button(self.BACK_RECT, "QUAY LẠI", RED, self.BACK_RECT.collidepoint(mouse))
            self._button(self.LVL_NEXT_RECT, "TRANG 2 >", CYBER_PINK if self.level_page < 1 else GREY,
                         self.level_page < 1 and self.LVL_NEXT_RECT.collidepoint(mouse), font=self.small)

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
            self._title("CỬA HÀNG & TÙY BIẾN", CYBER_YELLOW, 20)
            coins_txt = self.font.render(f"Coins: {engine.coins}", True, CYBER_YELLOW)
            self.screen.blit(coins_txt, (770 - coins_txt.get_width(), 28))

            tab_colors = {"UPGRADES": CYBER_YELLOW, "WEAPONS": ORANGE, "COSMETICS": CYBER_PINK}
            for key, label, tx in self.TABS:
                rect = pygame.Rect(tx, 76, 170, 38)
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
                rs = self.small.render(rb, True, CYBER_PINK if can_rb else (120, 120, 140))
                self.screen.blit(rs, (rebirth_rect.centerx - rs.get_width() // 2, rebirth_rect.centery - rs.get_height() // 2))

            elif engine.shop_tab == "WEAPONS":
                wpn_items = list(SHOP_WEAPONS.items())
                pages = max(1, (len(wpn_items) + self.WEAPONS_PER_PAGE - 1) // self.WEAPONS_PER_PAGE)
                self.weapon_page = min(self.weapon_page, pages - 1)
                start = self.weapon_page * self.WEAPONS_PER_PAGE
                visible = wpn_items[start:start + self.WEAPONS_PER_PAGE]

                for i, (wkey, (price, desc)) in enumerate(visible):
                    w = WEAPON_LIST[wkey]
                    card = pygame.Rect(55 + i * 235, 134, 220, 250)
                    pygame.draw.rect(self.screen, (28, 30, 52), card, border_radius=10)
                    pygame.draw.rect(self.screen, ORANGE, card, 2, border_radius=10)

                    name = self.font.render(w.name, True, WHITE)
                    if name.get_width() > card.w - 14:
                        name = pygame.transform.smoothscale(name, (card.w - 14, name.get_height()))
                    self.screen.blit(name, (card.centerx - name.get_width() // 2, card.y + 12))

                    img = pygame.transform.scale(w.image, (min(150, w.image.get_width() * 2),
                                                           min(44, w.image.get_height() * 2)))
                    self.screen.blit(img, (card.centerx - img.get_width() // 2, card.y + 46))

                    key_num = WEAPON_KEYS.index(wkey) + 1 if wkey in WEAPON_KEYS else "?"
                    stats = [f"Sát thương: {w.damage}", f"Băng đạn: {w.max_ammo}", f"Phím chọn: {key_num}"]
                    for j, s in enumerate(stats):
                        t = self.small.render(s, True, CYBER_BLUE)
                        self.screen.blit(t, (card.x + 14, card.y + 104 + j * 20))

                    d = self.tiny.render(desc, True, (195, 200, 220))
                    if d.get_width() > card.w - 16:
                        d = pygame.transform.smoothscale(d, (card.w - 16, d.get_height()))
                    self.screen.blit(d, (card.centerx - d.get_width() // 2, card.y + 172))

                    btn = pygame.Rect(65 + i * 235, 342, 200, 36)
                    if wkey in engine.weapons_owned:
                        self._button(btn, "ĐÃ SỞ HỮU", GREEN, font=self.small)
                    else:
                        can = engine.coins >= price
                        self._button(btn, f"MUA {price} C", CYBER_YELLOW if can else GREY,
                                     can and btn.collidepoint(mouse), font=self.small)

                # Nút chuyển trang vũ khí
                self._button(self.WPN_PREV_RECT, "< TRƯỚC", CYBER_BLUE if self.weapon_page > 0 else GREY,
                             self.weapon_page > 0 and self.WPN_PREV_RECT.collidepoint(mouse), font=self.small)
                pg = self.font.render(f"Trang {self.weapon_page + 1}/{pages}", True, CYBER_YELLOW)
                self.screen.blit(pg, (400 - pg.get_width() // 2, 400))
                self._button(self.WPN_NEXT_RECT, "SAU >", ORANGE if self.weapon_page < pages - 1 else GREY,
                             self.weapon_page < pages - 1 and self.WPN_NEXT_RECT.collidepoint(mouse), font=self.small)

            elif engine.shop_tab == "COSMETICS":
                engine.cosmetic_mgr.render(self.screen, preview_player=engine.player, tick=self.tick, coins=engine.coins)

            self._button(self.BACK_RECT, "QUAY LẠI", RED, self.BACK_RECT.collidepoint(mouse))
