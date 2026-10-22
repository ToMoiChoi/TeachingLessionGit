import os
import sys
import random

_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from Enemy import FlyingEnemy


def setup(enemies_group, boss_group, EnemyClass, BossClass, platforms_group, powerups_group, PlatformClass, PowerUpClass):
    platform_data = [
        (200, 280, 120, 15), (450, 200, 120, 15), (700, 130, 120, 15),
        (1000, 280, 130, 15), (1250, 200, 120, 15), (1500, 130, 120, 15),
        (1800, 280, 130, 15), (2050, 200, 120, 15)
    ]
    for x, y, w, h in platform_data:
        platforms_group.add(PlatformClass(x, y, w, h))

    # Mật độ quái rất cao dưới đất
    for x in [350, 650, 950, 1250, 1550, 1850, 2150]:
        enemies_group.add(EnemyClass(x, 330))

    # Kẻ địch bay trên không (x, y, fly_range)
    flying_enemies_data = [
        (325, 160, 140),   # Bay giữa platform 200 và 450
        (575, 100, 140),   # Bay tầm cao gần platform tầng 3 (700)
        (850, 180, 150),   # Bay chuyển tiếp giữa khu 700 và 1000
        (1125, 150, 140),  # Bay giữa platform 1000 và 1250
        (1375, 90, 140),   # Bay tầm cao gần platform tầng 3 (1500)
        (1650, 180, 150),  # Bay giữa platform 1500 và 1800
        (1925, 150, 140),  # Bay giữa platform 1800 và 2050
    ]
    for x, y, fly_range in flying_enemies_data:
        enemies_group.add(FlyingEnemy(x, y, fly_range=fly_range))

    # Kẻ địch & HP trên các platform
    for plat in platforms_group:
        enemies_group.add(EnemyClass(plat.rect.centerx, plat.rect.top - 40))
        if random.random() < 0.4:
            powerups_group.add(PowerUpClass(plat.rect.centerx, plat.rect.top - 20, "HP"))