import math
import random
import pygame

from config import CYBER_BLUE, CYBER_PINK, CYBER_YELLOW, GREEN, RED
from cosmetics import CosmeticManager
from Enemy import Boss, Enemy, FlyingEnemy, ShieldEnemy
from game_engine_layout import Platform
from menu import Menu
from particle import ParticleManager
from player import Player
from powerups import PowerUp
from weapon import WEAPON_LIST
from save_manager import load_game_data, save_game_data

ORANGE = (255, 140, 0)
WHITE = (255, 255, 255)


class GameplayManager:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.state = "MENU"
        self.shop_tab = "UPGRADES"

        self.level_width = 2400
        self.camera_x = 0

        self.menu = Menu(self.screen)
        self.particle_mgr = ParticleManager()
        self.cosmetic_mgr = CosmeticManager()

        # Âm thanh hiệu ứng chiến đấu
        try:
            self.shield_clank_sound = pygame.mixer.Sound("Sounds/sounds/shield_clank.wav")
        except Exception:
            self.shield_clank_sound = None

        try:
            self.ricochet_sound = pygame.mixer.Sound("Sounds/sounds/ricochet.wav")
        except Exception:
            self.ricochet_sound = None

        try:
            self.slash_sound = pygame.mixer.Sound("Sounds/sounds/sword_slash.wav")
        except Exception:
            self.slash_sound = None

        try:
            self.dash_sound = pygame.mixer.Sound("Sounds/sounds/cyber_dash.wav")
        except Exception:
            self.dash_sound = None

        # Thông số Cyber Dash (Phím Q)
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_dir = 1
        self.dash_speed = 18

        # QUẢN LÝ DANH SÁCH SÚNG
        self.available_weapons = WEAPON_LIST
        self.current_weapon_key = "Blaster"
        self.current_weapon = self.available_weapons[self.current_weapon_key]

        # TẢI DỮ LIỆU TỪ BỘ NHỚ LƯU TRỮ
        saved_data = load_game_data()
        self.coins = saved_data.get("coins", 300)
        self.max_unlocked_level = saved_data.get("max_unlocked_level", 1)
        self.hp_lvl = saved_data.get("hp_lvl", 1)
        self.hp_cost = saved_data.get("hp_cost", 500)
        self.dmg_lvl = saved_data.get("dmg_lvl", 1)
        self.dmg_cost = saved_data.get("dmg_cost", 600)
        self.speed_lvl = saved_data.get("speed_lvl", 1)
        self.speed_cost = saved_data.get("speed_cost", 400)
        self.rebirths = saved_data.get("rebirths", 0)

        self.player = Player(100, 300)
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.boss_group = pygame.sprite.GroupSingle()
        self.platforms = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()

        self.active_buffs = []

        self.current_level = 1
        self.level_completed = False
        self.clear_timer = 0

        # THỐNG KÊ MÀN CHƠI + MÀN HÌNH "BẠN ĐÃ CHẾT"
        self.level_kills = 0
        self.level_frames = 0
        self.level_coins_start = self.coins
        self.death_timer = 0
        self.death_stats = {}

        # Nạp động các module từ thư mục levels/ (levels.lv1 -> levels.lv8)
        self.level_modules = {}
        for lvl_id in range(1, 9):
            try:
                mod = __import__(f"levels.lv{lvl_id}", fromlist=[f"lv{lvl_id}"])
                self.level_modules[lvl_id] = mod
            except ImportError:
                try:
                    mod = __import__(f"lv{lvl_id}")
                    self.level_modules[lvl_id] = mod
                except ImportError as e:
                    print(f"[Warning] Khong the nap Level {lvl_id}: {e}")

        self.start_level(self.current_level)

    def get_rebirth_cost(self):
        """Chi phí Rebirth tăng x1.5 sau mỗi lần trùng sinh"""
        return int(10000 * (1.5 ** self.rebirths))

    def get_coin_multiplier(self):
        """Mỗi lần Rebirth cộng thêm +0.5x lượng coins nhận được"""
        return 1.0 + (self.rebirths * 0.5)

    def can_rebirth(self):
        """Kiểm tra điều kiện Rebirth"""
        MAX_LVL = 10
        return (self.hp_lvl >= MAX_LVL and 
                self.dmg_lvl >= MAX_LVL and 
                self.speed_lvl >= MAX_LVL and 
                self.coins >= self.get_rebirth_cost())

    def perform_rebirth(self):
        """Thực hiện Rebirth"""
        if not self.can_rebirth():
            return False

        self.coins -= self.get_rebirth_cost()
        self.rebirths += 1

        self.hp_lvl = 1
        self.hp_cost = 500
        self.dmg_lvl = 1
        self.dmg_cost = 600
        self.speed_lvl = 1
        self.speed_cost = 400

        self.save_progress()
        return True

    def save_progress(self):
        """Đóng gói và ghi dữ liệu ra file save."""
        data = {
            "coins": self.coins,
            "max_unlocked_level": self.max_unlocked_level,
            "hp_lvl": self.hp_lvl,
            "hp_cost": self.hp_cost,
            "dmg_lvl": self.dmg_lvl,
            "dmg_cost": self.dmg_cost,
            "speed_lvl": self.speed_lvl,
            "speed_cost": self.speed_cost,
            "rebirths": self.rebirths
        }
        save_game_data(data)

    def update_camera(self):
        target_x = self.player.rect.centerx - 400
        self.camera_x = max(0, min(target_x, self.level_width - 800))

    def switch_weapon(self, weapon_key):
        if weapon_key in self.available_weapons:
            self.current_weapon_key = weapon_key
            self.current_weapon = self.available_weapons[weapon_key]
            self.player.change_weapon(weapon_key)

    def buy_upgrade(self, upgrade_type):
        MAX_LVL = 10
        purchased = False
        if upgrade_type == "HP" and self.hp_lvl < MAX_LVL and self.coins >= self.hp_cost:
            self.coins -= self.hp_cost
            self.hp_lvl += 1
            self.hp_cost = int(self.hp_cost * 1.8)
            purchased = True
        elif upgrade_type == "DMG" and self.dmg_lvl < MAX_LVL and self.coins >= self.dmg_cost:
            self.coins -= self.dmg_cost
            self.dmg_lvl += 1
            self.dmg_cost = int(self.dmg_cost * 1.8)
            purchased = True
        elif upgrade_type == "SPEED" and self.speed_lvl < MAX_LVL and self.coins >= self.speed_cost:
            self.coins -= self.speed_cost
            self.speed_lvl += 1
            self.speed_cost = int(self.speed_cost * 1.8)
            purchased = True

        if purchased:
            self.save_progress()

    def start_level(self, level_num):
        self.current_level = level_num
        self.player_bullets.empty()
        self.enemy_bullets.empty()
        self.enemies.empty()
        self.boss_group.empty()
        self.platforms.empty()
        self.powerups.empty()
        self.active_buffs.clear()
        self.dash_timer = 0
        self.dash_cooldown = 0

        if hasattr(self.particle_mgr, 'particles') and isinstance(self.particle_mgr.particles, list):
            self.particle_mgr.particles.clear()

        self.level_completed = False
        self.player.rect.topleft = (100, 300)
        self.level_kills = 0
        self.level_frames = 0
        self.level_coins_start = self.coins
        self.death_timer = 0

        buffs = self.cosmetic_mgr.get_total_buffs()
        self.player.max_hp = 100 + (self.hp_lvl - 1) * 10 + buffs.get("hp", 0)
        self.player.hp = self.player.max_hp
        self.player.speed = 5 + (self.speed_lvl - 1) * 0.3 + buffs.get("speed", 0)

        for w in self.available_weapons.values():
            if not hasattr(w, 'base_max_ammo'):
                w.base_max_ammo = w.max_ammo
            w.max_ammo = w.base_max_ammo + buffs.get("ammo", 0)
            w.ammo = w.max_ammo

        self.player.apply_cosmetics(buffs.get("body_color", CYBER_BLUE), buffs.get("head_visual", "NONE"))

        if level_num in self.level_modules:
            try:
                self.level_modules[level_num].setup(
                    self.enemies, self.boss_group, Enemy, FlyingEnemy, ShieldEnemy, Boss,
                    self.platforms, self.powerups, Platform, PowerUp
                )
            except TypeError:
                try:
                    self.level_modules[level_num].setup(
                        self.enemies, self.boss_group, Enemy, FlyingEnemy, Boss,
                        self.platforms, self.powerups, Platform, PowerUp
                    )
                except TypeError:
                    self.level_modules[level_num].setup(
                        self.enemies, self.boss_group, Enemy, Boss, self.platforms,
                        self.powerups, Platform, PowerUp
                    )

    def perform_dash(self):
        """Lướt nhanh (Cyber Dash) bằng phím Q kèm miễn nhiễm sát thương"""
        if self.dash_cooldown > 0 or self.dash_timer > 0:
            return

        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.dash_dir = -1
            self.player.facing_right = False
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.dash_dir = 1
            self.player.facing_right = True
        else:
            self.dash_dir = 1 if self.player.facing_right else -1

        self.dash_timer = 12      # Lướt trong 0.2 giây (12 frames)
        self.dash_cooldown = 75   # Hồi chiêu 1.25 giây (75 frames)

        if self.dash_sound:
            self.dash_sound.play()

        # Hiệu ứng bùng nổ hạt neon lúc xuất phát
        self.particle_mgr.add_hit_particles(self.player.rect.centerx, self.player.rect.centery, CYBER_BLUE, 10)
        self.particle_mgr.add_hit_particles(self.player.rect.centerx, self.player.rect.centery, CYBER_PINK, 6)

    def perform_shoot(self):
        """Bắn đạn theo hướng con chuột"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_mouse_x = mouse_x + self.camera_x
        world_mouse_y = mouse_y

        if world_mouse_x < self.player.rect.centerx:
            self.player.facing_right = False
        else:
            self.player.facing_right = True

        spawn_x = self.player.rect.right if self.player.facing_right else self.player.rect.left
        spawn_y = self.player.rect.centery - 5

        dx = world_mouse_x - spawn_x
        dy = world_mouse_y - spawn_y
        dist = math.hypot(dx, dy)
        if dist == 0:
            dist = 1
        dir_x = dx / dist
        dir_y = dy / dist

        bonus_damage = (self.dmg_lvl - 1) * 4 + self.cosmetic_mgr.get_total_buffs().get("dmg", 0)
        shot_success, ammo_used = self.current_weapon.shoot(
            x=spawn_x,
            y=spawn_y,
            dir_x=dir_x,
            dir_y=dir_y,
            player_ammo=self.current_weapon.ammo,
            bullet_group=self.player_bullets,
            bonus_dmg=bonus_damage
        )
        if shot_success:
            self.current_weapon.ammo -= ammo_used
            self.player.shoot()

    def perform_slash_attack(self):
        if not self.player.can_slash():
            return
        self.player.attack('slash')
        if self.slash_sound:
            self.slash_sound.play()

        slash_range = 75
        if self.player.facing_right:
            slash_rect = pygame.Rect(self.player.rect.right - 10, self.player.rect.top - 15, slash_range, self.player.rect.height + 30)
        else:
            slash_rect = pygame.Rect(self.player.rect.left - slash_range + 10, self.player.rect.top - 15, slash_range, self.player.rect.height + 30)

        bonus_dmg = (self.dmg_lvl - 1) * 4 + self.cosmetic_mgr.get_total_buffs().get("dmg", 0)
        damage = self.current_weapon.damage + bonus_dmg + 15

        for _ in range(8):
            px = slash_rect.centerx + random.randint(-15, 15)
            py = slash_rect.centery + random.randint(-15, 15)
            self.particle_mgr.add_hit_particles(px, py, CYBER_BLUE, 1)

        # --- TÍNH NĂNG PARRY: CHÉM BẬT NGƯỢC ĐẠN CỦA BOSS / QUÁI ---
        parry_rect = slash_rect.inflate(20, 20)
        parried_any = False
        for bullet in list(self.enemy_bullets):
            if parry_rect.colliderect(bullet.rect):
                self.enemy_bullets.remove(bullet)
                if hasattr(bullet, "parry"):
                    bullet.parry(bonus_dmg=bonus_dmg)
                else:
                    bullet.vel_x = -bullet.vel_x * 1.4
                    bullet.vel_y = -bullet.vel_y * 1.4
                    bullet.damage = int(bullet.damage * 4) + bonus_dmg
                self.player_bullets.add(bullet)
                self.particle_mgr.add_hit_particles(bullet.rect.centerx, bullet.rect.centery, CYBER_BLUE, 12)
                self.particle_mgr.add_hit_particles(bullet.rect.centerx, bullet.rect.centery, WHITE, 6)
                parried_any = True

        if parried_any:
            if self.ricochet_sound:
                self.ricochet_sound.play()
            self.active_buffs.append({"text": "PARRY DEFLECT!", "color": CYBER_BLUE, "timer": 60, "max_timer": 60})

        # Chém trúng quái thường / Shield Bot
        for enemy in list(self.enemies):
            if slash_rect.colliderect(enemy.rect):
                if hasattr(enemy, "break_shield"):
                    enemy.break_shield(150)  # Chém trúng làm vỡ khiên 2.5 giây
                enemy.hp -= damage
                self.particle_mgr.add_hit_particles(enemy.rect.centerx, enemy.rect.centery, CYBER_BLUE, 8)

        # Chém trúng Boss
        boss = self.boss_group.sprite
        if boss and slash_rect.colliderect(boss.rect):
            boss.hp -= damage
            self.particle_mgr.add_hit_particles(boss.rect.centerx, boss.rect.centery, CYBER_BLUE, 12)

    # ==================================================================
    # CHẾT / GAME OVER
    # ==================================================================
    GAMEOVER_INPUT_DELAY = 45          # khung hình chờ trước khi nhận phím (tránh bấm nhầm)
    RETRY_RECT = pygame.Rect(215, 395, 170, 46)
    MENU_RECT = pygame.Rect(415, 395, 170, 46)

    def trigger_death(self):
        """Người chơi hết máu: nổ tung, lưu tiến trình, chuyển sang màn hình BẠN ĐÃ CHẾT."""
        cx, cy = self.player.rect.centerx, self.player.rect.centery
        self.particle_mgr.add_death_explosion(cx, cy)
        boss = self.boss_group.sprite
        self.death_stats = {
            "level": self.current_level,
            "kills": self.level_kills,
            "coins": max(0, self.coins - self.level_coins_start),
            "seconds": self.level_frames // 60,
            "boss_hp": (max(0, boss.hp), boss.max_hp) if boss else None,
        }
        self.dash_timer = 0
        self.death_timer = 0
        self.state = "GAME_OVER"
        self.save_progress()
        if self.ricochet_sound:
            self.ricochet_sound.play()

    def retry_level(self):
        self.start_level(self.current_level)
        self.state = "GAME"

    def exit_to_menu(self):
        self.start_level(self.current_level)
        self.state = "MENU"

    def handle_game_over_event(self, event):
        if self.death_timer < self.GAMEOVER_INPUT_DELAY:
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                self.retry_level()
            elif event.key in (pygame.K_m, pygame.K_ESCAPE):
                self.exit_to_menu()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.RETRY_RECT.collidepoint(event.pos):
                self.retry_level()
            elif self.MENU_RECT.collidepoint(event.pos):
                self.exit_to_menu()

    def handle_event(self, event):
        if self.state == "GAME_OVER":
            self.handle_game_over_event(event)
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.state in ["MENU", "LEVEL_SELECT", "SHOP"]:
                self.state = self.menu.handle_click(event.pos, self.state, self)
            elif self.state == "LEVEL_CLEAR":
                self.start_level(self.current_level)
                self.state = "MENU"
            elif self.state == "GAME":
                if event.button == 1:
                    self.perform_shoot()
                elif event.button == 3:
                    self.perform_slash_attack()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = "MENU" if self.state == "GAME" else "GAME"
            if self.state == "LEVEL_CLEAR":
                self.start_level(self.current_level)
                self.state = "MENU"
            if self.state == "GAME":
                if event.key in [pygame.K_w, pygame.K_SPACE, pygame.K_UP]:
                    if self.player.on_ground:
                        self.particle_mgr.add_jump_dust(self.player.rect.centerx, self.player.rect.bottom)
                    self.player.jump()
                elif event.key == pygame.K_q:
                    self.perform_dash()
                elif event.key == pygame.K_j:
                    self.perform_slash_attack()
                elif event.key == pygame.K_k:
                    self.perform_shoot()
                elif event.key == pygame.K_1:
                    self.switch_weapon("Blaster")
                elif event.key == pygame.K_2:
                    self.switch_weapon("Shotgun")
                elif event.key == pygame.K_3:
                    self.switch_weapon("Rifle")

    def update_game_logic(self):
        if self.state == "LEVEL_CLEAR":
            self.clear_timer -= 1
            if self.clear_timer <= 0:
                self.start_level(self.current_level)
                self.state = "MENU"
            return

        if self.state == "GAME_OVER":
            self.death_timer += 1
            self.particle_mgr.update()
            return

        if self.state != "GAME":
            return

        self.level_frames += 1

        self.current_weapon.update()
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        self.player.update(floor_y=380, platforms=self.platforms, level_width=self.level_width)

        # --- CẬP NHẬT CYBER DASH (PHÍM Q) ---
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        if self.dash_timer > 0:
            self.dash_timer -= 1
            self.player.rect.x += self.dash_dir * self.dash_speed
            self.player.rect.x = max(0, min(self.player.rect.x, self.level_width - self.player.rect.width))
            if hasattr(self.player, "vel_y"):
                self.player.vel_y = 0
            # Vệt sáng tàn ảnh khi lướt
            self.particle_mgr.add_hit_particles(
                self.player.rect.centerx,
                self.player.rect.centery + random.randint(-12, 12),
                CYBER_BLUE,
                2
            )
            self.particle_mgr.add_hit_particles(
                self.player.rect.centerx,
                self.player.rect.centery + random.randint(-8, 8),
                CYBER_PINK,
                1
            )

        # GIỮ CHUỘT TRÁI ĐỂ XẢ ĐẠN LIÊN TỤC VỚI RIFLE
        if pygame.mouse.get_pressed()[0] and self.current_weapon.type == "ASSAULT_RIFLE":
            self.perform_shoot()

        self.update_camera()
        self.player_bullets.update()
        self.enemy_bullets.update()
        self.powerups.update()

        collected = pygame.sprite.spritecollide(self.player, self.powerups, True)
        for p in collected:
            if p.type == "HP":
                self.player.hp = min(self.player.max_hp, self.player.hp + 30)
                self.particle_mgr.add_hit_particles(p.rect.centerx, p.rect.centery, GREEN, 8)
                self.active_buffs.append({"text": "+30 HP RECOVER", "color": GREEN, "timer": 180, "max_timer": 180})
            elif p.type == "DMG":
                self.active_buffs.append({"text": "+5 DMG BOOST", "color": CYBER_YELLOW, "timer": 240, "max_timer": 240})
            elif p.type == "SPEED":
                self.player.speed += 1
                self.particle_mgr.add_hit_particles(p.rect.centerx, p.rect.centery, CYBER_PINK, 8)
                self.active_buffs.append({"text": "+1 SPEED UP", "color": CYBER_PINK, "timer": 240, "max_timer": 240})
            elif p.type == "AMMO":
                for w in self.available_weapons.values():
                    w.ammo = w.max_ammo
                self.particle_mgr.add_hit_particles(p.rect.centerx, p.rect.centery, ORANGE, 8)
                self.active_buffs.append({"text": "FULL AMMO REFILL", "color": ORANGE, "timer": 180, "max_timer": 180})

        for buff in self.active_buffs[:]:
            buff["timer"] -= 1
            if buff["timer"] <= 0:
                self.active_buffs.remove(buff)

        for enemy in list(self.enemies):
            try:
                enemy.update(self.enemy_bullets, self.player)
            except TypeError:
                try:
                    enemy.update(self.enemy_bullets)
                except TypeError:
                    enemy.update()
            if enemy.hp <= 0:
                enemy.kill()
                self.level_kills += 1
                self.coins += int(15 * self.get_coin_multiplier())

        boss = self.boss_group.sprite
        if boss:
            try:
                boss.update(self.player, self.enemy_bullets)
            except TypeError:
                try:
                    boss.update(self.enemy_bullets)
                except TypeError:
                    boss.update()
            if boss.hp <= 0:
                boss.kill()
                self.level_kills += 1
                self.coins += int(100 * self.get_coin_multiplier())

        hits = pygame.sprite.groupcollide(self.enemies, self.player_bullets, False, True)
        for enemy, bullets in hits.items():
            for bullet in bullets:
                if hasattr(enemy, "is_blocked") and enemy.is_blocked(bullet.rect.centerx):
                    self.particle_mgr.add_hit_particles(bullet.rect.centerx, bullet.rect.centery, CYBER_BLUE, 6)
                    if self.shield_clank_sound:
                        self.shield_clank_sound.play()
                else:
                    dmg = bullet.damage
                    if getattr(enemy, "shield_active", False):
                        dmg = int(dmg * 1.5)
                    enemy.hp -= dmg
                    self.particle_mgr.add_hit_particles(bullet.rect.centerx, bullet.rect.centery, CYBER_YELLOW, 5)

        # VA CHẠM GIỮA ĐẠN CỦA PLAYER (BAO GỒM ĐẠN ĐÃ PARRY) VÀ BOSS
        if boss:
            boss_hits = pygame.sprite.spritecollide(boss, self.player_bullets, True)
            for bullet in boss_hits:
                boss.hp -= bullet.damage
                hit_color = CYBER_BLUE if getattr(bullet, "parried", False) else CYBER_YELLOW
                self.particle_mgr.add_hit_particles(bullet.rect.centerx, bullet.rect.centery, hit_color, 10)

        # MIỄN NHIỄM SÁT THƯƠNG KHI ĐANG LƯỚT CYBER DASH
        if self.dash_timer <= 0:
            # VA CHẠM GIỮA PLAYER VÀ ĐẠN CỦA QUÁI
            player_hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True)
            for bullet in player_hits:
                self.player.take_damage(bullet.damage)
                self.particle_mgr.add_hit_particles(self.player.rect.centerx, self.player.rect.centery, RED, 6)

            # VA CHẠM TRỰC TIẾP GIỮA PLAYER VÀ QUÁI
            enemy_touch = pygame.sprite.spritecollide(self.player, self.enemies, False)
            for enemy in enemy_touch:
                dmg = getattr(enemy, 'damage', 10)
                self.player.take_damage(dmg)
                self.particle_mgr.add_hit_particles(self.player.rect.centerx, self.player.rect.centery, RED, 8)

            # VA CHẠM TRỰC TIẾP GIỮA PLAYER VÀ BOSS
            if boss and self.player.rect.colliderect(boss.rect):
                dmg = getattr(boss, 'damage', 20)
                self.player.take_damage(dmg)
                self.particle_mgr.add_hit_particles(self.player.rect.centerx, self.player.rect.centery, RED, 10)

        if self.player.hp <= 0:
            self.trigger_death()
            return

        self.particle_mgr.update()

        if len(self.enemies) == 0 and not self.boss_group.sprite and not self.level_completed:
            self.level_completed = True
            self.clear_timer = 120
            self.coins += int((50 + self.current_level * 25) * self.get_coin_multiplier())
            next_lvl = min(8, self.current_level + 1)
            self.max_unlocked_level = max(self.max_unlocked_level, next_lvl)
            self.current_level = next_lvl
            self.state = "LEVEL_CLEAR"
            self.save_progress()