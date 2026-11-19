"""Các loại quái mới: Kamikaze (lao tới tự nổ), Sniper (ngắm laser rồi bắn tỉa),
Teleporter (dịch chuyển cạnh người chơi) và boss Mẫu Hạm Drone (màn 6).

Mọi quái đều có: hp, max_hp, damage, rect, image, update(enemy_bullets, player), draw(screen, camera_x).
"""
import math
import random

import pygame

from Enemy import ENEMY_COLOR_MAP, EnemyBullet, FlyingEnemy, create_sprite_surface
from font_vn import get_font

RED = (255, 50, 50)
GREEN = (50, 255, 50)
CYBER_BLUE = (0, 243, 255)
CYBER_PINK = (255, 0, 127)
YELLOW = (255, 220, 0)
ORANGE = (255, 140, 0)
WHITE = (255, 255, 255)

KAMIKAZE_PIXELS = [
    "......##......",
    ".....#YY#.....",
    "....######....",
    "..##XXXXXX##..",
    ".#XXXXXXXXXX#.",
    "#XXRRXXXXRRXX#",
    "#XXRRXXXXRRXX#",
    "#XXXXXXXXXXXX#",
    "#XGGGGGGGGGGX#",
    ".#XXXXXXXXXX#.",
    "..##XXXXXX##..",
    "...#GG##GG#...",
    "...###..###...",
]

SNIPER_PIXELS = [
    "....######..........",
    "...#XXXXXX#.........",
    "..#XXRRRRXX#........",
    "..#XXXXXXXX#########",
    "..#XXXXXXXXGGGGGGGG#",
    "...##########.......",
    "...#GGGGGGGG#.......",
    "..#XXXXXXXXXX#......",
    "..#XX#GGGG#XX#......",
    "..#XX#....#XX#......",
    ".#GGG#....#GGG#.....",
    ".#####....#####.....",
]

TELEPORT_PIXELS = [
    "....########....",
    "..##PPPPPPPP##..",
    ".#PPXXXXXXXXPP#.",
    "#PXXXCCCCCCXXXP#",
    "#PXXCCWWWWCCXXP#",
    "#PXXCCWWWWCCXXP#",
    "#PXXXCCCCCCXXXP#",
    ".#PPXXXXXXXXPP#.",
    "..##PPPPPPPP##..",
    "....#P#..#P#....",
    "...#P#....#P#...",
    "...##......##...",
]

MOTHERSHIP_PIXELS = [
    "..........############..........",
    "........##CCCCCCCCCCCC##........",
    "......##XXXXXXXXXXXXXXXX##......",
    "....##XXXXXXRRRRRRRRXXXXXX##....",
    "..##XXXXXXXXRRRRRRRRXXXXXXXX##..",
    ".#XXGGGGXXXXXXXXXXXXXXXXGGGGXX#.",
    "#XXGGGGGGXXXXXXXXXXXXXXGGGGGGXX#",
    "#PPPPPPPPPPPPPPPPPPPPPPPPPPPPPP#",
    "#XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX#",
    ".##XXX##XXXXX######XXXXX##XXX##.",
    "...#C#..#C#..........#C#..#C#...",
    "....#....#............#....#....",
]


def _draw_hp_bar(screen, ren_rect, hp, max_hp, offset=8):
    ratio = max(0.0, hp / max(1, max_hp))
    pygame.draw.rect(screen, RED, (ren_rect.x, ren_rect.top - offset, ren_rect.width, 4))
    pygame.draw.rect(screen, GREEN, (ren_rect.x, ren_rect.top - offset, int(ren_rect.width * ratio), 4))


