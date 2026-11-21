"""game/data.py - Dữ liệu cấu hình chế độ chơi, độ khó, chủng loại Zombie, vật phẩm tiếp tế và lưu trữ."""
import random
import luu_tru

SAVE_KEY = "tunglam_lotus_fps_v3"

# ==============================================================================
# 1. CHẾ ĐỘ CHƠI (GAME MODES)
# ==============================================================================
GAME_MODES = [
    {
        "id": "HYBRID",
        "name": "CHIẾN THUẬT + ZOMBIE",
        "short": "Hỗn chiến",
        "desc": "Đấu hiệp 5 đặc nhiệm AI kết hợp đàn Zombie đột kích từ cổng lây nhiễm.",
        "color": (235, 95, 55),
    },
    {
        "id": "ZOMBIE",
        "name": "SINH TỒN ZOMBIE",
        "short": "Sinh tồn Wave",
        "desc": "Chống trả các đợt Zombie tăng dần sức mạnh, nhặt hộp tiếp tế & diệt Boss Đột Biến.",
        "color": (85, 210, 95),
    },
    {
        "id": "TACTICAL",
        "name": "ĐẤU HIỆP CỔ ĐIỂN",
        "short": "Đấu hiệp 5v1",
        "desc": "Đấu súng chiến thuật truyền thống với đội đặc nhiệm AI (chạm 13 thắng).",
        "color": (70, 155, 245),
    },
]

MODE_BY_ID = {m["id"]: m for m in GAME_MODES}

# ==============================================================================
# 2. ĐỘ KHÓ (DIFFICULTIES)
# ==============================================================================
DIFFICULTIES = [
    {
        "id": "EASY",
        "name": "DỄ",
        "hp_mult": 0.80,
        "speed_mult": 0.88,
        "dmg_mult": 0.72,
        "bot_fire_mult": 1.28,
        "bot_acc_bonus": -0.12,
        "money_mult": 1.25,
        "zombie_extra": 0,
        "color": (80, 220, 120),
    },
    {
        "id": "NORMAL",
        "name": "THƯỜNG",
        "hp_mult": 1.00,
        "speed_mult": 1.00,
        "dmg_mult": 1.00,
        "bot_fire_mult": 1.00,
        "bot_acc_bonus": 0.00,
        "money_mult": 1.00,
        "zombie_extra": 1,
        "color": (245, 205, 65),
    },
    {
        "id": "HARD",
        "name": "KHÓ",
        "hp_mult": 1.28,
        "speed_mult": 1.14,
        "dmg_mult": 1.28,
        "bot_fire_mult": 0.78,
        "bot_acc_bonus": 0.12,
        "money_mult": 1.15,
        "zombie_extra": 2,
        "color": (235, 65, 75),
    },
]

DIFF_BY_ID = {d["id"]: d for d in DIFFICULTIES}

# ==============================================================================
# 3. DỮ LIỆU CHỦNG LOẠI ZOMBIE (ZOMBIE ARCHETYPES)
# ==============================================================================
ZOMBIE_TYPES = {
    "WALKER": {
        "id": "WALKER",
        "label": "ZOMBIE",
        "hp": 110,
        "armor": 0,
        "speed": 128,
        "melee_damage": 16,
        "attack_cooldown": 0.95,
        "attack_range": 52,
        "scale": 1.0,
        "reward": 200,
        "drop_chance": 0.32,
        "skin": (108, 158, 92),
        "shirt": (72, 82, 68),
        "pants": (48, 52, 46),
        "eye": (255, 55, 55),
    },
    "RUNNER": {
        "id": "RUNNER",
        "label": "CUỒNG TỐC",
        "hp": 78,
        "armor": 0,
        "speed": 198,
        "melee_damage": 14,
        "attack_cooldown": 0.72,
        "attack_range": 50,
        "scale": 0.94,
        "reward": 250,
        "drop_chance": 0.38,
        "skin": (175, 105, 98),
        "shirt": (135, 42, 42),
        "pants": (45, 38, 42),
        "eye": (255, 185, 35),
    },
    "BRUTE": {
        "id": "BRUTE",
        "label": "KHỔNG LỒ",
        "hp": 265,
        "armor": 35,
        "speed": 92,
        "melee_damage": 28,
        "attack_cooldown": 1.25,
        "attack_range": 62,
        "scale": 1.24,
        "reward": 400,
        "drop_chance": 0.65,
        "skin": (92, 118, 132),
        "shirt": (58, 46, 82),
        "pants": (36, 34, 50),
        "eye": (190, 90, 255),
    },
    "MUTANT": {
        "id": "MUTANT",
        "label": "BOSS ĐỘT BIẾN",
        "hp": 520,
        "armor": 65,
        "speed": 136,
        "melee_damage": 35,
        "attack_cooldown": 0.90,
        "attack_range": 68,
        "scale": 1.38,
        "reward": 850,
        "drop_chance": 1.00,
        "skin": (68, 185, 110),
        "shirt": (32, 65, 48),
        "pants": (26, 38, 34),
        "eye": (80, 255, 120),
    },
}

