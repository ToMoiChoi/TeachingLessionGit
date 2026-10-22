import pygame
import random
import math
import sys

from config import (
    WIDTH, HEIGHT, FPS, GROUND_Y, ARENA_LEFT, ARENA_RIGHT,
    PLAYER_HP, START_GOLD, LIGHT_DAMAGE, HEAVY_DAMAGE, SKILL_DAMAGE,
    WHITE, BLACK, RED, GREEN, BLUE, CYAN, YELLOW, PURPLE, GRAY, DARK,
    LEVELS, FONT_TITLE, FONT_BIG, FONT_MED, FONT, FONT_SMALL,
    clamp, draw_text, draw_bar, play_sound, SOUND_FILES
)
from entities import Particle, Fighter
from ui import draw_menu, draw_map_select, draw_character_select, draw_shop, draw_hud, draw_gameover

# ============================================================
# SÁT THƯƠNG CỘNG THÊM CHO NGƯỜI CHƠI (+50)
# ============================================================
BONUS_DAMAGE = 50
PLAYER_LIGHT_DAMAGE = LIGHT_DAMAGE + BONUS_DAMAGE
PLAYER_HEAVY_DAMAGE = HEAVY_DAMAGE + BONUS_DAMAGE
PLAYER_SKILL_DAMAGE = SKILL_DAMAGE + BONUS_DAMAGE

# Tăng máu cho General Gaia và Shadow Blade thêm 2000 HP
for lv in LEVELS:
    if lv["boss_name"] in ["General Gaia", "Shadow Blade"]:
        lv["boss_hp"] += 2000

PLAYER_CLASSES = [
    {
        "name": "KAEL",
        "title": "Kiếm Sĩ Lang Thang",
        "color": BLUE,
        "hp": 1750,
        "speed": 280,
        "desc": "Cân bằng, linh hoạt và dễ sử dụng."
    },
    {
        "name": "ALEX",
        "title": "Cuồng Phong Kiếm",
        "color": CYAN,
        "hp": 1750,
        "speed": 340,
        "desc": "Tốc độ di chuyển cao, né tránh cực tốt."
    },
    {
        "name": "VALEN",
        "title": "Hộ Vệ Thép",
        "color": GREEN,
        "hp": 1750,
        "speed": 230,
        "desc": "Lượng HP trâu, chịu đòn bền bỉ."
    }
]

MAPS = [
    {
        "name": "Đền Cổ Ánh Trăng",
        "bg_top": (15, 23, 42),
        "bg_bottom": (30, 41, 59),
        "floor": (40, 46, 58),
        "accent": (255, 215, 0)
    },
    {
        "name": "Vương Quốc Băng Giá",
        "bg_top": (10, 30, 50),
        "bg_bottom": (20, 60, 90),
        "floor": (45, 75, 105),
        "accent": (135, 206, 250)
    },
    {
        "name": "Hỏa Ngục Dung Nham",
        "bg_top": (50, 15, 10),
        "bg_bottom": (90, 30, 15),
        "floor": (65, 30, 25),
        "accent": (255, 69, 0)
    }
]

