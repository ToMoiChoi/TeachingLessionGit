import pygame
import random
from config import GROUND_Y

# ============================================================
# PARTICLE
# ============================================================

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-180, 180)
        self.vy = random.uniform(-220, -40)
        self.life = random.uniform(0.25, 0.6)
        self.color = color
        self.size = random.randint(3, 7)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 600 * dt
        self.life -= dt

    def draw(self, surface):
        if self.life <= 0:
            return
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)


# ============================================================
# FIGHTER
# ============================================================

class Fighter:
    def __init__(self, name, color, max_hp, speed=160):
        self.name = name
        self.color = color
        self.max_hp = max_hp
        self.hp = max_hp
        self.max_stamina = 100
        self.stamina = 100
        self.x = 250
        self.y = GROUND_Y
        self.width = 55
        self.height = 110
        self.facing = 1
        self.stance = "MID"
        self.speed = speed # Thêm tốc độ di chuyển linh hoạt

        self.light_cd = 0
        self.heavy_cd = 0
        self.skill_cd = 0
        self.attack_timer = 0
        self.attack_type = None
        self.parry_timer = 0
        self.dodge_timer = 0
        self.stun_timer = 0
        self.hit_flash = 0
        self.alive = True
        self.last_action = "Sẵn sàng"

    def reset(self, x):
        self.hp = self.max_hp
        self.stamina = self.max_stamina
        self.x = x
        self.y = GROUND_Y
        self.facing = 1
        self.stance = "MID"
        self.light_cd = 0
        self.heavy_cd = 0
        self.skill_cd = 0
        self.attack_timer = 0
        self.attack_type = None
        self.parry_timer = 0
        self.dodge_timer = 0
        self.stun_timer = 0
        self.hit_flash = 0
        self.alive = True
        self.last_action = "Sẵn sàng"

    def update(self, dt):
        self.light_cd = max(0, self.light_cd - dt)
        self.heavy_cd = max(0, self.heavy_cd - dt)
        self.skill_cd = max(0, self.skill_cd - dt)
        self.attack_timer = max(0, self.attack_timer - dt)
        self.parry_timer = max(0, self.parry_timer - dt)
        self.dodge_timer = max(0, self.dodge_timer - dt)
        self.stun_timer = max(0, self.stun_timer - dt)
        self.hit_flash = max(0, self.hit_flash - dt)
        self.stamina = min(self.max_stamina, self.stamina + dt * 18)

    def rect(self):
        return pygame.Rect(
            int(self.x - self.width // 2),
            int(self.y - self.height),
            self.width,
            self.height
        )

    def center_y(self):
        return self.y - self.height // 2