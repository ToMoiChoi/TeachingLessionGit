import math
import pygame

from graphics import gun3d

# ==============================================================================
# HỆ THỐNG VIEWMODEL GÓC NHÌN THỨ NHẤT CHUẨN CS:GO / CS2
# ==============================================================================

class CSViewModel:
    """
    Quản lý góc nhìn thứ nhất (FPS Viewmodel) chuẩn xác 100% như CS:GO:
    - Góc nhìn dọc theo sống lưng súng về phía đầu ruồi và tâm ngắm
    - Bàn tay đeo găng đặc nhiệm CT ôm báng súng và đỡ nòng súng chuyên nghiệp
    - Đổi tay cầm (Trái / Phải - cl_righthand 1 / 0)
    - Neo góc dưới (bottomright / bottomleft) không che HUD hay tầm nhìn
    - Giảm rung lắc khi di chuyển (cl_bobamt_lat 0.1, cl_bobamt_vert 0.1)
    - Giật lùi và nảy lên khi bắn (Recoil Kickback) chân thực
    - Hoạt ảnh chém (slash) và đâm mạnh (stab) của dao
    - Đầu nòng đạn (muzzle_pos) trùng khớp 100% với nòng súng thực tế
    """

    PISTOLS = {"CLASSIC", "GHOST", "SHERIFF"}
    MELEE = {"KNIFE"}

    def __init__(self, screen_w=1600, screen_h=900):
        self.sw = screen_w
        self.sh = screen_h

        # Vị trí đầu nòng bắn đạn mặc định
        self.muzzle_pos = (self.sw * 0.58, self.sh * 0.52)

        # Trạng thái di chuyển, quán tính và bobbing
        self.bob_t = 0.0
        self.bob_x = 0.0
        self.bob_y = 0.0
        self.last_pos = (0.0, 0.0)
        self.sway_x = 0.0
        self.last_angle = 0.0
        self.last_time = 0.0


    def update(self, dt, player):
        now = pygame.time.get_ticks() / 1000.0
        frame_dt = min(0.08, max(0.0, now - self.last_time)) if self.last_time else 0.016
        self.last_time = now

        # Quán tính chuột nhẹ (Mouse sway)
        dang = (player.angle - self.last_angle + math.pi) % (2 * math.pi) - math.pi
        self.last_angle = player.angle
        target_sway = max(-8.0, min(8.0, -dang * 75.0))
        self.sway_x += (target_sway - self.sway_x) * min(1.0, frame_dt * 12.0)

        # Bobbing di chuyển chuẩn CS:GO (cl_bobamt_lat 0.1, cl_bobamt_vert 0.1)
        dist_moved = math.hypot(player.x - self.last_pos[0], player.y - self.last_pos[1])
        self.last_pos = (player.x, player.y)
        is_moving = frame_dt > 0 and (dist_moved / frame_dt) > 20.0

        if is_moving:
            self.bob_t += frame_dt * 8.0
            self.bob_x = math.sin(self.bob_t) * 2.2
            self.bob_y = abs(math.cos(self.bob_t)) * 1.8
        else:
            self.bob_t += frame_dt * 1.5
            self.bob_x = math.sin(self.bob_t) * 0.5
            self.bob_y = abs(math.cos(self.bob_t)) * 0.6

    def draw(self, screen, player, reload_drop=0, side_sway=0):
        cur_w = getattr(player, "weapon", "CLASSIC")
        righthand = getattr(player, "righthand", True)
        recoil = max(0.0, float(getattr(player, "recoil", 0.0)))

        # Ẩn viewmodel khi đang ngắm Scope
        if getattr(player, "scoped", False) and cur_w in ("AWM", "M24", "AK-47", "M416", "UMP", "MP5"):
            self.muzzle_pos = (self.sw // 2, self.sh // 2)
            return self.muzzle_pos

        if cur_w == "KNIFE":
            return self._draw_knife_viewmodel(screen, player, righthand)
        elif cur_w in ("SMOKE", "MOLOTOV", "BOMB"):
            return self.muzzle_pos
        else:
            return self._draw_gun_viewmodel(screen, player, cur_w, righthand, recoil, reload_drop, side_sway)

    # ==========================================================================
    # 1. VIEWMODEL SÚNG: VẼ 3D BẰNG HÌNH KHỐI (graphics/gun3d.py), KHÔNG DÙNG PNG
    # ==========================================================================

    # Vị trí gốc súng (chỗ tay phải nắm) trong hệ camera: (phải, xuống, sâu) - đơn vị ~mét
    POSE_RIFLE = ((0.25, 0.19, 0.62), -17.0, 3.0)    # (vị trí, góc quay ngang, góc ngóc lên)
    POSE_PISTOL = ((0.17, 0.13, 0.42), -14.0, 3.0)
    POSE_KNIFE = ((0.17, 0.16, 0.32), -28.0, 10.0)

    def _px_to_m(self, px, depth):
        """Đổi độ lệch tính bằng pixel (bob, sway, nạp đạn) sang mét ở độ sâu depth."""
        f = (self.sw / 2) / math.tan(math.radians(34))
        return px * depth / f

    def _draw_gun_viewmodel(self, screen, player, weapon_id, righthand, recoil, reload_drop, side_sway):
        is_pistol = weapon_id in self.PISTOLS
        (x, y, z), yaw, pitch = self.POSE_PISTOL if is_pistol else self.POSE_RIFLE

        kick = min(1.0, recoil / 0.14)               # 0..1 ngay sau phát bắn
        reload_p = min(1.0, reload_drop / 110.0)     # 0..1 khi đang nạp đạn

        x += self._px_to_m(self.bob_x + self.sway_x + side_sway, z)
        y += self._px_to_m(self.bob_y + reload_drop * 0.6, z)
        z -= 0.035 * kick                            # súng giật lùi về phía người chơi
        pitch += 5.0 * kick                          # và nảy nòng lên
        roll = -22.0 * reload_p                      # nghiêng súng khi nạp đạn

        if not righthand:
            x = -x                                   # tay trái: lật gương sang bên trái
        self.muzzle_pos = gun3d.render(
            screen, weapon_id, (x, y, z), math.radians(yaw), math.radians(pitch),
            math.radians(roll), mirror=not righthand)
        return self.muzzle_pos

    # ==========================================================================
    # 2. VIEWMODEL DAO CẬN CHIẾN (3D)
    # ==========================================================================

    def _draw_knife_viewmodel(self, screen, player, righthand):
        (x, y, z), yaw, pitch = self.POSE_KNIFE
        roll = -20.0

        swing_timer = getattr(player, "knife_swing", 0.0)
        is_stab = getattr(player, "knife_is_stab", False)
        swing_total = 0.28
        if swing_timer > 0:
            p = math.sin((1.0 - swing_timer / swing_total) * math.pi)   # 0 -> 1 -> 0
            if is_stab:      # Chuột phải: đâm thẳng về phía trước
                z += 0.12 * p
                x -= 0.06 * p
                pitch += 6 * p
            else:            # Chuột trái: chém quét ngang
                yaw += 40 * p
                roll -= 35 * p
                x -= 0.08 * p
                y -= 0.03 * p

        x += self._px_to_m(self.bob_x + self.sway_x, z)
        y += self._px_to_m(self.bob_y, z)
        if not righthand:
            x = -x
        self.muzzle_pos = gun3d.render(
            screen, "KNIFE", (x, y, z), math.radians(yaw), math.radians(pitch),
            math.radians(roll), mirror=not righthand)
        return self.muzzle_pos
