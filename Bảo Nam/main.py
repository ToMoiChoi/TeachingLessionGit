"""Chú Thuật Hồi Chiến: Đại Chiến Chú Thuật (Jujutsu Kaisen 2D Arena) - Bảo Nam."""

import asyncio
import math
import random
import sys
import pygame

from config import (
    WIDTH, HEIGHT, FPS, GROUND_Y, ARENA_LEFT, ARENA_RIGHT, START_GOLD,
    WHITE, BLACK, RED, CRIMSON, GREEN, RCT_GREEN, BLUE, LAPSE_BLUE,
    REVERSAL_RED, HOLLOW_PURPLE, CYAN, YELLOW, GOLD, PURPLE, PINK, ORANGE,
    FONT_MED, clamp, play_sound
)
from levels import CHARACTERS, MAPS, LEVELS, SHOP_ITEMS
from entities import Particle, LightningBolt, Projectile, Shikigami, Fighter
from fighter import draw_arena_background, draw_jjk_fighter, draw_projectile, draw_shikigami
from ui import (
    draw_menu, draw_map_select, draw_character_select,
    draw_shop, draw_guide, draw_hud, draw_gameover
)
import luu_tru

SAVE_KEY = "baonam_jjk_v2"


class JujutsuArena:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Chú Thuật Hồi Chiến: Đại Chiến Chú Thuật - Bảo Nam")
        self.clock = pygame.time.Clock()
        self.dim_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        self.characters = CHARACTERS
        self.maps = MAPS
        self.levels = LEVELS
        self.shop_items = SHOP_ITEMS

        self.state = "MENU"
        self.prev_state = "MENU"
        self.ui_buttons = []
        self.anim_time = 0.0

        # Đọc dữ liệu lưu trữ (tương thích cả Web localStorage & Desktop JSON)
        saved = luu_tru.doc(SAVE_KEY, {
            "gold": START_GOLD,
            "weapon_level": 1,
            "crit_level": 1,
            "armor_level": 1,
            "ce_level": 1,
            "level_index": 0,
            "char_index": 0,
            "map_index": 0,
        })
        self.gold = int(saved.get("gold", START_GOLD))
        self.weapon_level = int(saved.get("weapon_level", 1))
        self.crit_level = int(saved.get("crit_level", 1))
        self.armor_level = int(saved.get("armor_level", 1))
        self.ce_level = int(saved.get("ce_level", 1))
        self.current_level_index = int(clamp(saved.get("level_index", 0), 0, len(LEVELS) - 1))
        self.selected_class_index = int(clamp(saved.get("char_index", 0), 0, len(CHARACTERS) - 1))
        self.selected_map_index = int(clamp(saved.get("map_index", 0), 0, len(MAPS) - 1))

        cls = CHARACTERS[self.selected_class_index]
        self.player = Fighter(
            cls["id"], cls["name"], cls["color"], cls["hp"],
            cls["speed"], cls["max_ce"], cls["technique"], cls["domain_name"]
        )

        lv = LEVELS[self.current_level_index]
        self.enemy = Fighter(
            lv["boss_id"], lv["boss_name"], lv["boss_color"],
            lv["boss_hp"], lv["boss_speed"], 130, lv["boss_tech"], lv["boss_domain"]
        )

        self.apply_selected_character()
        self.load_current_level_boss()

        # Trạng thái Bành Trướng Lãnh Địa (Domain Expansion)
        self.domain_state = {
            "active": False,
            "owner": None,
            "char_id": "",
            "name": "",
            "timer": 0.0,
            "tick": 0.0,
            "clash": False,
        }

        self.projectiles = []
        self.shikigamis = []
        self.particles = []
        self.lightnings = []
        self.blood_stains = []
        self.floating_texts = []

        self.black_flash_flash = 0.0
        self.screen_shake = 0.0
        self.message = ""
        self.winner = None
        self.match_black_flashes = 0
        self.match_domains = 0

        # Biến AI của Boss
        self.bot_attack_cd = 0.5
        self.bot_special_cd = 2.2
        self.bot_def_cd = 2.0

    # ============================================================
    # LƯU TRỮ & CẬP NHẬT CHỈ SỐ NHÂN VẬT / BOSS
    # ============================================================

    def save_progress(self):
        luu_tru.ghi(SAVE_KEY, {
            "gold": self.gold,
            "weapon_level": self.weapon_level,
            "crit_level": self.crit_level,
            "armor_level": self.armor_level,
            "ce_level": self.ce_level,
            "level_index": self.current_level_index,
            "char_index": self.selected_class_index,
            "map_index": self.selected_map_index,
        })

    def apply_selected_character(self):
        cls = self.characters[self.selected_class_index]
        self.player.char_id = cls["id"]
        self.player.name = cls["name"]
        self.player.technique = cls["technique"]
        self.player.domain_name = cls["domain_name"]
        self.player.color = cls["color"]
        self.player.secondary = cls["secondary"]
        bonus_hp = (self.armor_level - 1) * 150
        self.player.max_hp = float(cls["hp"] + bonus_hp)
        self.player.hp = self.player.max_hp
        self.player.max_ce = float(cls["max_ce"] + (self.ce_level - 1) * 12)
        self.player.ce = self.player.max_ce
        self.player.speed = float(cls["speed"])
        self.player.max_rct_uses = 4 + (self.ce_level - 1)
        self.player.rct_uses = self.player.max_rct_uses

    def load_current_level_boss(self):
        lv = self.levels[self.current_level_index]
        self.enemy.char_id = lv["boss_id"]
        self.enemy.name = lv["boss_name"]
        self.enemy.technique = lv["boss_tech"]
        self.enemy.domain_name = lv["boss_domain"]
        self.enemy.color = lv["boss_color"]
        self.enemy.max_hp = float(lv["boss_hp"])
        self.enemy.hp = self.enemy.max_hp
        self.enemy.speed = float(lv["boss_speed"])
        self.enemy.max_ce = 140.0
        self.enemy.ce = 140.0
        self.enemy.max_rct_uses = 3 if lv["id"] >= 4 else 2
        self.enemy.rct_uses = self.enemy.max_rct_uses

    def buy_upgrade(self, key):
        item = next((it for it in self.shop_items if it["key"] == key), None)
        if not item:
            return
        cur_lv = getattr(self, f"{key}_level")
        cost = item["cost"] + (cur_lv - 1) * 400
        if self.gold >= cost:
            self.gold -= cost
            setattr(self, f"{key}_level", cur_lv + 1)
            self.apply_selected_character()
            self.save_progress()
            play_sound("buy")
            self.message = f"Đã cường hóa {item['name']} lên Cấp {cur_lv + 1}!"
        else:
            self.message = f"Chưa đủ Điểm Chú Thuật (Cần {cost} P)!"

    # ============================================================
    # HIỆU ỨNG HÌNH ẢNH (HẮC THIỂM, CHÚ LỰC, CHỮ NỔI)
    # ============================================================

    def add_floating_text(self, text, x, y, color=GOLD):
        fy = min(float(y), GROUND_Y - 148.0)
        fx = clamp(float(x), 135.0, WIDTH - 135.0)
        for ft in self.floating_texts:
            if abs(ft["x"] - fx) < 160 and abs(ft["y"] - fy) < 24:
                fy = ft["y"] - 25.0
        self.floating_texts.append({
            "text": str(text),
            "x": fx,
            "y": max(145.0, fy),
            "color": color,
            "life": 1.15,
        })

    def spawn_particles(self, x, y, color, count=18, gravity=520, shape="circle"):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, gravity=gravity, shape=shape))

    def spawn_black_flash_vfx(self, x, y):
        """Hiệu ứng tia sét Đen-Đỏ trứ danh của Hắc Thiểm (Black Flash)!"""
        self.black_flash_flash = 0.16
        self.screen_shake = 0.25
        play_sound("black_flash")
        for i in range(7):
            ang = i * (math.pi * 2 / 7) + random.uniform(-0.25, 0.25)
            dist = random.uniform(95, 175)
            x2 = x + math.cos(ang) * dist
            y2 = y + math.sin(ang) * dist
            self.lightnings.append(
                LightningBolt(x, y, x2, y2, outer_color=(245, 25, 55), inner_color=(8, 8, 12), life=0.38, width=7)
            )
        self.spawn_particles(x, y, REVERSAL_RED, count=28, shape="slash")
        self.spawn_particles(x, y, BLACK, count=18, shape="square")

    def spawn_blood_stain(self, x, color=(135, 16, 32)):
        self.blood_stains.append({
            "x": x + random.uniform(-35, 35),
            "w": random.randint(22, 48),
            "h": random.randint(7, 14),
            "color": color,
        })
        if len(self.blood_stains) > 65:
            self.blood_stains = self.blood_stains[-65:]

    # ============================================================
    # HỆ THỐNG SÁT THƯƠNG & CƠ CHẾ PHÒNG THỦ CHÚ THUẬT
    # ============================================================

    def deal_damage(self, attacker, defender, damage, sure_hit=False, is_skill=False, tag=None):
        if not defender.alive or self.state != "PLAYING":
            return False

        # Nếu chủ nhân đang mở Lãnh Địa (không bị Giằng Co), mọi đòn đều mang tính Trúng Đích Tuyệt Đối
        if self.domain_state["active"] and not self.domain_state["clash"] and self.domain_state["owner"] is attacker:
            sure_hit = True

        # 1. Kiểm tra Giản Dị Lãnh Địa vô hiệu hóa Sure-Hit!
        if sure_hit and defender.simple_domain_timer > 0:
            if tag == "domain_tick":
                play_sound("shield_hit")
                self.spawn_particles(defender.x, defender.y - 55, CYAN, count=12)
                self.add_floating_text("GIẢN DỊ LĐ: CHẶN SURE-HIT!", defender.x, defender.y - 125, CYAN)
                return False
            sure_hit = False  # Hạ đòn đánh thường về trạng thái có thể giảm sát thương

        # 2. Kiểm tra Né & Parry (nếu không phải Trúng Đích Tuyệt Đối)
        if not sure_hit:
            if defender.dodge_timer > 0:
                play_sound("dash")
                self.spawn_particles(defender.x, defender.y - 55, CYAN, count=12)
                self.add_floating_text("NÉ ĐÒN!", defender.x, defender.y - 115, CYAN)
                return False

            if defender.parry_timer > 0:
                play_sound("parry")
                attacker.stun_timer = max(attacker.stun_timer, 1.05)
                defender.domain_gauge = min(100.0, defender.domain_gauge + 14.0)
                defender.ce = min(defender.max_ce, defender.ce + 18.0)
                self.spawn_particles(defender.x, defender.y - 60, WHITE, count=20)
                self.add_floating_text("PHẢN ĐÒN TÂN ÂM LƯU!", defender.x, defender.y - 120, WHITE)
                return False

        # 3. Tính hệ số Khuếch Đại của người tấn công
        mult = 1.0
        if attacker.zone_timer > 0:
            mult *= 1.20  # Zone Hắc Thiểm 120% tiềm năng!
        if attacker.overtime_timer > 0:
            mult *= 1.30  # Nanami Tăng Ca!
        if attacker.char_id == "sukuna" and is_skill:
            mult *= 1.15  # Nội tại Vua Nguyền Rủa
        if self.domain_state["active"] and self.domain_state["owner"] is attacker and not self.domain_state["clash"]:
            mult *= 1.20  # Cường hóa thuật thức trong Lãnh Địa

        # Toji cầm Thiên Nghịch Mâu chém trúng làm suy yếu Giản Dị Lãnh Địa
        if attacker.char_id == "toji" and defender.simple_domain_timer > 0:
            defender.simple_domain_timer = max(0.0, defender.simple_domain_timer - 1.2)
            self.add_floating_text("THIÊN NGHỊCH MÂU PHÁ CHIÊU!", defender.x, defender.y - 135, CYAN)

        # 4. Tính hệ số Giảm Sát Thương của người phòng thủ
        if defender.char_id == "gojo":
            mult *= 0.85  # Nội tại Vô Hạ Hạn
        if defender.simple_domain_timer > 0:
            mult *= 0.45  # Giản Dị Lãnh Địa giảm mạnh sát thương nhận vào
        if defender.is_crouching:
            mult *= 0.80
        if defender is self.player:
            armor_red = max(0.45, 1.0 - (self.armor_level - 1) * 0.05)
            mult *= armor_red

        real_dmg = max(1.0, damage * mult)

        # Hấp thụ qua Khiên Chú Lực Rika / Vô Hạ Hạn nếu có
        if defender.shield_hp > 0:
            absorbed = min(defender.shield_hp, real_dmg)
            defender.shield_hp -= absorbed
            real_dmg -= absorbed
            if real_dmg <= 0:
                self.add_floating_text("KHIÊN CHÚ LỰC CHẶN!", defender.x, defender.y - 110, PINK)
                return True

        defender.hp -= real_dmg
        defender.hit_flash = 0.14
        self.screen_shake = max(self.screen_shake, 0.09)

        # Tích thanh Bành Trướng Lãnh Địa cho cả 2 bên
        gain_atk = 7.5 * (1.0 + (self.ce_level - 1) * 0.12 if attacker is self.player else 1.0)
        attacker.domain_gauge = min(100.0, attacker.domain_gauge + gain_atk)
        defender.domain_gauge = min(100.0, defender.domain_gauge + 4.5)

        if tag == "black_flash":
            self.add_floating_text(f"HẮC THIỂM! -{int(real_dmg)}", defender.x, defender.y - 130, REVERSAL_RED)
        elif tag == "ratio_crit":
            self.add_floating_text(f"7:3 CHÍ MẠNG! -{int(real_dmg)}", defender.x, defender.y - 122, GOLD)
        elif tag == "resonance":
            self.add_floating_text(f"CỘNG HƯỞNG! -{int(real_dmg)}", defender.x, defender.y - 125, ORANGE)
        elif tag != "domain_tick":
            self.add_floating_text(f"-{int(real_dmg)}", defender.x + random.uniform(-18, 18), defender.y - 98, WHITE)

        self.spawn_particles(defender.x, defender.y - 58, attacker.color, count=14)
        self.spawn_blood_stain(defender.x)

        if defender.hp <= 0:
            defender.hp = 0
            defender.alive = False
            self.spawn_particles(defender.x, defender.y - 55, REVERSAL_RED, count=45)
            self.end_game(defender is self.enemy)
        return True

    # ============================================================
    # KỸ NĂNG CHUNG: GIẢN DỊ LÃNH ĐỊA, NGHỊCH CHUYỂN & BÀNH TRƯỚNG LÃNH ĐỊA
    # ============================================================

    def use_simple_domain(self, fighter):
        """[Z] Giản Dị Lãnh Địa (Simple Domain): Parry đầu chiêu + Vô hiệu hóa Sure-Hit."""
        if not fighter.alive or fighter.stun_timer > 0 or fighter.simple_cd > 0 or fighter.ce < 16:
            return
        fighter.ce -= 16
        fighter.simple_cd = 3.6
        fighter.parry_timer = 0.45
        fighter.simple_domain_timer = 2.8
        play_sound("simple_domain")
        self.spawn_particles(fighter.x, GROUND_Y - 10, CYAN, count=18, gravity=-160)
        self.add_floating_text("GIẢN DỊ LÃNH ĐỊA!", fighter.x, fighter.y - 115, CYAN)

    def use_rct(self, fighter):
        """[X] Nghịch Chuyển Thuật Thức (Reverse Cursed Technique): Hồi phục cơ thể."""
        if not fighter.alive or fighter.rct_uses <= 0 or fighter.rct_heal_left > 0:
            return
        if fighter.hp >= fighter.max_hp - 5 and fighter.stun_timer <= 0:
            return
        fighter.rct_uses -= 1
        fighter.ce = max(0.0, fighter.ce - 20.0)
        fighter.stun_timer = 0.0
        fighter.slow_timer = 0.0
        heal_total = 340.0 + ((self.armor_level - 1) * 50.0 if fighter is self.player else 0.0)
        fighter.rct_heal_left = heal_total
        fighter.rct_timer = 1.8
        play_sound("rct")
        self.spawn_particles(fighter.x, fighter.y - 50, RCT_GREEN, count=26, gravity=-220)
        self.add_floating_text(f"NGHỊCH CHUYỂN THUẬT THỨC (+{int(heal_total)})", fighter.x, fighter.y - 125, RCT_GREEN)

    def activate_domain_expansion(self, caster):
        """[R] Bành Trướng Lãnh Địa (Domain Expansion)!"""
        if not caster.alive or caster.stun_timer > 0 or caster.domain_gauge < 100.0:
            return
        caster.domain_gauge = 0.0
        play_sound("domain")
        self.screen_shake = 0.35
        self.spawn_particles(caster.x, caster.y - 60, caster.color, count=42, gravity=-80)

        if caster is self.player:
            self.match_domains += 1

        # Nếu đối phương ĐANG mở Lãnh Địa -> Nổ ra GIẰNG CO LÃNH ĐỊA (DOMAIN CLASH)!
        if self.domain_state["active"] and self.domain_state["owner"] is not caster:
            self.domain_state["clash"] = True
            self.domain_state["timer"] = 4.5
            self.add_floating_text("GIẰNG CO LÃNH ĐỊA - TRIỆT TIÊU SURE-HIT!", WIDTH // 2, 165, GOLD)
            return

        self.domain_state = {
            "active": True,
            "owner": caster,
            "char_id": caster.char_id,
            "name": caster.domain_name,
            "timer": 6.5,
            "tick": 0.35,
            "clash": False,
        }
        self.add_floating_text(f"BÀNH TRƯỚNG LÃNH ĐỊA: {caster.domain_name.upper()}!", caster.x, caster.y - 145, GOLD)

    def _apply_domain_sure_hit(self, owner, target):
        """Đòn đánh Trúng Đích Tuyệt Đối mỗi nhịp bên trong Bành Trướng Lãnh Địa."""
        cid = owner.char_id
        base = 58.0 + ((self.weapon_level - 1) * 8.0 if owner is self.player else 0.0)

        hit_ok = self.deal_damage(owner, target, base, sure_hit=True, is_skill=True, tag="domain_tick")
        if not hit_ok or not target.alive:
            return

        if cid == "gojo":
            target.stun_timer = max(target.stun_timer, 0.38)
            self.spawn_particles(target.x, target.y - 65, LAPSE_BLUE, count=14)
            self.add_floating_text("VÔ LƯỢNG KHÔNG XỬ!", target.x, target.y - 115, LAPSE_BLUE)
        elif cid in ("sukuna", "heian_sukuna"):
            play_sound("light")
            self.projectiles.append(
                Projectile(owner, "cleave_web", target.x, target.y - 58, 0, 0, damage=0, radius=32, life=0.22, color=REVERSAL_RED)
            )
            self.add_floating_text("BỔ & PHÂN!", target.x, target.y - 115, REVERSAL_RED)
        elif cid == "megumi":
            target.slow_timer = max(target.slow_timer, 1.0)
            self.spawn_particles(target.x, GROUND_Y - 8, (70, 120, 255), count=16, gravity=-180)
            self.add_floating_text("KHẢM ÁM NUỐT CHỬNG!", target.x, target.y - 115, CYAN)
        elif cid == "yuta":
            self.lightnings.append(
                LightningBolt(target.x, 60, target.x, target.y - 50, outer_color=PINK, inner_color=WHITE, life=0.25, width=5)
            )
            self.add_floating_text("KIẾM SAO CHÉP!", target.x, target.y - 115, PINK)
        elif cid == "inumaki":
            target.stun_timer = max(target.stun_timer, 0.28)
            self.add_floating_text("CHÚ NGÔN VANG VỌNG!", target.x, target.y - 115, PURPLE)
        elif cid == "kamo":
            owner.red_scale_timer = max(owner.red_scale_timer, 1.5)
            self.lightnings.append(
                LightningBolt(target.x - 40, 50, target.x, target.y - 55, outer_color=CRIMSON, inner_color=RED, life=0.24, width=5)
            )
        elif cid == "nobara":
            target.nail_stacks = min(6, target.nail_stacks + 1)
            self.add_floating_text("ĐINH CỘNG HƯỞNG!", target.x, target.y - 115, ORANGE)
        elif cid == "nanami":
            self.add_floating_text("7 : 3 TẤT TRÚNG!", target.x, target.y - 115, GOLD)
        else:
            self.spawn_particles(target.x, target.y - 60, owner.color, count=16)

    # ============================================================
    # HỆ THỐNG CHIÊU THỨC CỦA 8 NHÂN VẬT & 5 BOSS ([E], [Y], [C], [F])
    # ============================================================

    def _face_target(self, attacker, defender):
        if defender.x != attacker.x:
            attacker.facing = 1 if defender.x > attacker.x else -1

    def perform_basic(self, attacker, defender):
        """[E] Đòn đánh Chú Lực / Chú Cụ & Cơ chế nổ HẮC THIỂM (Black Flash)!"""
        if not attacker.alive or attacker.stun_timer > 0 or attacker.light_cd > 0 or attacker.ce < 8:
            return

        self._face_target(attacker, defender)
        attacker.ce -= 8
        cd = 0.36 if attacker.red_scale_timer > 0 else 0.42
        attacker.light_cd = cd
        attacker.attack_timer = 0.22
        attacker.attack_type = "light"
        play_sound("light")

        is_player = (attacker is self.player)
        wep_bonus = (self.weapon_level - 1) * 15 if is_player else 0
        base_dmg = 72 + wep_bonus
        cid = attacker.char_id
        dist = abs(defender.x - attacker.x)

        # Đặc trưng đòn [E] từng thuật thức:
        if cid in ("sukuna", "heian_sukuna"):
            # Phóng nhát chém vô hình Phân (Dismantle) tầm trung
            self.projectiles.append(
                Projectile(
                    attacker, "slash", attacker.x + attacker.facing * 38, attacker.y - 58,
                    attacker.facing * 640, 0, damage=base_dmg * 0.85, radius=26, life=0.42, color=REVERSAL_RED
                )
            )
        elif cid == "nobara":
            # Đập búa + Phóng 1 Đinh Chú Lực găm vào mục tiêu!
            play_sound("nail")
            self.projectiles.append(
                Projectile(
                    attacker, "nail", attacker.x + attacker.facing * 34, attacker.y - 58,
                    attacker.facing * 680, 0, damage=base_dmg * 0.78, radius=16, life=0.55,
                    color=ORANGE, nail_add=1
                )
            )
        elif cid == "inumaki":
            # Sóng âm ngắn "Văng Ra!"
            self.projectiles.append(
                Projectile(
                    attacker, "speech_wave", attacker.x + attacker.facing * 42, attacker.y - 60,
                    attacker.facing * 520, 0, damage=base_dmg * 0.8, radius=24, life=0.32,
                    color=PURPLE, knockback=90
                )
            )
        elif cid == "kamo":
            # Xích Lân Dược Động tăng tốc bản thân!
            attacker.red_scale_timer = 3.5

        # Đòn cận chiến trực tiếp + Kiểm tra nổ HẮC THIỂM (Black Flash)!
        melee_range = 128 if cid in ("yuta", "megumi", "nanami", "toji") else 112
        if dist <= melee_range:
            bf_chance = 0.18 + ((self.crit_level - 1) * 0.04 if is_player else 0.0)
            if attacker.zone_timer > 0:
                bf_chance += 0.12
            if attacker.overtime_timer > 0:
                bf_chance += 0.22
            if cid == "nanami":
                bf_chance += 0.10
            if not is_player and cid not in ("mahito", "heian_sukuna"):
                bf_chance = 0.05

            if random.random() < bf_chance:
                # NỔ HẮC THIỂM (BLACK FLASH)!
                attacker.attack_type = "black_flash"
                bf_mult = 2.5 + ((self.crit_level - 1) * 0.10 if is_player else 0.0)
                attacker.ce = min(attacker.max_ce, attacker.ce + 28.0)
                attacker.domain_gauge = min(100.0, attacker.domain_gauge + 20.0)
                attacker.zone_timer = 6.0
                if is_player:
                    self.match_black_flashes += 1
                self.spawn_black_flash_vfx(defender.x, defender.y - 58)
                self.deal_damage(attacker, defender, base_dmg * bf_mult, tag="black_flash")
            elif cid == "nanami":
                # Đoản đao trúng điểm yếu vạch 7:3!
                play_sound("parry")
                self.deal_damage(attacker, defender, base_dmg * 1.35, tag="ratio_crit")
            else:
                self.deal_damage(attacker, defender, base_dmg)

    def perform_skill1(self, attacker, defender):
        """[Y] Thuật Thức Đặc Trưng 1 của từng nhân vật."""
        if not attacker.alive or attacker.stun_timer > 0 or attacker.skill1_cd > 0 or attacker.ce < 22:
            return

        self._face_target(attacker, defender)
        attacker.ce -= 22
        attacker.skill1_cd = 2.4
        attacker.attack_timer = 0.30
        is_player = (attacker is self.player)
        skill_bonus = (self.weapon_level - 1) * 26 if is_player else 0
        cid = attacker.char_id
        f = attacker.facing

        if cid == "gojo":
            # Đảo Thuận Chuyển: XANH (hút xoáy) <-> Nghịch Chuyển: ĐỎ (đẩy nổ)
            attacker.blue_combo_timer = 5.5
            if not attacker.gojo_red_next:
                attacker.gojo_red_next = True
                play_sound("beam")
                self.add_floating_text("THUẬN CHUYỂN: XANH (BLUE)!", attacker.x, attacker.y - 120, LAPSE_BLUE)
                orb = Projectile(
                    attacker, "blue_orb", attacker.x + f * 55, attacker.y - 62,
                    f * 310, 0, damage=48 + skill_bonus * 0.45, radius=28, life=1.25,
                    color=LAPSE_BLUE, pierce=True, pull=340, multi_hit=True
                )
                self.projectiles.append(orb)
            else:
                attacker.gojo_red_next = False
                play_sound("fire")
                self.add_floating_text("NGHỊCH CHUYỂN: ĐỎ (RED)!", attacker.x, attacker.y - 120, REVERSAL_RED)
                orb = Projectile(
                    attacker, "red_orb", attacker.x + f * 48, attacker.y - 60,
                    f * 660, 0, damage=148 + skill_bonus, radius=24, life=0.95,
                    color=REVERSAL_RED, knockback=220
                )
                self.projectiles.append(orb)

        elif cid in ("sukuna", "heian_sukuna"):
            # BỔ / BÁT (Cleave): Lao nhanh tới chém lưới chữ thập theo % HP tối đa!
            play_sound("dash")
            attacker.x = clamp(attacker.x + f * 135, ARENA_LEFT, ARENA_RIGHT)
            play_sound("light")
            pct_dmg = defender.max_hp * 0.045
            total = 125 + skill_bonus + pct_dmg
            self.projectiles.append(
                Projectile(
                    attacker, "cleave_web", attacker.x + f * 65, attacker.y - 58,
                    f * 260, 0, damage=total, radius=42, life=0.32, color=REVERSAL_RED
                )
            )
            self.add_floating_text("TRẢM KÍCH: BỔ (CLEAVE)!", attacker.x, attacker.y - 120, REVERSAL_RED)

        elif cid == "megumi":
            # Triệu hồi Sói NGỌC KHUYỂN: HỖN + Chim sấm sét NUE!
            play_sound("dash")
            self.shikigamis.append(
                Shikigami(attacker, "divine_dog", attacker.x + f * 35, GROUND_Y, f, damage=92 + skill_bonus * 0.6, life=1.1)
            )
            self.shikigamis.append(
                Shikigami(attacker, "nue", attacker.x - f * 20, GROUND_Y - 125, f, damage=75 + skill_bonus * 0.5, life=1.25, color=PURPLE)
            )
            self.add_floating_text("NGỌC KHUYỂN & NUE!", attacker.x, attacker.y - 120, CYAN)

        elif cid == "yuta":
            # SAO CHÉP THUẬT THỨC (luân phiên 3 thuật thức kinh điển!)
            mode = attacker.copy_index % 3
            attacker.copy_index += 1
            if mode == 0:
                play_sound("beam")
                self.add_floating_text("SAO CHÉP CHÚ NGÔN: ĐỨNG IM!", attacker.x, attacker.y - 122, PURPLE)
                self.projectiles.append(
                    Projectile(
                        attacker, "speech_wave", attacker.x + f * 48, attacker.y - 60,
                        f * 580, 0, damage=115 + skill_bonus, radius=34, life=0.85, color=PURPLE, stun=1.05
                    )
                )
            elif mode == 1:
                play_sound("light")
                self.add_floating_text("SAO CHÉP NGỰ TRÙ TỬ: TRẢM!", attacker.x, attacker.y - 122, REVERSAL_RED)
                for dy in (-18, 16):
                    self.projectiles.append(
                        Projectile(
                            attacker, "slash", attacker.x + f * 42, attacker.y - 58 + dy,
                            f * 680, 0, damage=78 + skill_bonus * 0.6, radius=26, life=0.75, color=PINK
                        )
                    )
            else:
                play_sound("domain")
                self.add_floating_text("SAO CHÉP: QUANG TRỤ THIÊN THẦN!", defender.x, defender.y - 135, GOLD)
                self.lightnings.append(
                    LightningBolt(defender.x, 40, defender.x, GROUND_Y, outer_color=GOLD, inner_color=WHITE, life=0.42, width=9)
                )
                self.deal_damage(attacker, defender, 145 + skill_bonus, is_skill=True)

        elif cid == "inumaki":
            # CHÚ NGÔN: "ĐỨNG IM!" (Don't Move!) khóa cứng đối phương
            play_sound("beam")
            self.add_floating_text('CHÚ NGÔN: "ĐỨNG IM!"', attacker.x, attacker.y - 122, PURPLE)
            self.projectiles.append(
                Projectile(
                    attacker, "speech_wave", attacker.x + f * 46, attacker.y - 60,
                    f * 610, 0, damage=118 + skill_bonus, radius=38, life=0.95,
                    color=PURPLE, pierce=True, stun=1.20
                )
            )

        elif cid == "kamo":
            # BÁCH LIỄM -> XUYÊN HUYẾT (Piercing Blood siêu thanh!)
            play_sound("beam")
            self.add_floating_text("BÁCH LIỄM: XUYÊN HUYẾT!", attacker.x, attacker.y - 122, CRIMSON)
            self.projectiles.append(
                Projectile(
                    attacker, "piercing_blood", attacker.x + f * 60, attacker.y - 58,
                    f * 1150, 0, damage=150 + skill_bonus, radius=24, life=0.75,
                    color=CRIMSON, pierce=True
                )
            )

        elif cid == "nobara":
            # TRÂM (Hairpin): Phóng chùm 3 đinh chú lực găm và phát nổ!
            play_sound("nail")
            self.add_floating_text("SÔ LINH: TRÂM (HAIRPIN)!", attacker.x, attacker.y - 122, ORANGE)
            for vy_off in (-75, 0, 65):
                self.projectiles.append(
                    Projectile(
                        attacker, "nail", attacker.x + f * 38, attacker.y - 60,
                        f * 680, vy_off, damage=58 + skill_bonus * 0.45, radius=18, life=0.85,
                        color=ORANGE, nail_add=1
                    )
                )

        elif cid == "nanami":
            # THẬP HOẠCH: SỤP ĐỔ (Collapse) lao bổ điểm 7:3 làm nứt mặt đất!
            play_sound("blast")
            attacker.x = clamp(attacker.x + f * 125, ARENA_LEFT, ARENA_RIGHT)
            self.add_floating_text("THẬP HOẠCH: SỤP ĐỔ (7:3)!", attacker.x, attacker.y - 122, GOLD)
            self.projectiles.append(
                Projectile(
                    attacker, "slash", attacker.x + f * 50, GROUND_Y - 40,
                    f * 480, 0, damage=155 + skill_bonus, radius=38, life=0.55,
                    color=GOLD, knockback=140
                )
            )

        else:
            # Kỹ năng Boss đặc biệt (Hanami, Jogo, Mahito, Toji)
            self._perform_boss_skill(attacker, defender, heavy=False)

    def perform_skill2(self, attacker, defender):
        """[C] Tuyệt Chiêu Tối Thượng của từng nhân vật."""
        if not attacker.alive or attacker.stun_timer > 0 or attacker.skill2_cd > 0 or attacker.ce < 36:
            return

        self._face_target(attacker, defender)
        attacker.ce -= 36
        attacker.skill2_cd = 5.0
        attacker.attack_timer = 0.45
        is_player = (attacker is self.player)
        skill_bonus = (self.weapon_level - 1) * 34 if is_player else 0
        cid = attacker.char_id
        f = attacker.facing

        if cid == "gojo":
            # HƯ THỨC: TÍM (HOLLOW PURPLE)!
            play_sound("blast")
            self.screen_shake = 0.28
            fusion_mult = 1.35 if attacker.blue_combo_timer > 0 else 1.0
            attacker.blue_combo_timer = 0.0
            label = "DUNG HỢP XANH+ĐỎ: HƯ THỨC TÍM!" if fusion_mult > 1.0 else "HƯ THỨC: TÍM (HOLLOW PURPLE)!"
            self.add_floating_text(label, attacker.x, attacker.y - 135, HOLLOW_PURPLE)
            self.projectiles.append(
                Projectile(
                    attacker, "hollow_purple", attacker.x + f * 65, attacker.y - 68,
                    f * 620, 0, damage=(235 + skill_bonus) * fusion_mult, radius=48, life=1.6,
                    color=HOLLOW_PURPLE, pierce=True, knockback=240
                )
            )

        elif cid in ("sukuna", "heian_sukuna"):
            # THẦN HỎA: KHAI — FUGA!
            play_sound("fire")
            self.screen_shake = 0.25
            self.add_floating_text("THẦN HỎA: KHAI (FUGA)!", attacker.x, attacker.y - 135, ORANGE)
            self.projectiles.append(
                Projectile(
                    attacker, "fuga_arrow", attacker.x + f * 58, attacker.y - 64,
                    f * 720, 0, damage=245 + skill_bonus, radius=38, life=1.35,
                    color=ORANGE, knockback=210
                )
            )

        elif cid == "megumi":
            # TRIỆU HỒI DỊ GIỚI THẦN TƯỚNG MAHORAGA!
            play_sound("roar")
            self.screen_shake = 0.28
            spawn_x = clamp(attacker.x + f * 95, ARENA_LEFT + 30, ARENA_RIGHT - 30)
            self.shikigamis.append(
                Shikigami(attacker, "mahoraga", spawn_x, GROUND_Y, f, damage=230 + skill_bonus, life=1.65, color=GOLD)
            )
            self.add_floating_text("THẦN TƯỚNG MAHORAGA!", spawn_x, GROUND_Y - 175, GOLD)

        elif cid == "yuta":
            # THUẦN ÁI PHÁO — RIKA CỰC QUANG (Pure Love Beam)!
            play_sound("beam")
            play_sound("blast")
            self.screen_shake = 0.26
            self.add_floating_text("RIKA: THUẦN ÁI PHÁO!", attacker.x, attacker.y - 135, PINK)
            self.projectiles.append(
                Projectile(
                    attacker, "love_beam", attacker.x + f * 90, attacker.y - 62,
                    f * 980, 0, damage=240 + skill_bonus, radius=42, life=0.95,
                    color=PINK, pierce=True, knockback=200
                )
            )

        elif cid == "inumaki":
            # CHÚ NGÔN TỐI THƯỢNG: "NỔ TUNG!" (Explode!)
            play_sound("blast")
            self.screen_shake = 0.24
            self.add_floating_text('CHÚ NGÔN: "NỔ TUNG!"', attacker.x, attacker.y - 135, PURPLE)
            for idx in range(3):
                self.projectiles.append(
                    Projectile(
                        attacker, "speech_wave", attacker.x + f * (48 + idx * 45), attacker.y - 60,
                        f * (640 + idx * 60), 0, damage=86 + skill_bonus * 0.4, radius=44, life=0.9,
                        color=CYAN if idx == 1 else PURPLE, stun=0.65, knockback=120
                    )
                )

        elif cid == "kamo":
            # SIÊU TÂN TINH & XÍCH PHƯỢC (Supernova)!
            play_sound("blast")
            self.add_floating_text("HUYẾT ĐẠO: SIÊU TÂN TINH!", attacker.x, attacker.y - 135, CRIMSON)
            for vy_off in (-140, -45, 45, 130):
                self.projectiles.append(
                    Projectile(
                        attacker, "red_orb", attacker.x + f * 48, attacker.y - 62,
                        f * 520, vy_off, damage=72 + skill_bonus * 0.35, radius=20, life=1.0,
                        color=CRIMSON, slow=1.5
                    )
                )

        elif cid == "nobara":
            # CỘNG HƯỞNG BÚP BÊ RƠM (Resonance): Đánh thẳng vào linh hồn mục tiêu ở MỌI CỰ LY!
            play_sound("blast")
            self.screen_shake = 0.24
            stacks = defender.nail_stacks
            defender.nail_stacks = 0
            soul_dmg = 155 + skill_bonus + stacks * 52
            self.projectiles.append(
                Projectile(
                    attacker, "resonance_spike", defender.x, defender.y - 55,
                    0, 0, damage=0, radius=44, life=0.45, color=ORANGE
                )
            )
            self.spawn_particles(defender.x, defender.y - 60, ORANGE, count=32)
            self.spawn_particles(attacker.x + f * 25, attacker.y - 55, PINK, count=16)
            self.deal_damage(attacker, defender, soul_dmg, sure_hit=True, is_skill=True, tag="resonance")

        elif cid == "nanami":
            # KHẾ ƯỚC: TĂNG CA (Overtime)!
            play_sound("black_flash")
            attacker.overtime_timer = 6.5
            attacker.x = clamp(attacker.x + f * 95, ARENA_LEFT, ARENA_RIGHT)
            self.spawn_particles(attacker.x, attacker.y - 55, GOLD, count=30, gravity=-150)
            self.add_floating_text("KHẾ ƯỚC: TĂNG CA BỘC PHÁT!", attacker.x, attacker.y - 135, GOLD)
            if abs(defender.x - attacker.x) < 155:
                self.deal_damage(attacker, defender, 195 + skill_bonus, is_skill=True, tag="ratio_crit")

        else:
            self._perform_boss_skill(attacker, defender, heavy=True)

    def perform_shikigami(self, attacker, defender):
        """[F] Triệu hồi Thức Thần hộ chiến hoặc kích hoạt Chú Cụ Đặc Cấp."""
        if not attacker.alive or attacker.stun_timer > 0 or attacker.shiki_cd > 0 or attacker.ce < 18:
            return

        self._face_target(attacker, defender)
        attacker.ce -= 18
        attacker.shiki_cd = 3.2 if attacker.char_id == "megumi" else 4.4
        cid = attacker.char_id
        f = attacker.facing
        bonus = (self.weapon_level - 1) * 18 if attacker is self.player else 0

        if cid == "gojo":
            # Xung áp Vô Hạ Hạn đẩy lùi kẻ địch & tạo khiên không gian
            play_sound("simple_domain")
            attacker.shield_hp = 110.0
            self.spawn_particles(attacker.x, attacker.y - 55, LAPSE_BLUE, count=24)
            if abs(defender.x - attacker.x) < 210:
                defender.x = clamp(defender.x + f * 145, ARENA_LEFT, ARENA_RIGHT)
                defender.slow_timer = 1.4
                self.deal_damage(attacker, defender, 85 + bonus, is_skill=True)
            self.add_floating_text("XUNG ÁP VÔ HẠ HẠN!", attacker.x, attacker.y - 118, LAPSE_BLUE)

        elif cid in ("sukuna", "heian_sukuna"):
            # Chú cụ Đặc Cấp Kamutoke giáng sấm sét xuống đầu mục tiêu!
            play_sound("black_flash")
            self.lightnings.append(
                LightningBolt(defender.x, 30, defender.x, defender.y - 45, outer_color=YELLOW, inner_color=REVERSAL_RED, life=0.35, width=7)
            )
            self.deal_damage(attacker, defender, 118 + bonus, is_skill=True)
            self.add_floating_text("THẦN VŨ KAMUTOKE!", defender.x, defender.y - 125, YELLOW)

        elif cid == "megumi":
            # Thức Thần Mãng Xà Orochi trồi lên khóa chân địch!
            play_sound("roar")
            self.shikigamis.append(
                Shikigami(attacker, "orochi", defender.x, GROUND_Y, f, damage=105 + bonus, life=0.95, color=CYAN)
            )
            self.add_floating_text("THỨC THẦN: MÃNG XÀ!", defender.x, GROUND_Y - 135, CYAN)

        elif cid == "yuta":
            # Rika hiện thân lao tới đấm & tạo khiên chú lực cho Yuta
            play_sound("roar")
            attacker.shield_hp = 150.0
            self.shikigamis.append(
                Shikigami(attacker, "rika", attacker.x + f * 40, GROUND_Y, f, damage=125 + bonus, life=1.25, color=PINK)
            )
            self.add_floating_text("RIKA HỘ VỆ!", attacker.x, attacker.y - 120, PINK)

        elif cid == "inumaki":
            # Thuốc ho dịu cổ họng + Sóng âm đẩy lùi
            play_sound("rct")
            attacker.hp = min(attacker.max_hp, attacker.hp + 115)
            attacker.ce = min(attacker.max_ce, attacker.ce + 25)
            self.add_floating_text("THUỐC HO +115 HP & +25 CL!", attacker.x, attacker.y - 120, RCT_GREEN)
            if abs(defender.x - attacker.x) < 180:
                defender.x = clamp(defender.x + f * 120, ARENA_LEFT, ARENA_RIGHT)

        elif cid == "kamo":
            # Phóng cặp Huyết Tiễn truy kích
            play_sound("light")
            for dy in (-22, 12):
                self.projectiles.append(
                    Projectile(
                        attacker, "slash", attacker.x + f * 42, attacker.y - 55 + dy,
                        f * 720, 0, damage=65 + bonus * 0.6, radius=20, life=0.85, color=CRIMSON
                    )
                )
            self.add_floating_text("HUYẾT TIỄN!", attacker.x, attacker.y - 118, CRIMSON)

        elif cid == "nobara":
            # Phóng 2 Đinh Sô Linh găm nhanh lên mục tiêu
            play_sound("nail")
            for idx in range(2):
                self.projectiles.append(
                    Projectile(
                        attacker, "nail", attacker.x + f * (32 + idx * 24), attacker.y - 52 - idx * 14,
                        f * 740, 0, damage=55 + bonus * 0.5, radius=16, life=0.85, color=PINK, nail_add=1
                    )
                )
            self.add_floating_text("GĂM ĐINH SÔ LINH!", attacker.x, attacker.y - 118, PINK)

        elif cid == "nanami":
            # Phóng trảm kích Chú Cụ tỷ lệ 7:3 tầm xa
            play_sound("light")
            self.projectiles.append(
                Projectile(
                    attacker, "slash", attacker.x + f * 44, attacker.y - 58,
                    f * 680, 0, damage=125 + bonus, radius=28, life=0.8, color=GOLD
                )
            )
            self.add_floating_text("CHÚ CỤ TỶ LỆ 7:3!", attacker.x, attacker.y - 118, GOLD)

    def _perform_boss_skill(self, boss, player, heavy=False):
        bid = boss.char_id
        f = boss.facing
        if bid == "hanami":
            play_sound("blast")
            target_x = player.x if heavy else boss.x + f * 180
            self.projectiles.append(
                Projectile(boss, "roots", target_x, GROUND_Y - 40, 0, 0, damage=125 if heavy else 90, radius=38, life=0.65, color=GREEN, slow=1.2)
            )
            self.add_floating_text("MỘC ĐỘN GAI RỪNG!", target_x, GROUND_Y - 125, GREEN)
        elif bid == "jogo":
            if heavy:
                play_sound("fire")
                self.add_floating_text("CỰC PHIÊN: THIÊN THẠCH!", player.x, 120, ORANGE)
                self.projectiles.append(
                    Projectile(
                        boss, "meteor", player.x - f * 180, 70,
                        f * 260, 440, damage=185, radius=46, life=1.3, color=ORANGE, knockback=160
                    )
                )
            else:
                play_sound("fire")
                self.projectiles.append(
                    Projectile(boss, "red_orb", boss.x + f * 45, boss.y - 58, f * 580, 0, damage=105, radius=24, life=1.0, color=ORANGE)
                )
        elif bid == "mahito":
            play_sound("dash")
            boss.x = clamp(player.x - f * 75, ARENA_LEFT, ARENA_RIGHT)
            self.add_floating_text("VÔ VI CHUYỂN BIẾN!", boss.x, boss.y - 120, PURPLE)
            self.deal_damage(boss, player, 145 if heavy else 100, is_skill=True)
        elif bid == "toji":
            play_sound("dash")
            boss.x = clamp(player.x - f * 65, ARENA_LEFT, ARENA_RIGHT)
            play_sound("parry")
            self.add_floating_text("THIÊN NGHỊCH MÂU TRẢM!", boss.x, boss.y - 120, CYAN)
            self.deal_damage(boss, player, 165 if heavy else 115, is_skill=True)

    # ============================================================
    # CẬP NHẬT ĐẠN THUẬT THỨC, THỨC THẦN, NGƯỜI CHƠI & AI BOSS
    # ============================================================

    def update_projectiles_and_shikigami(self, dt):
        # 1. Cập nhật Projectiles
        for proj in self.projectiles[:]:
            proj.update(dt)
            if proj.life <= 0 or proj.x < -120 or proj.x > WIDTH + 120 or proj.y > GROUND_Y + 60:
                if proj in self.projectiles:
                    self.projectiles.remove(proj)
                continue

            target = self.enemy if proj.owner is self.player else self.player
            if not target.alive:
                continue

            # Hiệu ứng hút trọng lực của Thuận Chuyển: Xanh (Lapse Blue)
            if proj.pull > 0:
                dx = proj.x - target.x
                if abs(dx) < 260:
                    pull_dir = 1 if dx > 0 else -1
                    target.x = clamp(target.x + pull_dir * proj.pull * dt, ARENA_LEFT, ARENA_RIGHT)

            # Kiểm tra va chạm với mục tiêu
            hit_dist = math.hypot(proj.x - target.x, proj.y - target.center_y())
            # Tia laser dài (Xuyên Huyết / Thuần Ái Pháo) có vùng quét ngang rộng hơn
            beam_hit = proj.kind in ("piercing_blood", "love_beam") and (
                abs(proj.y - target.center_y()) < proj.radius + 36 and abs(proj.x - target.x) < 160
            )

            if hit_dist <= proj.radius + 32 or beam_hit:
                if proj.multi_hit:
                    if proj.tick_timer <= 0:
                        proj.tick_timer = 0.28
                        self.deal_damage(proj.owner, target, proj.damage, is_skill=True)
                elif id(target) not in proj.hit_targets:
                    proj.hit_targets.add(id(target))
                    landed = self.deal_damage(proj.owner, target, proj.damage, is_skill=True)
                    if landed and target.alive:
                        if proj.stun > 0:
                            target.stun_timer = max(target.stun_timer, proj.stun)
                        if proj.slow > 0:
                            target.slow_timer = max(target.slow_timer, proj.slow)
                        if proj.knockback != 0:
                            kb_dir = 1 if proj.vx >= 0 else -1
                            target.x = clamp(target.x + kb_dir * proj.knockback, ARENA_LEFT, ARENA_RIGHT)
                        if proj.nail_add > 0:
                            target.nail_stacks = min(6, target.nail_stacks + proj.nail_add)
                    if proj.kind == "fuga_arrow":
                        # Cột lửa Thần Hỏa Fuga bùng lên khi trúng đích!
                        self.spawn_particles(target.x, GROUND_Y - 30, ORANGE, count=35, gravity=-260)
                        self.spawn_particles(target.x, GROUND_Y - 50, YELLOW, count=20, gravity=-300)
                    if not proj.pierce and proj in self.projectiles:
                        self.projectiles.remove(proj)

        # 2. Cập nhật Thức Thần (Shikigami)
        for shiki in self.shikigamis[:]:
            target = self.enemy if shiki.owner is self.player else self.player
            shiki.update(dt, target)
            if shiki.life <= 0:
                self.shikigamis.remove(shiki)
                continue

            if not shiki.has_hit and target.alive:
                dist_x = abs(shiki.x - target.x)
                hit_range = 135 if shiki.kind == "mahoraga" else 75
                if dist_x <= hit_range:
                    shiki.has_hit = True
                    if shiki.kind == "nue":
                        self.lightnings.append(
                            LightningBolt(target.x, shiki.y, target.x, target.y - 45, outer_color=PURPLE, inner_color=WHITE, life=0.3, width=6)
                        )
                        target.stun_timer = max(target.stun_timer, 0.45)
                    elif shiki.kind == "orochi":
                        target.stun_timer = max(target.stun_timer, 0.85)
                    elif shiki.kind == "mahoraga":
                        self.screen_shake = 0.25
                        self.spawn_particles(shiki.x + shiki.facing * 50, GROUND_Y - 20, GOLD, count=28)
                    self.deal_damage(shiki.owner, target, shiki.damage, is_skill=True)

    def update_domain(self, dt):
        dom = self.domain_state
        if not dom["active"]:
            return
        dom["timer"] -= dt
        if dom["timer"] <= 0 or not dom["owner"].alive:
            dom["active"] = False
            dom["clash"] = False
            dom["owner"] = None
            return

        if not dom["clash"]:
            dom["tick"] -= dt
            if dom["tick"] <= 0:
                dom["tick"] = 0.65
                owner = dom["owner"]
                target = self.enemy if owner is self.player else self.player
                if target.alive:
                    self._apply_domain_sure_hit(owner, target)

    def update_player_movement(self, dt):
        p = self.player
        if not p.alive or p.stun_timer > 0:
            return

        keys = pygame.key.get_pressed()
        spd = p.speed
        if p.red_scale_timer > 0:
            spd *= 1.22
        if p.overtime_timer > 0:
            spd *= 1.18
        if p.slow_timer > 0:
            spd *= 0.55

        if keys[pygame.K_s] and p.y >= GROUND_Y - 2:
            p.is_crouching = True
        else:
            p.is_crouching = False
            if keys[pygame.K_LSHIFT] or keys[pygame.K_q]:
                spd *= 1.32
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                p.x -= spd * dt
                p.facing = -1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                p.x += spd * dt
                p.facing = 1

        p.x = clamp(p.x, ARENA_LEFT, ARENA_RIGHT)

    def update_bot(self, dt):
        bot = self.enemy
        player = self.player
        if not bot.alive or bot.stun_timer > 0:
            return

        self.bot_attack_cd = max(0.0, self.bot_attack_cd - dt)
        self.bot_special_cd = max(0.0, self.bot_special_cd - dt)
        self.bot_def_cd = max(0.0, self.bot_def_cd - dt)

        # 1. Boss tự dùng Nghịch Chuyển Thuật Thức khi máu dưới 42%
        if bot.hp < bot.max_hp * 0.42 and bot.rct_uses > 0 and bot.rct_heal_left <= 0:
            self.use_rct(bot)

        # 2. Nếu Người Chơi mở Lãnh Địa, Boss thông minh bật Giản Dị Lãnh Địa hoặc đối kháng Lãnh Địa!
        if self.domain_state["active"] and self.domain_state["owner"] is player and not self.domain_state["clash"]:
            if bot.domain_gauge >= 100.0 and bot.char_id != "toji":
                self.activate_domain_expansion(bot)
                return
            if bot.simple_cd <= 0 and bot.simple_domain_timer <= 0 and random.random() < 0.08:
                self.use_simple_domain(bot)

        # 3. Boss chủ động mở Bành Trướng Lãnh Địa khi đầy 100% thanh Lãnh Địa!
        if bot.domain_gauge >= 100.0 and bot.char_id != "toji" and not self.domain_state["active"]:
            if bot.hp < bot.max_hp * 0.72:
                self.activate_domain_expansion(bot)
                return

        # 4. Di chuyển tiếp cận và phản xạ phòng thủ
        dist = abs(bot.x - player.x)
        bot.facing = -1 if bot.x > player.x else 1
        move_spd = bot.speed * (0.55 if bot.slow_timer > 0 else 1.18)

        if dist > 105:
            bot.x = clamp(bot.x + bot.facing * move_spd * dt, ARENA_LEFT, ARENA_RIGHT)

        if dist < 135 and self.bot_def_cd <= 0 and player.attack_timer > 0:
            roll = random.random()
            dodge_rate = 0.30 if bot.char_id == "toji" else 0.14
            if roll < dodge_rate:
                bot.dodge_timer = 0.35
                self.bot_def_cd = 2.4
                bot.x = clamp(bot.x - bot.facing * 85, ARENA_LEFT, ARENA_RIGHT)

        # 5. Tung thuật thức tầm xa hoặc cận chiến
        if self.bot_special_cd <= 0:
            self.bot_special_cd = random.uniform(2.3, 3.8)
            if random.random() < 0.42 and bot.ce >= 36:
                self.perform_skill2(bot, player)
                return
            elif bot.ce >= 22:
                self.perform_skill1(bot, player)
                return

        if dist < 135 and self.bot_attack_cd <= 0:
            self.bot_attack_cd = random.uniform(0.42, 0.72)
            self.perform_basic(bot, player)

    # ============================================================
    # BẮT ĐẦU & KẾT THÚC TRẬN ĐẤU
    # ============================================================

    def start_match(self):
        self.apply_selected_character()
        self.load_current_level_boss()
        self.player.reset(260, facing=1)
        self.enemy.reset(840, facing=-1)

        self.domain_state = {
            "active": False, "owner": None, "char_id": "",
            "name": "", "timer": 0.0, "tick": 0.0, "clash": False,
        }
        self.projectiles.clear()
        self.shikigamis.clear()
        self.particles.clear()
        self.lightnings.clear()
        self.blood_stains.clear()
        self.floating_texts.clear()

        self.match_black_flashes = 0
        self.match_domains = 0
        self.winner = None
        self.message = ""
        self.state = "PLAYING"

    def end_game(self, won):
        if self.state != "PLAYING":
            return
        self.winner = won
        lv = self.levels[self.current_level_index]
        if won:
            play_sound("victory")
            bf_bonus = self.match_black_flashes * 150
            reward = lv["reward_gold"] + bf_bonus
            self.gold += reward
            self.message = f"Thưởng Thanh Tẩy: +{reward} Điểm Chú Thuật!"
            if self.current_level_index < len(self.levels) - 1:
                self.current_level_index += 1
                self.load_current_level_boss()
        else:
            play_sound("defeat")
            consolation = 250
            self.gold += consolation
            self.message = f"Nhận +{consolation} Điểm Chú Thuật để cường hóa Chú Cụ!"

        self.save_progress()
        self.state = "GAMEOVER"

    # ============================================================
    # XỬ LÝ SỰ KIỆN BÀN PHÍM & CHUỘT
    # ============================================================

    def trigger_ui_action(self, action):
        if action == "START":
            self.start_match()
        elif action == "CHAR_SELECT":
            self.state = "CHARACTER_SELECT"
        elif action == "MAP_SELECT":
            self.state = "MAP_SELECT"
        elif action == "SHOP":
            self.message = ""
            self.state = "SHOP"
        elif action == "GUIDE":
            self.prev_state = self.state
            self.state = "GUIDE"
        elif action == "CLOSE_GUIDE":
            self.state = self.prev_state
        elif action == "NEXT_LEVEL":
            self.current_level_index = (self.current_level_index + 1) % len(self.levels)
            self.load_current_level_boss()
            self.save_progress()
        elif action == "BACK_MENU":
            self.apply_selected_character()
            self.save_progress()
            self.state = "MENU"
        elif action.startswith("PICK_CHAR_"):
            idx = int(action.split("_")[-1])
            self.selected_class_index = idx
            self.apply_selected_character()
            self.save_progress()
            play_sound("simple_domain")
        elif action.startswith("PICK_MAP_"):
            idx = int(action.split("_")[-1])
            self.selected_map_index = idx
            self.save_progress()
            self.state = "MENU"
        elif action.startswith("BUY_"):
            key = action.replace("BUY_", "")
            self.buy_upgrade(key)

    def handle_key(self, key):
        if self.state == "MENU":
            if key == pygame.K_RETURN:
                self.start_match()
            elif key == pygame.K_c:
                self.state = "CHARACTER_SELECT"
            elif key == pygame.K_m:
                self.state = "MAP_SELECT"
            elif key == pygame.K_s:
                self.message = ""
                self.state = "SHOP"
            elif key == pygame.K_h:
                self.prev_state = "MENU"
                self.state = "GUIDE"
            elif key == pygame.K_l:
                self.trigger_ui_action("NEXT_LEVEL")
            elif key == pygame.K_q and sys.platform != "emscripten":
                pygame.quit()
                sys.exit()

        elif self.state == "CHARACTER_SELECT":
            if key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.trigger_ui_action("BACK_MENU")
            elif pygame.K_1 <= key <= pygame.K_8:
                idx = key - pygame.K_1
                if idx < len(self.characters):
                    self.selected_class_index = idx
                    self.apply_selected_character()
                    self.save_progress()
                    play_sound("simple_domain")
            elif key == pygame.K_RIGHT:
                self.selected_class_index = (self.selected_class_index + 1) % len(self.characters)
                self.apply_selected_character()
            elif key == pygame.K_LEFT:
                self.selected_class_index = (self.selected_class_index - 1) % len(self.characters)
                self.apply_selected_character()

        elif self.state == "MAP_SELECT":
            if key == pygame.K_ESCAPE:
                self.state = "MENU"
            elif pygame.K_1 <= key <= pygame.K_3:
                self.selected_map_index = key - pygame.K_1
                self.save_progress()
                self.state = "MENU"

        elif self.state == "SHOP":
            if key == pygame.K_ESCAPE:
                self.state = "MENU"
            elif key == pygame.K_1:
                self.buy_upgrade("weapon")
            elif key == pygame.K_2:
                self.buy_upgrade("crit")
            elif key == pygame.K_3:
                self.buy_upgrade("armor")
            elif key == pygame.K_4:
                self.buy_upgrade("ce")

        elif self.state == "GUIDE":
            if key in (pygame.K_ESCAPE, pygame.K_h, pygame.K_RETURN):
                self.state = self.prev_state

        elif self.state == "PLAYING":
            if key in (pygame.K_w, pygame.K_SPACE, pygame.K_UP):
                if self.player.jump_count < self.player.max_jumps and not self.player.is_crouching:
                    self.player.vy = self.player.jump_force
                    self.player.jump_count += 1
            elif key in (pygame.K_e, pygame.K_j):
                self.perform_basic(self.player, self.enemy)
            elif key in (pygame.K_y, pygame.K_u):
                self.perform_skill1(self.player, self.enemy)
            elif key in (pygame.K_c, pygame.K_i):
                self.perform_skill2(self.player, self.enemy)
            elif key in (pygame.K_f, pygame.K_k):
                self.perform_shikigami(self.player, self.enemy)
            elif key == pygame.K_z:
                self.use_simple_domain(self.player)
            elif key == pygame.K_x:
                self.use_rct(self.player)
            elif key in (pygame.K_r, pygame.K_o):
                self.activate_domain_expansion(self.player)
            elif key == pygame.K_h:
                self.prev_state = "PLAYING"
                self.state = "GUIDE"
            elif key == pygame.K_ESCAPE:
                self.state = "MENU"

        elif self.state == "GAMEOVER":
            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE):
                self.state = "MENU"

    def handle_mouse_click(self, button, pos):
        if self.state != "PLAYING":
            if button == 1:
                for rect, act in self.ui_buttons:
                    if rect.collidepoint(pos):
                        self.trigger_ui_action(act)
                        return
        else:
            if button == 1:
                self.perform_basic(self.player, self.enemy)
            elif button == 3:
                self.perform_skill1(self.player, self.enemy)

    # ============================================================
    # VÒNG LẶP CẬP NHẬT & VẼ MÀN HÌNH
    # ============================================================

    def draw_background(self):
        draw_arena_background(
            self.screen,
            self.maps[self.selected_map_index],
            self.domain_state if self.state in ("PLAYING", "GAMEOVER") else {"active": False},
            self.blood_stains if self.state in ("PLAYING", "GAMEOVER") else [],
            self.anim_time,
        )

    def draw_gameplay(self):
        self.draw_background()

        show_ratio_on_enemy = (self.player.char_id == "nanami")
        draw_jjk_fighter(self.screen, self.player, self.enemy, self.anim_time, show_ratio=False)
        draw_jjk_fighter(self.screen, self.enemy, self.player, self.anim_time, show_ratio=show_ratio_on_enemy)

        for shiki in self.shikigamis:
            draw_shikigami(self.screen, shiki)

        for proj in self.projectiles:
            draw_projectile(self.screen, proj)

        for p in self.particles:
            p.draw(self.screen)

        for bolt in self.lightnings:
            bolt.draw(self.screen)

        # Chớp đỏ-đen đặc trưng khoảnh khắc nổ Hắc Thiểm!
        if self.black_flash_flash > 0:
            pygame.draw.rect(self.screen, REVERSAL_RED, (0, 0, WIDTH, HEIGHT), 10)
            pygame.draw.rect(self.screen, BLACK, (8, 8, WIDTH - 16, HEIGHT - 16), 6)

        for ft in self.floating_texts:
            img = FONT_MED.render(ft["text"], True, ft["color"])
            sh = FONT_MED.render(ft["text"], True, BLACK)
            rect = img.get_rect(center=(int(ft["x"]), int(ft["y"])))
            self.screen.blit(sh, (rect.x + 2, rect.y + 2))
            self.screen.blit(img, rect)

        draw_hud(self.screen, self, self.levels[self.current_level_index], self.maps[self.selected_map_index]["accent"])

    def update(self, dt):
        self.anim_time += dt
        self.black_flash_flash = max(0.0, self.black_flash_flash - dt)
        self.screen_shake = max(0.0, self.screen_shake - dt)

        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

        for bolt in self.lightnings:
            bolt.update(dt)
        self.lightnings = [b for b in self.lightnings if b.life > 0]

        for ft in self.floating_texts:
            ft["y"] -= 34 * dt
            ft["life"] -= dt
        self.floating_texts = [ft for ft in self.floating_texts if ft["life"] > 0]

        if self.state == "PLAYING":
            ce_mult = 1.0 + (self.ce_level - 1) * 0.20
            self.player.update(dt, ce_regen_mult=ce_mult)
            self.enemy.update(dt, ce_regen_mult=1.0)
            self.update_player_movement(dt)
            self.update_bot(dt)
            self.update_projectiles_and_shikigami(dt)
            self.update_domain(dt)

    def render(self):
        if self.state == "MENU":
            draw_menu(
                self.screen, self,
                self.levels[self.current_level_index],
                self.maps[self.selected_map_index],
                self.characters[self.selected_class_index],
            )
        elif self.state == "MAP_SELECT":
            draw_map_select(self.screen, self, self.maps)
        elif self.state == "CHARACTER_SELECT":
            draw_character_select(self.screen, self, self.characters)
        elif self.state == "SHOP":
            draw_shop(self.screen, self, self.shop_items)
        elif self.state == "GUIDE":
            draw_guide(self.screen, self)
        elif self.state == "PLAYING":
            self.draw_gameplay()
        elif self.state == "GAMEOVER":
            self.draw_gameplay()
            draw_gameover(self.screen, self)

        pygame.display.flip()

    async def run(self):
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_click(event.button, event.pos)

            self.update(dt)
            self.render()
            await asyncio.sleep(0)

        pygame.quit()


# Hỗ trợ tên lớp cũ nếu có file bên ngoài import
BladeMaster = JujutsuArena

if __name__ == "__main__":
    game = JujutsuArena()
    asyncio.run(game.run())
