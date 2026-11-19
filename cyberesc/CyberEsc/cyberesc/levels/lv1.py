import os
import sys
import random

_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from Enemy import FlyingEnemy


def setup(enemies_group, boss_group, EnemyClass, BossClass, platforms_group, powerups_group, PlatformClass, PowerUpClass):

    # Platform đơn giản ở Tầng 1 (280) và Tầng 2 (200)
    platform_data = [
        (300, 280, 150, 15),
        (700, 280, 140, 15),
        (1100, 250, 140, 15),
        (1500, 280, 150, 15),
        (1900, 250, 130, 15),
    ]
    for x, y, w, h in platform_data:
        platforms_group.add(PlatformClass(x, y, w, h))

    # Kẻ địch trên sàn chính
    for x in [600, 1000, 1400, 1800]:
        enemies_group.add(EnemyClass(x, 330))

    # Kẻ địch bay trên không (x, y, fly_range)
    flying_enemies_data = [
        (450, 180, 160),   # Quái bay đoạn đầu màn
        (1150, 150, 180),  # Quái bay phía trên platform giữa
        (1700, 170, 150),  # Quái bay gần cuối màn
    ]
    for x, y, fly_range in flying_enemies_data:
        enemies_group.add(FlyingEnemy(x, y, fly_range=fly_range))

    # Tiếp tế cố định
    powerups_group.add(PowerUpClass(750, 255, "HP"))
    powerups_group.add(PowerUpClass(1550, 255, "AMMO"))


# Cho phép chạy thử trực tiếp màn 1 độc lập
if __name__ == '__main__':
    import pygame
    from game_engine import GameEngine
    from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS

    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Cyber Escape - Test Level 1")

    engine = GameEngine(screen)
    engine.state = "PLAYING"
    engine.start_level(1)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            engine.handle_event(event)

        engine.update_and_render()
        engine.clock.tick(FPS)