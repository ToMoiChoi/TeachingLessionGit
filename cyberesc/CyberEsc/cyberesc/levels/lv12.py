# File: lv12.py — BOSS: Mẫu Hạm Băng (Frost Mothership)
from Enemy import FlyingEnemy, ShieldEnemy


def setup(enemies, boss_group, Enemy, Boss, platforms, powerups, Platform, PowerUp):
    # 1. Nền tảng chiến đấu tầm cao cho Boss bay
    platforms.add(Platform(260, 300, 200, 15))
    platforms.add(Platform(620, 235, 210, 15))
    platforms.add(Platform(1020, 290, 220, 15))
    platforms.add(Platform(1420, 225, 220, 15))
    platforms.add(Platform(1820, 285, 220, 15))

    # 2. Tiếp tế
    powerups.add(PowerUp(340, 260, "AMMO"))
    powerups.add(PowerUp(700, 195, "DMG"))
    powerups.add(PowerUp(1110, 250, "HP"))
    powerups.add(PowerUp(1510, 185, "AMMO"))
    powerups.add(PowerUp(1910, 245, "HP"))

    # 3. Vệ binh mặt đất & không trung (MothershipBoss được thêm qua extras.py)
    for x in (480, 980, 1540):
        enemies.add(Enemy(x, 330))
    for x in (760, 1320, 1740):
        enemies.add(ShieldEnemy(x, 335))
    for x, y, r in ((540, 160, 160), (1160, 145, 180), (1680, 135, 180)):
        enemies.add(FlyingEnemy(x, y, fly_range=r))
