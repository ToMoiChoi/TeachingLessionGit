# File: lv14.py — BOSS: Hộ Vệ Nham Thạch (Magma Warden)
from Enemy import FlyingEnemy, ShieldEnemy


def setup(enemies, boss_group, Enemy, Boss, platforms, powerups, Platform, PowerUp):
    # 1. Đấu trường Lò Luyện
    platforms.add(Platform(250, 300, 190, 15))
    platforms.add(Platform(620, 230, 200, 15))
    platforms.add(Platform(1040, 285, 220, 15))
    platforms.add(Platform(1460, 220, 210, 15))
    platforms.add(Platform(1850, 280, 210, 15))

    # 2. PowerUps
    powerups.add(PowerUp(325, 260, "HP"))
    powerups.add(PowerUp(700, 190, "DMG"))
    powerups.add(PowerUp(1130, 245, "AMMO"))
    powerups.add(PowerUp(1545, 180, "SPEED"))
    powerups.add(PowerUp(1935, 240, "HP"))

    # 3. Quái hộ tống
    for x in (500, 1020, 1540):
        enemies.add(Enemy(x, 330))
    for x in (780, 1340, 1760):
        enemies.add(ShieldEnemy(x, 335))
    for x, y, r in ((580, 150, 170), (1180, 140, 190), (1720, 125, 180)):
        enemies.add(FlyingEnemy(x, y, fly_range=r))

    # 4. Boss Hộ Vệ Nham Thạch (2400 HP)
    boss = Boss(2040, 330, map_width=2400)
    boss.max_hp = 2400
    boss.hp = 2400
    boss_group.add(boss)
