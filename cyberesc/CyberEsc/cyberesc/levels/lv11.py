# File: lv11.py — Trạm Máy Chủ Băng Giá (Arctic Server Farm)
from Enemy import FlyingEnemy, ShieldEnemy


def setup(enemies, boss_group, Enemy, Boss, platforms, powerups, Platform, PowerUp):
    # 1. Nền tảng bậc thang băng giá
    platforms.add(Platform(240, 305, 180, 15))
    platforms.add(Platform(520, 240, 180, 15))
    platforms.add(Platform(820, 185, 190, 15))
    platforms.add(Platform(1180, 265, 220, 15))
    platforms.add(Platform(1540, 200, 200, 15))
    platforms.add(Platform(1900, 275, 210, 15))

    # 2. Vật phẩm bổ trợ
    powerups.add(PowerUp(890, 145, "DMG"))
    powerups.add(PowerUp(1270, 225, "AMMO"))
    powerups.add(PowerUp(1620, 160, "HP"))
    powerups.add(PowerUp(1990, 235, "SPEED"))

    # 3. Kẻ địch mặt đất & khiên
    for x in (400, 960, 1420, 1820, 2120):
        enemies.add(Enemy(x, 330))
    for x in (650, 1260, 1700, 2040):
        enemies.add(ShieldEnemy(x, 335))

    # 4. Bầy Drone tuần tra tầng không
    for x, y, r in ((420, 165, 170), (920, 120, 200), (1440, 135, 190), (1860, 140, 180), (2140, 155, 150)):
        enemies.add(FlyingEnemy(x, y, fly_range=r))
