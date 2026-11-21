import time
import random
import math


class Weapon:

    def __init__(
        self,
        name,
        damage=40,
        fire_rate=0.095,
        magazine=25,
        reserve=75,
        price=0,
        category="RIFLE",
        fire_mode="Full-Auto",
        damage_table=None,
        reload_time=1.8,
        description="",
        scoped_fire_rate=None,
        scoped_zoom=None,
        scoped_recoil_mult=0.7,
        burst_count=1,
        secondary_fire_mode=None
    ):
        """
        Khởi tạo vũ khí. Tương thích hoàn toàn với code gốc:
        Weapon(name, damage, fire_rate, magazine, reserve)
        Đồng thời hỗ trợ đầy đủ bảng sát thương theo cự ly mét (PDF) và chế độ bắn phụ (Scope / Burst).
        """
        self.name = name
        self.id = name.upper()
        self.category = category
        self.price = price

        self.damage = damage
        self.fire_rate = fire_rate

        self.magazine = magazine
        self.max_magazine = magazine
        self.reserve = reserve

        self.fire_mode = fire_mode
        self.reload_time = reload_time
        self.description = description

        # Chế độ bắn phụ / Ống ngắm (Scope / Burst / Giảm giãn hồng tâm)
        self.scoped_fire_rate = scoped_fire_rate if scoped_fire_rate is not None else fire_rate
        self.scoped_zoom = scoped_zoom
        self.scoped_recoil_mult = scoped_recoil_mult
        self.burst_count = burst_count
        self.secondary_fire_mode = secondary_fire_mode

        # Bảng sát thương theo cự ly mét [(max_range_m, {"body": ..., "head": ..., "legs": ...})]
        if damage_table is not None:
            self.damage_table = damage_table
        else:
            self.damage_table = [
                (50.0, {"body": damage, "head": int(damage * 3), "legs": int(damage * 0.85)})
            ]

        # File ảnh skin súng tương ứng trong assets/skin súng
        self.skin_file = {
            "CLASSIC": "classic.png",
            "GHOST": "ghost.png",
            "SHERIFF": "sheriff.png",
            "MP5": "mp5.png",
            "UMP": "ump.png",
            "M014": "m1014.png",
            "MAG-7": "mag-7.png",
            "MAG7": "mag-7.png",
            "AK-47": "vandal.png",
            "AK47": "vandal.png",
            "VANDAL": "vandal.png",
            "M416": "m416.png",
            "PHANTOM": "m416.png",
            "GUARDIAN": "guardian.png",
            "M24": "m24.png",
            "AWM": "awm.png",
            "KNIFE": "knife.png",
        }.get(self.id, "")

        self.last_shot = 0.0

    def can_fire(self):
        now = time.time()
        return (
            now - self.last_shot >= self.fire_rate
            and self.magazine > 0
        )

    def fire(self):
        if not self.can_fire():
            return False
        self.magazine -= 1
        self.last_shot = time.time()
        return True

    def reload(self):
        if self.magazine >= self.max_magazine or self.reserve <= 0:
            return
        needed = self.max_magazine - self.magazine
        amount = min(needed, self.reserve)
        self.magazine += amount
        self.reserve -= amount

    def get_damage(self, distance_m=0, part="body"):
        """
        Tính sát thương dựa trên khoảng cách (mét) và bộ phận trúng (head, body, legs).
        """
        part_key = str(part).lower()
        if part_key not in ("head", "body", "legs"):
            part_key = "body"

        for max_range, stats in self.damage_table:
            if distance_m <= max_range:
                return stats.get(part_key, stats.get("body", self.damage))
        # Nếu xa hơn mốc cuối cùng, lấy mốc cự ly xa nhất
        return self.damage_table[-1][1].get(part_key, self.damage)


# ==============================================================================
# PHẦN 1: SÚNG PHỤ (PISTOLS)
# ==============================================================================

CLASSIC = Weapon(
    name="CLASSIC",
    damage=26,
    fire_rate=1.0 / 6.75,
    magazine=12,
    reserve=60,
    price=0,
    category="PISTOL",
    fire_mode="Bán tự động",
    damage_table=[
        (30.0, {"body": 26, "head": 78, "legs": 22}),
        (50.0, {"body": 22, "head": 66, "legs": 18}),
    ],
    reload_time=1.5,
    description="Súng phụ cơ bản, miễn phí · Bán tự động (6.75 viên/s)"
)
classic = CLASSIC

