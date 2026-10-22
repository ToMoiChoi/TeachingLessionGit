import os
import sys
import random

_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from Enemy import FlyingEnemy


def setup(enemies_group, boss_group, EnemyClass, BossClass, platforms_group, powerups_group, PlatformClass, PowerUpClass):
    platform_data = [
        (250, 280, 150, 15), (550, 200, 140, 15), (850, 280, 150, 15),
        (1200, 200, 140, 15), (1500, 130, 130, 15), (1800, 280, 150, 15), (2100, 200, 140, 15)
    ]
    for x, y, w, h in platform_data:
        platforms_group.add(PlatformClass(x, y, w, h))

    # Kẻ địch đông đảo dưới đất
    for x in [300, 600, 900, 1200, 1500, 1800, 2100]:
        enemies_group.add(EnemyClass(x, 330))

    # Kẻ địch bay trên không (x, y, fly_range)
    flying_enemies_data = [
        (400, 160, 150),   # Bay giữa platform 250 và 550
        (700, 180, 160),   # Bay giữa platform 550 và 850
        (1050, 160, 150),  # Bay giữa platform 850 và 1200
        (1350, 110, 140),  # Bay tầm cao trước khu vực platform tầng 3 (1500)
        (1650, 180, 160),  # Bay giữa platform 1500 và 1800
        (1950, 150, 150),  # Bay giữa platform 1800 và 2100
    ]
    for x, y, fly_range in flying_enemies_data:
        enemies_group.add(FlyingEnemy(x, y, fly_range=fly_range))

    # Nhiều vật phẩm tăng tốc và đạn
    for plat in platforms_group:
        ptype = random.choice(["SPEED", "AMMO", "HP"])
        powerups_group.add(PowerUpClass(plat.rect.centerx, plat.rect.top - 20, ptype))