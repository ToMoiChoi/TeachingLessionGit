import pygame
import math
import random

CYBER_PINK = (255, 0, 127)
CYBER_YELLOW = (255, 230, 0)
CYBER_BLUE = (0, 243, 255)
RED = (255, 50, 50)
DARK_RED = (200, 0, 0)
GREEN = (50, 255, 50)
WHITE = (255, 255, 255)
ORANGE = (255, 140, 0)

# --- BẢNG MÀU PIXEL ART ENEMY ---
ENEMY_COLOR_MAP = {
    '#': (20, 20, 30),       # Viền khung tối
    'X': (90, 100, 120),    # Thân vỏ kim loại xám
    'R': (255, 30, 60),      # Mắt/Laser đỏ Cyber
    'C': (0, 220, 255),      # Đèn Neon Xanh / Khiên năng lượng
    'P': (255, 0, 128),      # Đèn Neon Hồng (Boss)
    'G': (50, 60, 75),       # Khớp nối / Giáp nặng
    'Y': (255, 200, 0),      # Đèn cảnh báo Vàng
    'W': (240, 240, 255),    # Cánh quạt Drone
    '.': None                # Trong suốt
}

# --- MODEL PIXEL ART ---
PATROL_BOT_PIXELS = [
    "....########....",
    "...#XXXXXXXX#...",
    "..#XXRRRRRRXX#..",
    "..#XXRRRRRRXX#..",
    "..#XXXXXXXXXX#..",
    "...##########...",
    "....#GGGGGG#....",
    "...#XXXXXXXX#...",
    "..#XXXXXXXXXX#..",
    "..#XX######XX#..",
    "..#XX#....#XX#..",
    "..#XX#....#XX#..",
    ".#GGGG#..#GGGG#.",
    ".######..######."
]

SHIELD_BOT_PIXELS = [
    "...##########..CC.",
    "..#GGGGGGGGGG#.CC.",
    ".#GXXXXXXXXXXG#CC.",
    ".#GXRRRRRRRRXG#CC.",
    ".#GXXXXXXXXXXG#CC.",
    "..############.CC.",
    ".#GGGGGGGGGGGG#CC.",
    "#GXXXXXXXXXXXXGCC.",
    "#GXGGGGGGGGGGXGCC.",
    "#GXXXXXXXXXXXXGCC.",
    ".#GGGGGGGGGGGG#CC.",
    "..#XXXX##XXXX#.CC.",
    "..#XXXX##XXXX#.CC.",
    ".#GGGG#..#GGGG#CC.",
    ".######..######CC."
]

SHIELD_BOT_BROKEN_PIXELS = [
    "...##########.....",
    "..#GGGGGGGGGG#....",
    ".#GXXXXXXXXXXG#...",
    ".#GXYYYYYYYYXG#...",
    ".#GXXXXXXXXXXG#...",
    "..############....",
    ".#GGGGGGGGGGGG#...",
    "#GXXXXXXXXXXXXG...",
    "#GXGGGGGGGGGGXG...",
    "#GXXXXXXXXXXXXG...",
    ".#GGGGGGGGGGGG#...",
    "..#XXXX##XXXX#....",
    "..#XXXX##XXXX#....",
    ".#GGGG#..#GGGG#...",
    ".######..######..."
]

FLYING_DRONE_PIXELS = [
    "#WW..........WW#",
    "####........####",
    "..#G#......#G#..",
    "..#GG######GG#..",
    ".#XXXXXXXXXXXX#.",
    "#XXXXXXXXXXXXXX#",
    "#XXCCCCCCCCCCCC#",
    "#XXCCCCCCCCCCCC#",
    ".#XXXXXXXXXXXX#.",
    "..############..",
    "....#GG##GG#....",
    "....##....##...."
]

BOSS_PHASE1_PIXELS = [
    "........########........",
    ".......#XXXXXXXX#.......",
    "......#XXCCCCCCCC#......",
    "......#XXCCCCCCCC#......",
    ".....#XXXXXXXXXXXX#.....",
    "....################....",
    "...#XXXXXXXXXXXXXXXX#...",
    "..#XXPP##########PPXX#..",
    "..#XXPP#RRRRRRRR#PPXX#..",
    "..#XXPP#RRRRRRRR#PPXX#..",
    "..#XXPP##########PPXX#..",
    "...#XXXXXXXXXXXXXXXX#...",
    "....################....",
    "....#GGGG######GGGG#....",
    "...#XXXXX#....#XXXXX#...",
    "...#XXXXX#....#XXXXX#...",
    "..#GGGGGG#....#GGGGGG#..",
    "..######........######.."
]

