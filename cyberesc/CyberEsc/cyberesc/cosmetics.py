import pygame
from font_vn import get_font
from config import CYBER_BLUE, CYBER_PINK, CYBER_YELLOW, DARK_BG, WHITE, GREEN, RED

class CosmeticManager:
    def __init__(self):
        self.font = get_font(16, bold=True)
        self.title_font = get_font(18, bold=True)
        self.current_subtab = "HEAD"  # "HEAD" (Đội) hoặc "BODY" (Mặc)

        # Danh sách Vật phẩm Đội (Mũ, Visor, Vương miện, Hào quang)
        self.head_items = [
            {"name": "Không Đội Mũ", "visual": "NONE", "color": WHITE, "price": 0, "unlocked": True, "hp": 0, "dmg": 0, "speed": 0, "ammo": 0, "buff": "Không có"},
            {"name": "Cyber Visor", "visual": "VISOR", "color": CYBER_BLUE, "price": 100, "unlocked": False, "hp": 0, "dmg": 8, "speed": 1, "ammo": 0, "buff": "+8 DMG, +1 Speed"},
            {"name": "Mũ Giáp Thép", "visual": "HELMET", "color": (150, 150, 160), "price": 150, "unlocked": False, "hp": 35, "dmg": 0, "speed": 0, "ammo": 0, "buff": "+35 Max HP"},
            {"name": "Vương Miện Rồng", "visual": "CROWN", "color": CYBER_YELLOW, "price": 280, "unlocked": False, "hp": 15, "dmg": 15, "speed": 0, "ammo": 15, "buff": "+15 DMG, +15 HP, +15 Ammo"},
            {"name": "Hào Quang Thánh", "visual": "HALO", "color": (255, 230, 100), "price": 350, "unlocked": False, "hp": 20, "dmg": 0, "speed": 2, "ammo": 20, "buff": "+20 HP, +2 Speed, +20 Ammo"},
            {"name": "Sừng Quỷ Neon", "visual": "HORNS", "color": (255, 40, 90), "price": 600, "unlocked": False, "hp": 10, "dmg": 25, "speed": 1, "ammo": 10, "buff": "+25 DMG, +10 HP, +1 Speed, +10 Ammo"}
        ]

        # Danh sách Vật phẩm Mặc (Trang phục, Áo giáp, Choàng)
        self.body_items = [
            {"name": "Áo Thường Cyan", "color": CYBER_BLUE, "price": 0, "unlocked": True, "hp": 0, "dmg": 0, "speed": 0, "ammo": 0, "buff": "Không có"},
            {"name": "Giáp Neon Armor", "color": (50, 255, 100), "price": 120, "unlocked": False, "hp": 40, "dmg": 0, "speed": 0, "ammo": 0, "buff": "+40 Max HP"},
            {"name": "Áo Choàng Pink Shadow", "color": CYBER_PINK, "price": 180, "unlocked": False, "hp": 0, "dmg": 10, "speed": 2, "ammo": 0, "buff": "+2 Speed, +10 DMG"},
            {"name": "Giáp Mech Red", "color": (255, 60, 60), "price": 250, "unlocked": False, "hp": 25, "dmg": 18, "speed": 0, "ammo": 0, "buff": "+18 DMG, +25 HP"},
            {"name": "Giáp Golden Legend", "color": CYBER_YELLOW, "price": 400, "unlocked": False, "hp": 30, "dmg": 15, "speed": 1, "ammo": 30, "buff": "+30 HP, +15 DMG, +30 Ammo"},
            {"name": "Giáp Plasma Tím", "color": (170, 80, 255), "price": 700, "unlocked": False, "hp": 50, "dmg": 20, "speed": 2, "ammo": 20, "buff": "+50 HP, +20 DMG, +2 Speed, +20 Ammo"}
        ]

        # Slot đang đeo
        self.equipped = {
            "HEAD": 0,
            "BODY": 0
        }

    # ---------------- LƯU / NẠP ----------------
    def export_state(self):
        return {
            "head_unlocked": [i for i, it in enumerate(self.head_items) if it["unlocked"]],
            "body_unlocked": [i for i, it in enumerate(self.body_items) if it["unlocked"]],
            "equipped": dict(self.equipped),
        }

    def import_state(self, state):
        if not isinstance(state, dict):
            return
        for i in state.get("head_unlocked", []):
            if 0 <= i < len(self.head_items):
                self.head_items[i]["unlocked"] = True
        for i in state.get("body_unlocked", []):
            if 0 <= i < len(self.body_items):
                self.body_items[i]["unlocked"] = True
        eq = state.get("equipped", {})
        for cat, items in (("HEAD", self.head_items), ("BODY", self.body_items)):
            idx = eq.get(cat, 0)
            if 0 <= idx < len(items) and items[idx]["unlocked"]:
                self.equipped[cat] = idx

    def get_total_buffs(self):
        """Tính tổng cộng dồn chỉ số từ đồ ĐỘI + đồ MẶC"""
        head = self.head_items[self.equipped["HEAD"]]
        body = self.body_items[self.equipped["BODY"]]
        return {
            "hp": head["hp"] + body["hp"],
            "dmg": head["dmg"] + body["dmg"],
            "speed": head["speed"] + body["speed"],
            "ammo": head["ammo"] + body["ammo"],
            "head_visual": head["visual"],
            "body_color": body["color"]
        }

    def buy_or_equip(self, category, index, engine):
        items = self.head_items if category == "HEAD" else self.body_items
        if 0 <= index < len(items):
            item = items[index]
            if item["unlocked"]:
                self.equipped[category] = index
            elif engine.coins >= item["price"]:
                engine.coins -= item["price"]
                item["unlocked"] = True
                self.equipped[category] = index
            if hasattr(engine, "save_progress"):
                engine.save_progress()

    def handle_click(self, pos, engine):
        x, y = pos

        # Chuyển Sub-tab ĐỘI / MẶC
        if 100 <= x <= 250 and 145 <= y <= 175:
            self.current_subtab = "HEAD"
            return
        elif 270 <= x <= 420 and 145 <= y <= 175:
            self.current_subtab = "BODY"
            return

        # Click mua/đeo đồ theo Sub-tab
        items = self.head_items if self.current_subtab == "HEAD" else self.body_items
        for idx in range(len(items)):
            cy = 185 + idx * 40
            btn_rect = pygame.Rect(600, cy + 4, 110, 28)
            if btn_rect.collidepoint(x, y):
                self.buy_or_equip(self.current_subtab, idx, engine)

    def render(self, screen):
        # --- THÔNG TIN TỔNG BUFF ĐANG KẾT HỢP ---
        total = self.get_total_buffs()
        summary_txt = f"Tổng Buff đang đeo: HP +{total['hp']} | DMG +{total['dmg']} | Speed +{total['speed']} | Ammo +{total['ammo']}"
        sum_surf = self.font.render(summary_txt, True, CYBER_YELLOW)
        screen.blit(sum_surf, (400 - sum_surf.get_width() // 2, 123))

        # --- NÚT CHUYỂN SUB-TAB (ĐỘI / MẶC) ---
        btn_head = pygame.Rect(100, 145, 150, 30)
        btn_body = pygame.Rect(270, 145, 150, 30)

        bg_h = (50, 50, 80) if self.current_subtab == "HEAD" else (25, 25, 40)
        bd_h = CYBER_BLUE if self.current_subtab == "HEAD" else (70, 70, 90)
        pygame.draw.rect(screen, bg_h, btn_head, border_radius=6)
        pygame.draw.rect(screen, bd_h, btn_head, 2, border_radius=6)
        txt_h = self.font.render("VẬT PHẨM ĐỘI", True, WHITE)
        screen.blit(txt_h, (btn_head.centerx - txt_h.get_width() // 2, btn_head.centery - txt_h.get_height() // 2))

        bg_b = (50, 50, 80) if self.current_subtab == "BODY" else (25, 25, 40)
        bd_b = CYBER_PINK if self.current_subtab == "BODY" else (70, 70, 90)
        pygame.draw.rect(screen, bg_b, btn_body, border_radius=6)
        pygame.draw.rect(screen, bd_b, btn_body, 2, border_radius=6)
        txt_b = self.font.render("VẬT PHẨM MẶC", True, WHITE)
        screen.blit(txt_b, (btn_body.centerx - txt_b.get_width() // 2, btn_body.centery - txt_b.get_height() // 2))

        # --- DANH SÁCH VẬT PHẨM ---
        items = self.head_items if self.current_subtab == "HEAD" else self.body_items
        equipped_idx = self.equipped[self.current_subtab]

        for idx, item in enumerate(items):
            cy = 185 + idx * 40
            row_rect = pygame.Rect(80, cy, 640, 36)
            pygame.draw.rect(screen, (30, 30, 50), row_rect, border_radius=8)

            if equipped_idx == idx:
                pygame.draw.rect(screen, CYBER_YELLOW, row_rect, 2, border_radius=8)
            else:
                pygame.draw.rect(screen, (60, 60, 80), row_rect, 1, border_radius=8)

            # Preview Màu / Icon
            pygame.draw.circle(screen, item["color"], (110, cy + 18), 11)
            pygame.draw.circle(screen, WHITE, (110, cy + 18), 11, 1)

            # Tên & Buff
            name_txt = self.font.render(item["name"], True, WHITE)
            buff_txt = self.font.render(f"Buff: {item['buff']}", True, CYBER_BLUE)
            screen.blit(name_txt, (135, cy + 9))
            screen.blit(buff_txt, (310, cy + 9))

            # Nút Mua / Trang bị
            btn_rect = pygame.Rect(600, cy + 4, 110, 28)
            if equipped_idx == idx:
                pygame.draw.rect(screen, GREEN, btn_rect, border_radius=6)
                st_txt = self.font.render("EQUIPPED", True, DARK_BG)
            elif item["unlocked"]:
                pygame.draw.rect(screen, CYBER_BLUE, btn_rect, border_radius=6)
                st_txt = self.font.render("EQUIP", True, DARK_BG)
            else:
                pygame.draw.rect(screen, CYBER_YELLOW, btn_rect, border_radius=6)
                st_txt = self.font.render(f"{item['price']} C", True, DARK_BG)

            screen.blit(st_txt, (btn_rect.centerx - st_txt.get_width() // 2, btn_rect.centery - st_txt.get_height() // 2))