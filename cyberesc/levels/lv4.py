import os
import sys
import random

_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from Enemy import FlyingEnemy


def setup(enemies_group, boss_group, EnemyClass, BossClass, platforms_group, powerups_group, PlatformClass, PowerUpClass):
    # Đấu trường có nhiều tầng giúp né đòn Boss
    platform_data = [
        (300, 280, 140, 15), (600, 200, 140, 15),
        (1000, 280, 160, 15), (1300, 200, 140, 15), (1500, 130, 130, 15),
        (1800, 280, 200, 15), (2050, 200, 180, 15)
    ]
    for x, y, w, h in platform_data:
        platforms_group.add(PlatformClass(x, y, w, h))

    # Kẻ địch lính gác dưới đất
    for x in [450, 850, 1250]:
        enemies_group.add(EnemyClass(x, 330))

    # Kẻ địch bay trên không (x, y, fly_range) bảo vệ đường vào Boss
    flying_enemies_data = [
        (450, 160, 150),   # Bay giữa platform 300 và 600
        (800, 180, 160),   # Bay canh giữ khu vực đường tiến giữa map
        (1400, 100, 140),  # Bay tầm cao gần platform 1500
        (1700, 180, 150),  # Bay lơ lửng trước khu vực Đấu trường Boss
    ]
    for x, y, fly_range in flying_enemies_data:
        enemies_group.add(FlyingEnemy(x, y, fly_range=fly_range))

    # Boss ở khu vực x = 2000
    boss_group.add(BossClass(2000, 330))

    # Viện trợ cho trận đánh Boss
    powerups_group.add(PowerUpClass(1850, 255, "HP"))
    powerups_group.add(PowerUpClass(2100, 175, "AMMO"))