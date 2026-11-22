import pygame
from font_vn import get_font
from config import CYBER_BLUE, CYBER_PINK, CYBER_YELLOW, DARK_BG, WHITE, GREEN, RED, ORANGE

PURPLE = (170, 80, 255)
CYAN_LIGHT = (140, 240, 255)


class CosmeticManager:
    SUBTABS = [
        ("HEAD", "ĐỘI", CYBER_BLUE),
        ("BODY", "COSTUME", CYBER_PINK),
        ("BACK", "CÁNH/LƯNG", PURPLE),
        ("ACCESSORY", "TRANG BỊ", CYBER_YELLOW),
    ]
    ITEMS_PER_PAGE = 5

    def __init__(self):
        self.font = get_font(15, bold=True)
        self.small_font = get_font(13)
        self.title_font = get_font(17, bold=True)
        self.current_subtab = "HEAD"
        self.page = 0

        # 1. Vật phẩm Đội (10 món)
        self.head_items = [
            {"name": "Không Đội Mũ", "visual": "NONE", "color": WHITE, "price": 0, "unlocked": True, "hp": 0, "dmg": 0, "speed": 0, "ammo": 0, "buff": "Không có"},
            {"name": "Cyber Visor", "visual": "VISOR", "color": CYBER_BLUE, "price": 100, "unlocked": False, "hp": 0, "dmg": 8, "speed": 1, "ammo": 0, "buff": "+8 DMG, +1 Spd"},
            {"name": "Mũ Giáp Thép", "visual": "HELMET", "color": (160, 170, 185), "price": 150, "unlocked": False, "hp": 35, "dmg": 0, "speed": 0, "ammo": 0, "buff": "+35 Max HP"},
            {"name": "Tai Mèo Neon", "visual": "CAT_EARS", "color": CYBER_PINK, "price": 220, "unlocked": False, "hp": 10, "dmg": 6, "speed": 2, "ammo": 15, "buff": "+2 Spd, +15 Ammo"},
            {"name": "Vương Miện Rồng", "visual": "CROWN", "color": CYBER_YELLOW, "price": 280, "unlocked": False, "hp": 15, "dmg": 15, "speed": 0, "ammo": 15, "buff": "+15 DMG/HP/Ammo"},
            {"name": "Mũ Trùm Hacker", "visual": "CYBER_HOOD", "color": (80, 255, 180), "price": 340, "unlocked": False, "hp": 15, "dmg": 14, "speed": 2, "ammo": 10, "buff": "+14 DMG, +2 Spd"},
            {"name": "Hào Quang Thánh", "visual": "HALO", "color": (255, 230, 100), "price": 400, "unlocked": False, "hp": 25, "dmg": 8, "speed": 2, "ammo": 20, "buff": "+25 HP, +2 Spd"},
            {"name": "Mũ Samurai Cyber", "visual": "SAMURAI", "color": (255, 70, 70), "price": 520, "unlocked": False, "hp": 25, "dmg": 22, "speed": 1, "ammo": 10, "buff": "+22 DMG, +25 HP"},
            {"name": "Sừng Quỷ Neon", "visual": "HORNS", "color": (255, 40, 90), "price": 650, "unlocked": False, "hp": 15, "dmg": 28, "speed": 1, "ammo": 15, "buff": "+28 DMG, +15 HP"},
            {"name": "Ăng-ten Mecha", "visual": "MECHA_ANTENNA", "color": CYBER_BLUE, "price": 850, "unlocked": False, "hp": 40, "dmg": 25, "speed": 2, "ammo": 30, "buff": "+40 HP, +25 DMG, +30 Ammo"},
        ]

        # 2. Trang phục / Costume (10 món — có tạo hình body_style riêng)
        self.body_items = [
            {"name": "Áo Thường Cyan", "style": "BASIC", "color": CYBER_BLUE, "price": 0, "unlocked": True, "hp": 0, "dmg": 0, "speed": 0, "ammo": 0, "buff": "Mặc định"},
            {"name": "Giáp Neon Armor", "style": "ARMOR", "color": (50, 255, 100), "price": 120, "unlocked": False, "hp": 40, "dmg": 0, "speed": 0, "ammo": 0, "buff": "+40 Max HP"},
            {"name": "Áo Choàng Shadow", "style": "COAT", "color": CYBER_PINK, "price": 180, "unlocked": False, "hp": 0, "dmg": 10, "speed": 2, "ammo": 0, "buff": "+2 Spd, +10 DMG"},
            {"name": "Giáp Mech Red", "style": "ARMOR", "color": (255, 60, 60), "price": 260, "unlocked": False, "hp": 25, "dmg": 18, "speed": 0, "ammo": 0, "buff": "+18 DMG, +25 HP"},
            {"name": "Đồ Ninja Bóng Đêm", "style": "NINJA", "color": (120, 130, 175), "price": 350, "unlocked": False, "hp": 15, "dmg": 20, "speed": 3, "ammo": 10, "buff": "+3 Spd, +20 DMG"},
            {"name": "Giáp Golden Legend", "style": "ARMOR", "color": CYBER_YELLOW, "price": 450, "unlocked": False, "hp": 35, "dmg": 16, "speed": 1, "ammo": 30, "buff": "+35 HP, +16 DMG, +30 Ammo"},
            {"name": "Áo Khoác Phantom", "style": "COAT", "color": (90, 210, 255), "price": 580, "unlocked": False, "hp": 40, "dmg": 24, "speed": 2, "ammo": 15, "buff": "+40 HP, +24 DMG, +2 Spd"},
            {"name": "Giáp Plasma Tím", "style": "EXO", "color": PURPLE, "price": 750, "unlocked": False, "hp": 55, "dmg": 22, "speed": 2, "ammo": 20, "buff": "+55 HP, +22 DMG, +2 Spd"},
            {"name": "Giáp Titan Exo", "style": "EXO", "color": ORANGE, "price": 950, "unlocked": False, "hp": 95, "dmg": 20, "speed": 1, "ammo": 20, "buff": "+95 HP, +20 DMG"},
            {"name": "Chiến Giáp Thiên Hà", "style": "GALAXY", "color": (110, 80, 255), "price": 1400, "unlocked": False, "hp": 80, "dmg": 35, "speed": 2, "ammo": 35, "buff": "+80 HP, +35 DMG, +35 Ammo"},
        ]

        # 3. Trang bị Lưng / Cánh / Jetpack (7 món)
        self.back_items = [
            {"name": "Không Đeo Lưng", "visual": "NONE", "color": WHITE, "price": 0, "unlocked": True, "hp": 0, "dmg": 0, "speed": 0, "ammo": 0, "jump": 0.0, "buff": "Không có"},
            {"name": "Áo Choàng Cyber", "visual": "CAPE", "color": CYBER_PINK, "price": 180, "unlocked": False, "hp": 20, "dmg": 5, "speed": 1, "ammo": 0, "jump": 0.0, "buff": "+20 HP, +5 DMG, +1 Spd"},
            {"name": "Ba Lô Phản Lực", "visual": "JETPACK", "color": ORANGE, "price": 320, "unlocked": False, "hp": 10, "dmg": 0, "speed": 2, "ammo": 10, "jump": 1.2, "buff": "+2 Spd, Nhảy cao hơn"},
            {"name": "Cánh Neon", "visual": "NEON_WINGS", "color": CYBER_BLUE, "price": 480, "unlocked": False, "hp": 30, "dmg": 14, "speed": 1, "ammo": 10, "jump": 0.8, "buff": "+30 HP, +14 DMG, +Nhảy"},
            {"name": "Động Cơ Mech", "visual": "THRUSTER", "color": (255, 80, 80), "price": 680, "unlocked": False, "hp": 35, "dmg": 22, "speed": 2, "ammo": 15, "jump": 1.0, "buff": "+35 HP, +22 DMG, +2 Spd"},
            {"name": "Dải Lụa Bóng Tối", "visual": "RIBBON", "color": PURPLE, "price": 850, "unlocked": False, "hp": 20, "dmg": 30, "speed": 3, "ammo": 10, "jump": 0.6, "buff": "+30 DMG, +3 Spd"},
            {"name": "Cánh Thiên Thần", "visual": "ANGEL_WINGS", "color": (255, 245, 200), "price": 1300, "unlocked": False, "hp": 70, "dmg": 28, "speed": 2, "ammo": 25, "jump": 1.5, "buff": "+70 HP, +28 DMG, Siêu nhảy"},
        ]

        # 4. Trang bị Phụ trợ / Chip / Hào quang (7 món)
        self.acc_items = [
            {"name": "Không Gắn Chip", "visual": "NONE", "color": WHITE, "price": 0, "unlocked": True, "hp": 0, "dmg": 0, "speed": 0, "ammo": 0, "jump": 0.0, "shield": 0, "lifesteal": 0, "buff": "Không có"},
            {"name": "Lõi Khiên Mk.I", "visual": "SHIELD_CORE", "color": CYBER_BLUE, "price": 240, "unlocked": False, "hp": 35, "dmg": 0, "speed": 0, "ammo": 0, "jump": 0.0, "shield": 60, "lifesteal": 0, "buff": "+35 HP, Khiên E +1s"},
            {"name": "Chip Sát Thương", "visual": "CRIT_CHIP", "color": RED, "price": 320, "unlocked": False, "hp": 0, "dmg": 20, "speed": 0, "ammo": 0, "jump": 0.0, "shield": 0, "lifesteal": 0, "buff": "+20 DMG mọi đòn"},
            {"name": "Giày Turbo", "visual": "TURBO_BOOTS", "color": GREEN, "price": 400, "unlocked": False, "hp": 10, "dmg": 0, "speed": 2.5, "ammo": 0, "jump": 1.2, "shield": 0, "lifesteal": 0, "buff": "+2.5 Spd, Nhảy cao"},
            {"name": "Băng Đạn Mở Rộng", "visual": "AMMO_MODULE", "color": ORANGE, "price": 450, "unlocked": False, "hp": 15, "dmg": 8, "speed": 0, "ammo": 40, "jump": 0.0, "shield": 0, "lifesteal": 0, "buff": "+40 Ammo, +8 DMG"},
            {"name": "Chip Hút Máu", "visual": "VAMP_CHIP", "color": CYBER_PINK, "price": 780, "unlocked": False, "hp": 30, "dmg": 22, "speed": 0, "ammo": 0, "jump": 0.0, "shield": 0, "lifesteal": 4, "buff": "+22 DMG, Hạ quái +4 HP"},
            {"name": "Hào Quang Omega", "visual": "OMNI_AURA", "color": CYBER_YELLOW, "price": 1500, "unlocked": False, "hp": 60, "dmg": 32, "speed": 2, "ammo": 30, "jump": 1.0, "shield": 60, "lifesteal": 3, "buff": "Toàn diện + Hút 3 HP"},
        ]

        # Slot đang đeo
        self.equipped = {
            "HEAD": 0,
            "BODY": 0,
            "BACK": 0,
            "ACCESSORY": 0,
        }

    def _items_for(self, category):
        return {
            "HEAD": self.head_items,
            "BODY": self.body_items,
            "BACK": self.back_items,
            "ACCESSORY": self.acc_items,
        }[category]

    # ---------------- LƯU / NẠP ----------------
    def export_state(self):
        return {
            "head_unlocked": [i for i, it in enumerate(self.head_items) if it["unlocked"]],
            "body_unlocked": [i for i, it in enumerate(self.body_items) if it["unlocked"]],
            "back_unlocked": [i for i, it in enumerate(self.back_items) if it["unlocked"]],
            "acc_unlocked": [i for i, it in enumerate(self.acc_items) if it["unlocked"]],
            "equipped": dict(self.equipped),
        }

    def import_state(self, state):
        if not isinstance(state, dict):
            return
        mapping = (
            ("head_unlocked", self.head_items),
            ("body_unlocked", self.body_items),
            ("back_unlocked", self.back_items),
            ("acc_unlocked", self.acc_items),
        )
        for key, items in mapping:
            for i in state.get(key, []):
                if 0 <= i < len(items):
                    items[i]["unlocked"] = True
        eq = state.get("equipped", {})
        for cat in ("HEAD", "BODY", "BACK", "ACCESSORY"):
            items = self._items_for(cat)
            idx = eq.get(cat, 0)
            if 0 <= idx < len(items) and items[idx]["unlocked"]:
                self.equipped[cat] = idx

    def get_total_buffs(self):
        """Tính tổng cộng dồn chỉ số từ cả 4 slot ĐỘI + COSTUME + LƯNG + TRANG BỊ"""
        head = self.head_items[self.equipped["HEAD"]]
        body = self.body_items[self.equipped["BODY"]]
        back = self.back_items[self.equipped["BACK"]]
        acc = self.acc_items[self.equipped["ACCESSORY"]]
        return {
            "hp": head["hp"] + body["hp"] + back["hp"] + acc["hp"],
            "dmg": head["dmg"] + body["dmg"] + back["dmg"] + acc["dmg"],
            "speed": head["speed"] + body["speed"] + back["speed"] + acc["speed"],
            "ammo": head["ammo"] + body["ammo"] + back["ammo"] + acc["ammo"],
            "jump_bonus": back.get("jump", 0.0) + acc.get("jump", 0.0),
            "shield_bonus": acc.get("shield", 0),
            "lifesteal": acc.get("lifesteal", 0),
            "head_visual": head["visual"],
            "head_color": head["color"],
            "body_color": body["color"],
            "body_style": body.get("style", "BASIC"),
            "back_visual": back["visual"],
            "back_color": back["color"],
            "acc_visual": acc["visual"],
            "acc_color": acc["color"],
            "head_name": head["name"],
            "body_name": body["name"],
            "back_name": back["name"],
            "acc_name": acc["name"],
        }

    def buy_or_equip(self, category, index, engine):
        items = self._items_for(category)
        if 0 <= index < len(items):
            item = items[index]
            changed = False
            if item["unlocked"]:
                self.equipped[category] = index
                changed = True
            elif engine.coins >= item["price"]:
                engine.coins -= item["price"]
                item["unlocked"] = True
                self.equipped[category] = index
                changed = True
                try:
                    import sfx
                    sfx.play("cash_transfer.wav", 0.5)
                except Exception:
                    pass
            if changed:
                if hasattr(engine, "sync_player_cosmetics"):
                    engine.sync_player_cosmetics()
                if hasattr(engine, "save_progress"):
                    engine.save_progress()

    def _page_count(self):
        items = self._items_for(self.current_subtab)
        return max(1, (len(items) + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE)

    def handle_click(self, pos, engine):
        x, y = pos

        # 4 nút Sub-tab (cột phải: x=245..765)
        for i, (cat, _, _) in enumerate(self.SUBTABS):
            tab_rect = pygame.Rect(245 + i * 132, 132, 126, 30)
            if tab_rect.collidepoint(x, y):
                self.current_subtab = cat
                self.page = 0
                return

        # Nút phân trang
        pages = self._page_count()
        prev_rect = pygame.Rect(425, 396, 44, 26)
        next_rect = pygame.Rect(555, 396, 44, 26)
        if prev_rect.collidepoint(x, y) and self.page > 0:
            self.page -= 1
            return
        if next_rect.collidepoint(x, y) and self.page < pages - 1:
            self.page += 1
            return

        # Click mua/đeo trên trang hiện tại
        items = self._items_for(self.current_subtab)
        start = self.page * self.ITEMS_PER_PAGE
        for slot in range(self.ITEMS_PER_PAGE):
            idx = start + slot
            if idx >= len(items):
                break
            cy = 172 + slot * 43
            btn_rect = pygame.Rect(658, cy + 5, 100, 28)
            if btn_rect.collidepoint(x, y):
                self.buy_or_equip(self.current_subtab, idx, engine)
                return

    def render(self, screen, preview_player=None, tick=0, coins=0):
        total = self.get_total_buffs()

        # --- CỘT TRÁI: KHUNG PREVIEW NHÂN VẬT TRỰC TIẾP ---
        panel = pygame.Rect(30, 132, 200, 290)
        pygame.draw.rect(screen, (22, 24, 42), panel, border_radius=12)
        pygame.draw.rect(screen, CYBER_BLUE, panel, 2, border_radius=12)

        hdr = self.font.render("NHÂN VẬT CỦA BẠN", True, CYBER_BLUE)
        screen.blit(hdr, (panel.centerx - hdr.get_width() // 2, panel.y + 8))

        # Bệ đứng neon
        stage = pygame.Rect(panel.x + 16, panel.y + 32, panel.w - 32, 148)
        pygame.draw.rect(screen, (14, 16, 30), stage, border_radius=8)
        pygame.draw.rect(screen, (45, 55, 85), stage, 1, border_radius=8)
        pygame.draw.ellipse(screen, (0, 160, 210), (stage.centerx - 48, stage.bottom - 22, 96, 14), 2)

        if preview_player is not None and hasattr(preview_player, "draw_preview"):
            preview_player.draw_preview(screen, stage.centerx, stage.bottom - 14, scale=2.1, tick=tick)

        # Tổng buff dưới khung preview
        stats_lines = [
            (f"HP +{total['hp']}   |   DMG +{total['dmg']}", CYBER_YELLOW),
            (f"SPD +{total['speed']:.1f}  |   AMMO +{total['ammo']}", CYBER_BLUE),
            (f"Đội: {total['head_name']}", WHITE),
            (f"Mặc: {total['body_name']}", WHITE),
            (f"Lưng: {total['back_name']}", (200, 180, 255)),
            (f"Chip: {total['acc_name']}", (180, 255, 200)),
        ]
        for i, (txt, col) in enumerate(stats_lines):
            surf = self.small_font.render(txt, True, col)
            if surf.get_width() > panel.w - 16:
                surf = pygame.transform.smoothscale(surf, (panel.w - 16, surf.get_height()))
            screen.blit(surf, (panel.x + 10, panel.y + 188 + i * 16))

        # --- CỘT PHẢI: 4 SUB-TAB ---
        for i, (cat, label, col) in enumerate(self.SUBTABS):
            tab_rect = pygame.Rect(245 + i * 132, 132, 126, 30)
            active = self.current_subtab == cat
            bg = (45, 48, 78) if active else (24, 24, 40)
            bd = col if active else (70, 70, 90)
            pygame.draw.rect(screen, bg, tab_rect, border_radius=6)
            pygame.draw.rect(screen, bd, tab_rect, 2 if active else 1, border_radius=6)
            t = self.font.render(label, True, col if active else WHITE)
            screen.blit(t, (tab_rect.centerx - t.get_width() // 2, tab_rect.centery - t.get_height() // 2))

        # --- DANH SÁCH VẬT PHẨM (5 món / trang) ---
        items = self._items_for(self.current_subtab)
        equipped_idx = self.equipped[self.current_subtab]
        pages = self._page_count()
        self.page = min(self.page, pages - 1)
        start = self.page * self.ITEMS_PER_PAGE

        for slot in range(self.ITEMS_PER_PAGE):
            idx = start + slot
            if idx >= len(items):
                break
            item = items[idx]
            cy = 172 + slot * 43
            row_rect = pygame.Rect(245, cy, 522, 38)
            pygame.draw.rect(screen, (30, 32, 54), row_rect, border_radius=8)
            if equipped_idx == idx:
                pygame.draw.rect(screen, CYBER_YELLOW, row_rect, 2, border_radius=8)
            else:
                pygame.draw.rect(screen, (60, 62, 86), row_rect, 1, border_radius=8)

            # Icon màu
            pygame.draw.circle(screen, item["color"], (267, cy + 19), 10)
            pygame.draw.circle(screen, WHITE, (267, cy + 19), 10, 1)

            # Tên & Buff
            name_txt = self.font.render(item["name"], True, WHITE)
            buff_txt = self.small_font.render(item["buff"], True, CYAN_LIGHT)
            screen.blit(name_txt, (286, cy + 3))
            screen.blit(buff_txt, (286, cy + 20))

            # Nút Mua / Trang bị
            btn_rect = pygame.Rect(658, cy + 5, 100, 28)
            if equipped_idx == idx:
                pygame.draw.rect(screen, GREEN, btn_rect, border_radius=6)
                st_txt = self.font.render("ĐANG ĐEO", True, DARK_BG)
            elif item["unlocked"]:
                pygame.draw.rect(screen, CYBER_BLUE, btn_rect, border_radius=6)
                st_txt = self.font.render("ĐEO", True, DARK_BG)
            else:
                can_buy = coins >= item["price"]
                pygame.draw.rect(screen, CYBER_YELLOW if can_buy else (75, 75, 95), btn_rect, border_radius=6)
                st_txt = self.font.render(f"{item['price']} C", True, DARK_BG if can_buy else (170, 170, 190))

            screen.blit(st_txt, (btn_rect.centerx - st_txt.get_width() // 2, btn_rect.centery - st_txt.get_height() // 2))

        # --- THANH PHÂN TRANG ---
        prev_rect = pygame.Rect(425, 396, 44, 26)
        next_rect = pygame.Rect(555, 396, 44, 26)
        for rect, lbl, enabled in ((prev_rect, "<", self.page > 0), (next_rect, ">", self.page < pages - 1)):
            pygame.draw.rect(screen, (40, 44, 70) if enabled else (24, 24, 38), rect, border_radius=6)
            pygame.draw.rect(screen, CYBER_BLUE if enabled else (65, 65, 85), rect, 1, border_radius=6)
            t = self.font.render(lbl, True, WHITE if enabled else (100, 100, 120))
            screen.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))

        pg_txt = self.font.render(f"{self.page + 1} / {pages}", True, CYBER_YELLOW)
        screen.blit(pg_txt, (512 - pg_txt.get_width() // 2, 400))
