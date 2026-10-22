import os
import sys
import random

_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from Enemy import FlyingEnemy


def setup(enemies_group, boss_group, EnemyClass, BossClass, platforms_group, powerups_group, PlatformClass, PowerUpClass):
    platform_data = [
        (300, 280, 140, 15), (550, 200, 130, 15),
        (850, 280, 140, 15), (1150, 200, 130, 15), (1350, 130, 120, 15),
        (1650, 280, 140, 15), (1950, 200, 130, 15)
    ]
    for x, y, w, h in platform_data:
        platforms_group.add(PlatformClass(x, y, w, h))

    # Kẻ địch trên sàn chính
    for x in [400, 750, 1100, 1500, 1850, 2150]:
        enemies_group.add(EnemyClass(x, 330))

    # Kẻ địch bay trên không (x, y, fly_range)
    flying_enemies_data = [
        (420, 160, 150),   # Bay giữa platform 300 và 550
        (1000, 150, 160),  # Bay giữa platform 850 và 1150
        (1450, 100, 140),  # Bay tầm cao gần platform tầng 3 (1350)
        (1800, 160, 160),  # Bay giữa platform 1650 và 1950
    ]
    for x, y, fly_range in flying_enemies_data:
        enemies_group.add(FlyingEnemy(x, y, fly_range=fly_range))

    # Kẻ địch & PowerUp ngẫu nhiên trên các platform
    for plat in platforms_group:
        if random.random() < 0.5:
            enemies_group.add(EnemyClass(plat.rect.centerx, plat.rect.top - 40))
            powerups_group.add(PowerUpClass(plat.rect.centerx, plat.rect.top - 20, random.choice(["HP", "AMMO", "SPEED"])))