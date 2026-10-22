import os
import sys
import random

_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from Enemy import FlyingEnemy


def setup(enemies_group, boss_group, EnemyClass, BossClass, platforms_group, powerups_group, PlatformClass, PowerUpClass):
    platform_data = [
        (200, 280, 120, 15), (380, 200, 120, 15), (560, 130, 120, 15),
        (900, 280, 130, 15), (1100, 200, 130, 15), (1300, 130, 130, 15),
        (1650, 280, 140, 15), (1900, 200, 130, 15), (2100, 130, 120, 15)
    ]
    for x, y, w, h in platform_data:
        platforms_group.add(PlatformClass(x, y, w, h))

    # Kẻ địch trên sàn
    for x in [350, 750, 1200, 1550, 1800, 2200]:
        enemies_group.add(EnemyClass(x, 330))

    # Kẻ địch bay trên không (x, y, fly_range)
    flying_enemies_data = [
        (290, 160, 140),   # Bay giữa các tầng dốc đầu màn
        (730, 180, 150),   # Bay canh giữ khoảng trống giữa màn
        (1200, 90, 140),   # Bay tầm cao gần tầng 3 (y=130)
        (1500, 170, 150),  # Bay khoảng nghỉ giữa 1300 và 1650
        (2000, 100, 140),  # Bay tầm cao ở khu vực tầng dốc cuối
    ]
    for x, y, fly_range in flying_enemies_data:
        enemies_group.add(FlyingEnemy(x, y, fly_range=fly_range))

    # Quái và buff trên các tầng cao nhất (y = 130)
    for plat in platforms_group:
        if plat.rect.y == 130:
            enemies_group.add(EnemyClass(plat.rect.centerx, plat.rect.top - 40))
            powerups_group.add(PowerUpClass(plat.rect.centerx, plat.rect.top - 20, "DMG"))