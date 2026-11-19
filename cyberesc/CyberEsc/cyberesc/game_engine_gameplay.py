import math
import random
import pygame

import sfx
from config import CYBER_BLUE, CYBER_PINK, CYBER_YELLOW, GREEN, RED
from cosmetics import CosmeticManager
from endless import EndlessDirector
from Enemy import Boss, Enemy
from enemies_extra import KamikazeEnemy, MothershipBoss, SniperEnemy, TeleportEnemy
from game_engine_layout import Platform
from menu import Menu
from missions import MissionManager, today_str
from particle import ParticleManager
from pickups import Checkpoint, CoinPickup
from player import Player
from powerups import PowerUp
from save_manager import load_game_data, save_game_data
from touch import TouchControls
from weapon import WEAPON_KEYS, WEAPON_LIST

ORANGE = (255, 140, 0)
WHITE = (255, 255, 255)
FLOOR_Y = 380

DIFFICULTIES = {
    "EASY": {"name": "DỄ", "enemy_hp": 0.75, "enemy_dmg": 0.6, "coins": 0.8, "color": GREEN},
    "NORMAL": {"name": "THƯỜNG", "enemy_hp": 1.0, "enemy_dmg": 1.0, "coins": 1.0, "color": CYBER_BLUE},
    "HARD": {"name": "KHÓ", "enemy_hp": 1.35, "enemy_dmg": 1.5, "coins": 1.4, "color": RED},
}
DIFF_ORDER = ["EASY", "NORMAL", "HARD"]
BOSS_LEVELS = {4, 6, 8}

# Kỹ năng (đơn vị: khung hình, 60 khung = 1 giây)
SHIELD_TIME, SHIELD_CD = 150, 480
SLOW_TIME, SLOW_CD = 180, 720
DASH_TIME, DASH_CD = 12, 75
DMG_BOOST_TIME = 600


def par_time(level):
    """Thời gian chuẩn (giây) để lấy sao thứ 3."""
    return 120 if level in BOSS_LEVELS else 75