BOSS_PHASE2_PIXELS = [
    "........########........",
    ".......#XXXXXXXX#.......",
    "......#XXRRRRRRXX#......",
    "......#XXRRRRRRXX#......",
    ".....#XXXXXXXXXXXX#.....",
    "....################....",
    "...#XXXXXXXXXXXXXXXX#...",
    "..#XXRR##########RRXX#..",
    "..#XXRR#YYYYYYYY#RRXX#..",
    "..#XXRR#YYYYYYYY#RRXX#..",
    "..#XXRR##########RRXX#..",
    "...#XXXXXXXXXXXXXXXX#...",
    "....################....",
    "....#GGGG######GGGG#....",
    "...#XXXXX#....#XXXXX#...",
    "...#XXXXX#....#XXXXX#...",
    "..#GGGGGG#....#GGGGGG#..",
    "..######........######.."
]

def create_sprite_surface(pixel_data, scale=2, palette=ENEMY_COLOR_MAP):
    height = len(pixel_data)
    width = max(len(row) for row in pixel_data)
    surface = pygame.Surface((width * scale, height * scale), pygame.SRCALPHA)
    for y, row in enumerate(pixel_data):
        for x, char in enumerate(row):
            color = palette.get(char)
            if color:
                rect = pygame.Rect(x * scale, y * scale, scale, scale)
                pygame.draw.rect(surface, color, rect)
    return surface


class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, target_x, target_y, speed=7, damage=10, angle_offset=0.0):
        super().__init__()
        self.image = pygame.Surface((12, 12), pygame.SRCALPHA)
        
        # Đạn Phase 2 đổi màu sắc nổi bật hơn
        bullet_color = ORANGE if damage > 15 else RED
        pygame.draw.circle(self.image, bullet_color, (6, 6), 6)
        pygame.draw.circle(self.image, CYBER_YELLOW, (6, 6), 3)
        self.rect = self.image.get_rect(center=(x, y))

        # Tính toán góc bay + độ lệch góc (dùng cho bắn chùm)
        dx = target_x - x
        dy = target_y - y
        base_angle = math.atan2(dy, dx) + angle_offset
        
        self.vel_x = speed * math.cos(base_angle)
        self.vel_y = speed * math.sin(base_angle)
        self.damage = damage
        self.parried = False

    def parry(self, bonus_dmg=0):
        """Đảo ngược hướng đạn khi bị chém Parry và chuyển sang sát thương phản đòn"""
        self.parried = True
        self.vel_x = -self.vel_x * 1.4
        self.vel_y = -self.vel_y * 1.4
        self.damage = int(self.damage * 4) + bonus_dmg

        # Đổi diện mạo viên đạn sang tia năng lượng xanh neon
        self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(self.image, CYBER_BLUE, (8, 8), 8)
        pygame.draw.circle(self.image, WHITE, (8, 8), 4)
        self.rect = self.image.get_rect(center=self.rect.center)

    def update(self):
        self.rect.x += int(self.vel_x)
        self.rect.y += int(self.vel_y)
        if self.rect.right < -100 or self.rect.left > 3000 or self.rect.bottom < -100 or self.rect.top > 1000:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, map_width=2400):
        super().__init__()
        self.image_right = create_sprite_surface(PATROL_BOT_PIXELS, scale=3)
        self.image_left = pygame.transform.flip(self.image_right, True, False)
        self.image = self.image_right
        self.rect = self.image.get_rect(topleft=(x, y))

        self.max_hp = 50
        self.hp = 50
        self.damage = 10
        self.speed = 2
        self.direction = 1
        self.map_width = map_width

    def update(self, *args):
        self.rect.x += self.speed * self.direction
        
        if self.direction > 0:
            self.image = self.image_right
        else:
            self.image = self.image_left

        # Giữ quái luôn ở trong giới hạn Map, quay đầu khi chạm viền
        if self.rect.left <= 0:
            self.rect.left = 0
            self.direction = 1
        elif self.rect.right >= self.map_width:
            self.rect.right = self.map_width
            self.direction = -1
        elif random.random() < 0.01:
            self.direction *= -1

    def draw(self, screen, camera_x=0):
        ren_rect = self.rect.move(-camera_x, 0)
        screen.blit(self.image, ren_rect)

        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(screen, RED, (ren_rect.x, ren_rect.top - 8, self.rect.width, 4))
        pygame.draw.rect(screen, GREEN, (ren_rect.x, ren_rect.top - 8, int(self.rect.width * hp_ratio), 4))


