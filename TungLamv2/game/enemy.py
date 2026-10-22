import pygame
import math
import random


class Enemy:

    def __init__(self, x, y, armor=25):

        # =========================
        # POSITION & HITBOX
        # =========================

        self.x = x
        self.y = y

        # Bán kính va chạm di chuyển trên bản đồ 2D
        self.radius = 17

        # =========================
        # TỈ LỆ CƠ THỂ 3D (ĐẦU - THÂN - CHÂN)
        # =========================
        # Tổng chiều cao mô phỏng trong không gian: 70 đơn vị
        # - Đầu: 22% chiều cao phía trên
        # - Thân: 43% chiều cao ở giữa
        # - Chân: 35% chiều cao phía dưới
        self.head_ratio = 0.22
        self.body_ratio = 0.43
        self.leg_ratio = 0.35

        # Hitbox 2D (phụ trợ)
        self.head_radius = 13
        self.head_offset_y = -32

        self.body_width = 30
        self.body_height = 55
        self.body_offset_y = 10

        self.leg_width = 26
        self.leg_height = 25
        self.leg_offset_y = 48

        # =========================
        # HP / ARMOR
        # =========================

        self.hp = 100
        self.armor = armor

        # =========================
        # MOVEMENT
        # =========================

        self.speed = 95
        self.angle = 0

        # =========================
        # SHOOTING
        # =========================

        self.last_shot = 0
        self.fire_delay = random.uniform(0.45, 0.75)
        self.alive = True

        # Trạng thái trúng đòn gần nhất (dùng cho hiệu ứng hiển thị)
        self.last_hit_part = None
        self.last_hit_damage = 0
        self.last_hit_time = 0

    # =========================================================
    # XÁC ĐỊNH BỘ PHẬN TRÚNG ĐẠN TRÊN MÀN HÌNH 3D
    # =========================================================

    def check_hit_3d(self, sx, btop, bw, bh, screen_x, screen_y):
        """
        Kiểm tra điểm bắn (screen_x, screen_y) có trúng vào kẻ địch không.
        Nếu trúng, trả về tên bộ phận ('head', 'body', 'legs').
        Nếu không trúng, trả về None.
        """
        # Kiểm tra theo trục ngang X (cho phép dung sai một chút để ngắm mượt hơn)
        half_w = bw * 0.55
        if abs(screen_x - sx) > half_w:
            return None

        # Chiều dọc Y:
        # Đầu: [btop, btop + bh * 0.22]
        # Thân: [btop + bh * 0.22, btop + bh * 0.65]
        # Chân: [btop + bh * 0.65, btop + bh]
        head_end_y = btop + bh * self.head_ratio
        body_end_y = btop + bh * (self.head_ratio + self.body_ratio)
        leg_end_y = btop + bh

        # Đỉnh đầu có thể nhô cao hơn một chút do hình cầu/mũ
        if btop - (bh * 0.05) <= screen_y < head_end_y:
            return "head"
        elif head_end_y <= screen_y < body_end_y:
            return "body"
        elif body_end_y <= screen_y <= leg_end_y + (bh * 0.05):
            return "legs"

        return None

    # =========================================================
    # DAMAGE
    # =========================================================

    def damage(self, amount, part="body"):
        """
        Nhận sát thương dựa trên vị trí bắn trúng.
        Giáp hấp thụ 50% sát thương, phần còn lại trừ vào máu.
        """
        self.last_hit_part = part
        self.last_hit_damage = amount
        self.last_hit_time = pygame.time.get_ticks()

        actual_damage = amount
        if self.armor > 0:
            absorbed = min(self.armor, actual_damage * 0.5)
            self.armor -= absorbed
            actual_damage -= absorbed

        self.hp -= actual_damage

        if self.hp <= 0:
            self.hp = 0
            self.alive = False

        return actual_damage

    # =========================================================
    # HITBOX 2D (DỰ PHÒNG)
    # =========================================================

    def get_hitboxes(self):
        head = {
            "type": "head",
            "x": self.x,
            "y": self.y + self.head_offset_y,
            "radius": self.head_radius
        }

        body = pygame.Rect(
            int(self.x - self.body_width / 2),
            int(self.y + self.body_offset_y - self.body_height / 2),
            self.body_width,
            self.body_height
        )

        legs = pygame.Rect(
            int(self.x - self.leg_width / 2),
            int(self.y + self.leg_offset_y - self.leg_height / 2),
            self.leg_width,
            self.leg_height
        )

        return {"head": head, "body": body, "legs": legs}

    def check_hit(self, hit_x, hit_y):
        hitboxes = self.get_hitboxes()
        head = hitboxes["head"]
        dist = math.hypot(hit_x - head["x"], hit_y - head["y"])
        if dist <= head["radius"]:
            return "head"
        if hitboxes["body"].collidepoint(int(hit_x), int(hit_y)):
            return "body"
        if hitboxes["legs"].collidepoint(int(hit_x), int(hit_y)):
            return "legs"
        return None

    # =========================================================
    # MOVEMENT & COLLISION
    # =========================================================

    def move(self, dx, dy, walls):
        # Trục X
        test_x = pygame.Rect(
            int(self.x + dx - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2
        )
        if not any(test_x.colliderect(w) for w in walls):
            self.x += dx

        # Trục Y
        test_y = pygame.Rect(
            int(self.x - self.radius),
            int(self.y + dy - self.radius),
            self.radius * 2,
            self.radius * 2
        )
        if not any(test_y.colliderect(w) for w in walls):
            self.y += dy