class KamikazeEnemy(pygame.sprite.Sprite):
    """Robot cảm tử: thấy người chơi thì lao tới, chạm gần thì kích nổ sau 0.5 giây."""

    BLAST_RADIUS = 85
    BLAST_DAMAGE = 30

    def __init__(self, x, y, map_width=2400):
        super().__init__()
        self.image_right = create_sprite_surface(KAMIKAZE_PIXELS, scale=3)
        self.image_left = pygame.transform.flip(self.image_right, True, False)
        self.image = self.image_right
        self.rect = self.image.get_rect(topleft=(x, y))
        self.rect.bottom = 380 if y > 300 else self.rect.bottom
        self.max_hp = self.hp = 30
        self.damage = 0            # không gây sát thương khi chạm, chỉ nổ
        self.speed = 1.4
        self.chase_speed = 4.4
        self.direction = -1
        self.map_width = map_width
        self.fuse = -1             # -1: chưa kích hoạt
        self.explode_now = False   # gameplay đọc cờ này để tạo vụ nổ

    def update(self, enemy_bullets=None, player=None, *args):
        if self.fuse >= 0:
            self.fuse -= 1
            if self.fuse <= 0:
                self.explode_now = True
            return
        speed = self.speed
        if player is not None:
            dx = player.rect.centerx - self.rect.centerx
            dy = abs(player.rect.centery - self.rect.centery)
            if abs(dx) < 340 and dy < 130:
                self.direction = 1 if dx > 0 else -1
                speed = self.chase_speed
                if abs(dx) < 46 and dy < 60:
                    self.fuse = 30
            elif random.random() < 0.01:
                self.direction *= -1
        self.rect.x += int(speed * self.direction)
        if self.rect.left <= 0:
            self.rect.left, self.direction = 0, 1
        elif self.rect.right >= self.map_width:
            self.rect.right, self.direction = self.map_width, -1
        self.image = self.image_right if self.direction > 0 else self.image_left

    def draw(self, screen, camera_x=0):
        ren = self.rect.move(-camera_x, 0)
        if self.fuse >= 0:
            # nhấp nháy đỏ càng lúc càng nhanh
            flash = (self.fuse // (2 if self.fuse < 12 else 4)) % 2 == 0
            screen.blit(self.image, ren)
            if flash:
                glow = pygame.Surface(ren.size, pygame.SRCALPHA)
                glow.fill((255, 40, 40, 150))
                screen.blit(glow, ren)
            pygame.draw.circle(screen, (255, 80, 80), ren.center, int(self.BLAST_RADIUS * (1 - self.fuse / 30)), 1)
        else:
            screen.blit(self.image, ren)
        _draw_hp_bar(screen, ren, self.hp, self.max_hp)


class SniperEnemy(pygame.sprite.Sprite):
    """Lính bắn tỉa đứng yên: chiếu tia ngắm đỏ ~1.2 giây, khóa mục tiêu rồi bắn đạn rất nhanh."""

    def __init__(self, x, y, map_width=2400):
        super().__init__()
        self.image_right = create_sprite_surface(SNIPER_PIXELS, scale=3)
        self.image_left = pygame.transform.flip(self.image_right, True, False)
        self.image = self.image_left
        self.rect = self.image.get_rect(topleft=(x, y))
        if y > 300:                      # đứng trên sàn chính
            self.rect.bottom = 380
        self.max_hp = self.hp = 45
        self.damage = 10
        self.map_width = map_width
        self.facing = -1
        self.aim_timer = 0
        self.aim_total = 75
        self.cooldown = random.randint(40, 90)
        self.target = None
        self.range = 640

    def _muzzle(self):
        if self.facing > 0:
            return self.rect.right - 2, self.rect.top + 13
        return self.rect.left + 2, self.rect.top + 13

    def update(self, enemy_bullets=None, player=None, *args):
        if player is None:
            return
        dx = player.rect.centerx - self.rect.centerx
        dist = math.hypot(dx, player.rect.centery - self.rect.centery)
        if self.aim_timer == 0:
            self.facing = 1 if dx > 0 else -1
            self.image = self.image_right if self.facing > 0 else self.image_left
        if self.cooldown > 0:
            self.cooldown -= 1
            return
        if self.aim_timer == 0:
            if dist < self.range:
                self.aim_timer = 1
            return
        self.aim_timer += 1
        if self.aim_timer < self.aim_total - 15:
            self.target = player.rect.center          # bám theo
        if self.aim_timer >= self.aim_total:
            if enemy_bullets is not None and self.target:
                mx, my = self._muzzle()
                enemy_bullets.add(EnemyBullet(mx, my, self.target[0], self.target[1], speed=16, damage=25))
            self.aim_timer = 0
            self.cooldown = 110
            self.target = None

    def draw(self, screen, camera_x=0):
        ren = self.rect.move(-camera_x, 0)
        if self.aim_timer > 0 and self.target:
            mx, my = self._muzzle()
            locked = self.aim_timer >= self.aim_total - 15
            col = (255, 255, 255) if locked and self.aim_timer % 4 < 2 else (255, 40, 60)
            tx, ty = self.target
            ang = math.atan2(ty - my, tx - mx)
            ex, ey = mx + math.cos(ang) * 900, my + math.sin(ang) * 900
            pygame.draw.line(screen, col, (mx - camera_x, my), (ex - camera_x, ey), 2 if locked else 1)
        screen.blit(self.image, ren)
        _draw_hp_bar(screen, ren, self.hp, self.max_hp)


class TeleportEnemy(pygame.sprite.Sprite):
    """Robot dịch chuyển: biến mất rồi hiện ra cạnh người chơi, bắn chùm 3 viên."""

    def __init__(self, x, y, map_width=2400):
        super().__init__()
        self.base_image = create_sprite_surface(TELEPORT_PIXELS, scale=3)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.max_hp = self.hp = 55
        self.damage = 12
        self.map_width = map_width
        self.timer = random.randint(60, 140)
        self.phase = "IDLE"     # IDLE -> FADE_OUT -> FADE_IN -> SHOOT
        self.alpha = 255
        self.bob = random.uniform(0, 6.28)
        self.base_y = self.rect.y

    def update(self, enemy_bullets=None, player=None, *args):
        self.bob += 0.07
        if self.phase == "IDLE":
            self.rect.y = int(self.base_y + math.sin(self.bob) * 6)
            self.timer -= 1
            if self.timer <= 0 and player is not None:
                self.phase, self.timer = "FADE_OUT", 20
        elif self.phase == "FADE_OUT":
            self.timer -= 1
            self.alpha = int(255 * self.timer / 20)
            if self.timer <= 0 and player is not None:
                side = random.choice((-1, 1))
                nx = player.rect.centerx + side * random.randint(170, 260)
                nx = max(20, min(self.map_width - self.rect.width - 20, nx))
                ny = random.randint(170, 300)
                self.rect.topleft = (nx, ny)
                self.base_y = ny
                self.phase, self.timer = "FADE_IN", 20
        elif self.phase == "FADE_IN":
            self.timer -= 1
            self.alpha = int(255 * (1 - self.timer / 20))
            if self.timer <= 0:
                self.phase, self.timer = "SHOOT", 25
        elif self.phase == "SHOOT":
            self.timer -= 1
            if self.timer <= 0:
                if enemy_bullets is not None and player is not None:
                    for off in (-0.2, 0.0, 0.2):
                        enemy_bullets.add(EnemyBullet(self.rect.centerx, self.rect.centery,
                                                      player.rect.centerx, player.rect.centery,
                                                      speed=6, damage=12, angle_offset=off))
                self.phase, self.timer = "IDLE", random.randint(150, 210)
        self.image = self.base_image.copy()
        self.image.set_alpha(max(0, min(255, self.alpha)))

    @property
    def untargetable(self):
        """Đang tàng hình thì đạn bay xuyên qua."""
        return self.phase in ("FADE_OUT", "FADE_IN") and self.alpha < 120

    def draw(self, screen, camera_x=0):
        ren = self.rect.move(-camera_x, 0)
        if self.phase in ("FADE_OUT", "FADE_IN"):
            r = int(30 * (1 - self.alpha / 255)) + 6
            pygame.draw.circle(screen, CYBER_PINK, ren.center, r, 2)
        if self.phase == "SHOOT" and self.timer % 6 < 3:
            pygame.draw.circle(screen, YELLOW, ren.center, 26, 1)
        screen.blit(self.image, ren)
        if self.alpha > 120:
            _draw_hp_bar(screen, ren, self.hp, self.max_hp)


class MothershipBoss(pygame.sprite.Sprite):
    """Boss giữa game (màn 6): bay trên cao, thả mưa đạn và gọi drone hộ tống."""

    def __init__(self, x, y=70, map_width=2400, max_hp=1400):
        super().__init__()
        self.image = create_sprite_surface(MOTHERSHIP_PIXELS, scale=3.5)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.max_hp = self.hp = max_hp
        self.damage = 20
        self.map_width = map_width
        self.phase = 1
        self.speed = 2.2
        self.detect_range = 900
        self.shoot_cooldown = 60
        self.summon_cooldown = 240
        self.spawn_queue = []      # gameplay lấy quái từ đây thêm vào nhóm enemies
        self.children = []
        self.t = 0
        self.base_y = y

    def update(self, player=None, enemy_bullets=None):
        if player is None:
            return
        self.t += 1
        if self.phase == 1 and self.hp <= self.max_hp * 0.5:
            self.phase = 2
            self.speed = 3.2
        dx = player.rect.centerx - self.rect.centerx
        if abs(dx) > self.detect_range:
            return
        if abs(dx) > 30:
            self.rect.x += int(self.speed if dx > 0 else -self.speed)
        self.rect.x = max(0, min(self.rect.x, self.map_width - self.rect.width))
        self.rect.y = int(self.base_y + math.sin(self.t * 0.04) * 14)

        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0 and enemy_bullets is not None:
            n = 3 if self.phase == 1 else 5
            for i in range(n):
                off = (i - (n - 1) / 2) * 0.22
                enemy_bullets.add(EnemyBullet(self.rect.centerx, self.rect.bottom - 6,
                                              player.rect.centerx, player.rect.centery,
                                              speed=6 if self.phase == 1 else 7.5,
                                              damage=14 if self.phase == 1 else 20, angle_offset=off))
            self.shoot_cooldown = 70 if self.phase == 1 else 48

        self.children = [c for c in self.children if c.alive()]
        self.summon_cooldown -= 1
        if self.summon_cooldown <= 0:
            limit = 2 if self.phase == 1 else 4
            for _ in range(max(0, limit - len(self.children))):
                d = FlyingEnemy(self.rect.centerx + random.randint(-60, 60), self.rect.bottom + 20,
                                fly_range=140, map_width=self.map_width)
                d.max_hp = d.hp = 25
                self.children.append(d)
                self.spawn_queue.append(d)
            self.summon_cooldown = 300 if self.phase == 1 else 210

    def draw(self, screen, camera_x=0):
        ren = self.rect.move(-camera_x, 0)
        # chùm sáng quét bên dưới
        beam = pygame.Surface((ren.width - 40, 380 - ren.bottom), pygame.SRCALPHA)
        a = 25 + int(15 * math.sin(self.t * 0.1))
        beam.fill((255, 0, 127, a) if self.phase == 2 else (0, 243, 255, a))
        screen.blit(beam, (ren.x + 20, ren.bottom))
        screen.blit(self.image, ren)

    def draw_health_bar(self, screen, player):
        if abs(player.rect.centerx - self.rect.centerx) > self.detect_range or self.hp <= 0:
            return
        bar_w, bar_h = 360, 20
        bx, by = (screen.get_width() - bar_w) // 2, 20
        border = CYBER_PINK if self.phase == 2 else CYBER_BLUE
        pygame.draw.rect(screen, (15, 15, 25), (bx - 4, by - 4, bar_w + 8, bar_h + 8), border_radius=6)
        pygame.draw.rect(screen, border, (bx - 4, by - 4, bar_w + 8, bar_h + 8), 2, border_radius=6)
        pygame.draw.rect(screen, RED, (bx, by, bar_w, bar_h), border_radius=3)
        pygame.draw.rect(screen, GREEN, (bx, by, int(bar_w * max(0, self.hp) / self.max_hp), bar_h), border_radius=3)
        font = get_font(13, bold=True)
        name = "MẪU HẠM DRONE - CUỒNG NỘ" if self.phase == 2 else "MẪU HẠM DRONE"
        txt = font.render(f"{name} [{max(0, int(self.hp))}/{self.max_hp}]", True, WHITE)
        screen.blit(txt, (screen.get_width() // 2 - txt.get_width() // 2, by + 3))
