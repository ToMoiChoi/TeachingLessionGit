import pygame
import random
import math
from config import CYBER_YELLOW, CYBER_PINK, CYBER_BLUE, ORANGE

# --- BẢNG MÀU VÀ NGUYÊN MẪU MODEL VŨ KHÍ (PIXEL ART) ---
COLOR_MAP = {
    '#': (20, 20, 25),       # Viền ngoài
    'X': (220, 220, 235),   # Thân súng kim loại
    'D': (100, 105, 115),   # Tay cầm / Chi tiết tối
    'G': (70, 75, 85),      # Ốp lót dưới
    '.': None               # Trong suốt
}

PISTOL_PIXELS = [
    "................",
    "....#########...",
    "...#XXXXXXXXX#..",
    "..#XXXXXXXXXXX#.",
    "..###########X#.",
    "....#DD#....##..",
    "....#DD#........",
    "....#DD#........",
    ".....##.........",
    "................"
]

SHOTGUN_PIXELS = [
    "........................",
    "........................",
    "..######................",
    ".#DDDDDD################",
    "#DDDDDDDD#GGGG#XXXXXXXX#",
    ".######DD#GGGG##########",
    ".......#D#..............",
    "........##.............."
]

ASSAULT_RIFLE_PIXELS = [
    "........................",
    "...................#....",
    "....##############.#....",
    "...#XXXXXXXXXXXXXX###...",
    "..#XXXXXXXXXXXXXXXXXX#..",
    "..#XX##########XXXXXX#..",
    ".##D#....#GGGG#..######.",
    ".#DD#....#GGGG#.........",
    ".#DD#....######.........",
    "..##....................",
]

def create_weapon_surface(pixel_data, scale=2, palette=COLOR_MAP):
    height = len(pixel_data)
    width = max(len(row) for row in pixel_data)
    surface = pygame.Surface((width * scale, height * scale), pygame.SRCALPHA)
    for y, row in enumerate(pixel_data):
        for x, char in enumerate(row):
            color = palette.get(char)
            if color:
                rect = pygame.Rect(x * scale, y * scale, scale, scale)
                pygame.draw.rect(surface, color, rect)
    return surface


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, dx, dy, damage=20, color=CYBER_YELLOW, size=(10, 4)):
        super().__init__()
        self.rect = pygame.Rect(x, y, size[0], size[1])
        self.dx = dx
        self.dy = dy
        self.damage = damage
        self.color = color

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        if self.rect.x < -100 or self.rect.x > 2500 or self.rect.y < -100 or self.rect.y > 700:
            self.kill()


class Weapon:
    def __init__(self, name, damage, fire_rate, ammo_cost, weapon_type="BLASTER", max_ammo=18):
        self.name = name
        self.damage = damage
        self.fire_rate = fire_rate
        self.cooldown = 0
        self.ammo_cost = ammo_cost
        self.type = weapon_type
        self.max_ammo = max_ammo
        self.ammo = max_ammo

        # Khởi tạo model hình ảnh (self.image) theo từng loại súng
        if self.type == "BLASTER":
            self.image = create_weapon_surface(PISTOL_PIXELS, scale=2)
        elif self.type == "SHOTGUN":
            self.image = create_weapon_surface(SHOTGUN_PIXELS, scale=2)
        elif self.type == "ASSAULT_RIFLE":
            self.image = create_weapon_surface(ASSAULT_RIFLE_PIXELS, scale=2)
        else:
            self.image = create_weapon_surface(PISTOL_PIXELS, scale=2)

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= 1

    def can_shoot(self, current_ammo):
        return self.cooldown <= 0 and current_ammo >= self.ammo_cost

    def add_ammo(self, amount):
        self.ammo = min(self.max_ammo, self.ammo + amount)

    def shoot(self, x, y, dir_x, dir_y, player_ammo, bullet_group, bonus_dmg=0):
        if not self.can_shoot(player_ammo):
            return False, 0

        self.cooldown = self.fire_rate
        total_dmg = self.damage + bonus_dmg

        # 1. BLASTER: Bắn chính xác theo hướng chuột
        if self.type == "BLASTER":
            speed = 15
            bullet = Bullet(x, y, dir_x * speed, dir_y * speed, damage=total_dmg, color=CYBER_YELLOW)
            bullet_group.add(bullet)

        # 2. SHOTGUN: Bắn tỏa chùm 5 viên quanh hướng chuột
        elif self.type == "SHOTGUN":
            pellets = 5
            pellet_dmg = max(5, int(total_dmg / 3))
            base_angle = math.atan2(dir_y, dir_x)
            for _ in range(pellets):
                spread_angle = base_angle + math.radians(random.uniform(-15, 15))
                speed = random.uniform(11, 15)
                p_dx = math.cos(spread_angle) * speed
                p_dy = math.sin(spread_angle) * speed
                bullet = Bullet(x, y, p_dx, p_dy, damage=pellet_dmg, color=ORANGE, size=(6, 6))
                bullet_group.add(bullet)

        # 3. ASSAULT RIFLE: Liên thanh có độ giật nhẹ quanh hướng chuột
        elif self.type == "ASSAULT_RIFLE":
            base_angle = math.atan2(dir_y, dir_x)
            spread_angle = base_angle + math.radians(random.uniform(-3, 3))
            speed = 17
            p_dx = math.cos(spread_angle) * speed
            p_dy = math.sin(spread_angle) * speed
            bullet = Bullet(x, y, p_dx, p_dy, damage=total_dmg, color=CYBER_PINK, size=(12, 3))
            bullet_group.add(bullet)

        return True, self.ammo_cost


WEAPON_LIST = {
    "Blaster": Weapon(name="Blaster", damage=20, fire_rate=15, ammo_cost=1, weapon_type="BLASTER", max_ammo=18),
    "Shotgun": Weapon(name="Shotgun", damage=45, fire_rate=40, ammo_cost=1, weapon_type="SHOTGUN", max_ammo=7),
    "Rifle": Weapon(name="Assault Rifle", damage=12, fire_rate=5, ammo_cost=1, weapon_type="ASSAULT_RIFLE", max_ammo=25)
}