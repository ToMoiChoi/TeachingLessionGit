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
    COYOTE_FRAMES = 7
    JUMP_BUFFER_FRAMES = 7
    LANDING_SQUASH_FRAMES = 8

    def __init__(self, x, y):
        super().__init__()
        # Vị trí & Vật lý
        self.rect = pygame.Rect(x, y, 30, 50)
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 5
        self.base_jump_power = -12.0
        self.jump_power = -12.0
        self.gravity = 0.6
        self.on_ground = False
        self.was_on_ground = False
        self.just_landed = False
        self.land_impact_vy = 0.0
        self.landing_timer = 0
        self.coyote_timer = 0
        self.jump_buffer_timer = 0
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

        # Trạng thái Animation người que & Visuals (Costumes + Equipment)
        self.state = "IDLE"  # IDLE, RUN, JUMP, SLASH, SHOOT
        self.body_color = CYBER_BLUE
        self.color = CYBER_BLUE
        self.body_style = "BASIC"
        self.head_visual = "NONE"
        self.head_color = WHITE
        self.back_visual = "NONE"
        self.back_color = CYBER_BLUE
        self.acc_visual = "NONE"
        self.acc_color = CYBER_YELLOW
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

    def _execute_jump(self):
        self.vel_y = self.jump_power
        self.on_ground = False
        self.coyote_timer = 0
        self.jump_buffer_timer = 0
        self.landing_timer = 0
        Sounds.play("shield_pickup.wav")

    def jump(self):
        if self.on_ground or self.coyote_timer > 0:
            self._execute_jump()
            return True
        # Lưu đệm phím nhảy nếu vừa bấm sát lúc sắp chạm đất
        self.jump_buffer_timer = self.JUMP_BUFFER_FRAMES
        return False

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

    def apply_cosmetics(self, color, head_visual="NONE", head_color=WHITE,
                        body_style="BASIC", back_visual="NONE", back_color=CYBER_BLUE,
                        acc_visual="NONE", acc_color=CYBER_YELLOW):
        self.body_color = color
        self.color = color
        self.body_style = body_style
        self.head_visual = head_visual
        self.head_color = head_color
        self.back_visual = back_visual
        self.back_color = back_color
        self.acc_visual = acc_visual
        self.acc_color = acc_color

    def update(self, floor_y=380, platforms=None, level_width=2400):
        self.anim_frame += 1
        self.was_on_ground = self.on_ground
        self.just_landed = False
        self.land_impact_vy = 0.0

        if self.slash_cooldown > 0:
            self.slash_cooldown -= 1
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
        if self.landing_timer > 0:
            self.landing_timer -= 1
        if self.jump_buffer_timer > 0:
            self.jump_buffer_timer -= 1

        # 1. Trọng lực & Di chuyển
        prev_bottom = self.rect.bottom
        self.vel_y = min(18.0, self.vel_y + self.gravity)
        impact_vy = self.vel_y

        self.rect.x += int(round(self.vel_x))
        self.rect.x = max(0, min(self.rect.x, level_width - self.rect.width))

        self.rect.y += int(round(self.vel_y))
        self.on_ground = False

        # 2. Xử lý va chạm Platform (ổn định kể cả khi rơi nhanh)
        if platforms and self.vel_y >= 0:
            for plat in platforms:
                if self.rect.right > plat.rect.left + 2 and self.rect.left < plat.rect.right - 2:
                    if prev_bottom <= plat.rect.top + 8 and self.rect.bottom >= plat.rect.top:
                        self.rect.bottom = plat.rect.top
                        self.vel_y = 0
                        self.on_ground = True
                        break

        # 3. Va chạm Mặt sàn chính
        if self.rect.bottom >= floor_y:
            self.rect.bottom = floor_y
            self.vel_y = 0
            self.on_ground = True

        # 4. Coyote time, Landing detection & Jump buffer
        if self.on_ground:
            self.coyote_timer = self.COYOTE_FRAMES
            if not self.was_on_ground and impact_vy > 1.5:
                self.just_landed = True
                self.land_impact_vy = impact_vy
                self.landing_timer = self.LANDING_SQUASH_FRAMES
            if self.jump_buffer_timer > 0:
                self._execute_jump()
        else:
            if self.coyote_timer > 0:
                self.coyote_timer -= 1

        # 5. Cập nhật Animation State SAU KHI chốt vị trí
        if self.anim_timer > 0:
            self.anim_timer -= 1
        else:
            if not self.on_ground:
                self.state = "JUMP"
            elif self.vel_x != 0:
                self.state = "RUN"
            else:
                self.state = "IDLE"

    def _draw_back_equipment(self, screen, cx, ry, body_bottom_y, dir_sign):
        """Vẽ trang bị sau lưng (Áo choàng, Jetpack, Cánh, Dải lụa)"""
        if self.back_visual == "NONE":
            return
        col = self.back_color
        back_x = cx - dir_sign * 4
        shoulder_y = ry + 18
        flutter = math.sin(self.anim_frame * 0.18) * (4 if self.state == "RUN" else 2)

        if self.back_visual == "CAPE":
            pts = [
                (cx, shoulder_y),
                (cx - dir_sign * (16 + flutter), body_bottom_y + 12),
                (cx - dir_sign * (6 + flutter * 0.5), body_bottom_y + 14),
            ]
            pygame.draw.polygon(screen, col, pts)
            pygame.draw.polygon(screen, WHITE, pts, 1)

        elif self.back_visual == "JETPACK":
            jp_x = cx - dir_sign * 10 if dir_sign > 0 else cx + 3
            jp_rect = pygame.Rect(int(jp_x), int(shoulder_y - 2), 7, 16)
            pygame.draw.rect(screen, col, jp_rect, border_radius=2)
            pygame.draw.rect(screen, WHITE, jp_rect, 1, border_radius=2)
            # Tia lửa phản lực khi nhảy hoặc chạy
            if not self.on_ground or (self.anim_frame // 4) % 2 == 0:
                flame_len = 11 if not self.on_ground else 5
                fx = jp_rect.centerx
                fy = jp_rect.bottom
                pygame.draw.polygon(screen, (255, 160, 0), [(fx - 3, fy), (fx + 3, fy), (fx, fy + flame_len)])
                pygame.draw.polygon(screen, CYBER_YELLOW, [(fx - 1, fy), (fx + 1, fy), (fx, fy + flame_len - 2)])

        elif self.back_visual == "NEON_WINGS":
            flap = math.sin(self.anim_frame * 0.16) * 5
            for s in (-1, 1):
                pts = [
                    (cx, shoulder_y + 2),
                    (cx + s * 18, shoulder_y - 10 + flap),
                    (cx + s * 22, shoulder_y + 4 + flap * 0.5),
                    (cx + s * 10, shoulder_y + 10),
                ]
                pygame.draw.polygon(screen, col, pts, 2)
                pygame.draw.line(screen, WHITE, (cx, shoulder_y + 2), (cx + s * 17, shoulder_y - 6 + flap), 1)

        elif self.back_visual == "THRUSTER":
            tx = cx - dir_sign * 11 if dir_sign > 0 else cx + 3
            for dy in (-2, 7):
                r = pygame.Rect(int(tx), int(shoulder_y + dy), 8, 6)
                pygame.draw.rect(screen, col, r, border_radius=2)
                pygame.draw.rect(screen, WHITE, r, 1, border_radius=2)
                glow = 7 + int(abs(math.sin(self.anim_frame * 0.25)) * 5)
                pygame.draw.line(screen, CYBER_BLUE, (r.centerx - dir_sign * 4, r.centery),
                                 (r.centerx - dir_sign * (4 + glow), r.centery), 2)

        elif self.back_visual == "RIBBON":
            pts = [
                (cx, shoulder_y),
                (cx - dir_sign * 12, shoulder_y + 5 + flutter),
                (cx - dir_sign * 22, shoulder_y + 2 - flutter),
                (cx - dir_sign * 18, shoulder_y + 10 - flutter),
            ]
            pygame.draw.lines(screen, col, False, pts, 3)

        elif self.back_visual == "ANGEL_WINGS":
            flap = math.sin(self.anim_frame * 0.12) * 5
            for s in (-1, 1):
                pts = [
                    (cx, shoulder_y + 2),
                    (cx + s * 14, shoulder_y - 14 + flap),
                    (cx + s * 24, shoulder_y - 6 + flap),
                    (cx + s * 19, shoulder_y + 6 + flap * 0.4),
                    (cx + s * 8, shoulder_y + 10),
                ]
                pygame.draw.polygon(screen, col, pts)
                pygame.draw.polygon(screen, WHITE, pts, 1)

    def _draw_body_costume(self, screen, cx, head_y, body_bottom_y, dir_sign):
        """Vẽ thân & chi tiết Costume theo body_style"""
        col = self.body_color
        top_y = head_y + 8

        if self.body_style == "BASIC":
            pygame.draw.line(screen, col, (cx, top_y), (cx, body_bottom_y), 2)
            return

        if self.body_style == "ARMOR":
            # Giáp ngực + cầu vai
            torso = pygame.Rect(int(cx - 5), int(top_y), 10, int(body_bottom_y - top_y))
            pygame.draw.rect(screen, col, torso, border_radius=3)
            pygame.draw.rect(screen, WHITE, torso, 1, border_radius=3)
            pygame.draw.circle(screen, WHITE, (int(cx), int(top_y + 6)), 2)

        elif self.body_style == "COAT":
            # Áo khoác dài có vạt xòe
            pts = [
                (cx - 4, top_y), (cx + 4, top_y),
                (cx + 8, body_bottom_y + 5), (cx - 8, body_bottom_y + 5)
            ]
            pygame.draw.polygon(screen, col, pts)
            pygame.draw.polygon(screen, WHITE, pts, 1)
            pygame.draw.line(screen, (20, 20, 35), (cx, top_y + 1), (cx, body_bottom_y + 4), 1)

        elif self.body_style == "EXO":
            # Chiến giáp hạng nặng có vai lớn & lõi năng lượng
            torso = pygame.Rect(int(cx - 7), int(top_y - 1), 14, int(body_bottom_y - top_y + 1))
            pygame.draw.rect(screen, col, torso, border_radius=3)
            pygame.draw.rect(screen, WHITE, torso, 1, border_radius=3)
            pygame.draw.rect(screen, CYBER_YELLOW, (int(cx - 9), int(top_y - 1), 4, 6), border_radius=1)
            pygame.draw.rect(screen, CYBER_YELLOW, (int(cx + 5), int(top_y - 1), 4, 6), border_radius=1)
            pygame.draw.circle(screen, CYBER_BLUE, (int(cx), int(top_y + 7)), 3)

        elif self.body_style == "NINJA":
            # Trang phục Ninja + khăn quàng bay phía sau
            torso = pygame.Rect(int(cx - 4), int(top_y), 8, int(body_bottom_y - top_y))
            pygame.draw.rect(screen, col, torso, border_radius=2)
            pygame.draw.line(screen, CYBER_PINK, (cx - 4, top_y + 2), (cx + 4, top_y + 2), 2)
            wave = math.sin(self.anim_frame * 0.22) * 3
            pygame.draw.line(screen, CYBER_PINK, (cx, top_y + 2), (cx - dir_sign * 14, top_y + 5 + wave), 2)

        elif self.body_style == "GALAXY":
            # Chiến giáp Thiên Hà phát sáng chuyển sắc
            pulse = int(127 + 127 * math.sin(self.anim_frame * 0.12))
            trim = (pulse, 180, 255)
            torso = pygame.Rect(int(cx - 6), int(top_y), 12, int(body_bottom_y - top_y + 2))
            pygame.draw.rect(screen, col, torso, border_radius=4)
            pygame.draw.rect(screen, trim, torso, 2, border_radius=4)
            pygame.draw.circle(screen, CYBER_YELLOW, (int(cx), int(top_y + 7)), 3)

        else:
            pygame.draw.line(screen, col, (cx, top_y), (cx, body_bottom_y), 2)

    def _draw_accessory(self, screen, cx, ry, body_bottom_y, foot_y):
        """Vẽ phụ kiện / chip / hào quang"""
        if self.acc_visual == "NONE":
            return
        col = self.acc_color

        if self.acc_visual == "OMNI_AURA":
            pulse = 1 + 0.12 * math.sin(self.anim_frame * 0.15)
            r_x, r_y = int(19 * pulse), int(6 * pulse)
            pygame.draw.ellipse(screen, col, (int(cx - r_x), int(foot_y - r_y // 2 - 2), r_x * 2, r_y), 2)
            ang = self.anim_frame * 0.12
            ox = cx + math.cos(ang) * 18
            oy = ry + 24 + math.sin(ang) * 10
            pygame.draw.circle(screen, WHITE, (int(ox), int(oy)), 2)

        elif self.acc_visual == "SHIELD_CORE":
            pygame.draw.circle(screen, col, (int(cx), int(ry + 24)), 4, 1)

        elif self.acc_visual == "TURBO_BOOTS":
            pygame.draw.circle(screen, col, (int(cx - 6), int(foot_y - 2)), 3)
            pygame.draw.circle(screen, col, (int(cx + 6), int(foot_y - 2)), 3)

        elif self.acc_visual in ("CRIT_CHIP", "AMMO_MODULE", "VAMP_CHIP"):
            ang = self.anim_frame * 0.1
            ox = cx + math.cos(ang) * 15
            oy = ry + 14 + math.sin(ang) * 4
            pygame.draw.circle(screen, col, (int(ox), int(oy)), 3)
            pygame.draw.circle(screen, WHITE, (int(ox), int(oy)), 1)

    def _draw_head_visual(self, screen, cx, head_y):
        """Vẽ Mũ / Phụ kiện đầu"""
        hv = self.head_visual
        hc = self.head_color
        if hv == "VISOR":
            pygame.draw.line(screen, hc, (cx - 9, head_y - 1), (cx + 9, head_y - 1), 4)
            pygame.draw.line(screen, WHITE, (cx + (2 if self.facing_right else -6), head_y - 2),
                             (cx + (6 if self.facing_right else -2), head_y - 2), 1)
        elif hv == "HALO":
            bob = math.sin(self.anim_frame * 0.12) * 1.5
            pygame.draw.ellipse(screen, hc, (cx - 11, head_y - 20 + bob, 22, 7), 2)
        elif hv == "HORNS":
            pygame.draw.polygon(screen, hc, [(cx - 7, head_y - 5), (cx - 12, head_y - 17), (cx - 3, head_y - 7)])
            pygame.draw.polygon(screen, hc, [(cx + 7, head_y - 5), (cx + 12, head_y - 17), (cx + 3, head_y - 7)])
        elif hv == "HELMET":
            pygame.draw.arc(screen, hc, (cx - 10, head_y - 12, 20, 15), 0, math.pi, 3)
        elif hv == "CROWN":
            pygame.draw.polygon(screen, hc, [
                (cx - 8, head_y - 8), (cx - 8, head_y - 16),
                (cx - 3, head_y - 10), (cx, head_y - 18),
                (cx + 3, head_y - 10), (cx + 8, head_y - 16), (cx + 8, head_y - 8)
            ])
        elif hv == "SAMURAI":
            # Mũ Kabuto + vầng trăng khuyết vàng
            pygame.draw.arc(screen, hc, (cx - 11, head_y - 12, 22, 16), 0, math.pi, 3)
            pygame.draw.line(screen, hc, (cx - 12, head_y - 4), (cx + 12, head_y - 4), 2)
            pygame.draw.lines(screen, CYBER_YELLOW, False, [
                (cx - 7, head_y - 17), (cx, head_y - 10), (cx + 7, head_y - 17)
            ], 2)
        elif hv == "CAT_EARS":
            pygame.draw.polygon(screen, hc, [(cx - 8, head_y - 6), (cx - 9, head_y - 16), (cx - 2, head_y - 8)])
            pygame.draw.polygon(screen, hc, [(cx + 8, head_y - 6), (cx + 9, head_y - 16), (cx + 2, head_y - 8)])
            pygame.draw.polygon(screen, WHITE, [(cx - 7, head_y - 7), (cx - 7, head_y - 12), (cx - 4, head_y - 8)])
            pygame.draw.polygon(screen, WHITE, [(cx + 7, head_y - 7), (cx + 7, head_y - 12), (cx + 4, head_y - 8)])
        elif hv == "CYBER_HOOD":
            pygame.draw.polygon(screen, hc, [
                (cx - 10, head_y + 2), (cx - 9, head_y - 11),
                (cx, head_y - 14), (cx + 9, head_y - 11), (cx + 10, head_y + 2)
            ], 2)
            eye_x = cx + (3 if self.facing_right else -3)
            pygame.draw.circle(screen, CYBER_BLUE, (int(eye_x), int(head_y - 1)), 2)
        elif hv == "MECHA_ANTENNA":
            pygame.draw.rect(screen, hc, (int(cx - 9), int(head_y - 11), 18, 6), border_radius=2)
            pygame.draw.line(screen, CYBER_YELLOW, (cx - 6, head_y - 11), (cx - 10, head_y - 20), 2)
            pygame.draw.line(screen, CYBER_YELLOW, (cx + 6, head_y - 11), (cx + 10, head_y - 20), 2)
            pygame.draw.circle(screen, CYBER_BLUE, (int(cx - 10), int(head_y - 20)), 2)
            pygame.draw.circle(screen, CYBER_BLUE, (int(cx + 10), int(head_y - 20)), 2)

    def draw(self, screen, camera_x=0):
        """Vẽ nhân vật kèm Animation, hiệu ứng tiếp đất (squash), Costume & Trang bị"""
        if self.invincible_timer > 0 and (self.invincible_timer // 3) % 2 == 0:
            return

        # Nhịp thở nhẹ khi IDLE + nhún nhẹ khi vừa tiếp đất (landing squash)
        idle_bob = math.sin(self.anim_frame * 0.08) * 1.5 if self.state == "IDLE" else 0
        squash = (self.landing_timer / self.LANDING_SQUASH_FRAMES) * 4.0 if self.landing_timer > 0 else 0

        rx = self.rect.x - camera_x
        ry = self.rect.y + idle_bob + squash
        cx = rx + self.rect.width // 2
        foot_y = self.rect.bottom
        dir_sign = 1 if self.facing_right else -1

        head_y = ry + 10
        body_bottom_y = ry + 32

        # 0. Hào quang / Phụ kiện nền & Trang bị lưng
        self._draw_accessory(screen, cx, ry, body_bottom_y, foot_y)
        self._draw_back_equipment(screen, cx, ry, body_bottom_y, dir_sign)

        # 1. Đầu (Head)
        pygame.draw.circle(screen, self.body_color, (int(cx), int(head_y)), 8, 2)

        # 2. Thân / Costume (Body)
        self._draw_body_costume(screen, cx, head_y, body_bottom_y, dir_sign)

        # 3. Chân (Legs)
        if self.state == "RUN":
            leg_swing = math.sin(self.anim_frame * 0.25) * 10
            pygame.draw.line(screen, self.body_color, (cx, body_bottom_y), (cx - leg_swing, ry + 48), 2)
            pygame.draw.line(screen, self.body_color, (cx, body_bottom_y), (cx + leg_swing, ry + 48), 2)
        elif self.state == "JUMP":
            pygame.draw.line(screen, self.body_color, (cx, body_bottom_y), (cx - 10, ry + 42), 2)
            pygame.draw.line(screen, self.body_color, (cx, body_bottom_y), (cx + 10, ry + 42), 2)
        else:  # IDLE, SLASH, SHOOT (chân hơi dạng ra khi vừa tiếp đất)
            stance = 7 + squash * 1.1
            pygame.draw.line(screen, self.body_color, (cx, body_bottom_y), (cx - stance, foot_y), 2)
            pygame.draw.line(screen, self.body_color, (cx, body_bottom_y), (cx + stance, foot_y), 2)

        # 4. Tay & Vũ khí
        arm_y = ry + 18

        if self.state == "SLASH":
            sword_x = cx + (30 * dir_sign)
            pygame.draw.line(screen, CYBER_PINK, (cx, arm_y), (sword_x, arm_y - 12), 3)
            arc_rect = (cx, arm_y - 25, 30, 30) if self.facing_right else (cx - 30, arm_y - 25, 30, 30)
            pygame.draw.arc(screen, CYBER_PINK, arc_rect, 0, math.pi, 2)

        elif self.state == "SHOOT":
            hand_x = cx + (14 * dir_sign)
            pygame.draw.line(screen, self.body_color, (cx, arm_y), (hand_x, arm_y), 2)
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

        # 5. Mũ / Phụ kiện đầu
        self._draw_head_visual(screen, cx, head_y)

    def draw_preview(self, screen, cx, bottom_y, scale=2.2, tick=0):
        """Vẽ bản phóng to nhân vật (dùng cho Landing Screen và Shop Cosmetics)."""
        canvas_w, canvas_h = 120, 100
        surf = pygame.Surface((canvas_w, canvas_h), pygame.SRCALPHA)

        saved_rect = self.rect.copy()
        saved_state = self.state
        saved_facing = self.facing_right
        saved_frame = self.anim_frame
        saved_inv = self.invincible_timer
        saved_land = self.landing_timer

        self.rect.midbottom = (canvas_w // 2, canvas_h - 14)
        self.state = "IDLE"
        self.facing_right = True
        self.anim_frame = tick
        self.invincible_timer = 0
        self.landing_timer = 0

        self.draw(surf, camera_x=0)

        self.rect = saved_rect
        self.state = saved_state
        self.facing_right = saved_facing
        self.anim_frame = saved_frame
        self.invincible_timer = saved_inv
        self.landing_timer = saved_land

        scaled = pygame.transform.smoothscale(surf, (int(canvas_w * scale), int(canvas_h * scale)))
        screen.blit(scaled, (int(cx - scaled.get_width() // 2), int(bottom_y - scaled.get_height() + 14 * scale)))
