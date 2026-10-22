import pygame
import random
from config import GROUND_Y, ARENA_LEFT, ARENA_RIGHT, clamp

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
        self.speed = speed

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

    # Logic điều khiển di chuyển của Player từ bàn phím
    def update_player_input(self, dt):
        if not self.alive or self.stun_timer > 0:
            return

        keys = pygame.key.get_pressed()
        move_speed = 280
        if keys[pygame.K_LSHIFT]:
            move_speed *= 1.35

        if keys[pygame.K_a]:
            self.x -= move_speed * dt
            self.facing = -1
        if keys[pygame.K_d]:
            self.x += move_speed * dt
            self.facing = 1

        self.x = clamp(self.x, ARENA_LEFT, ARENA_RIGHT)

    # Logic điều khiển AI của Boss trong trận đấu
    def update_bot_ai(self, dt, player, attack_callback):
        if not self.alive or self.stun_timer > 0:
            return

        distance = abs(self.x - player.x)
        self.facing = -1 if self.x > player.x else 1

        if distance > 110:
            self.x += self.facing * self.speed * dt

        self.x = clamp(self.x, ARENA_LEFT, ARENA_RIGHT)
        
        # Lưu ý: Các biến theo dõi thời gian suy nghĩ của bot (bot_think, bot_attack_cd) 
        # bạn có thể quản lý tại main hoặc thêm thuộc tính riêng ở đây.