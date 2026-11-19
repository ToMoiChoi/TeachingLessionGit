"""Vật phẩm rơi ra trong màn: đồng coin (quái rơi ra) và cột checkpoint."""
import math
import random

import pygame

YELLOW = (255, 220, 0)
CYBER_BLUE = (0, 243, 255)
GREY = (90, 95, 110)
FLOOR_Y = 380


class CoinPickup(pygame.sprite.Sprite):
    """Coin bật ra khi hạ quái, rơi xuống sàn rồi tự hút về phía người chơi khi lại gần."""

    def __init__(self, x, y, value):
        super().__init__()
        self.rect = pygame.Rect(0, 0, 12, 12)
        self.rect.center = (x, y)
        self.fx, self.fy = float(x), float(y)
        self.vx = random.uniform(-3.2, 3.2)
        self.vy = random.uniform(-7, -4)
        self.value = value
        self.age = 0

    def update(self, player=None):
        self.age += 1
        if player is not None and self.age > 20:
            dx = player.rect.centerx - self.fx
            dy = player.rect.centery - self.fy
            dist = math.hypot(dx, dy)
            if dist < 150 or self.age > 420:     # nam châm
                spd = 10 if dist < 150 else 14
                self.fx += dx / max(1, dist) * spd
                self.fy += dy / max(1, dist) * spd
                self.rect.center = (int(self.fx), int(self.fy))
                return
        self.vy += 0.4
        self.fx += self.vx
        self.fy += self.vy
        if self.fy >= FLOOR_Y - 6:
            self.fy = FLOOR_Y - 6
            self.vy *= -0.45
            self.vx *= 0.7
        self.rect.center = (int(self.fx), int(self.fy))

    def draw(self, screen, camera_x=0):
        cx, cy = self.rect.centerx - camera_x, self.rect.centery
        w = max(2, int(6 * abs(math.cos(self.age * 0.15))))   # xoay tròn
        pygame.draw.ellipse(screen, YELLOW, (cx - w, cy - 6, w * 2, 12))
        pygame.draw.ellipse(screen, (255, 255, 200), (cx - w, cy - 6, w * 2, 12), 1)


class Checkpoint(pygame.sprite.Sprite):
    """Cột checkpoint giữa màn: chạm vào để lưu điểm hồi sinh."""

    def __init__(self, x):
        super().__init__()
        self.rect = pygame.Rect(x, FLOOR_Y - 90, 30, 90)
        self.active = False
        self.t = 0

    def update(self):
        self.t += 1

    def draw(self, screen, camera_x=0):
        x = self.rect.x - camera_x
        col = CYBER_BLUE if self.active else GREY
        pygame.draw.rect(screen, (40, 40, 60), (x + 4, FLOOR_Y - 8, 22, 8))
        pygame.draw.line(screen, col, (x + 15, FLOOR_Y - 8), (x + 15, self.rect.top), 3)
        wave = math.sin(self.t * 0.12) * 4 if self.active else 0
        flag = [(x + 17, self.rect.top), (x + 42, self.rect.top + 9 + wave), (x + 17, self.rect.top + 20)]
        pygame.draw.polygon(screen, col, flag)
        if self.active:
            glow = pygame.Surface((60, 60), pygame.SRCALPHA)
            a = 60 + int(40 * math.sin(self.t * 0.1))
            pygame.draw.circle(glow, (0, 243, 255, a), (30, 30), 28)
            screen.blit(glow, (x - 15, self.rect.top - 20))
