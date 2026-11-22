# File: lv16.py — FINAL BOSS: Thành Trì Omega (Omega Citadel)
from Enemy import FlyingEnemy, ShieldEnemy


def setup(enemies, boss_group, Enemy, Boss, platforms, powerups, Platform, PowerUp):
    # 1. Đấu trường Trùm Cuối đa tầng
    platforms.add(Platform(240, 300, 190, 15))
    platforms.add(Platform(580, 225, 210, 15))
    platforms.add(Platform(960, 285, 240, 15))
    platforms.add(Platform(1360, 210, 220, 15))
    platforms.add(Platform(1740, 275, 220, 15))
    platforms.add(Platform(2040, 205, 190, 15))

    # 2. Tiếp tế chiến đấu
    powerups.add(PowerUp(315, 260, "HP"))
    powerups.add(PowerUp(665, 185, "DMG"))
    powerups.add(PowerUp(1060, 245, "AMMO"))
    powerups.add(PowerUp(1450, 170, "SPEED"))
    powerups.add(PowerUp(1830, 235, "HP"))
    powerups.add(PowerUp(2115, 165, "AMMO"))

    # 3. Cận vệ Omega
    for x in (480, 1000, 1500):
        enemies.add(Enemy(x, 330))
    for x in (740, 1280, 1700):
        enemies.add(ShieldEnemy(x, 335))
    for x, y, r in ((520, 145, 180), (1080, 130, 200), (1580, 125, 190), (1960, 120, 170)):
        enemies.add(FlyingEnemy(x, y, fly_range=r))

    # 4. FINAL BOSS: OMEGA OVERLORD (3200 HP)
    boss = Boss(2080, 330, map_width=2400)
    boss.max_hp = 3200
    boss.hp = 3200
    boss_group.add(boss)
