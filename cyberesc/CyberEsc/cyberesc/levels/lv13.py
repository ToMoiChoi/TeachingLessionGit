# File: lv13.py — Lò Luyện Nham Thạch (Solar Foundry)
from Enemy import FlyingEnemy, ShieldEnemy


def setup(enemies, boss_group, Enemy, Boss, platforms, powerups, Platform, PowerUp):
    # 1. Nền tảng hẹp đòi hỏi nhảy/tiếp đất chính xác
    platforms.add(Platform(240, 305, 140, 15))
    platforms.add(Platform(480, 245, 140, 15))
    platforms.add(Platform(740, 195, 150, 15))
    platforms.add(Platform(1020, 275, 170, 15))
    platforms.add(Platform(1320, 215, 150, 15))
    platforms.add(Platform(1620, 285, 160, 15))
    platforms.add(Platform(1920, 210, 180, 15))

    # 2. PowerUps
    powerups.add(PowerUp(795, 155, "SPEED"))
    powerups.add(PowerUp(1090, 235, "HP"))
    powerups.add(PowerUp(1380, 175, "DMG"))
    powerups.add(PowerUp(1990, 170, "AMMO"))

    # 3. Đội hình tấn công áp sát
    for x in (420, 860, 1260, 1660, 2060):
        enemies.add(Enemy(x, 330))
    for x in (620, 1140, 1520, 1880):
        enemies.add(ShieldEnemy(x, 335))
    for x, y, r in ((520, 155, 180), (1080, 140, 200), (1580, 140, 190), (2060, 130, 170)):
        enemies.add(FlyingEnemy(x, y, fly_range=r))
