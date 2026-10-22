import pygame
import math

from settings import (
    PLAYER_SPEED,
    PLAYER_RADIUS
)


class Player:

    def __init__(self):

        # =====================================================
        # VỊ TRÍ
        # =====================================================

        self.x = 880
        self.y = 1050

        # Góc nhìn trái / phải (hướng chếch về hành lang lối đi chính)
        self.angle = -math.pi * 0.58

        # Góc nhìn lên / xuống
        self.pitch = 0.0

        # Giới hạn nhìn lên / xuống
        self.max_pitch = math.radians(75)

        # =====================================================
        # THÔNG SỐ DI CHUYỂN
        # =====================================================

        self.radius = PLAYER_RADIUS
        self.speed = PLAYER_SPEED

        # =====================================================
        # MÁU / GIÁP
        # =====================================================

        self.hp = 100
        self.armor = 50

        # =====================================================
        # HƯỚNG TAY CẦM SÚNG (CS:GO cl_righthand)
        # =====================================================
        self.righthand = True  # True = Tay phải (cl_righthand 1), False = Tay trái (cl_righthand 0)
        self.knife_swing = 0.0
        self.knife_is_stab = False

        # =====================================================
        # VŨ KHÍ
        # =====================================================

        self.weapon = "VANDAL"

        # =====================================================
        # ĐẠN
        # =====================================================

        self.magazine = 25
        self.max_magazine = 25
        self.reserve = 75

        self.fire_delay = 0.095
        self.last_shot = 0

        # =====================================================
        # RELOAD
        # =====================================================

        self.reloading = False
        self.reload_time = 1.8
        self.reload_start = 0

        # =====================================================
        # RECOIL
        # =====================================================

        self.recoil = 0

        # =====================================================
        # TIỀN
        # =====================================================

        self.money = 800

        # =====================================================
        # TRẠNG THÁI
        # =====================================================

        self.alive = True

        # =====================================================
        # NGỒI
        # =====================================================

        self.crouching = False

        # =====================================================
        # NHẢY
        # =====================================================

        self.is_jumping = False

        # Vận tốc theo chiều dọc
        self.vertical_velocity = 0.0

        # Độ cao hiện tại khi nhảy
        self.vertical_offset = 0.0

        # Sức bật
        self.jump_strength = 420.0

        # Trọng lực
        self.gravity = 1000.0

    # =====================================================
    # RECTANGLE VA CHẠM
    # =====================================================

    def rect(self):

        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2
        )

    # =====================================================
    # DI CHUYỂN
    # =====================================================

    def move(self, dx, dy, walls):

        # -----------------------------------------------------
        # DI CHUYỂN TRỤC X
        # -----------------------------------------------------

        test_x = pygame.Rect(
            int(self.x + dx - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2
        )

        blocked_x = any(
            test_x.colliderect(wall)
            for wall in walls
        )

        if not blocked_x:
            self.x += dx

        # -----------------------------------------------------
        # DI CHUYỂN TRỤC Y
        # -----------------------------------------------------

        test_y = pygame.Rect(
            int(self.x - self.radius),
            int(self.y + dy - self.radius),
            self.radius * 2,
            self.radius * 2
        )

        blocked_y = any(
            test_y.colliderect(wall)
            for wall in walls
        )

        if not blocked_y:
            self.y += dy

    # =====================================================
    # NHẬN SÁT THƯƠNG
    # =====================================================

    def damage(self, amount):

        # -----------------------------------------------------
        # GIÁP HẤP THỤ 50% SÁT THƯƠNG
        # -----------------------------------------------------

        if self.armor > 0:

            absorbed = min(
                self.armor,
                amount * 0.5
            )

            self.armor -= absorbed
            amount -= absorbed

        # -----------------------------------------------------
        # TRỪ MÁU
        # -----------------------------------------------------

        self.hp -= amount

        # -----------------------------------------------------
        # CHẾT
        # -----------------------------------------------------

        if self.hp <= 0:

            self.hp = 0
            self.alive = False

    # =====================================================
    # XOAY CAMERA
    # =====================================================

    def look(
        self,
        mouse_dx,
        mouse_dy,
        sensitivity=0.0025
    ):

        # =====================================================
        # XOAY TRÁI / PHẢI
        # =====================================================

        self.angle += (
            mouse_dx * sensitivity
        )

        # Giữ angle trong khoảng 0 -> 2π
        self.angle %= math.tau

        # =====================================================
        # NHÌN LÊN / XUỐNG
        # =====================================================

        self.pitch -= (
            mouse_dy * sensitivity
        )

        # =====================================================
        # GIỚI HẠN CAMERA
        # =====================================================

        self.pitch = max(
            -self.max_pitch,
            min(
                self.max_pitch,
                self.pitch
            )
        )

    # =====================================================
    # BẮT ĐẦU NHẢY
    # =====================================================

    def jump(self):

        # Không thể nhảy khi đang ở trên không
        if self.is_jumping:
            return

        self.is_jumping = True

        self.vertical_velocity = (
            self.jump_strength
        )

    # =====================================================
    # CẬP NHẬT NHẢY
    # =====================================================

    def update_vertical(self, dt):

        # Không nhảy
        if not self.is_jumping:
            return

        # -----------------------------------------------------
        # CẬP NHẬT VẬN TỐC
        # -----------------------------------------------------

        self.vertical_velocity -= (
            self.gravity * dt
        )

        # -----------------------------------------------------
        # CẬP NHẬT ĐỘ CAO
        # -----------------------------------------------------

        self.vertical_offset += (
            self.vertical_velocity * dt
        )

        # -----------------------------------------------------
        # CHẠM MẶT ĐẤT
        # -----------------------------------------------------

        if self.vertical_offset <= 0:

            self.vertical_offset = 0

            self.vertical_velocity = 0

            self.is_jumping = False

    # =====================================================
    # RESET PLAYER
    # =====================================================

    def reset(self):

        self.x = 880
        self.y = 1050

        self.angle = -math.pi * 0.58

        self.pitch = 0.0

        self.hp = 100
        self.armor = 50

        self.magazine = self.max_magazine
        self.reserve = 75

        self.reloading = False
        self.reload_start = 0

        self.recoil = 0

        self.alive = True

        self.crouching = False

        self.is_jumping = False
        self.vertical_velocity = 0.0
        self.vertical_offset = 0.0
        self.righthand = getattr(self, "righthand", True)
        self.knife_swing = 0.0
        self.knife_is_stab = False