GHOST = Weapon(
    name="GHOST",
    damage=30,
    fire_rate=1.0 / 6.75,
    magazine=15,
    reserve=60,
    price=500,
    category="PISTOL",
    fire_mode="Bán tự động",
    damage_table=[
        (30.0, {"body": 30, "head": 105, "legs": 26}),
        (50.0, {"body": 25, "head": 88, "legs": 21}),
    ],
    reload_time=1.5,
    description="Súng lục giảm thanh độ chính xác cao · Bán tự động (6.75 viên/s)"
)
ghost = GHOST

SHERIFF = Weapon(
    name="SHERIFF",
    damage=55,
    fire_rate=1.0 / 4.0,  # 4 viên/s
    magazine=6,
    reserve=36,
    price=800,
    category="PISTOL",
    fire_mode="Bán tự động",
    damage_table=[
        (30.0, {"body": 55, "head": 160, "legs": 47}),
        (50.0, {"body": 50, "head": 145, "legs": 43}),
    ],
    reload_time=1.8,
    description="Súng lục ổ quay uy lực khủng · Bán tự động (4 viên/s)"
)
sheriff = SHERIFF


# ==============================================================================
# PHẦN 2: SMG
# ==============================================================================

MP5 = Weapon(
    name="MP5",
    damage=26,
    fire_rate=1.0 / 13.33,
    magazine=30,
    reserve=90,
    price=1600,
    category="SMG",
    fire_mode="Tự động hoàn toàn",
    damage_table=[
        (20.0, {"body": 26, "head": 78, "legs": 22}),
        (50.0, {"body": 22, "head": 66, "legs": 18}),
    ],
    reload_time=1.7,
    scoped_fire_rate=1.0 / 12.0,
    scoped_zoom=[1.15],
    scoped_recoil_mult=0.7,
    secondary_fire_mode="Sử dụng kính ngắm 1.15x - Tốc độ bắn: 12 viên/s",
    description="SMG tốc độ bắn cao, giảm giãn hồng tâm · Ngắm 1.15x (12 viên/s)"
)
mp5 = MP5

UMP = Weapon(
    name="UMP",
    damage=27,
    fire_rate=1.0 / 18.0,
    magazine=20,
    reserve=80,
    price=1000,
    category="SMG",
    fire_mode="Tự động hoàn toàn",
    damage_table=[
        (20.0, {"body": 27, "head": 67, "legs": 23}),
        (50.0, {"body": 25, "head": 62, "legs": 21}),
    ],
    reload_time=1.6,
    scoped_fire_rate=1.0 / 4.0,
    scoped_zoom=[1.15],
    scoped_recoil_mult=0.65,
    burst_count=4,
    secondary_fire_mode="Sử dụng kính ngắm 1.15x, bắn chùm 4 viên, giảm nhẹ giãn hồng tâm - Tốc độ bắn: 4 viên/s",
    description="SMG xả đạn cực nhanh 18 viên/s · Ngắm 1.15x bắn chùm 4 viên (4 viên/s)"
)
ump = UMP


# ==============================================================================
# PHẦN 3: SHOTGUN
# ==============================================================================

M014 = Weapon(
    name="M014",
    damage=22,
    fire_rate=1.0 / 1.1,
    magazine=5,
    reserve=25,
    price=900,
    category="SHOTGUN",
    fire_mode="Bán tự động",
    damage_table=[
        (8.0, {"body": 22, "head": 44, "legs": 19}),
        (12.0, {"body": 17, "head": 34, "legs": 14}),
        (50.0, {"body": 9, "head": 18, "legs": 8}),
    ],
    reload_time=2.2,
    description="Shotgun bán tự động cận chiến (1.1 viên/s)"
)
m014 = M014

MAG7 = Weapon(
    name="MAG-7",
    damage=17,
    fire_rate=1.0 / 7.0,
    magazine=7,
    reserve=28,
    price=1500,
    category="SHOTGUN",
    fire_mode="Tự động hoàn toàn",
    damage_table=[
        (10.0, {"body": 17, "head": 34, "legs": 14}),
        (15.0, {"body": 13, "head": 26, "legs": 11}),
        (50.0, {"body": 10, "head": 20, "legs": 9}),
    ],
    reload_time=2.0,
    description="Shotgun tự động hoàn toàn 7 viên (7 viên/s)"
)
mag7 = MAG7
MAG_7 = MAG7
mag_7 = MAG7


