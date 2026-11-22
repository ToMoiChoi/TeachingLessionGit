# File: lv15.py — Hành Lang Hư Không (Astral Void)
from Enemy import FlyingEnemy, ShieldEnemy


def setup(enemies, boss_group, Enemy, Boss, platforms, powerups, Platform, PowerUp):
    # 1. Nền tảng lơ lửng tầng cao
    platforms.add(Platform(220, 300, 170, 15))
    platforms.add(Platform(500, 230, 170, 15))
    platforms.add(Platform(790, 175, 180, 15))
    platforms.add(Platform(1120, 255, 210, 15))
    platforms.add(Platform(1460, 190, 190, 15))
    platforms.add(Platform(1780, 260, 190, 15))
    platforms.add(Platform(2050, 195, 190, 15))

    # 2. PowerUps
    powerups.add(PowerUp(565, 190, "AMMO"))
    powerups.add(PowerUp(860, 135, "DMG"))
    powerups.add(PowerUp(1205, 215, "HP"))
    powerups.add(PowerUp(1535, 150, "SPEED"))
    powerups.add(PowerUp(2125, 155, "HP"))

    # 3. Đội quân tinh nhuệ trước Thành Trì Omega
    for x in (380, 760, 1180, 1580, 1960, 2180):
        enemies.add(Enemy(x, 330))
    for x in (600, 1020, 1440, 1840, 2100):
        enemies.add(ShieldEnemy(x, 335))
    for x, y, r in ((460, 150, 180), (920, 120, 200), (1380, 135, 200), (1820, 125, 190), (2120, 135, 170)):
        enemies.add(FlyingEnemy(x, y, fly_range=r))