# ==============================================================================
# 4. HỘP TIẾP TẾ RƠI RA KHI DIỆT ZOMBIE (3D SUPPLY DROPS)
# ==============================================================================
SUPPLY_TYPES = {
    "MEDKIT": {
        "label": "MÁU +35 HP",
        "short": "+HP",
        "color": (65, 225, 115),
        "border": (210, 255, 225),
        "weight": 38,
    },
    "AMMO": {
        "label": "TIẾP ĐẠN",
        "short": "+ĐẠN",
        "color": (245, 195, 55),
        "border": (255, 240, 175),
        "weight": 34,
    },
    "ARMOR_PACK": {
        "label": "GIÁP +25",
        "short": "+GIÁP",
        "color": (70, 165, 250),
        "border": (195, 230, 255),
        "weight": 18,
    },
    "CASH": {
        "label": "THƯỞNG +$350",
        "short": "+$350",
        "color": (185, 115, 255),
        "border": (235, 210, 255),
        "weight": 10,
    },
}


def pick_zombie_type(wave_or_round=1, force_boss=False):
    """Chọn loại Zombie phù hợp theo cấp độ đợt / hiệp hiện tại."""
    if force_boss:
        return "MUTANT"
    w = max(1, int(wave_or_round))
    pool = [("WALKER", 58)]
    if w >= 1:
        pool.append(("RUNNER", min(38, 16 + w * 4)))
    if w >= 2:
        pool.append(("BRUTE", min(28, 8 + (w - 1) * 4)))
    if w >= 4:
        pool.append(("MUTANT", min(10, (w - 3) * 2)))
    total = sum(weight for _, weight in pool)
    r = random.uniform(0, total)
    acc = 0.0
    for z_id, weight in pool:
        acc += weight
        if r <= acc:
            return z_id
    return "WALKER"


def pick_supply_kind(player_hp=100):
    """Ưu tiên rơi hộp máu nhiều hơn khi máu người chơi đang thấp."""
    items = []
    for k, info in SUPPLY_TYPES.items():
        w = info["weight"]
        if k == "MEDKIT" and player_hp < 55:
            w += 30
        items.append((k, w))
    total = sum(w for _, w in items)
    r = random.uniform(0, total)
    acc = 0.0
    for k, w in items:
        acc += w
        if r <= acc:
            return k
    return "MEDKIT"


# ==============================================================================
# 5. LƯU & ĐỌC HỒ SƠ KỶ LỤC (DÙNG CHUNG DESKTOP JSON & WEB LOCALSTORAGE)
# ==============================================================================
DEFAULT_PROFILE = {
    "best_wave": 0,
    "total_kills": 0,
    "zombie_kills": 0,
    "matches_won": 0,
    "last_map": "lotus",
    "last_mode": "HYBRID",
    "last_diff": "NORMAL",
}


def load_profile():
    return luu_tru.doc(SAVE_KEY, DEFAULT_PROFILE)


def save_profile(profile):
    return luu_tru.ghi(SAVE_KEY, profile)
