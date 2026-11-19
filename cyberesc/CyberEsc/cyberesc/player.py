import pygame
import math

try:
    from Sounds import Sounds
except ImportError:
    class Sounds:
        @staticmethod
        def play(sound_name):
            pass

try:
    from weapon import WEAPON_LIST
except ImportError:
    WEAPON_LIST = {}

CYBER_BLUE = (0, 243, 255)
CYBER_PINK = (255, 0, 127)
CYBER_YELLOW = (255, 230, 0)
WHITE = (255, 255, 255)


class PlayerAmmo:
    """Lớp quản lý kho đạn tương thích với GameEngine mới"""
    def __init__(self, ammo=25, max_ammo=50):
        self.ammo = ammo
        self.max_ammo = max_ammo

    def add_ammo(self, amount):
        self.ammo = min(self.max_ammo, self.ammo + amount)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Vị trí & Vật lý
        self.rect = pygame.Rect(x, y, 30, 50)
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 5
        self.jump_power = -12
        self.gravity = 0.6
        self.on_ground = False
        self.facing_right = True

        # Chỉ số sinh tồn
        self.max_hp = 100
        self.hp = 100
        self.invincible_timer = 0  # Thời gian bất tử sau khi trúng đòn

        # Quản lý đạn & Vũ khí
        self.weapon = PlayerAmmo(ammo=25, max_ammo=50)
        self.current_weapon = WEAPON_LIST.get("Blaster", None)  # Mặc định trang bị Blaster

        # Kỹ năng chém kiếm
        self.slash_delay = 25
        self.slash_cooldown = 0

        # Trạng thái Animation người que & Visuals
        self.state = "IDLE"  # IDLE, RUN, JUMP, SLASH, SHOOT
        self.body_color = CYBER_BLUE
        self.color = CYBER_BLUE
        self.head_visual = "NONE"
        self.anim_frame = 0
        self.anim_timer = 0

    @property
    def ammo(self):
        return self.weapon.ammo

    @ammo.setter
    def ammo(self, value):
        self.weapon.ammo = max(0, min(self.weapon.max_ammo, value))

    @property
    def max_ammo(self):
        return self.weapon.max_ammo

    @max_ammo.setter
    def max_ammo(self, value):
        self.weapon.max_ammo = value

    def change_weapon(self, weapon_name):
        """Chuyển đổi vũ khí hiện tại"""
        if weapon_name in WEAPON_LIST:
            self.current_weapon = WEAPON_LIST[weapon_name]

    def handle_input(self, keys):
        self.vel_x = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vel_x = -self.speed
            self.facing_right = False
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel_x = self.speed
            self.facing_right = True

    def jump(self):
        if self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False
            Sounds.play("shield_pickup.wav")

    def can_slash(self):
        return self.slash_cooldown <= 0

    def attack(self, attack_type):
        if attack_type == 'slash':
            self.state = "SLASH"
            self.anim_timer = 15
            self.slash_cooldown = self.slash_delay
            Sounds.play("sword_slash.wav")
        elif attack_type == 'shoot':
            self.state = "SHOOT"
            self.anim_timer = 10

    def shoot(self, bullet_group=None, camera_x=0):
        self.state = "SHOOT"
        self.anim_timer = 10
        Sounds.play("pistol.wav")
        return True

    def shoot_directional(self, bullet_group=None):
        self.state = "SHOOT"
        self.anim_timer = 10
        return True

    def take_damage(self, amount):
        if self.invincible_timer <= 0:
            self.hp = max(0, self.hp - amount)
            self.invincible_timer = 30  # Bất tử 30 frames (~0.5 giây)

    def apply_cosmetics(self, color, head_visual="NONE"):
        self.body_color = color
        self.color = color
        self.head_visual = head_visual

    def update(self, floor_y=380, platforms=None, level_width=2400):
        self.anim_frame += 1

        if self.slash_cooldown > 0:
            self.slash_cooldown -= 1

        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        # 1. Trọng lực & Di chuyển
        self.vel_y += self.gravity
        self.rect.x += self.vel_x
        self.rect.x = max(0, min(self.rect.x, level_width - self.rect.width))

        self.rect.y += self.vel_y
        self.on_ground = False

        # 2. Xử lý va chạm Platform
        if platforms:
            for plat in platforms:
                if self.rect.right > plat.rect.left and self.rect.left < plat.rect.right:
                    tolerance = max(10, int(self.vel_y + 4))
                    if self.vel_y >= 0 and plat.rect.top <= self.rect.bottom <= plat.rect.top + tolerance:
                        self.rect.bottom = plat.rect.top
                        self.vel_y = 0
                        self.on_ground = True

        # 3. Va chạm Mặt sàn chính
        if self.rect.bottom >= floor_y:
            self.rect.bottom = floor_y
            self.vel_y = 0
            self.on_ground = True

        # 4. Cập nhật Animation State SAU KHI chốt vị trí
        if self.anim_timer > 0:
            self.anim_timer -= 1
        else:
            if not self.on_ground:
                self.state = "JUMP"
            elif self.vel_x != 0:
                self.state = "RUN"
            else:
                self.state = "IDLE"

    def draw(self, screen, camera_x=0):
        """Vẽ Người Que với Animation tự nhiên & hiệu ứng nhịp thở"""
        # Bỏ qua vẽ nhân vật ở các frame chẵn để tạo hiệu ứng chớp tắt khi bất tử
        if self.invincible_timer > 0 and (self.invincible_timer // 3) % 2 == 0:
            return

        # Nhịp thở nhẹ cho trạng thái IDLE
        idle_bob = math.sin(self.anim_frame * 0.08) * 1.5 if self.state == "IDLE" else 0

        rx = self.rect.x - camera_x
        ry = self.rect.y + idle_bob
        cx = rx + self.rect.width // 2

        # 1. Đầu (Head)
        head_y = ry + 10
        pygame.draw.circle(screen, self.body_color, (cx, head_y), 8, 2)

        # 2. Thân (Body)
        body_bottom_y = ry + 32
        pygame.draw.line(screen, self.body_color, (cx, head_y + 8), (cx, body_bottom_y), 2)

        # 3. Chân (Legs)
        if self.state == "RUN":
            leg_swing = math.sin(self.anim_frame * 0.25) * 10
            pygame.draw.line(screen, self.body_color, (cx, body_bottom_y), (cx - leg_swing, ry + 48), 2)
            pygame.draw.line(screen, self.body_color, (cx, body_bottom_y), (cx + leg_swing, ry + 48), 2)
        elif self.state == "JUMP":
            pygame.draw.line(screen, self.body_color, (cx, body_bottom_y), (cx - 10, ry + 42), 2)
            pygame.draw.line(screen, self.body_color, (cx, body_bottom_y), (cx + 10, ry + 42), 2)
        else:  # IDLE, SLASH, SHOOT
            pygame.draw.line(screen, self.body_color, (cx, body_bottom_y), (cx - 7, self.rect.bottom), 2)
            pygame.draw.line(screen, self.body_color, (cx, body_bottom_y), (cx + 7, self.rect.bottom), 2)

        # 4. Tay & Vũ khí
        arm_y = ry + 18
        dir_sign = 1 if self.facing_right else -1

        if self.state == "SLASH":
            sword_x = cx + (30 * dir_sign)
            pygame.draw.line(screen, CYBER_PINK, (cx, arm_y), (sword_x, arm_y - 12), 3)
            arc_rect = (cx, arm_y - 25, 30, 30) if self.facing_right else (cx - 30, arm_y - 25, 30, 30)
            pygame.draw.arc(screen, CYBER_PINK, arc_rect, 0, math.pi, 2)

        elif self.state == "SHOOT":
            hand_x = cx + (14 * dir_sign)
            pygame.draw.line(screen, self.body_color, (cx, arm_y), (hand_x, arm_y), 2)
            
            # Vẽ Model súng khi ở trạng thái Bắn
            if hasattr(self, 'current_weapon') and self.current_weapon and hasattr(self.current_weapon, 'image'):
                gun_img = self.current_weapon.image
                if not self.facing_right:
                    gun_img = pygame.transform.flip(gun_img, True, False)
                    gun_x = hand_x - gun_img.get_width()
                else:
                    gun_x = hand_x
                gun_y = arm_y - gun_img.get_height() // 2
                screen.blit(gun_img, (gun_x, gun_y))
            else:
                gun_rect = (hand_x, arm_y - 3, 12, 5) if dir_sign > 0 else (hand_x - 12, arm_y - 3, 12, 5)
                pygame.draw.rect(screen, CYBER_YELLOW, gun_rect)

        elif self.state == "RUN":
            arm_swing = math.cos(self.anim_frame * 0.25) * 8
            pygame.draw.line(screen, self.body_color, (cx, arm_y), (cx + arm_swing, arm_y + 10), 2)
            pygame.draw.line(screen, self.body_color, (cx, arm_y), (cx - arm_swing, arm_y + 10), 2)

        elif self.state == "JUMP":
            pygame.draw.line(screen, self.body_color, (cx, arm_y), (cx - 10, arm_y - 6), 2)
            pygame.draw.line(screen, self.body_color, (cx, arm_y), (cx + 10, arm_y - 6), 2)

        else:  # IDLE
            arm_sway = math.sin(self.anim_frame * 0.08) * 1.5
            hand_x = cx + (8 * dir_sign)
            pygame.draw.line(screen, self.body_color, (cx, arm_y), (cx - (6 * dir_sign), arm_y + 10 + arm_sway), 2)
            pygame.draw.line(screen, self.body_color, (cx, arm_y), (hand_x, arm_y + 8 - arm_sway), 2)

        # Vẽ Model súng liên tục trên tay khi không chém kiếm / bắn
        if self.state not in ["SLASH", "SHOOT"]:
            if hasattr(self, 'current_weapon') and self.current_weapon and hasattr(self.current_weapon, 'image'):
                gun_img = self.current_weapon.image
                if not self.facing_right:
                    gun_img = pygame.transform.flip(gun_img, True, False)
                    gun_x = cx - gun_img.get_width() - 2
                else:
                    gun_x = cx + 2
                gun_y = arm_y - 4
                screen.blit(gun_img, (gun_x, gun_y))

        # 5. Mũ / Phụ kiện (Cosmetics)
        if self.head_visual == "HELMET":
            pygame.draw.arc(screen, CYBER_PINK, (cx - 10, head_y - 12, 20, 15), 0, math.pi, 3)
        elif self.head_visual == "CROWN":
            pygame.draw.polygon(screen, CYBER_YELLOW, [
                (cx - 8, head_y - 8), (cx - 8, head_y - 16),
                (cx - 3, head_y - 10), (cx, head_y - 18),
                (cx + 3, head_y - 10), (cx + 8, head_y - 16), (cx + 8, head_y - 8)
            ])