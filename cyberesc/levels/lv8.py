# File: lv8.py
import os
import sys
import random

# Đảm bảo import được các module từ thư mục cha (cyberesc)
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from Enemy import FlyingEnemy


def setup(enemies, boss_group, Enemy, Boss, platforms, powerups, Platform, PowerUp):
    # 1. Tạo các nền tảng (Platforms)
    platforms.add(Platform(300, 300, 200, 15))
    platforms.add(Platform(700, 250, 200, 15))
    platforms.add(Platform(1200, 280, 250, 15))
    platforms.add(Platform(1700, 220, 200, 15))

    # 2. Thêm các Vật phẩm bổ trợ (PowerUps)
    powerups.add(PowerUp(380, 260, "HP"))       # Hồi HP ở platform đầu
    powerups.add(PowerUp(780, 210, "DMG"))      # Tăng DMG ở platform thứ 2
    powerups.add(PowerUp(1300, 240, "AMMO"))    # Nạp đạn giữa bản đồ
    powerups.add(PowerUp(1780, 180, "SPEED"))   # Tăng tốc độ né đạn trước Boss
    powerups.add(PowerUp(1900, 340, "HP"))      # Hồi HP khẩn cấp sát sàn đấu Boss

    # 3. Kẻ địch thường (Ngang đường đi)
    enemies.add(Enemy(500, 330))
    enemies.add(Enemy(1100, 330))

    # 4. Kẻ địch bay trên không (x, y, fly_range) bảo vệ đấu trường Boss
    flying_enemies_data = [
        (500, 180, 160),   # Bay canh giữ khoảng giữa platform 1 và 2
        (950, 160, 180),   # Bay canh giữ khu vực giữa map
        (1450, 150, 170),  # Bay lơ lửng trước platform 1700
        (1850, 120, 150),  # Bay tầm cao gác cổng trước khi gặp Boss
    ]
    for x, y, fly_range in flying_enemies_data:
        enemies.add(FlyingEnemy(x, y, fly_range=fly_range))

    # 5. Khởi tạo Boss (Máu 1500)
    boss = Boss(2000, 330, map_width=2400)
    boss.max_hp = 1500
    boss.hp = 1500
    boss_group.add(boss)


# Cho phép chạy thử trực tiếp màn 8 độc lập
if __name__ == '__main__':
    import pygame
    from game_engine import GameEngine
    from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS

    pygame.init()
    pygame.font.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Cyber Escape - Test Level 8 (Boss Fight)")

    engine = GameEngine(screen)
    engine.state = "PLAYING"
    engine.start_level(8)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            engine.handle_event(event)

        engine.update_and_render()
        engine.clock.tick(FPS)