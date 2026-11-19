import random
import pygame
from config import CYBER_BLUE

class ParticleManager:
    def __init__(self):
        self.particles = []

    def add_hit_particles(self, x, y, color=CYBER_BLUE, count=5):
        for _ in range(count):
            vx = random.uniform(-4, 4)
            vy = random.uniform(-4, 4)
            size = random.randint(3, 6)
            life = random.randint(10, 20)
            self.particles.append([x, y, vx, vy, size, life, color])

    def add_jump_dust(self, x, y):
        for _ in range(6):
            px = x + random.randint(-10, 10)
            py = y
            self.particles.append([px, py, random.uniform(-2, 2), random.uniform(-1, 0), random.randint(2, 4), 15, (200, 200, 200)])

    def add_death_explosion(self, x, y):
        """Vụ nổ khi người chơi chết: mảnh neon văng ra mọi hướng."""
        import math
        colors = [(0, 220, 255), (255, 0, 128), (255, 50, 50), (255, 255, 255)]
        for _ in range(70):
            ang = random.uniform(0, 2 * math.pi)
            spd = random.uniform(2, 9)
            self.particles.append([x, y, math.cos(ang) * spd, math.sin(ang) * spd - 2,
                                   random.randint(3, 7), random.randint(35, 80), random.choice(colors)])

    def update(self):
        for p in self.particles[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[2] *= 0.95          # lực cản: mảnh chậm dần
            p[3] = p[3] * 0.95 + 0.12   # trọng lực nhẹ
            p[5] -= 1
            if p[5] <= 0:
                self.particles.remove(p)

    def draw(self, screen):
        for p in self.particles:
            pygame.draw.circle(screen, p[6], (int(p[0]), int(p[1])), p[4])