class BladeMaster:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Blade Master 2D - 6 Heals Edition")
        self.clock = pygame.time.Clock()
        self.state = "MENU"

        self.current_level_index = 0
        self.selected_class_index = 0
        self.selected_map_index = 0

        cls = PLAYER_CLASSES[0]
        self.player = Fighter(cls["name"], cls["color"], cls["hp"])
        self.player_speed = cls["speed"]

        self.player.vy = 0
        self.player.gravity = 1300
        self.player.jump_force = -480
        self.player.jump_count = 0
        self.player.max_jumps = 2
        self.player.is_crouching = False

        init_lv = LEVELS[0]
        self.enemy = Fighter(init_lv["boss_name"], init_lv["boss_color"], init_lv["boss_hp"], init_lv["boss_speed"])

        self.player.reset(300)
        self.enemy.reset(800)

        self.gold = START_GOLD
        self.weapon_level = 1
        self.armor_level = 1

        # Đặt số lần hồi máu của người chơi thành 6
        self.player_heal_uses = 6
        self.player_healing_timer = 0
        self.player_heal_amount_left = 0

        self.enemy_heal_uses = 2
        self.enemy_healing_timer = 0
        self.enemy_heal_amount_left = 0

        self.bot_parry_cd = 0
        self.bot_dodge_cd = 0

        self.walls = []

        self.message = ""
        self.message_timer = 0
        self.winner = None
        self.particles = []
        self.blood_stains = []
        self.floating_texts = []
        self.hit_effect_timer = 0
        self.screen_shake = 0
        self.bot_think = 0
        self.bot_attack_cd = 0

    def draw_background(self):
        current_map = MAPS[self.selected_map_index]
        bg_top = current_map["bg_top"]
        bg_bottom = current_map["bg_bottom"]
        floor_color = current_map["floor"]
        accent_color = current_map["accent"]

        for y in range(HEIGHT):
            ratio = y / HEIGHT
            color = (
                int(bg_top[0] * (1-ratio) + bg_bottom[0] * ratio),
                int(bg_top[1] * (1-ratio) + bg_bottom[1] * ratio),
                int(bg_top[2] * (1-ratio) + bg_bottom[2] * ratio),
            )
            pygame.draw.line(self.screen, color, (0, y), (WIDTH, y))

        pygame.draw.circle(self.screen, accent_color, (900, 120), 45)

        for i in range(12):
            x = i * 110
            h = 80 + (i * 37) % 150
            pygame.draw.rect(self.screen, (15, 20, 30), (x, GROUND_Y - h, 90, h))
            for wy in range(GROUND_Y - h + 20, GROUND_Y - 10, 30):
                pygame.draw.rect(self.screen, accent_color, (x + 15, wy, 12, 12))

        pygame.draw.rect(self.screen, floor_color, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
        pygame.draw.line(self.screen, accent_color, (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

        for stain in self.blood_stains:
            pygame.draw.ellipse(self.screen, stain["color"], (stain["x"] - stain["w"]//2, GROUND_Y + 2, stain["w"], stain["h"]))

        for x in range(0, WIDTH, 100):
            pygame.draw.line(self.screen, (50, 57, 70), (x, GROUND_Y), (x + 60, HEIGHT), 1)

    def draw_walls(self):
        accent_color = MAPS[self.selected_map_index]["accent"]
        for wall in self.walls:
            glow_rect = pygame.Rect(wall["x"] - 3, wall["y"] - 3, wall["w"] + 6, wall["h"] + 6)
            pygame.draw.rect(self.screen, accent_color, glow_rect, border_radius=6)

            wall_rect = pygame.Rect(wall["x"], wall["y"], wall["w"], wall["h"])
            pygame.draw.rect(self.screen, (40, 45, 60), wall_rect, border_radius=4)
            pygame.draw.rect(self.screen, accent_color, wall_rect, 2, border_radius=4)

            for line_y in range(wall["y"] + 15, wall["y"] + wall["h"], 20):
                pygame.draw.line(self.screen, (60, 70, 90), (wall["x"] + 3, line_y), (wall["x"] + wall["w"] - 3, line_y), 1)

            hits_left = wall["hits_left"]
            draw_text(self.screen, f"{hits_left}/4", wall["x"] + wall["w"] // 2, wall["y"] - 18, RED, FONT_SMALL)

    def gameplay(self):
        self.draw_background()
        self.draw_walls()
        self.draw_fighter(self.player)
        self.draw_fighter(self.enemy)
        
        draw_hud(self.screen, self, LEVELS[self.current_level_index], MAPS[self.selected_map_index]["accent"])
        
        # Hiển thị số lần hồi máu lên HUD
        draw_text(self.screen, f"Hồi máu còn: {self.player_heal_uses}/6 [X]", 35, 115, GREEN, FONT_SMALL)
        draw_text(self.screen, f"Boss Hồi máu: {self.enemy_heal_uses}/2", WIDTH - 365, 115, RED, FONT_SMALL)

        self.draw_particles()
        self.draw_floating_texts()

        if self.hit_effect_timer > 0:
            pygame.draw.circle(
                self.screen, MAPS[self.selected_map_index]["accent"],
                (WIDTH // 2, HEIGHT // 2),
                int(60 * self.hit_effect_timer), 3
            )

    def draw_fighter(self, fighter):
        color = WHITE if fighter.hit_flash > 0 else fighter.color
        is_crouch = getattr(fighter, 'is_crouching', False)
        
        current_height = fighter.height * 0.6 if is_crouch else fighter.height
        current_y_offset = 40 if is_crouch else 0
        
        rect = pygame.Rect(
            int(fighter.x - fighter.width // 2),
            int(fighter.y - current_height + current_y_offset),
            fighter.width,
            int(current_height)
        )

        pygame.draw.ellipse(self.screen, (15, 20, 30), (fighter.x - 45, GROUND_Y - 10, 90, 20))
        pygame.draw.ellipse(self.screen, MAPS[self.selected_map_index]["accent"], (fighter.x - 30, GROUND_Y - 6, 60, 12), 2)

        if not is_crouch:
            pygame.draw.line(self.screen, color, (fighter.x - 12, fighter.y - 35), (fighter.x - 18, fighter.y), 12)
            pygame.draw.line(self.screen, color, (fighter.x + 12, fighter.y - 35), (fighter.x + 18, fighter.y), 12)
            pygame.draw.circle(self.screen, WHITE, (int(fighter.x - 16), int(fighter.y - 18)), 4)
            pygame.draw.circle(self.screen, WHITE, (int(fighter.x + 16), int(fighter.y - 18)), 4)

        body_rect = pygame.Rect(rect.x + 6, rect.y + 15, rect.width - 12, current_height - 35)
        pygame.draw.rect(self.screen, (30, 35, 48), body_rect, border_radius=8)
        pygame.draw.rect(self.screen, color, body_rect, 3, border_radius=8)
        
        pygame.draw.circle(self.screen, WHITE, (int(fighter.x), int(rect.y + body_rect.height // 2)), 7)
        pygame.draw.circle(self.screen, MAPS[self.selected_map_index]["accent"], (int(fighter.x), int(rect.y + body_rect.height // 2)), 4)

        cape_pts = [
            (fighter.x - fighter.facing * 12, rect.y + 20),
            (fighter.x - fighter.facing * 35, rect.y + 45),
            (fighter.x - fighter.facing * 22, rect.y + 65)
        ]
        pygame.draw.polygon(self.screen, color, cape_pts)

        head_y = fighter.y - current_height - 15 if is_crouch else fighter.y - 95
        pygame.draw.circle(self.screen, (35, 40, 52), (int(fighter.x), int(head_y)), 20)
        pygame.draw.circle(self.screen, color, (int(fighter.x), int(head_y)), 20, 2)
        
        visor_x = fighter.x + fighter.facing * 4
        pygame.draw.rect(self.screen, MAPS[self.selected_map_index]["accent"], (int(visor_x - 7), int(head_y - 3), 14, 5), border_radius=2)

        sword_start_x = fighter.x + fighter.facing * 18
        sword_start_y = fighter.y - 45 if is_crouch else fighter.y - 55
        sword_length = 70

        if fighter.attack_timer > 0:
            sword_length = 110
            if fighter.attack_type == "skill":
                arc_rect = (fighter.x - 100, fighter.y - 120, 200, 150)
                start_angle, stop_angle = (-1.2, 1.2) if fighter.facing == 1 else (math.pi - 1.2, math.pi + 1.2)
                pygame.draw.arc(self.screen, PURPLE, arc_rect, start_angle, stop_angle, 10)
                pygame.draw.arc(self.screen, WHITE, arc_rect, start_angle, stop_angle, 3)
            else:
                arc_rect = (fighter.x - 85, fighter.y - 105, 170, 130)
                start_angle, stop_angle = (-1.2, 1.2) if fighter.facing == 1 else (math.pi - 1.2, math.pi + 1.2)
                pygame.draw.arc(self.screen, MAPS[self.selected_map_index]["accent"], arc_rect, start_angle, stop_angle, 8)
                pygame.draw.arc(self.screen, WHITE, arc_rect, start_angle, stop_angle, 2)

        sword_end_x = sword_start_x + fighter.facing * sword_length
        sword_end_y = sword_start_y - 25

        hweza_x = sword_start_x + fighter.facing * 10
        hweza_y = sword_start_y - 4
        pygame.draw.line(self.screen, WHITE, (sword_start_x, sword_start_y), (hweza_x, hweza_y), 5)
        pygame.draw.line(self.screen, MAPS[self.selected_map_index]["accent"], (hweza_x - 5, hweza_y - 5), (hweza_x + 5, hweza_y + 5), 4)

        pygame.draw.line(self.screen, (230, 240, 250), (hweza_x, hweza_y), (sword_end_x, sword_end_y), 6)
        pygame.draw.line(self.screen, WHITE, (hweza_x, hweza_y), (sword_end_x, sword_end_y), 2)

        if fighter.parry_timer > 0:
            pygame.draw.circle(self.screen, CYAN, (int(fighter.x), int(fighter.y - 55)), 55, 4)
            pygame.draw.circle(self.screen, WHITE, (int(fighter.x), int(fighter.y - 55)), 55, 1)
        if fighter.dodge_timer > 0:
            pygame.draw.circle(self.screen, BLUE, (int(fighter.x), int(fighter.y - 50)), 65, 3)

        name_surf = FONT_SMALL.render(fighter.name, True, WHITE)
        name_rect = name_surf.get_rect(center=(int(fighter.x), int(head_y - 25)))
        pygame.draw.rect(self.screen, DARK, name_rect.inflate(12, 6), border_radius=6)
        pygame.draw.rect(self.screen, MAPS[self.selected_map_index]["accent"], name_rect.inflate(12, 6), 1, border_radius=6)
        self.screen.blit(name_surf, name_rect)

    def spawn_blood_effect(self, x, y):
        colorful_bloods = [
            (200, 0, 0), (255, 69, 0), (220, 20, 60),
            (255, 20, 147), (178, 34, 34), (139, 0, 0)
        ]
        for _ in range(60):
            color = random.choice(colorful_bloods)
            self.particles.append(Particle(x, y - 50, color))
        
        for _ in range(random.randint(2, 4)):
            stain_width = random.randint(20, 50)
            stain_height = random.randint(8, 16)
            stain_color = random.choice([(139, 0, 0), (128, 0, 32), (165, 42, 42), (100, 0, 0)])
            self.blood_stains.append({
                "x": x + random.uniform(-40, 40), 
                "w": stain_width, 
                "h": stain_height, 
                "color": stain_color
            })
        
        if len(self.blood_stains) > 80:
            self.blood_stains = self.blood_stains[-80:]

    def add_floating_text(self, text, x, y, color=(255, 215, 0)):
        self.floating_texts.append({"text": text, "x": x, "y": y, "color": color, "life": 1.0})

    def draw_floating_texts(self):
        for ft in self.floating_texts:
            img = FONT_MED.render(ft["text"], True, ft["color"])
            self.screen.blit(img, (int(ft["x"]), int(ft["y"])))
            ft["y"] -= 30 * 0.016
            ft["life"] -= 0.016
        self.floating_texts = [ft for ft in self.floating_texts if ft["life"] > 0]

    def spawn_particles(self, x, y, color):
        for _ in range(18):
            self.particles.append(Particle(x, y, color))

    def draw_particles(self):
        for p in self.particles:
            p.draw(self.screen)

    def update_particles(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]

    def deal_damage(self, attacker, defender, damage):
        if not defender.alive:
            return

        for wall in self.walls:
            if (attacker.x < wall["x"] < defender.x) or (defender.x < wall["x"] < attacker.x):
                wall["hits_left"] -= 1
                self.spawn_particles(wall["x"], GROUND_Y - 40, CYAN)
                play_sound(SOUND_FILES["hit"])
                if wall["hits_left"] <= 0:
                    self.walls.remove(wall)
                return

        if defender.dodge_timer > 0:
            defender.last_action = "NÉ THÀNH CÔNG!"
            play_sound(SOUND_FILES["dodge"])
            attacker.stun_timer = 0.8
            self.spawn_particles(defender.x, defender.y - 60, CYAN)
            return

        if defender.parry_timer > 0:
            defender.last_action = "PARRY!"
            play_sound(SOUND_FILES["parry"])
            attacker.stun_timer = 1.4
            self.spawn_particles(defender.x, defender.y - 60, WHITE)
            return

        multiplier = 1.0
        if defender.stance == "LOW" or getattr(defender, 'is_crouching', False):
            multiplier *= 0.75

        if defender is self.player:
            multiplier *= max(0.25, 1 - (self.armor_level - 1) * 0.05)

        real_damage = damage * multiplier
        defender.hp -= real_damage
        defender.hit_flash = 0.15
        play_sound(SOUND_FILES["hit"])
        self.hit_effect_timer = 0.2
        self.screen_shake = 0.12

        self.spawn_blood_effect(defender.x, defender.y)
        self.spawn_particles(defender.x, defender.y - 60, RED if defender is self.player else MAPS[self.selected_map_index]["accent"])

        if defender.hp <= 0:
            defender.hp = 0
            defender.alive = False
            self.spawn_blood_effect(defender.x, defender.y)
            if defender is self.enemy:
                self.end_game(True)
            else:
                self.end_game(False)

    def attack(self, attacker, defender, attack_type):
        if not attacker.alive or attacker.stun_timer > 0:
            return

        dx = defender.x - attacker.x
        if (dx > 0 and attacker.facing != 1) or (dx < 0 and attacker.facing != -1):
            attacker.facing = 1 if dx > 0 else -1

        distance = abs(dx)
        is_player = (attacker is self.player)

        if attack_type == "light":
            if attacker.light_cd > 0 or attacker.stamina < 10:
                return
            attacker.stamina -= 10
            attacker.light_cd = 0.45
            attacker.attack_timer = 0.18
            attacker.attack_type = "light"
            attacker.last_action = "Đánh nhẹ!"
            play_sound(SOUND_FILES["light"])
            
            base_dmg = PLAYER_LIGHT_DAMAGE if is_player else (LIGHT_DAMAGE + (50 if attacker.name == "Ronin" else 0))
            damage = base_dmg + ((self.weapon_level - 1) * 10 if is_player else 0)
            if distance < 105:
                self.deal_damage(attacker, defender, damage)

        elif attack_type == "heavy":
            if attacker.heavy_cd > 0 or attacker.stamina < 25:
                return
            attacker.stamina -= 25
            attacker.heavy_cd = 1.2
            attacker.attack_timer = 0.35
            attacker.attack_type = "heavy"
            attacker.last_action = "ĐÒN NẶNG!"
            play_sound(SOUND_FILES["heavy"])
            
            base_dmg = PLAYER_HEAVY_DAMAGE if is_player else (HEAVY_DAMAGE + (50 if attacker.name == "Ronin" else 0))
            damage = base_dmg + ((self.weapon_level - 1) * 20 if is_player else 0)
            if distance < 125:
                self.deal_damage(attacker, defender, damage)

        elif attack_type == "skill":
            if attacker.skill_cd > 0 or attacker.stamina < 40:
                return
            attacker.stamina -= 40
            attacker.skill_cd = 5
            attacker.attack_timer = 0.5
            attacker.attack_type = "skill"
            attacker.last_action = "SKILL!"
            play_sound(SOUND_FILES["skill"])
            
            base_dmg = PLAYER_SKILL_DAMAGE if is_player else (SKILL_DAMAGE + (50 if attacker.name == "Ronin" else 0))
            if distance < 160:
                self.deal_damage(attacker, defender, base_dmg)

    def update_player(self, dt):
        if not self.player.alive or self.player.stun_timer > 0:
            return

        keys = pygame.key.get_pressed()
        speed = self.player_speed

        if keys[pygame.K_s] and self.player.y >= GROUND_Y - 2:
            self.player.is_crouching = True
            speed = 0
        else:
            self.player.is_crouching = False
            is_running = keys[pygame.K_q] and (keys[pygame.K_a] or keys[pygame.K_d])
            if is_running:
                speed *= 1.3

            if keys[pygame.K_LSHIFT]:
                speed *= 1.35

            if keys[pygame.K_a]:
                self.player.x -= speed * dt
                self.player.facing = -1
            if keys[pygame.K_d]:
                self.player.x += speed * dt
                self.player.facing = 1

        self.player.x = clamp(self.player.x, ARENA_LEFT, ARENA_RIGHT)
        self.player.vy += self.player.gravity * dt
        self.player.y += self.player.vy * dt

        if self.player.y >= GROUND_Y:
            self.player.y = GROUND_Y
            self.player.vy = 0
            self.player.jump_count = 0

    def update_bot(self, dt):
        bot = self.enemy
        player = self.player

        if not bot.alive or bot.stun_timer > 0:
            return

        self.bot_parry_cd = max(0, self.bot_parry_cd - dt)
        self.bot_dodge_cd = max(0, self.bot_dodge_cd - dt)

        if bot.hp < bot.max_hp * 0.5 and self.enemy_heal_uses > 0 and self.enemy_heal_amount_left <= 0:
            self.enemy_heal_uses -= 1
            self.enemy_heal_amount_left = 200
            self.enemy_healing_timer = 3.0
            self.add_floating_text("+200 HP (Bot)", bot.x, bot.y - 100, GREEN)

        distance = abs(bot.x - player.x)
        bot.facing = -1 if bot.x > player.x else 1

        enhanced_bot_speed = bot.speed * 1.3
        if distance > 100:
            next_x = bot.x + bot.facing * enhanced_bot_speed * dt
            
            can_move = True
            blocked_wall = None
            for wall in self.walls:
                if (bot.x <= wall["x"] <= next_x) or (next_x <= wall["x"] <= bot.x):
                    can_move = False
                    blocked_wall = wall
                    break
            
            if can_move:
                bot.x = next_x
            else:
                if blocked_wall and self.bot_attack_cd <= 0:
                    self.bot_attack_cd = random.uniform(0.4, 0.7)
                    blocked_wall["hits_left"] -= 1
                    play_sound(SOUND_FILES["hit"])
                    self.spawn_particles(blocked_wall["x"], GROUND_Y - 40, CYAN)
                    if blocked_wall["hits_left"] <= 0:
                        self.walls.remove(blocked_wall)

        bot.x = clamp(bot.x, ARENA_LEFT, ARENA_RIGHT)
        self.bot_think -= dt
        self.bot_attack_cd -= dt

        if self.bot_think <= 0:
            self.bot_think = random.uniform(0.2, 0.5)
            choice = random.random()
            if player.stance == "HIGH":
                bot.stance = "LOW"
            elif player.stance == "LOW":
                bot.stance = "HIGH"
            else:
                bot.stance = "MID" if choice < 0.4 else ("HIGH" if choice < 0.7 else "LOW")

        if distance < 130 and bot.hp < bot.max_hp * 0.6:
            roll = random.random()
            if roll < 0.04 and self.bot_parry_cd <= 0:
                bot.parry_timer = 0.4
                self.bot_parry_cd = 2.0
                bot.stamina = max(0, bot.stamina - 10)
                bot.last_action = "BOT PARRY!"
            elif roll < 0.08 and self.bot_dodge_cd <= 0:
                bot.dodge_timer = 0.4
                self.bot_dodge_cd = 2.0
                bot.stamina = max(0, bot.stamina - 10)
                bot.x += bot.facing * -80
                bot.last_action = "BOT NÉ!"

        if distance < 140 and self.bot_attack_cd <= 0:
            self.bot_attack_cd = random.uniform(0.3, 0.6)
            roll = random.random()
            if roll < 0.25:
                self.attack(bot, player, "skill")
            elif roll < 0.65:
                self.attack(bot, player, "heavy")
            else:
                self.attack(bot, player, "light")

    def handle_key(self, key):
        if self.state == "MENU":
            if key == pygame.K_RETURN:
                self.start_match()
            elif key == pygame.K_c:
                self.state = "CHARACTER_SELECT"
            elif key == pygame.K_m:
                self.state = "MAP_SELECT"
            elif key == pygame.K_s:
                self.state = "SHOP"
            elif key == pygame.K_l:
                self.current_level_index = (self.current_level_index + 1) % len(LEVELS)
                self.load_current_level_boss()
            elif key == pygame.K_q:
                pygame.quit()
                sys.exit()

        elif self.state == "MAP_SELECT":
            if key == pygame.K_ESCAPE:
                self.state = "MENU"
            elif key == pygame.K_1:
                self.selected_map_index = 0
                self.state = "MENU"
            elif key == pygame.K_2:
                self.selected_map_index = 1
                self.state = "MENU"
            elif key == pygame.K_3:
                self.selected_map_index = 2
                self.state = "MENU"

        elif self.state == "CHARACTER_SELECT":
            if key == pygame.K_ESCAPE:
                self.state = "MENU"
            elif key == pygame.K_1:
                self.selected_class_index = 0
                self.apply_selected_character()
                self.state = "MENU"
            elif key == pygame.K_2:
                self.selected_class_index = 1
                self.apply_selected_character()
                self.state = "MENU"
            elif key == pygame.K_3:
                self.selected_class_index = 2
                self.apply_selected_character()
                self.state = "MENU"

        elif self.state == "SHOP":
            if key == pygame.K_ESCAPE:
                self.state = "MENU"
            elif key == pygame.K_1:
                self.upgrade_weapon()
            elif key == pygame.K_2:
                self.upgrade_armor()

        elif self.state == "PLAYING":
            if key in (pygame.K_w, pygame.K_SPACE):
                if self.player.jump_count < self.player.max_jumps and not getattr(self.player, 'is_crouching', False):
                    self.player.vy = self.player.jump_force
                    self.player.jump_count += 1

            elif key == pygame.K_e:
                self.attack(self.player, self.enemy, "light")
            elif key == pygame.K_y:
                self.attack(self.player, self.enemy, "heavy")
            elif key == pygame.K_c:
                self.attack(self.player, self.enemy, "skill")
            
            elif key == pygame.K_x:
                if self.player_heal_uses > 0 and self.player_heal_amount_left <= 0:
                    self.player_heal_uses -= 1
                    self.player_heal_amount_left = 200
                    self.player_healing_timer = 3.0
                    self.add_floating_text("+200 HP", self.player.x, self.player.y - 100, GREEN)
                    play_sound(SOUND_FILES["victory"])

            elif key == pygame.K_f:
                wall_x = self.player.x + self.player.facing * 60
                if len(self.walls) >= 4:
                    self.walls.pop(0)

                self.walls.append({
                    "x": wall_x,
                    "y": GROUND_Y - 90,
                    "w": 20,
                    "h": 90,
                    "hits_left": 4,
                    "timer": 5.0,
                    "color": MAPS[self.selected_map_index]["accent"]
                })
                self.add_floating_text("TƯỜNG CHẮN!", wall_x, GROUND_Y - 110, CYAN)

            elif key == pygame.K_z:
                if self.player.stamina >= 12:
                    self.player.stamina -= 12
                    self.player.parry_timer = 0.4
                    play_sound(SOUND_FILES["parry"])
                    self.player.last_action = "PARRY!"
            elif key == pygame.K_v:
                if self.enemy.stun_timer > 0:
                    self.attack(self.player, self.enemy, "heavy")
                    self.player.last_action = "PHẢN CÔNG!"
                    play_sound(SOUND_FILES["counter"])
                else:
                    self.player.last_action = "Phản công trượt!"
            elif key == pygame.K_1:
                self.player.stance = "HIGH"
            elif key == pygame.K_2:
                self.player.stance = "MID"
            elif key == pygame.K_3:
                self.player.stance, self.player.last_action = "LOW", "Thế LOW"
            elif key == pygame.K_ESCAPE:
                self.state = "MENU"

        elif self.state == "GAMEOVER":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.state = "MENU"

    def handle_mouse_click(self, button):
        if self.state == "PLAYING" and button == 1:
            self.attack(self.player, self.enemy, "heavy")

    def apply_selected_character(self):
        cls = PLAYER_CLASSES[self.selected_class_index]
        self.player.name = cls["name"]
        self.player.color = cls["color"]
        self.player.max_hp = cls["hp"]
        self.player.hp = cls["hp"]
        self.player_speed = cls["speed"]

    def load_current_level_boss(self):
        lv_data = LEVELS[self.current_level_index]
        self.enemy.name = lv_data["boss_name"]
        self.enemy.color = lv_data["boss_color"]
        self.enemy.max_hp = lv_data["boss_hp"]
        self.enemy.hp = lv_data["boss_hp"]
        self.enemy.speed = lv_data["boss_speed"]

    def upgrade_weapon(self):
        if self.gold >= 1000:
            self.gold -= 1000
            self.weapon_level += 1
            self.message = "Đã nâng cấp KIẾM!"
        else:
            self.message = "Không đủ vàng!"

    def upgrade_armor(self):
        if self.gold >= 1000:
            self.gold -= 1000
            self.armor_level += 1
            self.message = "Đã nâng cấp GIÁP!"
        else:
            self.message = "Không đủ vàng!"

    def start_match(self):
        self.apply_selected_character()
        self.load_current_level_boss()
        self.player.reset(300)
        self.player.vy = 0
        self.player.jump_count = 0
        self.player.is_crouching = False
        self.enemy.reset(800)
        
        # Reset lại số lần hồi máu về 6 khi bắt đầu trận mới
        self.player_heal_uses = 6
        self.player_heal_amount_left = 0
        self.enemy_heal_uses = 2
        self.enemy_heal_amount_left = 0
        self.bot_parry_cd = 0
        self.bot_dodge_cd = 0
        self.walls.clear()

        self.particles.clear()
        self.blood_stains.clear()
        self.floating_texts.clear()
        self.state = "PLAYING"
        self.winner = None

    def end_game(self, won):
        if self.state != "PLAYING":
            return
        self.winner = won
        lv_data = LEVELS[self.current_level_index]
        
        if won:
            play_sound(SOUND_FILES["victory"])
            reward = lv_data["reward_gold"]
            self.gold += reward
            self.message = f"CHIẾN THẮNG! +{reward} VÀNG"
            self.add_floating_text(f"+{reward} G", WIDTH // 2, HEIGHT // 2 - 50, (255, 215, 0))
            
            if self.current_level_index < len(LEVELS) - 1:
                self.current_level_index += 1
        else:
            play_sound(SOUND_FILES["defeat"])
            self.gold = max(0, self.gold - 1000)
            self.message = "THẤT BẠI! -1000 VÀNG"
            self.add_floating_text("-1000 G", WIDTH // 2, HEIGHT // 2 - 50, (255, 80, 80))

        self.state = "GAMEOVER"

    def update(self, dt):
        if self.player_heal_amount_left > 0 and self.player_healing_timer > 0:
            heal_step = (200 / 3.0) * dt
            self.player.hp = min(self.player.max_hp, self.player.hp + heal_step)
            self.player_heal_amount_left -= heal_step
            self.player_healing_timer -= dt

        if self.enemy_heal_amount_left > 0 and self.enemy_healing_timer > 0:
            heal_step = (200 / 3.0) * dt
            self.enemy.hp = min(self.enemy.max_hp, self.enemy.hp + heal_step)
            self.enemy_heal_amount_left -= heal_step
            self.enemy_healing_timer -= dt

        for wall in self.walls[:]:
            wall["timer"] -= dt
            if wall["timer"] <= 0:
                self.walls.remove(wall)

        self.player.update(dt)
        self.enemy.update(dt)
        self.update_particles(dt)
        self.hit_effect_timer = max(0, self.hit_effect_timer - dt)
        self.message_timer = max(0, self.message_timer - dt)

        if self.state == "PLAYING":
            self.update_player(dt)
            self.update_bot(dt)

    def render(self):
        if self.state == "MENU":
            draw_menu(self.screen, self, LEVELS[self.current_level_index], MAPS[self.selected_map_index], PLAYER_CLASSES[self.selected_class_index])
        elif self.state == "MAP_SELECT":
            draw_map_select(self.screen, self, MAPS)
        elif self.state == "CHARACTER_SELECT":
            draw_character_select(self.screen, self, PLAYER_CLASSES)
        elif self.state == "SHOP":
            draw_shop(self.screen, self)
        elif self.state == "PLAYING":
            self.gameplay()
        elif self.state == "GAMEOVER":
            self.gameplay()
            draw_gameover(self.screen, self)
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000
            dt = min(dt, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_click(event.button)

            self.update(dt)
            self.render()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = BladeMaster()
    game.run()