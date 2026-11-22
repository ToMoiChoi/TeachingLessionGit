import pygame
import random
import math
from config import CYBER_YELLOW, CYBER_PINK, CYBER_BLUE, ORANGE

# --- BẢNG MÀU VÀ NGUYÊN MẪU MODEL VŨ KHÍ (PIXEL ART) ---
COLOR_MAP = {
    '#': (20, 20, 25),       # Viền ngoài
    'C': (0, 220, 255),     # Lõi năng lượng xanh
    'P': (255, 0, 160),     # Lõi năng lượng hồng/plasma
    'Y': (255, 220, 0),     # Chi tiết vàng neon
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

SMG_PIXELS = [
    "....................",
    "...############.....",
    "..#XXCCCCCCCCXX###..",
    ".#XXXXXXXXXXXXXXXX#.",
    ".####DD####GGGG####.",
    "....#DD#...#GG#.....",
    "....#DD#...#GG#.....",
    ".....##.....##......",
]

LASER_PIXELS = [
    "..........................",
    "...######.................",
    "..#XXXXXX################.",
    ".#XXCCCCXXXXXXXXXXXXXXXXC#",
    ".#XXCCCCXXXXXXXXXXXXXXXXC#",
    "..#XXXXXX################.",
    "...#DD#GGGG#..............",
    "...#DD#####...............",
    "...#DD#...................",
    "....##....................",
]

GRENADE_PIXELS = [
    "......................",
    "...########...........",
    "..#XXXXXXXX##########.",
    ".#XXGGGGGGXXXXXXXXXXX#",
    ".#XXGGGGGGXXX#######X#",
    ".#XXGGGGGGXXX#.....#X#",
    "..#XXXXXXXX##########.",
    "...#DD#..#DD#.........",
    "...#DD#..####.........",
    "....##................",
]

PLASMA_PIXELS = [
    "........................",
    "..########..............",
    ".#XXPPPPPP#############.",
    "#XXPPPPPPPPXXPPPPXXXXXP#",
    "#XXPPPPPPPPXXPPPPXXXXXP#",
    ".#XXPPPPPP#############.",
    "..###DD###GGGG#.........",
    "....#DD#..#####.........",
    ".....##.................",
]

RAILGUN_PIXELS = [
    "............................",
    "..#########.................",
    ".#XXYYYYYYY################.",
    "#XXYYPPPPPPYYYYYYYYYYYYYYYY#",
    "#XXYYPPPPPPYYYYYYYYYYYYYYYY#",
    ".#XXYYYYYYY################.",
    "...#DD#..#GGGG#.............",
    "...#DD#..######.............",
    "....##......................",
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
    def __init__(self, x, y, dx, dy, damage=20, color=CYBER_YELLOW, size=(10, 4), pierce=0, plasma=False):
        super().__init__()
        self.rect = pygame.Rect(x, y, size[0], size[1])
        self.fx = float(x)
        self.fy = float(y)
        self.dx = dx
        self.dy = dy
        self.damage = damage
        self.color = color
        self.pierce = pierce
        self.plasma = plasma
        self.hit_ids = set()

    def update(self):
        self.fx += self.dx
        self.fy += self.dy
        self.rect.x = int(self.fx)
        self.rect.y = int(self.fy)
        if self.rect.x < -100 or self.rect.x > 2600 or self.rect.y < -100 or self.rect.y > 700:
            self.kill()


class Grenade(Bullet):
    """Lựu đạn bay theo đường cong, nổ khi chạm đất / quái (gameplay xử lý vụ nổ)."""
    explosive = True

    def __init__(self, x, y, dx, dy, damage):
        super().__init__(x, y, dx, dy, damage=damage, color=(120, 255, 90), size=(10, 10))
        self.radius = 95
        self.spin = 0

    def update(self):
        self.dy += 0.38
        self.fx += self.dx
        self.fy += self.dy
        self.rect.x, self.rect.y = int(self.fx), int(self.fy)
        self.spin += 1
        if self.rect.x < -100 or self.rect.x > 2600 or self.rect.y > 700:
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
        pixel_map = {
            "BLASTER": PISTOL_PIXELS,
            "SHOTGUN": SHOTGUN_PIXELS,
            "ASSAULT_RIFLE": ASSAULT_RIFLE_PIXELS,
            "SMG": SMG_PIXELS,
            "LASER": LASER_PIXELS,
            "GRENADE": GRENADE_PIXELS,
            "PLASMA": PLASMA_PIXELS,
            "RAILGUN": RAILGUN_PIXELS,
        }
        self.image = create_weapon_surface(pixel_map.get(self.type, PISTOL_PIXELS), scale=2)

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

        # 4. SMG: Tốc độ bắn siêu nhanh, đạn xanh neon
        elif self.type == "SMG":
            base_angle = math.atan2(dir_y, dir_x)
            spread_angle = base_angle + math.radians(random.uniform(-6, 6))
            speed = 18
            p_dx = math.cos(spread_angle) * speed
            p_dy = math.sin(spread_angle) * speed
            bullet = Bullet(x, y, p_dx, p_dy, damage=total_dmg, color=CYBER_BLUE, size=(10, 3))
            bullet_group.add(bullet)

        # 5. LASER: tia xuyên thấu tức thời (gameplay tính sát thương theo đường thẳng)
        elif self.type == "LASER":
            self.last_beam = (x, y, dir_x, dir_y, total_dmg, "LASER")

        # 6. GRENADE: lựu đạn bay vòng cung
        elif self.type == "GRENADE":
            speed = 11
            bullet_group.add(Grenade(x, y, dir_x * speed, dir_y * speed - 3, total_dmg))

        # 7. PLASMA: cầu năng lượng lớn, xuyên tối đa 2 mục tiêu
        elif self.type == "PLASMA":
            speed = 13
            bullet = Bullet(x - 4, y - 4, dir_x * speed, dir_y * speed,
                            damage=total_dmg, color=(200, 90, 255), size=(14, 14), pierce=2, plasma=True)
            bullet_group.add(bullet)

        # 8. RAILGUN: tia siêu thanh xuyên thấu cực mạnh
        elif self.type == "RAILGUN":
            self.last_beam = (x, y, dir_x, dir_y, total_dmg, "RAILGUN")

        return True, self.ammo_cost


# Súng mua thêm trong cửa hàng (tab VŨ KHÍ): tên khóa -> (giá, mô tả)
SHOP_WEAPONS = {
    "SMG": (550, "Bắn siêu tốc, băng đạn lớn, giữ chuột liên thanh"),
    "Laser": (800, "Tia xuyên thấu mọi quái & khiên trên đường bắn"),
    "Grenade": (1200, "Lựu đạn nổ lan, gây sát thương diện rộng"),
    "Plasma": (1500, "Cầu Plasma sát thương cao, xuyên qua 2 mục tiêu"),
    "Railgun": (2200, "Tia siêu thanh xuyên phá toàn màn hình cực mạnh"),
}
WEAPON_KEYS = ["Blaster", "Shotgun", "Rifle", "SMG", "Laser", "Grenade", "Plasma", "Railgun"]   # phím 1..8

WEAPON_LIST = {
    "Blaster": Weapon(name="Blaster", damage=20, fire_rate=15, ammo_cost=1, weapon_type="BLASTER", max_ammo=18),
    "Shotgun": Weapon(name="Shotgun", damage=45, fire_rate=40, ammo_cost=1, weapon_type="SHOTGUN", max_ammo=7),
    "Rifle": Weapon(name="Assault Rifle", damage=12, fire_rate=5, ammo_cost=1, weapon_type="ASSAULT_RIFLE", max_ammo=25),
    "SMG": Weapon(name="Cyber Dual-SMG", damage=11, fire_rate=4, ammo_cost=1, weapon_type="SMG", max_ammo=40),
    "Laser": Weapon(name="Laser Lance", damage=38, fire_rate=32, ammo_cost=1, weapon_type="LASER", max_ammo=10),
    "Grenade": Weapon(name="Grenade Launcher", damage=70, fire_rate=50, ammo_cost=1, weapon_type="GRENADE", max_ammo=6),
    "Plasma": Weapon(name="Plasma Cannon", damage=58, fire_rate=28, ammo_cost=1, weapon_type="PLASMA", max_ammo=12),
    "Railgun": Weapon(name="Hyper Railgun", damage=95, fire_rate=48, ammo_cost=1, weapon_type="RAILGUN", max_ammo=8),
}
