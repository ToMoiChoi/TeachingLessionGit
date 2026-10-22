import pygame
import math
from config import CYBER_YELLOW, GREEN, CYBER_PINK, WHITE

ORANGE = (255, 140, 0)

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, p_type="HP"):
        super().__init__()
        self.type = p_type  # "HP", "SPEED", "DMG", "AMMO"
        self.rect = pygame.Rect(x, y, 22, 22)
        self.base_y = y
        self.float_timer = 0

    def update(self):
        self.float_timer += 0.08
        self.rect.y = self.base_y + int(math.sin(self.float_timer) * 5)

    def draw(self, screen):
        if self.type == "AMMO":
            color = ORANGE
        elif self.type == "HP":
            color = GREEN
        elif self.type == "DMG":
            color = CYBER_YELLOW
        else:
            color = CYBER_PINK

        pygame.draw.circle(screen, color, self.rect.center, 11)
        pygame.draw.circle(screen, WHITE, self.rect.center, 11, 2)

        # Biểu tượng ô hình hộp đạn bên trong
        if self.type == "AMMO":
            box = pygame.Rect(self.rect.centerx - 4, self.rect.centery - 4, 8, 8)
            pygame.draw.rect(screen, WHITE, box)