class ShieldEnemy(pygame.sprite.Sprite):
    """Robot hộ vệ mang khiên năng lượng phía trước, có độ trễ quay đầu"""
    def __init__(self, x, y, map_width=2400):
        super().__init__()
        self.shield_right = create_sprite_surface(SHIELD_BOT_PIXELS, scale=3)
        self.shield_left = pygame.transform.flip(self.shield_right, True, False)
        self.broken_right = create_sprite_surface(SHIELD_BOT_BROKEN_PIXELS, scale=3)
        self.broken_left = pygame.transform.flip(self.broken_right, True, False)

        self.image = self.shield_left
        self.rect = self.image.get_rect(topleft=(x, y))

        self.max_hp = 90
        self.hp = 90
        self.damage = 15
        self.speed = 1.2
        self.direction = -1
        self.map_width = map_width

        # Trạng thái khiên và độ trễ quay đầu
        self.shield_active = True
        self.shield_broken_timer = 0
        self.turn_delay = 48  # 0.8 giây ở 60 FPS
        self.turn_timer = 0
        self.detect_range = 420

    def is_blocked(self, bullet_x):
        """Kiểm tra viên đạn có bay trúng mặt trước đang bật khiên không"""
        if not self.shield_active:
            return False
        if self.direction == 1:
            return bullet_x >= self.rect.centerx - 4
        else:
            return bullet_x <= self.rect.centerx + 4

    def break_shield(self, duration=150):
        """Tạm ngắt khiên khi bị chém cận chiến"""
        self.shield_active = False
        self.shield_broken_timer = duration

    def update(self, enemy_bullets=None, player=None, *args):
        if self.shield_broken_timer > 0:
            self.shield_broken_timer -= 1
            if self.shield_broken_timer <= 0:
                self.shield_active = True

        in_guard_mode = False
        if player is not None:
            dx = player.rect.centerx - self.rect.centerx
            dy = abs(player.rect.centery - self.rect.centery)
            if abs(dx) <= self.detect_range and dy <= 160:
                in_guard_mode = True
                desired_dir = 1 if dx > 0 else -1
                if desired_dir != self.direction:
                    self.turn_timer += 1
                    if self.turn_timer >= self.turn_delay:
                        self.direction = desired_dir
                        self.turn_timer = 0
                else:
                    self.turn_timer = 0
                    if abs(dx) > 45:
                        self.rect.x += int(self.speed * self.direction)

        if not in_guard_mode:
            self.turn_timer = 0
            self.rect.x += int(self.speed * self.direction)
            if random.random() < 0.008:
                self.direction *= -1

        if self.rect.left <= 0:
            self.rect.left = 0
            self.direction = 1
        elif self.rect.right >= self.map_width:
            self.rect.right = self.map_width
            self.direction = -1

        if self.shield_active:
            self.image = self.shield_right if self.direction > 0 else self.shield_left
        else:
            self.image = self.broken_right if self.direction > 0 else self.broken_left

    def draw(self, screen, camera_x=0):
        ren_rect = self.rect.move(-camera_x, 0)
        screen.blit(self.image, ren_rect)

        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(screen, RED, (ren_rect.x, ren_rect.top - 12, self.rect.width, 4))
        pygame.draw.rect(screen, GREEN, (ren_rect.x, ren_rect.top - 12, int(self.rect.width * hp_ratio), 4))

        if self.shield_active:
            pygame.draw.rect(screen, CYBER_BLUE, (ren_rect.x, ren_rect.top - 7, self.rect.width, 3))


class FlyingEnemy(pygame.sprite.Sprite):
    """Lớp quái bay di chuyển uốn lượn trên không"""
    def __init__(self, x, y, fly_range=180, map_width=2400):
        super().__init__()
        self.image_right = create_sprite_surface(FLYING_DRONE_PIXELS, scale=2.5)
        self.image_left = pygame.transform.flip(self.image_right, True, False)
        self.image = self.image_right
        self.rect = self.image.get_rect(topleft=(x, y))

        self.max_hp = 35
        self.hp = 35
        self.damage = 12
        self.speed = 2.5

        self.start_x = x
        self.fly_range = fly_range
        self.direction = 1
        self.map_width = map_width

        self.angle = random.uniform(0, math.pi * 2)
        self.float_amplitude = 12
        self.base_y = y

        self.shoot_cooldown = random.randint(60, 120)

    def update(self, enemy_bullets=None, *args):
        self.rect.x += int(self.speed * self.direction)

        if abs(self.rect.x - self.start_x) > self.fly_range:
            self.direction *= -1

        if self.rect.left <= 0:
            self.rect.left = 0
            self.direction = 1
        elif self.rect.right >= self.map_width:
            self.rect.right = self.map_width
            self.direction = -1

        if self.direction > 0:
            self.image = self.image_right
        else:
            self.image = self.image_left

        self.angle += 0.08
        self.rect.y = int(self.base_y + math.sin(self.angle) * self.float_amplitude)

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def draw(self, screen, camera_x=0):
        ren_rect = self.rect.move(-camera_x, 0)
        screen.blit(self.image, ren_rect)

        hp_ratio = max(0, self.hp / self.max_hp)
        pygame.draw.rect(screen, RED, (ren_rect.x, ren_rect.top - 8, self.rect.width, 4))
        pygame.draw.rect(screen, GREEN, (ren_rect.x, ren_rect.top - 8, int(self.rect.width * hp_ratio), 4))


