import math
import pygame
from graphics.weapon_skins import get_viewmodel_skin


class GameWeaponView:
    """
    Vẽ vũ khí góc nhìn thứ nhất.
    Mặc định đầu nòng hướng chéo lên-trái, về vùng ngắm ở giữa màn hình.
    MUZZLE_OFFSET_X/Y có thể chỉnh theo ảnh skin thực tế.
    """

    THROWABLES = {"KNIFE", "SMOKE", "MOLOTOV", "BOMB"}

    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height
        self.font_small = pygame.font.SysFont("Arial", 22)

        # Điểm xuất phát tia đạn mặc định. Có thể chỉnh để khớp đầu nòng skin.
        self.muzzle_x = width // 2 + 80
        self.muzzle_y = height - 145

        # Offset đầu nòng tương đối với góc trên-trái của ảnh skin.
        # Nếu tia đạn lệch khỏi đầu nòng, chỉnh hai giá trị này.
        self.MUZZLE_OFFSET_X = 0
        self.MUZZLE_OFFSET_Y = 0

    def draw(self, player, bomb_fuse=None):
        now_sec = pygame.time.get_ticks() / 1000.0
        reload_drop = 0
        side_sway = 0
        reload_progress = 0.0

        if getattr(player, "reloading", False):
            elapsed = now_sec - getattr(player, "reload_start", 0)
            reload_time = max(0.1, getattr(player, "reload_time", 1.8))
            reload_progress = min(1.0, elapsed / reload_time)
            reload_drop = int(math.sin(reload_progress * math.pi) * 110)
            side_sway = int(math.sin(reload_progress * math.pi * 2) * 18)

        cur_w = getattr(player, "weapon", "")
        recoil = max(0.0, float(getattr(player, "recoil", 0.0)))

        if cur_w not in self.THROWABLES:
            vm_skin = get_viewmodel_skin(cur_w)

            if vm_skin is not None:
                vw, vh = vm_skin.get_size()
                recoil_x = int(recoil * 35)
                recoil_y = int(recoil * 25)

                gun_pos_x = self.width - vw + 20 + side_sway + recoil_x
                gun_pos_y = self.height - vh + 15 + reload_drop - recoil_y
                self.screen.blit(vm_skin, (gun_pos_x, gun_pos_y))

                # Ước lượng đầu nòng ở mép trên-trái của skin.
                # Nếu skin có đầu nòng ở vị trí khác, chỉnh MUZZLE_OFFSET_X/Y.
                self.muzzle_x = int(gun_pos_x + self.MUZZLE_OFFSET_X)
                self.muzzle_y = int(gun_pos_y + self.MUZZLE_OFFSET_Y)
            else:
                self._draw_fallback_gun(reload_drop, side_sway, recoil)

            if (
                vm_skin is None
                and getattr(player, "reloading", False)
                and 0.25 <= reload_progress <= 0.75
            ):
                gun_x = self.width // 2 + 80 + side_sway
                wy = self.height - 145 + reload_drop
                mag_y = wy + 40 + int(
                    math.sin((reload_progress - 0.25) / 0.5 * math.pi) * 25
                )
                pygame.draw.rect(
                    self.screen, (75, 80, 90),
                    (gun_x + 20, mag_y, 28, 55), border_radius=3
                )
                pygame.draw.rect(
                    self.screen, (240, 190, 60),
                    (gun_x + 24, mag_y + 8, 20, 6)
                )

        elif cur_w == "KNIFE":
            self._draw_knife(reload_drop, side_sway)
        elif cur_w == "SMOKE":
            self._draw_smoke()
        elif cur_w == "MOLOTOV":
            self._draw_molotov()
        elif cur_w == "BOMB":
            self._draw_bomb(bomb_fuse)

    def _draw_fallback_gun(self, reload_drop, side_sway, recoil):
        """Vẽ súng đơn giản với nòng hướng từ góc phải-dưới về giữa màn hình."""
        # Trục nòng: đầu nòng nằm cao và lệch trái; báng nằm thấp và lệch phải.
        muzzle_x = int(self.width * 0.61 + side_sway - recoil * 10)
        muzzle_y = int(self.height * 0.67 + reload_drop - recoil * 20)
        grip_x = int(self.width * 0.83 + side_sway)
        grip_y = int(self.height * 0.98 + reload_drop)

        # Nòng súng hướng về phía trước / tâm màn hình.
        pygame.draw.polygon(self.screen, (25, 28, 34), [
            (muzzle_x - 9, muzzle_y + 5),
            (muzzle_x + 10, muzzle_y - 5),
            (grip_x + 35, grip_y - 30),
            (grip_x + 10, grip_y - 5),
        ])
        pygame.draw.polygon(self.screen, (65, 70, 78), [
            (muzzle_x - 5, muzzle_y + 2),
            (muzzle_x + 6, muzzle_y - 4),
            (grip_x + 17, grip_y - 29),
            (grip_x + 2, grip_y - 15),
        ])

        # Đầu nòng rõ ràng để dễ căn chỉnh điểm bắn.
        pygame.draw.circle(self.screen, (12, 14, 18), (muzzle_x, muzzle_y), 7)
        pygame.draw.circle(self.screen, (100, 105, 112), (muzzle_x, muzzle_y), 4, 2)

        # Thân và báng súng ở góc phải phía dưới.
        pygame.draw.polygon(self.screen, (42, 45, 52), [
            (grip_x - 18, grip_y - 65),
            (grip_x + 25, grip_y - 55),
            (self.width + 15, self.height + 10),
            (grip_x - 30, self.height + 10),
        ])
        pygame.draw.polygon(self.screen, (70, 74, 82), [
            (grip_x - 5, grip_y - 60),
            (grip_x + 14, grip_y - 55),
            (grip_x + 5, grip_y - 8),
            (grip_x - 15, grip_y - 12),
        ])

        self.muzzle_x = muzzle_x
        self.muzzle_y = muzzle_y

    def _draw_knife(self, reload_drop, side_sway):
        x = self.width // 2 + 125 + side_sway
        y = self.height - 115 + reload_drop
        pygame.draw.polygon(self.screen, (185, 195, 205), [
            (x, y + 45), (x + 68, y - 55), (x + 42, y + 58)
        ])
        pygame.draw.polygon(self.screen, (70, 75, 85), [
            (x - 10, y + 45), (x + 12, y + 40),
            (x + 5, y + 95), (x - 15, y + 90)
        ])

    def _draw_smoke(self):
        gx, gy = self.width // 2 + 120, self.height - 130
        pygame.draw.rect(self.screen, (75, 80, 90), (gx, gy, 46, 75), border_radius=6)
        pygame.draw.rect(self.screen, (240, 210, 50), (gx, gy + 20, 46, 12))
        pygame.draw.rect(self.screen, (50, 55, 62), (gx + 14, gy - 16, 18, 18), border_radius=3)
        pygame.draw.circle(self.screen, (200, 200, 210), (gx + 10, gy - 8), 7, 2)
        self.screen.blit(
            self.font_small.render("SMOKE", True, (240, 240, 245)),
            (gx - 5, gy + 36)
        )

    def _draw_molotov(self):
        gx, gy = self.width // 2 + 120, self.height - 140
        pygame.draw.rect(self.screen, (40, 110, 70), (gx + 6, gy + 25, 42, 70), border_radius=8)
        pygame.draw.rect(self.screen, (40, 110, 70), (gx + 20, gy, 14, 28))
        pygame.draw.rect(self.screen, (200, 190, 170), (gx + 18, gy - 8, 18, 12))
        flame_size = int(12 + 5 * math.sin(pygame.time.get_ticks() * 0.02))
        pygame.draw.circle(self.screen, (255, 120, 20), (gx + 27, gy - 16), flame_size)
        pygame.draw.circle(
            self.screen, (255, 230, 40),
            (gx + 27, gy - 16), max(2, flame_size // 2)
        )
        self.screen.blit(
            self.font_small.render("MOLOTOV", True, (255, 200, 60)),
            (gx - 12, gy + 45)
        )

    def _draw_bomb(self, bomb_fuse):
        gx, gy = self.width // 2 + 130, self.height - 110
        pygame.draw.circle(self.screen, (32, 35, 42), (gx + 20, gy + 20), 40)
        pygame.draw.circle(self.screen, (60, 65, 75), (gx + 12, gy + 12), 12)
        pygame.draw.rect(self.screen, (10, 12, 16), (gx - 2, gy + 8, 44, 22), border_radius=4)

        fuse_text = (
            f"{max(0.0, bomb_fuse):.1f}s"
            if bomb_fuse is not None and bomb_fuse > 0
            else "5.0s"
        )
        color = (
            (255, 40, 40)
            if (pygame.time.get_ticks() // 200) % 2 == 0
            else (255, 180, 40)
        )
        label = self.font_small.render(fuse_text, True, color)
        self.screen.blit(label, (gx + 20 - label.get_width() // 2, gy + 11))