# ==============================================================================
# PHẦN 4: SÚNG TRƯỜNG (RIFLES)
# ==============================================================================

AK47 = Weapon(
    name="AK-47",
    damage=40,
    fire_rate=1.0 / 9.25,
    magazine=25,
    reserve=75,
    price=2900,
    category="RIFLE",
    fire_mode="Tự động hoàn toàn",
    damage_table=[
        (50.0, {"body": 40, "head": 160, "legs": 34}),
    ],
    reload_time=1.9,
    scoped_fire_rate=1.0 / 8.32,
    scoped_zoom=[1.25],
    scoped_recoil_mult=0.7,
    secondary_fire_mode="Sử dụng kính ngắm 1.25x, giảm nhẹ giãn hồng tâm - Tốc độ bắn: 8.32 viên/s",
    description="Súng trường uy lực cao, One-shot Headshot mọi tầm bắn"
)
ak47 = AK47
AK_47 = AK47
ak_47 = AK47

# Alias VANDAL chuẩn theo game
VANDAL = Weapon(
    name="VANDAL",
    damage=40,
    fire_rate=1.0 / 9.25,
    magazine=25,
    reserve=75,
    price=2900,
    category="RIFLE",
    fire_mode="Tự động hoàn toàn",
    damage_table=[
        (50.0, {"body": 40, "head": 160, "legs": 34}),
    ],
    reload_time=1.9,
    scoped_fire_rate=1.0 / 8.32,
    scoped_zoom=[1.25],
    scoped_recoil_mult=0.7,
    secondary_fire_mode="Sử dụng kính ngắm 1.25x, giảm nhẹ giãn hồng tâm - Tốc độ bắn: 8.32 viên/s",
    description="Súng trường Vandal uy lực cao, One-shot Headshot mọi tầm bắn"
)
vandal = VANDAL

M416 = Weapon(
    name="M416",
    damage=39,
    fire_rate=1.0 / 11.0,
    magazine=30,
    reserve=90,
    price=2900,
    category="RIFLE",
    fire_mode="Tự động hoàn toàn",
    damage_table=[
        (15.0, {"body": 39, "head": 156, "legs": 33}),
        (30.0, {"body": 35, "head": 140, "legs": 29}),
        (50.0, {"body": 31, "head": 124, "legs": 26}),
    ],
    reload_time=1.8,
    scoped_fire_rate=1.0 / 9.9,
    scoped_zoom=[1.25],
    scoped_recoil_mult=0.7,
    secondary_fire_mode="Sử dụng kính ngắm 1.25x, giảm nhẹ giãn hồng tâm - Tốc độ bắn: 9.9 viên/s",
    description="Súng trường 30 viên ổn định · Ngắm 1.25x (9.9 viên/s)"
)
m416 = M416

# Alias PHANTOM chuẩn theo game
PHANTOM = Weapon(
    name="PHANTOM",
    damage=39,
    fire_rate=1.0 / 11.0,
    magazine=30,
    reserve=90,
    price=2900,
    category="RIFLE",
    fire_mode="Tự động hoàn toàn",
    damage_table=[
        (15.0, {"body": 39, "head": 156, "legs": 33}),
        (30.0, {"body": 35, "head": 140, "legs": 29}),
        (50.0, {"body": 31, "head": 124, "legs": 26}),
    ],
    reload_time=1.8,
    scoped_fire_rate=1.0 / 9.9,
    scoped_zoom=[1.25],
    scoped_recoil_mult=0.7,
    secondary_fire_mode="Sử dụng kính ngắm 1.25x, giảm nhẹ giãn hồng tâm - Tốc độ bắn: 9.9 viên/s",
    description="Súng trường Phantom 30 viên ổn định · Ngắm 1.25x (9.9 viên/s)"
)
phantom = PHANTOM

GUARDIAN = Weapon(
    name="GUARDIAN",
    damage=65,
    fire_rate=1.0 / 6.5,
    magazine=12,
    reserve=36,
    price=2700,
    category="RIFLE",
    fire_mode="Bán tự động",
    damage_table=[
        (50.0, {"body": 65, "head": 195, "legs": 49}),
    ],
    reload_time=2.0,
    scoped_fire_rate=1.0 / 6.5,
    scoped_zoom=[1.5],
    scoped_recoil_mult=0.65,
    secondary_fire_mode="Sử dụng kính ngắm 1.5x, giảm nhẹ giãn hồng tâm - Tốc độ bắn: 6.5 viên/s",
    description="Súng trường bán tự động uy lực cực lớn · Ngắm 1.5x (6.5 viên/s)"
)
guardian = GUARDIAN