class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y, map_width=2400, max_hp=1500):
        super().__init__()
        self.img_p1 = create_sprite_surface(BOSS_PHASE1_PIXELS, scale=3.5)
        self.img_p2 = create_sprite_surface(BOSS_PHASE2_PIXELS, scale=3.5)
        self.image = self.img_p1
        self.rect = self.image.get_rect(topleft=(x, y))
        
        self.max_hp = max_hp
        self.hp = max_hp
        self.damage = 20
        
        self.speed = 2
        self.map_width = map_width
        self.phase = 1
        self.shoot_cooldown = 0
        self.shoot_delay = 75
        self.detect_range = 800

    def update(self, player=None, enemy_bullets=None):
        if not player:
            return

        # --- CHUYỂN PHASE KHI HP <= 50% ---
        if self.hp <= self.max_hp * 0.5 and self.phase == 1:
            self.phase = 2
            self.image = self.img_p2
            self.max_hp = 3000
            self.hp = 3000
            self.speed = 3.5
            self.shoot_delay = 45

        self.rect.x = max(0, min(self.rect.x, self.map_width - self.rect.width))

        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if dist <= self.detect_range:
            if abs(dx) > 80:
                self.rect.x += self.speed if dx > 0 else -self.speed

            if self.shoot_cooldown <= 0 and enemy_bullets is not None:
                if self.phase == 1:
                    bullet = EnemyBullet(
                        x=self.rect.centerx,
                        y=self.rect.centery - 10,
                        target_x=player.rect.centerx,
                        target_y=player.rect.centery,
                        speed=8,
                        damage=15
                    )
                    enemy_bullets.add(bullet)
                else:
                    for angle_offset in [-0.25, 0.0, 0.25]:
                        bullet = EnemyBullet(
                            x=self.rect.centerx,
                            y=self.rect.centery - 10,
                            target_x=player.rect.centerx,
                            target_y=player.rect.centery,
                            speed=10,
                            damage=30,
                            angle_offset=angle_offset
                        )
                        enemy_bullets.add(bullet)

                self.shoot_cooldown = self.shoot_delay

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def draw(self, screen, camera_x=0):
        ren_rect = self.rect.move(-camera_x, 0)
        screen.blit(self.image, ren_rect)

    def draw_health_bar(self, screen, player):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)

        if dist <= self.detect_range and self.hp > 0:
            bar_w, bar_h = 420, 20
            bar_x = (screen.get_width() - bar_w) // 2
            bar_y = 20

            border_color = ORANGE if self.phase == 2 else CYBER_PINK
            pygame.draw.rect(screen, (15, 15, 25), (bar_x - 4, bar_y - 4, bar_w + 8, bar_h + 8), border_radius=6)
            pygame.draw.rect(screen, border_color, (bar_x - 4, bar_y - 4, bar_w + 8, bar_h + 8), 2, border_radius=6)

            hp_ratio = max(0, self.hp / self.max_hp)
            fill_color = DARK_RED if self.phase == 2 else RED
            pygame.draw.rect(screen, fill_color, (bar_x, bar_y, bar_w, bar_h), border_radius=3)
            pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h), border_radius=3)

            font = pygame.font.SysFont("Arial", 13, bold=True)
            status_str = "BOSS PHASE 2: RAGE MODE (2x DMG)" if self.phase == 2 else "BOSS PHASE 1"
            txt_color = ORANGE if self.phase == 2 else WHITE
            
            txt = font.render(f"{status_str} [{max(0, self.hp)}/{self.max_hp}]", True, txt_color)
            screen.blit(txt, (screen.get_width() // 2 - txt.get_width() // 2, bar_y + 3))