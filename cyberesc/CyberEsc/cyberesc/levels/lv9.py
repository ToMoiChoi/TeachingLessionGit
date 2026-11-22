# File: lv9.py — Phòng Thí Nghiệm Axit (Acid Lab)
from Enemy import FlyingEnemy, ShieldEnemy


def setup(enemies, boss_group, Enemy, Boss, platforms, powerups, Platform, PowerUp):
    # 1. Nền tảng nhiều tầng so le
    platforms.add(Platform(250, 310, 170, 15))
    platforms.add(Platform(560, 240, 180, 15))
    platforms.add(Platform(900, 300, 200, 15))
    platforms.add(Platform(1300, 230, 190, 15))
    platforms.add(Platform(1680, 290, 200, 15))
    platforms.add(Platform(2020, 220, 180, 15))

    # 2. Vật phẩm bổ trợ
    powerups.add(PowerUp(630, 200, "AMMO"))
    powerups.add(PowerUp(1370, 190, "HP"))
    powerups.add(PowerUp(2090, 180, "DMG"))

    # 3. Kẻ địch tuần tra + Robot khiên
    for x in (420, 820, 1180, 1600, 1950):
        enemies.add(Enemy(x, 330))
    for x in (680, 1420, 1840):
        enemies.add(ShieldEnemy(x, 335))

    # 4. Drone bay canh giữ các tầng cao
    for x, y, r in ((480, 175, 160), (1050, 155, 190), (1560, 145, 180), (2050, 140, 160)):
        enemies.add(FlyingEnemy(x, y, fly_range=r))