# ==============================================================================
# PHẦN 5: SÚNG TỈA (SNIPERS)
# ==============================================================================

AWM = Weapon(
    name="AWM",
    damage=150,
    fire_rate=1.0 / 0.75,
    magazine=5,
    reserve=15,
    price=4500,
    category="SNIPER",
    fire_mode="Bán tự động",
    damage_table=[
        (50.0, {"body": 150, "head": 255, "legs": 120}),
    ],
    reload_time=2.5,
    scoped_fire_rate=1.0 / 0.75,
    scoped_zoom=[2.5, 5.0],
    scoped_recoil_mult=0.5,
    secondary_fire_mode="Sử dụng kính ngắm 2.5x và 5x, giảm nhẹ giãn hồng tâm - Tốc độ bắn: 0.75 viên/s",
    description="Súng ngắm tối thượng, One-shot Body mọi cự ly · Ngắm 2.5x và 5.0x"
)
awm = AWM

M24 = Weapon(
    name="M24",
    damage=101,
    fire_rate=1.0 / 1.5,
    magazine=5,
    reserve=15,
    price=1100,
    category="SNIPER",
    fire_mode="Bán tự động",
    damage_table=[
        (50.0, {"body": 101, "head": 202, "legs": 85}),
    ],
    reload_time=2.2,
    scoped_fire_rate=1.0 / 1.2,
    scoped_zoom=[2.5],
    scoped_recoil_mult=0.5,
    secondary_fire_mode="Sử dụng kính ngắm 2.5x, giảm nhẹ giãn hồng tâm - Tốc độ bắn: 1.2 viên/s",
    description="Súng ngắm cơ động, giá rẻ · Ngắm 2.5x (1.2 viên/s)"
)
m24 = M24


# ==============================================================================
# PHẦN 6: VŨ KHÍ CẬN CHIẾN (MELEE)
# ==============================================================================

KNIFE = Weapon(
    name="KNIFE",
    damage=50,
    fire_rate=0.4,
    magazine=0,
    reserve=0,
    price=0,
    category="MELEE",
    fire_mode="Melee",
    damage_table=[
        (8.0, {"body": 50, "head": 50, "legs": 50}),
    ],
    reload_time=0.0,
    description="Dao găm cận chiến: Tầm sử dụng 0 ~ 8m · Đòn đâm chuột trái: 50, Đòn đâm chuột phải: 80"
)
knife = KNIFE


# ==============================================================================
# BẢNG TỔNG HỢP VŨ KHÍ (DATABASE)
# ==============================================================================

WEAPON_DATABASE = {
    "CLASSIC": CLASSIC,
    "GHOST": GHOST,
    "SHERIFF": SHERIFF,
    "MP5": MP5,
    "UMP": UMP,
    "M014": M014,
    "MAG-7": MAG7,
    "MAG7": MAG7,
    "AK-47": AK47,
    "AK47": AK47,
    "VANDAL": VANDAL,
    "M416": M416,
    "PHANTOM": PHANTOM,
    "GUARDIAN": GUARDIAN,
    "AWM": AWM,
    "M24": M24,
    "KNIFE": KNIFE,
}

WEAPONS = WEAPON_DATABASE


def get_weapon(weapon_id):
    """Lấy đối tượng Weapon từ mã ID hoặc tên."""
    w_key = str(weapon_id).upper()
    return WEAPON_DATABASE.get(w_key, CLASSIC)


def get_weapon_damage(weapon_id, distance_m, part="body", is_right_click=False):
    """
    Tính sát thương chuẩn xác theo:
    - Loại vũ khí
    - Khoảng cách (mét)
    - Vị trí trúng đạn (head, body, legs)
    - Đối với KNIFE: chuột trái = 50, chuột phải = 80
    """
    w_key = str(weapon_id).upper()
    if w_key == "KNIFE":
        return 80 if is_right_click else 50

    weapon = get_weapon(w_key)
    return weapon.get_damage(distance_m, part)
