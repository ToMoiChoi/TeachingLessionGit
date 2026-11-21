"""Các thực thể trong trận đấu: Hạt hiệu ứng, Tia sét Hắc Thiểm, Đạn Thuật Thức, Thức Thần và Đấu Sĩ."""

import math
import random
import pygame
from config import GROUND_Y, ARENA_LEFT, ARENA_RIGHT, clamp


# ============================================================
# PARTICLE (HẠT CHÚ LỰC / MÁU / TIA LỬA)
# ============================================================

class Particle:
    def __init__(self, x, y, color, vx=None, vy=None, gravity=520, life=None, size=None, shape="circle"):
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-210, 210) if vx is None else float(vx)
        self.vy = random.uniform(-250, -35) if vy is None else float(vy)
        self.gravity = gravity
        self.max_life = random.uniform(0.25, 0.62) if life is None else float(life)
        self.life = self.max_life
        self.color = color
        self.size = random.randint(3, 7) if size is None else int(size)
        self.shape = shape

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt

    def draw(self, surface):
        if self.life <= 0:
            return
        ratio = clamp(self.life / max(0.01, self.max_life), 0.15, 1.0)
        r = max(1, int(self.size * ratio))
        ix, iy = int(self.x), int(self.y)
        if self.shape == "slash":
            dx = int(self.vx * 0.04)
            dy = int(self.vy * 0.04)
            pygame.draw.line(surface, self.color, (ix - dx, iy - dy), (ix + dx, iy + dy), max(2, r // 2))
        elif self.shape == "square":
            pygame.draw.rect(surface, self.color, (ix - r, iy - r, r * 2, r * 2))
        else:
            pygame.draw.circle(surface, self.color, (ix, iy), r)


# ============================================================
# LIGHTNING BOLT (TIA SÉT ĐEN-ĐỎ HẮC THIỂM & LÔI ĐIỆN)
# ============================================================

class LightningBolt:
    def __init__(self, x1, y1, x2, y2, outer_color=(235, 25, 55), inner_color=(10, 10, 15), life=0.32, width=6):
        self.outer_color = outer_color
        self.inner_color = inner_color
        self.max_life = life
        self.life = life
        self.width = width
        self.points = self._build_points(x1, y1, x2, y2)

    @staticmethod
    def _build_points(x1, y1, x2, y2, segments=7):
        pts = [(x1, y1)]
        dx = (x2 - x1) / segments
        dy = (y2 - y1) / segments
        length = math.hypot(x2 - x1, y2 - y1)
        jitter = max(10.0, min(36.0, length * 0.16))
        for i in range(1, segments):
            px = x1 + dx * i + random.uniform(-jitter, jitter)
            py = y1 + dy * i + random.uniform(-jitter, jitter)
            pts.append((int(px), int(py)))
        pts.append((int(x2), int(y2)))
        return pts

    def update(self, dt):
        self.life -= dt

    def draw(self, surface):
        if self.life <= 0 or len(self.points) < 2:
            return
        w_out = max(2, int(self.width * (self.life / self.max_life) + 2))
        w_in = max(1, w_out // 2)
        pygame.draw.lines(surface, self.outer_color, False, self.points, w_out)
        pygame.draw.lines(surface, self.inner_color, False, self.points, w_in)


# ============================================================
# PROJECTILE (ĐẠN THUẬT THỨC / SÓNG ÂM / CẦU KHÔNG GIAN / TRẢM KÍCH)
# ============================================================

class Projectile:
    def __init__(
        self,
        owner,
        kind,
        x,
        y,
        vx,
        vy=0.0,
        damage=80,
        radius=24,
        life=1.4,
        color=(168, 85, 247),
        pierce=False,
        stun=0.0,
        slow=0.0,
        pull=0.0,
        knockback=0.0,
        nail_add=0,
        multi_hit=False,
    ):
        self.owner = owner
        self.kind = kind
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.damage = float(damage)
        self.radius = float(radius)
        self.max_life = float(life)
        self.life = float(life)
        self.color = color
        self.pierce = pierce
        self.stun = stun
        self.slow = slow
        self.pull = pull
        self.knockback = knockback
        self.nail_add = nail_add
        self.multi_hit = multi_hit
        self.hit_targets = set()
        self.tick_timer = 0.0
        self.phase = random.uniform(0, 6.28)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt
        self.phase += dt * 10.0
        if self.multi_hit:
            self.tick_timer = max(0.0, self.tick_timer - dt)


# ============================================================
# SHIKIGAMI (THỨC THẦN TRIỆU HỒI HỖ TRỢ CHIẾN ĐẤU)
# ============================================================

class Shikigami:
    def __init__(self, owner, kind, x, y, facing, damage=95, life=1.35, color=(120, 160, 255)):
        self.owner = owner
        self.kind = kind
        self.x = float(x)
        self.y = float(y)
        self.facing = facing
        self.damage = float(damage)
        self.max_life = float(life)
        self.life = float(life)
        self.color = color
        self.has_hit = False
        self.tick_timer = 0.0
        self.phase = 0.0

    def update(self, dt, target):
        self.life -= dt
        self.phase += dt * 9.0
        self.tick_timer = max(0.0, self.tick_timer - dt)

        if self.kind == "divine_dog":
            self.x += self.facing * 520 * dt
        elif self.kind == "nue":
            self.x += self.facing * 430 * dt
            self.y = GROUND_Y - 125 + math.sin(self.phase * 1.4) * 14
        elif self.kind == "rika":
            # Lao nhanh tới mục tiêu để tung cú đấm chú lực
            if target and target.alive:
                dir_x = 1 if target.x >= self.x else -1
                self.facing = dir_x
                if abs(target.x - self.x) > 55:
                    self.x += dir_x * 460 * dt
        elif self.kind == "mahoraga":
            # Đứng sừng sững ngay phía trước chủ nhân và giáng đòn chấn địa
            pass
        elif self.kind == "orochi":
            # Trồi thẳng từ bóng tối dưới chân mục tiêu
            pass
        elif self.kind == "garuda":
            self.x += self.facing * 490 * dt


# ============================================================
# FIGHTER (ĐẤU SĨ CHÚ THUẬT SƯ & CHÚ LINH BOSS)
# ============================================================

class Fighter:
    def __init__(self, char_id, name, color, max_hp, speed=280, max_ce=120, technique="", domain_name=""):
        self.char_id = char_id
        self.name = name
        self.technique = technique
        self.domain_name = domain_name
        self.color = color
        self.secondary = (185, 70, 255)

        self.max_hp = float(max_hp)
        self.hp = float(max_hp)
        self.max_ce = float(max_ce)
        self.ce = float(max_ce)
        self.domain_gauge = 50.0  # Bắt đầu ở 50% để người chơi tích nhanh mở Lãnh Địa

        self.x = 280.0
        self.y = float(GROUND_Y)
        self.vy = 0.0
        self.gravity = 1350.0
        self.jump_force = -510.0
        self.jump_count = 0
        self.max_jumps = 2
        self.is_crouching = False

        self.width = 54
        self.height = 112
        self.facing = 1
        self.speed = float(speed)

        # Thời gian hồi chiêu
        self.light_cd = 0.0
        self.skill1_cd = 0.0
        self.skill2_cd = 0.0
        self.shiki_cd = 0.0
        self.simple_cd = 0.0

        # Trạng thái chiến đấu & cơ chế Chú Thuật Hồi Chiến
        self.attack_timer = 0.0
        self.attack_type = None
        self.parry_timer = 0.0
        self.simple_domain_timer = 0.0  # Giản Dị Lãnh Địa
        self.dodge_timer = 0.0
        self.stun_timer = 0.0
        self.slow_timer = 0.0
        self.hit_flash = 0.0

        # Buff đặc biệt
        self.zone_timer = 0.0          # Hắc Thiểm Zone (120% tiềm năng)
        self.overtime_timer = 0.0      # Nanami Tăng Ca
        self.red_scale_timer = 0.0     # Kamo Xích Lân Dược Động
        self.shield_hp = 0.0           # Khiên chú lực Rika / Thức Thần

        # Dấu ấn kỹ năng giữa các nhân vật
        self.nail_stacks = 0           # Số đinh Sô Linh Chú Pháp của Nobara đang găm trên người
        self.gojo_red_next = False     # Đảo Thuận Chuyển Xanh <-> Nghịch Chuyển Đỏ
        self.blue_combo_timer = 0.0    # Cộng hưởng Xanh + Đỏ -> Cường hóa Hư Thức Tím
        self.copy_index = 0            # Yuta xoay vòng thuật thức Sao Chép

        # Nghịch Chuyển Thuật Thức (RCT)
        self.max_rct_uses = 4
        self.rct_uses = 4
        self.rct_timer = 0.0
        self.rct_heal_left = 0.0

        self.alive = True
        self.last_action = "Sẵn sàng"

    @property
    def stamina(self):
        return self.ce

    @property
    def max_stamina(self):
        return self.max_ce

    def reset(self, x, facing=1):
        self.hp = self.max_hp
        self.ce = self.max_ce
        self.domain_gauge = 50.0
        self.x = float(x)
        self.y = float(GROUND_Y)
        self.vy = 0.0
        self.jump_count = 0
        self.is_crouching = False
        self.facing = facing

        self.light_cd = 0.0
        self.skill1_cd = 0.0
        self.skill2_cd = 0.0
        self.shiki_cd = 0.0
        self.simple_cd = 0.0

        self.attack_timer = 0.0
        self.attack_type = None
        self.parry_timer = 0.0
        self.simple_domain_timer = 0.0
        self.dodge_timer = 0.0
        self.stun_timer = 0.0
        self.slow_timer = 0.0
        self.hit_flash = 0.0

        self.zone_timer = 0.0
        self.overtime_timer = 0.0
        self.red_scale_timer = 0.0
        self.shield_hp = 0.0

        self.nail_stacks = 0
        self.gojo_red_next = False
        self.blue_combo_timer = 0.0

        self.rct_uses = self.max_rct_uses
        self.rct_timer = 0.0
        self.rct_heal_left = 0.0

        self.alive = True
        self.last_action = "Sẵn sàng"

    def update(self, dt, ce_regen_mult=1.0):
        self.light_cd = max(0.0, self.light_cd - dt)
        self.skill1_cd = max(0.0, self.skill1_cd - dt)
        self.skill2_cd = max(0.0, self.skill2_cd - dt)
        self.shiki_cd = max(0.0, self.shiki_cd - dt)
        self.simple_cd = max(0.0, self.simple_cd - dt)

        self.attack_timer = max(0.0, self.attack_timer - dt)
        self.parry_timer = max(0.0, self.parry_timer - dt)
        self.simple_domain_timer = max(0.0, self.simple_domain_timer - dt)
        self.dodge_timer = max(0.0, self.dodge_timer - dt)
        self.stun_timer = max(0.0, self.stun_timer - dt)
        self.slow_timer = max(0.0, self.slow_timer - dt)
        self.hit_flash = max(0.0, self.hit_flash - dt)

        self.zone_timer = max(0.0, self.zone_timer - dt)
        self.overtime_timer = max(0.0, self.overtime_timer - dt)
        self.red_scale_timer = max(0.0, self.red_scale_timer - dt)
        self.blue_combo_timer = max(0.0, self.blue_combo_timer - dt)

        # Hồi phục Chú Lực tự nhiên (nhanh hơn khi vào Zone Hắc Thiểm hoặc Yuta)
        base_regen = 22.0 if self.char_id == "yuta" else 17.5
        if self.zone_timer > 0:
            base_regen *= 1.35
        self.ce = min(self.max_ce, self.ce + dt * base_regen * ce_regen_mult)

        # Hồi máu từ Nghịch Chuyển Thuật Thức (RCT)
        if self.rct_heal_left > 0 and self.rct_timer > 0:
            step = min(self.rct_heal_left, (280.0 / 1.8) * dt)
            self.hp = min(self.max_hp, self.hp + step)
            self.rct_heal_left -= step
            self.rct_timer -= dt

        # Vật lý trọng lực nhảy
        if self.y < GROUND_Y or self.vy != 0:
            self.vy += self.gravity * dt
            self.y += self.vy * dt
            if self.y >= GROUND_Y:
                self.y = float(GROUND_Y)
                self.vy = 0.0
                self.jump_count = 0

        self.x = clamp(self.x, ARENA_LEFT, ARENA_RIGHT)

    def rect(self):
        h = int(self.height * 0.65) if self.is_crouching else self.height
        return pygame.Rect(int(self.x - self.width // 2), int(self.y - h), self.width, h)

    def center_y(self):
        h = self.height * 0.65 if self.is_crouching else self.height
        return self.y - h * 0.5