class GameplayManager:
    MENU_STATES = ("MENU", "LEVEL_SELECT", "SHOP", "MISSIONS")
    OVERLAY_STATES = ("GAME_OVER", "PAUSED", "LEVEL_CLEAR")
    GAMEOVER_INPUT_DELAY = 45

    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.state = "MENU"
        self.shop_tab = "UPGRADES"
        self.mode = "STORY"            # STORY hoặc ENDLESS
        self.endless = None

        self.level_width = 2400
        self.camera_x = 0
        self.frame = 0

        self.menu = Menu(self.screen)
        self.particle_mgr = ParticleManager()
        self.cosmetic_mgr = CosmeticManager()
        self.touch = TouchControls(*self.screen.get_size())

        # Lướt (Q)
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_dir = 1
        self.dash_speed = 18
        # Khiên (E) và Làm chậm thời gian (F)
        self.shield_timer = self.shield_cd = 0
        self.slow_timer = self.slow_cd = 0
        self.dmg_boost_timer = 0

        # Hiệu ứng cảm giác
        self.shake = 0.0
        self.hurt_flash = 0
        self.floaters = []    # số sát thương bay lên
        self.beams = []       # vệt laser
        self.blasts = []      # vòng nổ
        self.no_ammo_cd = 0

        # Vũ khí
        self.available_weapons = WEAPON_LIST
        self.current_weapon_key = "Blaster"
        self.current_weapon = self.available_weapons[self.current_weapon_key]

        # Nạp dữ liệu lưu
        saved = load_game_data()
        self.coins = saved["coins"]
        self.max_unlocked_level = saved["max_unlocked_level"]
        self.hp_lvl = saved["hp_lvl"]
        self.hp_cost = saved["hp_cost"]
        self.dmg_lvl = saved["dmg_lvl"]
        self.dmg_cost = saved["dmg_cost"]
        self.speed_lvl = saved["speed_lvl"]
        self.speed_cost = saved["speed_cost"]
        self.rebirths = saved["rebirths"]
        self.stars = dict(saved.get("stars", {}))
        self.weapons_owned = [w for w in saved.get("weapons_owned", []) if w in WEAPON_LIST] or ["Blaster"]
        self.difficulty = saved.get("difficulty", "NORMAL") if saved.get("difficulty") in DIFFICULTIES else "NORMAL"
        self.endless_scores = list(saved.get("endless_scores", []))
        self.cosmetic_mgr.import_state(saved.get("cosmetics", {}))
        self.missions = MissionManager(saved.get("missions"))

        self.player = Player(100, 300)
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.boss_group = pygame.sprite.GroupSingle()
        self.platforms = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.coin_pickups = pygame.sprite.Group()
        self.checkpoint = None

        self.active_buffs = []
        self.current_level = 1
        self.level_completed = False
        self.clear_timer = 0
        self.clear_stats = {}

        # Thống kê màn chơi + màn hình chết
        self.level_kills = 0
        self.level_frames = 0
        self.level_coins_start = self.coins
        self.deaths_in_level = 0
        self.death_timer = 0
        self.death_stats = {}

        # Nạp các màn từ thư mục levels/
        self.level_modules = {}
        for lvl_id in range(1, 9):
            try:
                self.level_modules[lvl_id] = __import__(f"levels.lv{lvl_id}", fromlist=[f"lv{lvl_id}"])
            except ImportError as e:
                print(f"[Warning] Khong the nap Level {lvl_id}: {e}")
        try:
            from levels.extras import CHECKPOINT_X, LEVEL_EXTRAS
        except ImportError:
            CHECKPOINT_X, LEVEL_EXTRAS = {}, {}
        self.level_extras = LEVEL_EXTRAS
        self.checkpoint_x = CHECKPOINT_X

        self.start_level(self.current_level)

    # ==================================================================
    # TIẾN TRÌNH / LƯU
    # ==================================================================
    @property
    def diff(self):
        return DIFFICULTIES[self.difficulty]

    def cycle_difficulty(self):
        i = DIFF_ORDER.index(self.difficulty)
        self.difficulty = DIFF_ORDER[(i + 1) % len(DIFF_ORDER)]
        self.save_progress()

    def get_rebirth_cost(self):
        """Chi phí Rebirth tăng x1.5 sau mỗi lần trùng sinh"""
        return int(10000 * (1.5 ** self.rebirths))

    def get_coin_multiplier(self):
        """Mỗi lần Rebirth +0.5x coins, nhân thêm theo độ khó"""
        return (1.0 + self.rebirths * 0.5) * self.diff["coins"]

    def can_rebirth(self):
        MAX_LVL = 10
        return (self.hp_lvl >= MAX_LVL and self.dmg_lvl >= MAX_LVL and
                self.speed_lvl >= MAX_LVL and self.coins >= self.get_rebirth_cost())

    def perform_rebirth(self):
        if not self.can_rebirth():
            return False
        self.coins -= self.get_rebirth_cost()
        self.rebirths += 1
        self.hp_lvl, self.hp_cost = 1, 500
        self.dmg_lvl, self.dmg_cost = 1, 600
        self.speed_lvl, self.speed_cost = 1, 400
        self.save_progress()
        return True

    def save_progress(self):
        save_game_data({
            "coins": self.coins,
            "max_unlocked_level": self.max_unlocked_level,
            "hp_lvl": self.hp_lvl, "hp_cost": self.hp_cost,
            "dmg_lvl": self.dmg_lvl, "dmg_cost": self.dmg_cost,
            "speed_lvl": self.speed_lvl, "speed_cost": self.speed_cost,
            "rebirths": self.rebirths,
            "stars": self.stars,
            "weapons_owned": self.weapons_owned,
            "cosmetics": self.cosmetic_mgr.export_state(),
            "difficulty": self.difficulty,
            "endless_scores": self.endless_scores,
            "missions": self.missions.export_state(),
        })

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
            sfx.play("cash_transfer.wav", 0.5)
            self.save_progress()

    def buy_weapon(self, key, price):
        if key in self.weapons_owned or self.coins < price:
            return False
        self.coins -= price
        self.weapons_owned.append(key)
        sfx.play("cash_transfer.wav", 0.5)
        self.save_progress()
        return True

    def claim_mission(self, idx):
        reward = self.missions.claim(idx)
        if reward:
            self.coins += reward
            sfx.play("chest_open.wav", 0.6)
            self.save_progress()

    def mission_event(self, event, amount=1):
        for m in self.missions.record(event, amount):
            self.add_buff(f"NHIỆM VỤ XONG: +{m['reward']}", CYBER_YELLOW, 200)

    # ==================================================================
    # BẮT ĐẦU MÀN
    # ==================================================================
    def _reset_world(self):
        for g in (self.player_bullets, self.enemy_bullets, self.enemies, self.boss_group,
                  self.platforms, self.powerups, self.coin_pickups):
            g.empty()
        self.active_buffs.clear()
        self.floaters.clear()
        self.beams.clear()
        self.blasts.clear()
        self.particle_mgr.particles.clear()
        self.touch.reset()
        self.dash_timer = self.dash_cooldown = 0
        self.shield_timer = self.shield_cd = 0
        self.slow_timer = self.slow_cd = 0
        self.dmg_boost_timer = 0
        self.shake = 0
        self.hurt_flash = 0
        self.checkpoint = None

        self.level_completed = False
        self.level_kills = 0
        self.level_frames = 0
        self.level_coins_start = self.coins
        self.deaths_in_level = 0
        self.death_timer = 0
        self.clear_timer = 0

        p = self.player
        p.rect.topleft = (100, 300)
        p.vel_x = p.vel_y = 0
        p.invincible_timer = 0
        buffs = self.cosmetic_mgr.get_total_buffs()
        p.max_hp = 100 + (self.hp_lvl - 1) * 10 + buffs.get("hp", 0)
        p.hp = p.max_hp
        p.speed = 5 + (self.speed_lvl - 1) * 0.3 + buffs.get("speed", 0)
        for w in self.available_weapons.values():
            if not hasattr(w, "base_max_ammo"):
                w.base_max_ammo = w.max_ammo
            w.max_ammo = w.base_max_ammo + buffs.get("ammo", 0)
            w.ammo = w.max_ammo
            w.cooldown = 0
        if self.current_weapon_key not in self.weapons_owned:
            self.switch_weapon("Blaster")
        p.apply_cosmetics(buffs.get("body_color", CYBER_BLUE), buffs.get("head_visual", "NONE"))

    def start_level(self, level_num):
        self.mode = "STORY"
        self.endless = None
        self.current_level = level_num
        self._reset_world()

        mod = self.level_modules.get(level_num)
        if mod:
            mod.setup(self.enemies, self.boss_group, Enemy, Boss,
                      self.platforms, self.powerups, Platform, PowerUp)
        for item in self.level_extras.get(level_num, []):
            kind, x = item[0], item[1]
            y = item[2] if len(item) > 2 else 330
            if kind == "kami":
                self.enemies.add(KamikazeEnemy(x, 340))
            elif kind == "sniper":
                self.enemies.add(SniperEnemy(x, y))
            elif kind == "tele":
                self.enemies.add(TeleportEnemy(x, y))
            elif kind == "mothership" and not self.boss_group.sprite:
                self.boss_group.add(MothershipBoss(x, y))
        self.checkpoint = Checkpoint(self.checkpoint_x.get(level_num, 1200))
        self.apply_difficulty()

    def start_endless(self):
        self.mode = "ENDLESS"
        self.current_level = 0
        self._reset_world()
        self.endless = EndlessDirector()
        self.endless.setup_arena(self, Platform)
        self.powerups.add(PowerUp(1220, 135, "DMG"))
        self.state = "GAME"

    def apply_difficulty(self):
        """Nhân máu quái theo độ khó (mỗi quái chỉ nhân 1 lần)."""
        mult = self.diff["enemy_hp"]
        targets = list(self.enemies)
        if self.boss_group.sprite:
            targets.append(self.boss_group.sprite)
        for e in targets:
            if not getattr(e, "_diff_scaled", False):
                e.max_hp = max(1, int(e.max_hp * mult))
                e.hp = e.max_hp
                e._diff_scaled = True

    # ==================================================================
    # TIỆN ÍCH HIỆU ỨNG
    # ==================================================================
    def add_buff(self, text, color, timer=180):
        self.active_buffs.append({"text": text, "color": color, "timer": timer, "max_timer": timer})
        if len(self.active_buffs) > 5:
            self.active_buffs.pop(0)

    def add_floater(self, x, y, text, color, big=False):
        self.floaters.append({"x": x + random.randint(-6, 6), "y": y, "vy": -2.2, "text": text,
                              "color": color, "life": 45, "big": big})

    def shake_screen(self, amount):
        self.shake = max(self.shake, amount)

    def bonus_damage(self):
        b = (self.dmg_lvl - 1) * 4 + self.cosmetic_mgr.get_total_buffs().get("dmg", 0)
        if self.dmg_boost_timer > 0:
            b += 8
        return b

    def update_camera(self):
        target_x = self.player.rect.centerx - 400
        self.camera_x = max(0, min(target_x, self.level_width - 800))

    def switch_weapon(self, weapon_key):
        if weapon_key in self.available_weapons and weapon_key in self.weapons_owned:
            self.current_weapon_key = weapon_key
            self.current_weapon = self.available_weapons[weapon_key]
            self.player.change_weapon(weapon_key)

    def cycle_weapon(self, step=1):
        owned = [k for k in WEAPON_KEYS if k in self.weapons_owned]
        if not owned:
            return
        i = owned.index(self.current_weapon_key) if self.current_weapon_key in owned else 0
        self.switch_weapon(owned[(i + step) % len(owned)])

    # ==================================================================
    # SÁT THƯƠNG
    # ==================================================================
    def hurt_player(self, amount):
        p = self.player
        if amount <= 0 or p.invincible_timer > 0 or self.dash_timer > 0:
            return
        if self.shield_timer > 0:
            self.particle_mgr.add_hit_particles(p.rect.centerx, p.rect.centery, CYBER_BLUE, 6)
            sfx.play("shield_clank.wav", 0.4)
            p.invincible_timer = 8
            return
        dmg = max(1, int(round(amount * self.diff["enemy_dmg"])))
        p.take_damage(dmg)
        self.add_floater(p.rect.centerx, p.rect.top - 8, f"-{dmg}", RED, big=True)
        self.particle_mgr.add_hit_particles(p.rect.centerx, p.rect.centery, RED, 8)
        self.shake_screen(6)
        self.hurt_flash = 14

    def damage_enemy(self, target, dmg, x=None, y=None, color=CYBER_YELLOW, source="BULLET"):
        if getattr(target, "untargetable", False) or target.hp <= 0:
            return False
        dmg = int(dmg)
        target.hp -= dmg
        target.last_hit = source
        x = target.rect.centerx if x is None else x
        y = target.rect.top if y is None else y
        self.add_floater(x, y - 6, str(dmg), color, big=dmg >= 60)
        self.particle_mgr.add_hit_particles(x, y + 10, color, 4)
        return True

    def explode(self, x, y, radius, damage, hurt_player=False, hurt_enemies=True, source="GRENADE"):
        sfx.play("explosion.wav", 0.6)
        self.shake_screen(9)
        self.blasts.append({"x": x, "y": y, "r": radius, "life": 18})
        for _ in range(3):
            self.particle_mgr.add_hit_particles(x, y, random.choice([ORANGE, CYBER_YELLOW, RED]), 10)
        if hurt_enemies:
            targets = list(self.enemies)
            if self.boss_group.sprite:
                targets.append(self.boss_group.sprite)
            for e in targets:
                ex = max(e.rect.left, min(x, e.rect.right))
                ey = max(e.rect.top, min(y, e.rect.bottom))
                if math.hypot(ex - x, ey - y) <= radius:
                    self.damage_enemy(e, damage, color=ORANGE, source=source)
        if hurt_player:
            p = self.player.rect
            px = max(p.left, min(x, p.right))
            py = max(p.top, min(y, p.bottom))
            if math.hypot(px - x, py - y) <= radius:
                self.hurt_player(damage)

    def on_enemy_killed(self, enemy, is_boss=False):
        enemy.kill()
        self.level_kills += 1
        cx, cy = enemy.rect.center
        for col in (CYBER_BLUE, CYBER_PINK, WHITE):
            self.particle_mgr.add_hit_particles(cx, cy, col, 6 if not is_boss else 25)
        sfx.play("explosion.wav", 0.25 if not is_boss else 0.8)
        self.shake_screen(3 if not is_boss else 14)

        base = 100 if is_boss else 15
        total = max(1, int(base * self.get_coin_multiplier()))
        pieces = 10 if is_boss else 3
        for i in range(pieces):
            val = total // pieces + (1 if i < total % pieces else 0)
            if val > 0:
                self.coin_pickups.add(CoinPickup(cx, cy, val))

        if isinstance(enemy, KamikazeEnemy):
            self.explode(cx, cy, enemy.BLAST_RADIUS, 40, hurt_player=False, source="KAMI")

        if self.endless:
            self.endless.score += 250 if is_boss else 10
        self.mission_event("kill")
        if is_boss:
            self.mission_event("boss")
            self.add_buff("BOSS ĐÃ BỊ HẠ!", ORANGE, 200)
        if getattr(enemy, "last_hit", "") in ("LASER", "GRENADE"):
            self.mission_event("special_kill")

    # ==================================================================
    # HÀNH ĐỘNG CỦA NGƯỜI CHƠI
    # ==================================================================
    def perform_dash(self):
        """Lướt nhanh (Q) kèm miễn nhiễm sát thương"""
        if self.dash_cooldown > 0 or self.dash_timer > 0:
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] or keys[pygame.K_LEFT] or self.touch.held("left"):
            self.dash_dir = -1
            self.player.facing_right = False
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT] or self.touch.held("right"):
            self.dash_dir = 1
            self.player.facing_right = True
        else:
            self.dash_dir = 1 if self.player.facing_right else -1
        self.dash_timer = DASH_TIME
        self.dash_cooldown = DASH_CD
        sfx.play("cyber_dash.wav", 0.6)
        self.particle_mgr.add_hit_particles(self.player.rect.centerx, self.player.rect.centery, CYBER_BLUE, 10)
        self.particle_mgr.add_hit_particles(self.player.rect.centerx, self.player.rect.centery, CYBER_PINK, 6)
        self.mission_event("dash")

    def perform_shield(self):
        if self.shield_cd > 0:
            return
        self.shield_timer = SHIELD_TIME
        self.shield_cd = SHIELD_CD
        sfx.play("electric_zap.wav", 0.5)
        self.add_buff("KHIÊN NĂNG LƯỢNG", CYBER_BLUE, SHIELD_TIME)

    def perform_slow(self):
        if self.slow_cd > 0:
            return
        self.slow_timer = SLOW_TIME
        self.slow_cd = SLOW_CD
        sfx.play("terminal_hack.wav", 0.5)
        self.add_buff("LÀM CHẬM THỜI GIAN", (170, 120, 255), SLOW_TIME)

    def auto_aim_target(self):
        """Dùng cho điện thoại / phím K: ngắm quái gần nhất (ưu tiên phía đang nhìn)."""
        p = self.player.rect
        best, best_d = None, 650
        targets = list(self.enemies)
        if self.boss_group.sprite:
            targets.append(self.boss_group.sprite)
        for e in targets:
            if getattr(e, "untargetable", False):
                continue
            dx = e.rect.centerx - p.centerx
            d = math.hypot(dx, e.rect.centery - p.centery)
            if (dx > 0) != self.player.facing_right:
                d += 250
            if d < best_d:
                best, best_d = e, d
        if best:
            return best.rect.center
        return (p.centerx + (300 if self.player.facing_right else -300), p.centery - 5)

    def perform_shoot(self, target=None):
        """Bắn theo hướng chuột (hoặc theo điểm target trong thế giới game)."""
        if target is None:
            mx, my = pygame.mouse.get_pos()
            target = (mx + self.camera_x, my)
        tx, ty = target
        self.player.facing_right = tx >= self.player.rect.centerx
        spawn_x = self.player.rect.right if self.player.facing_right else self.player.rect.left
        spawn_y = self.player.rect.centery - 5
        dx, dy = tx - spawn_x, ty - spawn_y
        dist = math.hypot(dx, dy) or 1
        dir_x, dir_y = dx / dist, dy / dist

        w = self.current_weapon
        if w.ammo < w.ammo_cost:
            if self.no_ammo_cd <= 0 and w.cooldown <= 0:
                self.add_floater(self.player.rect.centerx, self.player.rect.top - 14, "HẾT ĐẠN!", ORANGE)
                sfx.play("reload.wav", 0.3)
                self.no_ammo_cd = 45
            return
        ok, used = w.shoot(x=spawn_x, y=spawn_y, dir_x=dir_x, dir_y=dir_y, player_ammo=w.ammo,
                           bullet_group=self.player_bullets, bonus_dmg=self.bonus_damage())
        if not ok:
            return
        w.ammo -= used
        self.player.shoot_directional()
        if w.type == "LASER":
            self.fire_laser(*w.last_beam)
        sound = {"BLASTER": ("pistol.wav", 0.35), "SHOTGUN": ("shotgun.wav", 0.5),
                 "ASSAULT_RIFLE": ("pistol.wav", 0.2), "LASER": ("laser_pulse.wav", 0.5),
                 "GRENADE": ("fireball.wav", 0.5)}.get(w.type)
        if sound:
            sfx.play(*sound)
        if w.type in ("SHOTGUN", "GRENADE"):
            self.shake_screen(3)

    def fire_laser(self, x, y, dx, dy, dmg):
        end = (x + dx * 900, y + dy * 900)
        targets = list(self.enemies)
        if self.boss_group.sprite:
            targets.append(self.boss_group.sprite)
        for e in targets:
            if e.rect.clipline((x, y), end):
                self.damage_enemy(e, dmg, color=CYBER_BLUE, source="LASER")   # xuyên cả khiên
        self.beams.append({"p1": (x, y), "p2": end, "life": 10})
        self.shake_screen(2)

    def perform_slash_attack(self):
        if not self.player.can_slash():
            return
        self.player.attack('slash')

        slash_range = 75
        pr = self.player.rect
        if self.player.facing_right:
            slash_rect = pygame.Rect(pr.right - 10, pr.top - 15, slash_range, pr.height + 30)
        else:
            slash_rect = pygame.Rect(pr.left - slash_range + 10, pr.top - 15, slash_range, pr.height + 30)

        bonus_dmg = self.bonus_damage()
        damage = self.available_weapons["Blaster"].damage + bonus_dmg + 15

        for _ in range(8):
            px = slash_rect.centerx + random.randint(-15, 15)
            py = slash_rect.centery + random.randint(-15, 15)
            self.particle_mgr.add_hit_particles(px, py, CYBER_BLUE, 1)

        # PARRY: chém bật ngược đạn của quái
        parry_rect = slash_rect.inflate(20, 20)
        parried = 0
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
                parried += 1
        if parried:
            sfx.play("ricochet.wav", 0.6)
            self.add_buff("PARRY DEFLECT!", CYBER_BLUE, 60)
            self.mission_event("parry", parried)

        for enemy in list(self.enemies):
            if slash_rect.colliderect(enemy.rect):
                if hasattr(enemy, "break_shield"):
                    enemy.break_shield(150)
                self.damage_enemy(enemy, damage, color=CYBER_BLUE, source="SLASH")
        boss = self.boss_group.sprite
        if boss and slash_rect.colliderect(boss.rect):
            self.damage_enemy(boss, damage, color=CYBER_BLUE, source="SLASH")

    # ==================================================================
    # CHECKPOINT / CHẾT / QUA MÀN
    # ==================================================================
    def respawn_at_checkpoint(self):
        cp = self.checkpoint
        p = self.player
        p.rect.midbottom = (cp.rect.centerx, FLOOR_Y)
        p.vel_x = p.vel_y = 0
        p.hp = p.max_hp
        p.invincible_timer = 90
        self.enemy_bullets.empty()
        self.dash_timer = 0
        self.deaths_in_level += 1
        self.touch.reset()
        self.state = "GAME"
        self.particle_mgr.add_hit_particles(p.rect.centerx, p.rect.centery, CYBER_BLUE, 20)
        sfx.play("shield_pickup.wav", 0.6)

    def trigger_death(self):
        """Người chơi hết máu: nổ tung, lưu tiến trình, chuyển sang màn hình BẠN ĐÃ CHẾT."""
        cx, cy = self.player.rect.centerx, self.player.rect.centery
        self.particle_mgr.add_death_explosion(cx, cy)
        sfx.play("player_death.wav", 0.8)
        self.shake_screen(12)
        boss = self.boss_group.sprite
        self.death_stats = {
            "mode": self.mode,
            "level": self.current_level,
            "kills": self.level_kills,
            "coins": max(0, self.coins - self.level_coins_start),
            "seconds": self.level_frames // 60,
            "boss_hp": (max(0, boss.hp), boss.max_hp) if boss else None,
        }
        if self.endless:
            score, wave = self.endless.score, self.endless.wave
            best_before = max([s["score"] for s in self.endless_scores], default=0)
            self.endless_scores.append({"score": score, "wave": wave, "date": today_str()})
            self.endless_scores.sort(key=lambda s: -s["score"])
            self.endless_scores = self.endless_scores[:5]
            self.death_stats.update({"score": score, "wave": wave,
                                     "best": max(best_before, score), "new_record": score > best_before})
            self.mission_event("wave", wave)
        self.dash_timer = 0
        self.death_timer = 0
        self.touch.reset()
        self.state = "GAME_OVER"
        self.save_progress()

    def complete_level(self):
        self.level_completed = True
        lvl = self.current_level
        leftover = sum(c.value for c in self.coin_pickups)   # tự gom coin còn rơi trên sàn
        self.coin_pickups.empty()
        if leftover:
            self.coins += leftover
            self.mission_event("coins", leftover)
        secs = self.level_frames / 60
        stars = 1 + (self.deaths_in_level == 0) + (secs <= par_time(lvl))
        prev = int(self.stars.get(str(lvl), 0))
        new_best = max(prev, stars)
        star_bonus = 40 * (new_best - prev)
        reward = int((50 + lvl * 25) * self.get_coin_multiplier())
        self.coins += reward + star_bonus
        self.stars[str(lvl)] = new_best
        self.max_unlocked_level = max(self.max_unlocked_level, min(8, lvl + 1))
        self.clear_stats = {
            "level": lvl, "stars": stars, "seconds": int(secs), "par": par_time(lvl),
            "kills": self.level_kills, "deaths": self.deaths_in_level,
            "reward": reward, "star_bonus": star_bonus,
            "earned": max(0, self.coins - self.level_coins_start),
            "final": lvl == 8,
        }
        self.mission_event("clear")
        if stars == 3 and prev < 3:
            self.mission_event("star3")
        self.clear_timer = 0
        self.touch.reset()
        self.state = "LEVEL_CLEAR"
        sfx.play("level_up.wav", 0.7)
        self.save_progress()

    def on_wave_start(self, wave):
        sfx.play("alarm_siren.wav", 0.35)

    def on_wave_cleared(self, wave):
        bonus = int(10 * wave * self.get_coin_multiplier())
        self.coins += bonus
        self.add_buff(f"WAVE {wave} XONG +{bonus}", CYBER_YELLOW, 150)
        self.mission_event("wave", wave)
        px = self.player.rect.centerx
        self.powerups.add(PowerUp(max(60, min(2340, px + random.choice((-160, 160)))), 340, "AMMO"))
        if wave % 2 == 0:
            self.powerups.add(PowerUp(max(60, min(2340, px + random.choice((-240, 240)))), 340, "HP"))
        if wave % 3 == 0:
            self.powerups.add(PowerUp(1220, 135, random.choice(["DMG", "SPEED"])))

    # ==================================================================
    # NÚT TRÊN CÁC MÀN HÌNH PHỦ (TẠM DỪNG / CHẾT / QUA MÀN)
    # ==================================================================
    def overlay_buttons(self):
        """Danh sách (mã, Rect, nhãn, màu) - dùng chung cho vẽ và bấm."""
        if self.state == "GAME_OVER":
            btns = []
            if self.mode == "STORY" and self.checkpoint and self.checkpoint.active:
                btns.append(("checkpoint", "[C] HỒI SINH", CYBER_PINK))
            btns += [("retry", "[R] CHƠI LẠI", GREEN), ("menu", "[M] VỀ MENU", CYBER_BLUE)]
            y = 400
        elif self.state == "PAUSED":
            btns = [("resume", "[ESC] TIẾP TỤC", GREEN), ("retry", "[R] CHƠI LẠI", CYBER_YELLOW),
                    ("menu", "[M] VỀ MENU", CYBER_BLUE)]
            y = 300
        elif self.state == "LEVEL_CLEAR":
            btns = []
            if self.current_level < 8:
                btns.append(("next", "[N] MÀN TIẾP", GREEN))
            btns += [("retry", "[R] CHƠI LẠI", CYBER_YELLOW), ("menu", "[M] VỀ MENU", CYBER_BLUE)]
            y = 400
        else:
            return []
        w, gap = 170, 18
        total = len(btns) * w + (len(btns) - 1) * gap
        x0 = (800 - total) // 2
        return [(key, pygame.Rect(x0 + i * (w + gap), y, w, 46), label, col)
                for i, (key, label, col) in enumerate(btns)]

    def overlay_ready(self):
        if self.state == "GAME_OVER":
            return self.death_timer >= self.GAMEOVER_INPUT_DELAY
        if self.state == "LEVEL_CLEAR":
            return self.clear_timer >= 30
        return True

    def do_overlay_action(self, key):
        if key == "checkpoint":
            self.respawn_at_checkpoint()
        elif key == "retry":
            if self.mode == "ENDLESS":
                self.start_endless()
            else:
                self.start_level(self.current_level)
                self.state = "GAME"
        elif key == "menu":
            self.exit_to_menu()
        elif key == "resume":
            self.state = "GAME"
        elif key == "next":
            self.start_level(min(8, self.current_level + 1))
            self.state = "GAME"

    def exit_to_menu(self):
        self.save_progress()
        if self.mode == "ENDLESS":
            self.start_level(min(self.max_unlocked_level, 8))
        self.touch.reset()
        self.state = "MENU"

    KEY_ACTIONS = {pygame.K_c: "checkpoint", pygame.K_r: "retry", pygame.K_m: "menu",
                   pygame.K_n: "next", pygame.K_p: "resume"}

    def handle_overlay_event(self, event):
        if not self.overlay_ready():
            return
        btns = self.overlay_buttons()
        keys = [b[0] for b in btns]
        action = None
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                action = keys[0] if keys else None
            elif event.key == pygame.K_ESCAPE:
                action = "resume" if self.state == "PAUSED" else "menu"
            else:
                action = self.KEY_ACTIONS.get(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, rect, _, _ in btns:
                if rect.collidepoint(event.pos):
                    action = key
        if action in keys:
            self.do_overlay_action(action)

    # ==================================================================
    # SỰ KIỆN
    # ==================================================================
    def handle_event(self, event):
        if self.touch.handle_event(event, self.state == "GAME"):
            return
        if self.state in self.OVERLAY_STATES:
            self.handle_overlay_event(event)
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.state in self.MENU_STATES:
                self.state = self.menu.handle_click(event.pos, self.state, self)
            elif self.state == "GAME" and not getattr(event, "touch", False):
                if event.button == 1:
                    self.perform_shoot()
                elif event.button == 3:
                    self.perform_slash_attack()
        elif event.type == pygame.MOUSEWHEEL and self.state == "GAME":
            self.cycle_weapon(-1 if event.y > 0 else 1)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state == "GAME":
                    self.state = "PAUSED"
                elif self.state in ("LEVEL_SELECT", "SHOP", "MISSIONS"):
                    self.state = "MENU"
                return
            if self.state != "GAME":
                return
            k = event.key
            if k in (pygame.K_w, pygame.K_SPACE, pygame.K_UP):
                self.do_jump()
            elif k == pygame.K_p:
                self.state = "PAUSED"
            elif k == pygame.K_q:
                self.perform_dash()
            elif k == pygame.K_e:
                self.perform_shield()
            elif k == pygame.K_f:
                self.perform_slow()
            elif k == pygame.K_j:
                self.perform_slash_attack()
            elif k == pygame.K_k:
                self.perform_shoot(self.auto_aim_target())
            elif pygame.K_1 <= k <= pygame.K_5:
                self.switch_weapon(WEAPON_KEYS[k - pygame.K_1])

    def do_jump(self):
        if self.player.on_ground:
            self.particle_mgr.add_jump_dust(self.player.rect.centerx, self.player.rect.bottom)
        self.player.jump()

    def handle_touch_actions(self):
        for key in self.touch.take_pressed():
            if key == "jump":
                self.do_jump()
            elif key == "dash":
                self.perform_dash()
            elif key == "slash":
                self.perform_slash_attack()
            elif key == "shield":
                self.perform_shield()
            elif key == "slow":
                self.perform_slow()
            elif key == "weapon":
                self.cycle_weapon(1)
            elif key == "pause":
                self.state = "PAUSED"

    # ==================================================================
    # VÒNG LẶP LOGIC
    # ==================================================================
    def _update_effects(self):
        self.particle_mgr.update()
        for f in self.floaters[:]:
            f["y"] += f["vy"]
            f["vy"] *= 0.93
            f["life"] -= 1
            if f["life"] <= 0:
                self.floaters.remove(f)
        for b in self.beams[:]:
            b["life"] -= 1
            if b["life"] <= 0:
                self.beams.remove(b)
        for b in self.blasts[:]:
            b["life"] -= 1
            if b["life"] <= 0:
                self.blasts.remove(b)
        self.shake *= 0.85
        if self.shake < 0.4:
            self.shake = 0
        if self.hurt_flash > 0:
            self.hurt_flash -= 1

    def update_game_logic(self):
        self.frame += 1
        if self.state == "LEVEL_CLEAR":
            self.clear_timer += 1
            self._update_effects()
            return
        if self.state == "GAME_OVER":
            self.death_timer += 1
            self._update_effects()
            return
        if self.state != "GAME":
            return

        self.level_frames += 1
        for name in ("dash_cooldown", "shield_timer", "shield_cd", "slow_timer", "slow_cd",
                     "dmg_boost_timer", "no_ammo_cd"):
            v = getattr(self, name)
            if v > 0:
                setattr(self, name, v - 1)
        slow = self.slow_timer > 0
        tick_enemies = (not slow) or (self.frame % 2 == 0)

        self.current_weapon.update()
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        if self.touch.enabled:
            if self.touch.held("left"):
                self.player.vel_x = -self.player.speed
                self.player.facing_right = False
            elif self.touch.held("right"):
                self.player.vel_x = self.player.speed
                self.player.facing_right = True
            self.handle_touch_actions()
            if self.state != "GAME":
                return
        self.player.update(floor_y=FLOOR_Y, platforms=self.platforms, level_width=self.level_width)

        # Lướt
        if self.dash_timer > 0:
            self.dash_timer -= 1
            self.player.rect.x += self.dash_dir * self.dash_speed
            self.player.rect.x = max(0, min(self.player.rect.x, self.level_width - self.player.rect.width))
            self.player.vel_y = 0
            self.particle_mgr.add_hit_particles(self.player.rect.centerx,
                                                self.player.rect.centery + random.randint(-12, 12), CYBER_BLUE, 2)
            self.particle_mgr.add_hit_particles(self.player.rect.centerx,
                                                self.player.rect.centery + random.randint(-8, 8), CYBER_PINK, 1)

        # Bắn liên tục: giữ chuột trái với Rifle, hoặc giữ nút BẮN trên điện thoại
        if self.touch.held("shoot"):
            if self.current_weapon.cooldown <= 0:
                self.perform_shoot(self.auto_aim_target())
        elif (not self.touch.enabled and pygame.mouse.get_pressed()[0]
              and self.current_weapon.type == "ASSAULT_RIFLE"):
            self.perform_shoot()

        self.update_camera()
        self.player_bullets.update()
        if tick_enemies:
            self.enemy_bullets.update()
        self.powerups.update()
        for c in self.coin_pickups:
            c.update(self.player)

        # Nhặt vật phẩm
        for p in pygame.sprite.spritecollide(self.player, self.powerups, True):
            if p.type == "HP":
                self.player.hp = min(self.player.max_hp, self.player.hp + 30)
                self.particle_mgr.add_hit_particles(p.rect.centerx, p.rect.centery, GREEN, 8)
                self.add_buff("+30 HP RECOVER", GREEN, 180)
            elif p.type == "DMG":
                self.dmg_boost_timer = DMG_BOOST_TIME
                self.particle_mgr.add_hit_particles(p.rect.centerx, p.rect.centery, CYBER_YELLOW, 8)
                self.add_buff("+8 DMG BOOST (10s)", CYBER_YELLOW, DMG_BOOST_TIME)
            elif p.type == "SPEED":
                self.player.speed += 1
                self.particle_mgr.add_hit_particles(p.rect.centerx, p.rect.centery, CYBER_PINK, 8)
                self.add_buff("+1 SPEED UP", CYBER_PINK, 240)
            elif p.type == "AMMO":
                for w in self.available_weapons.values():
                    w.ammo = w.max_ammo
                self.particle_mgr.add_hit_particles(p.rect.centerx, p.rect.centery, ORANGE, 8)
                self.add_buff("FULL AMMO REFILL", ORANGE, 180)
            sfx.play("potion_drink.wav", 0.4)
        got = 0
        for c in pygame.sprite.spritecollide(self.player, self.coin_pickups, True):
            got += c.value
        if got:
            self.coins += got
            sfx.play("coin.wav", 0.35)
            self.mission_event("coins", got)

        # Checkpoint
        cp = self.checkpoint
        if cp:
            cp.update()
            if not cp.active and self.player.rect.colliderect(cp.rect):
                cp.active = True
                self.player.hp = min(self.player.max_hp, self.player.hp + 20)
                self.add_buff("ĐÃ LƯU CHECKPOINT", CYBER_BLUE, 180)
                self.particle_mgr.add_hit_particles(cp.rect.centerx, cp.rect.top, CYBER_BLUE, 20)
                sfx.play("chest_open.wav", 0.5)

        for buff in self.active_buffs[:]:
            buff["timer"] -= 1
            if buff["timer"] <= 0:
                self.active_buffs.remove(buff)

        # Quái + boss
        boss = self.boss_group.sprite
        if tick_enemies:
            for enemy in list(self.enemies):
                try:
                    enemy.update(self.enemy_bullets, self.player)
                except TypeError:
                    enemy.update()
            if boss:
                boss.update(self.player, self.enemy_bullets)
                queue = getattr(boss, "spawn_queue", None)
                if queue:
                    for e in queue:
                        self.enemies.add(e)
                    queue.clear()
                    self.apply_difficulty()

        for enemy in list(self.enemies):
            if getattr(enemy, "explode_now", False):          # Kamikaze tự nổ
                enemy.kill()
                self.explode(enemy.rect.centerx, enemy.rect.centery, enemy.BLAST_RADIUS,
                             enemy.BLAST_DAMAGE, hurt_player=True, hurt_enemies=False, source="KAMI")
            elif enemy.hp <= 0:
                self.on_enemy_killed(enemy)
        if boss and boss.hp <= 0:
            self.on_enemy_killed(boss, is_boss=True)
            boss = None

        # Đạn của người chơi trúng quái
        for b in list(self.player_bullets):
            if getattr(b, "explosive", False):
                hit = b.rect.bottom >= FLOOR_Y
                if not hit and b.dy > 0:
                    hit = any(p.rect.colliderect(b.rect) for p in self.platforms)
                if not hit:
                    hit = any(e.rect.colliderect(b.rect) and not getattr(e, "untargetable", False)
                              for e in self.enemies) or (boss is not None and boss.rect.colliderect(b.rect))
                if hit:
                    self.explode(b.rect.centerx, b.rect.centery, b.radius, b.damage)
                    b.kill()
                continue
            source = "PARRY" if getattr(b, "parried", False) else "BULLET"
            for enemy in self.enemies:
                if not enemy.rect.colliderect(b.rect) or getattr(enemy, "untargetable", False):
                    continue
                if hasattr(enemy, "is_blocked") and enemy.is_blocked(b.rect.centerx):
                    self.particle_mgr.add_hit_particles(b.rect.centerx, b.rect.centery, CYBER_BLUE, 6)
                    sfx.play("shield_clank.wav", 0.35)
                    self.add_floater(b.rect.centerx, b.rect.top - 6, "CHẶN", CYBER_BLUE)
                else:
                    dmg = b.damage * (1.5 if getattr(enemy, "shield_active", False) else 1)
                    self.damage_enemy(enemy, dmg, b.rect.centerx, b.rect.centery,
                                      CYBER_BLUE if source == "PARRY" else CYBER_YELLOW, source)
                b.kill()
                break
            if b.alive() and boss and boss.rect.colliderect(b.rect):
                self.damage_enemy(boss, b.damage, b.rect.centerx, b.rect.centery,
                                  CYBER_BLUE if source == "PARRY" else CYBER_YELLOW, source)
                b.kill()

        # Người chơi trúng đòn (lướt thì miễn nhiễm)
        if self.dash_timer <= 0:
            for bullet in pygame.sprite.spritecollide(self.player, self.enemy_bullets, True):
                self.hurt_player(bullet.damage)
            for enemy in pygame.sprite.spritecollide(self.player, self.enemies, False):
                self.hurt_player(getattr(enemy, "damage", 10))
            if boss and self.player.rect.colliderect(boss.rect):
                self.hurt_player(getattr(boss, "damage", 20))

        self._update_effects()

        if self.player.hp <= 0:
            self.trigger_death()
            return

        if self.mode == "ENDLESS":
            self.endless.update(self)
        elif len(self.enemies) == 0 and not self.boss_group.sprite and not self.level_completed:
            self.complete_level()
