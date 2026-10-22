import os
import sys
import random

_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from Enemy import FlyingEnemy


def setup(enemies_group, boss_group, EnemyClass, BossClass, platforms_group, powerups_group, PlatformClass, PowerUpClass):
    platform_data = [
        (250, 280, 130, 15),
        (500, 200, 120, 15),
        (750, 130, 120, 15),  # Tầng 3
        (1100, 280, 140, 15),
        (1400, 200, 130, 15),
        (1750, 280, 140, 15),
        (2050, 200, 130, 15),
    ]
    for x, y, w, h in platform_data:
        platforms_group.add(PlatformClass(x, y, w, h))

    # Kẻ địch trên sàn & platform
    for x in [500, 900, 1300, 1700, 2100]:
        enemies_group.add(EnemyClass(x, 330))

    enemies_group.add(EnemyClass(780, 90))   # Trên tầng 3
    enemies_group.add(EnemyClass(1430, 160)) # Trên tầng 2

    # Kẻ địch bay trên không (x, y, fly_range)
    flying_enemies_data = [
        (350, 160, 150),   # Bay ở khoảng giữa tầng 1 và tầng 2
        (950, 180, 160),   # Bay canh giữ khu vực sau tầng 3
        (1600, 130, 170),  # Bay tầm cao giữa các platform cuối
        (1950, 150, 150),  # Bay trước khu vực platform 2050
    ]
    for x, y, fly_range in flying_enemies_data:
        enemies_group.add(FlyingEnemy(x, y, fly_range=fly_range))

    powerups_group.add(PowerUpClass(780, 105, "DMG"))