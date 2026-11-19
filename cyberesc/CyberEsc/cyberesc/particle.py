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

    def update(self):
        for p in self.particles[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[5] -= 1
            if p[5] <= 0:
                self.particles.remove(p)

    def draw(self, screen):
        for p in self.particles:
            pygame.draw.circle(screen, p[6], (int(p[0]), int(p[1])), p[4])