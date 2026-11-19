# File: lv8.py
import random
from CyberEsc.cyberesc.Enemy import FlyingEnemy, ShieldEnemy

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

    # Robot khiên chắn (Shield Bot) bảo vệ tuyến đường trước Boss
    for x in [750, 1300, 1650]:
        enemies.add(ShieldEnemy(x, 335))

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