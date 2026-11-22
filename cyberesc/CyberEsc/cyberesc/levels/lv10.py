# File: lv10.py — BOSS: Lõi Độc Hại (Toxic Core)
from Enemy import FlyingEnemy, ShieldEnemy


def setup(enemies, boss_group, Enemy, Boss, platforms, powerups, Platform, PowerUp):
    # 1. Đấu trường 2 tầng
    platforms.add(Platform(260, 300, 200, 15))
    platforms.add(Platform(680, 235, 220, 15))
    platforms.add(Platform(1150, 290, 240, 15))
    platforms.add(Platform(1620, 225, 220, 15))

    # 2. PowerUp chuẩn bị đánh Boss
    powerups.add(PowerUp(340, 260, "HP"))
    powerups.add(PowerUp(770, 195, "DMG"))
    powerups.add(PowerUp(1250, 250, "AMMO"))
    powerups.add(PowerUp(1710, 185, "SPEED"))
    powerups.add(PowerUp(1920, 340, "HP"))

    # 3. Đội hình hộ vệ
    for x in (520, 1080):
        enemies.add(Enemy(x, 330))
    for x in (820, 1400, 1750):
        enemies.add(ShieldEnemy(x, 335))
    for x, y, r in ((600, 165, 160), (1250, 150, 180), (1780, 130, 170)):
        enemies.add(FlyingEnemy(x, y, fly_range=r))

    # 4. Boss Lõi Độc Hại (1800 HP)
    boss = Boss(2020, 330, map_width=2400)
    boss.max_hp = 1800
    boss.hp = 1800
    boss_group.add(boss)
