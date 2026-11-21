import pygame
import math
import random

from settings import (
    WIDTH,
    HEIGHT,
    FOV,
    MAP_W,
    MAP_H
)
from game.map import site_A, site_B, site_C


class Renderer:
    """
    Hệ thống đồ họa 3D chuẩn xác (True 3D Analytical Engine):
    - Đồ họa không gian 3 chiều với phối cảnh góc nhìn thực tế (True 3D Perspective)
    - Phóng tia giao điểm chính xác từng pixel (Analytical Slab / Segment Raycaster - không bậc thang, không răng cưa)
    - Sàn nhà 3D phối cảnh (3D Perspective Floor) tụ về đường chân trời mượt mà
    - Bầu trời / Không gian đêm 3D có các chòm sao xoay theo góc nhìn chuột
    - Bề mặt tường 3D có gờ cột, chân tường gia cố, phào trần và vạch phản quang neon sci-fi
    - Ánh sáng định hướng 4 chiều (Directional Lighting 4 hướng: Bắc, Nam, Đông, Tây)
    - Cột mốc 3D Hologram phát sáng định vị các khu vực bom Site A, Site B, Site C
    - Bộ đệm độ sâu Z-Buffer chuẩn xác giúp các đối tượng 3D (kẻ địch Roblox, súng rơi, bom) không bị lỗi xuyên tường
    """

    def __init__(self):
        # Thiết lập góc nhìn và mặt phẳng chiếu
        self.num_rays = 400
        self.ray_width = WIDTH / self.num_rays
        self.fov = math.radians(FOV)
        self.projection_plane = (WIDTH / 2.0) / math.tan(self.fov / 2.0)

        # Thông số camera
        self.eye_height = 90.0
        self.crouch_height = 50.0
        self.jump_camera_scale = 0.35
        self.pitch_strength = 0.45
        self.max_pitch = 0.75

        # Cache các đoạn thẳng tường để tính giao điểm siêu tốc 120 FPS
        self._cached_walls = None
        self._h_north = []
        self._h_south = []
        self._v_west = []
        self._v_east = []

        # Z-Buffer lưu độ sâu thực của từng cột raycast
        self.z_buffer = [9999.0] * self.num_rays

        # Font chữ hiển thị Hologram 3D Site
        self._font_beacon = None

        # Cache sao trên bầu trời 3D
        self._stars = []
        rng = random.Random(1337)
        for _ in range(80):
            # Tọa độ góc theo vòng tròn 360 độ (0 -> 2pi) và độ cao y
            star_ang = rng.uniform(0.0, math.tau)
            star_y = rng.uniform(0.05, 0.45)
            star_sz = rng.choice([1, 1, 2])
            star_col = rng.choice([
                (190, 215, 255),
                (230, 240, 255),
                (160, 190, 240),
                (255, 230, 180)
            ])
            self._stars.append((star_ang, star_y, star_sz, star_col))

    def _prepare_walls(self, walls):
        """Tiền xử lý và phân loại các mặt tường để tối ưu hóa culling."""
        if self._cached_walls is walls:
            return
        self._cached_walls = walls
        self._h_north.clear()
        self._h_south.clear()
        self._v_west.clear()
        self._v_east.clear()

        for w in walls:
            self._h_north.append((float(w.top), float(w.left), float(w.right)))
            self._h_south.append((float(w.bottom), float(w.left), float(w.right)))
            self._v_west.append((float(w.left), float(w.top), float(w.bottom)))
            self._v_east.append((float(w.right), float(w.top), float(w.bottom)))

    def raycast(self, player, angle, walls):
        """Tính toán khoảng cách giao điểm chính xác tuyệt đối từ người chơi đến tường."""
        self._prepare_walls(walls)
        px, py = player.x, player.y
        dx = math.cos(angle)
        dy = math.sin(angle)

        closest_t = 2500.0

        if dy > 1e-6:
            inv_dy = 1.0 / dy
            for y, x1, x2 in self._h_north:
                t = (y - py) * inv_dy
                if 0.1 < t < closest_t:
                    x = px + t * dx
                    if x1 <= x <= x2:
                        closest_t = t
        elif dy < -1e-6:
            inv_dy = 1.0 / dy
            for y, x1, x2 in self._h_south:
                t = (y - py) * inv_dy
                if 0.1 < t < closest_t:
                    x = px + t * dx
                    if x1 <= x <= x2:
                        closest_t = t

        if dx > 1e-6:
            inv_dx = 1.0 / dx
            for x, y1, y2 in self._v_west:
                t = (x - px) * inv_dx
                if 0.1 < t < closest_t:
                    y = py + t * dy
                    if y1 <= y <= y2:
                        closest_t = t
        elif dx < -1e-6:
            inv_dx = 1.0 / dx
            for x, y1, y2 in self._v_east:
                t = (x - px) * inv_dx
                if 0.1 < t < closest_t:
                    y = py + t * dy
                    if y1 <= y <= y2:
                        closest_t = t

        return closest_t

    def get_camera_offset(self, player):
        """Tính toán độ cao camera khi ngồi hoặc nhảy."""
        if getattr(player, "crouching", False):
            crouch_offset = self.crouch_height - self.eye_height
        else:
            crouch_offset = 0.0

        jump_offset = getattr(player, "vertical_offset", 0.0) * self.jump_camera_scale
        return crouch_offset + jump_offset

    def get_pitch(self, player):
        """Lấy góc nghiêng lên / xuống (Pitch)."""
        pitch = getattr(player, "pitch", 0.0)
        return max(-self.max_pitch, min(self.max_pitch, pitch))

    def get_horizon(self, player):
        """Tính toán vị trí đường chân trời 3D trên màn hình."""
        pitch = self.get_pitch(player)
        pitch_offset = math.tan(pitch) * self.projection_plane * self.pitch_strength
        camera_height_offset = self.get_camera_offset(player)

        horizon = HEIGHT // 2 + pitch_offset + camera_height_offset
        return int(max(-HEIGHT, min(HEIGHT * 2, horizon)))

    def world_to_screen_x(self, player, world_x, world_y):
        """Chiếu tọa độ điểm thực tế trong bản đồ lên trục hoành X của màn hình."""
        dx = world_x - player.x
        dy = world_y - player.y
        distance = math.hypot(dx, dy)
        if distance <= 0.001:
            return WIDTH // 2, distance

        target_angle = math.atan2(dy, dx)
        relative_angle = math.atan2(
            math.sin(target_angle - player.angle),
            math.cos(target_angle - player.angle)
        )

        screen_x = WIDTH / 2.0 + math.tan(relative_angle) * self.projection_plane
        return int(screen_x), distance

    def get_object_size(self, distance, world_height=70):
        """Tính kích thước phóng đại của vật thể 3D theo khoảng cách."""
        dist = max(distance, 1.0)
        size = int(self.projection_plane * world_height / dist)
        return max(4, min(HEIGHT * 2, size))

    def render(self, screen, player, walls):
        """Vẽ toàn bộ thế giới 3D bao gồm bầu trời, sàn phối cảnh, tường kết cấu và cột mốc 3D."""
        self._prepare_walls(walls)
        horizon = self.get_horizon(player)
        px, py = player.x, player.y
        player_ang = player.angle

        # ======================================================================
        # 1. BẦU TRỜI 3D (3D ATMOSPHERIC CELESTIAL SKY & STARS)
        # ======================================================================
        sky_h = max(0, min(HEIGHT, horizon))
        if sky_h > 0:
            bands = 10
            for b in range(bands):
                t = b / float(bands)
                # Dải màu xanh đen chuyển dần sang màu sương khói chân trời
                col = (
                    int(14 + 24 * t),
                    int(18 + 30 * t),
                    int(28 + 42 * t)
                )
                y1 = int(sky_h * b / bands)
                y2 = int(sky_h * (b + 1) / bands) + 1
                pygame.draw.rect(screen, col, (0, y1, WIDTH, y2 - y1))

            # Vẽ các vì sao xoay theo góc quay chuột của người chơi (Yaw Tracking)
            half_fov = self.fov / 2.0
            for star_ang, star_y_f, star_sz, star_col in self._stars:
                diff_ang = (star_ang - player_ang + math.pi) % math.tau - math.pi
                if abs(diff_ang) < half_fov + 0.2:
                    star_sx = int(WIDTH / 2.0 + math.tan(diff_ang) * self.projection_plane)
                    star_sy = int(sky_h * star_y_f)
                    if 0 <= star_sx < WIDTH and 0 <= star_sy < sky_h:
                        pygame.draw.circle(screen, star_col, (star_sx, star_sy), star_sz)

        # ======================================================================
        # 2. SÀN NHÀ 3D PHỐI CẢNH (3D PERSPECTIVE FLOOR - NỀN SẠCH MỊN KHÔNG GẠCH)
        # ======================================================================
        floor_top = max(0, min(HEIGHT, horizon))
        eff_eye_h = self.eye_height + getattr(player, "vertical_offset", 0.0) * self.jump_camera_scale
        if getattr(player, "crouching", False):
            eff_eye_h -= (self.eye_height - self.crouch_height)
        eff_eye_h = max(20.0, eff_eye_h)

        half_fov = self.fov / 2.0

        # Quét sàn theo từng cặp dòng để đạt hiệu năng 120 FPS
        step_y = 2
        for y in range(floor_top + 1, HEIGHT, step_y):
            dy = y - horizon
            if dy <= 0:
                continue
            z = (eff_eye_h * self.projection_plane) / dy
            if z > 1600.0:
                continue

            # Hệ số sương mù xa mờ dần (Distance Fog)
            fog = max(0.0, min(1.0, 1.0 - (z / 1250.0) ** 1.3))

            base_r = int(32 + 50 * fog)
            base_g = int(36 + 46 * fog)
            base_b = int(44 + 40 * fog)

            pygame.draw.rect(screen, (base_r, base_g, base_b), (0, y, WIDTH, step_y))

        # ======================================================================
        # 3. PHÓNG TIA TƯỜNG 3D CHÍNH XÁC & KẾT CẤU BỀ MẶT (3D WALLS WITH TRIM)
        # ======================================================================
        ray_w = self.ray_width

        for i in range(self.num_rays):
            cam_x = (i / float(self.num_rays)) - 0.5
            ray_ang = player_ang + math.atan(cam_x * 2.0 * math.tan(half_fov))
            dx = math.cos(ray_ang)
            dy = math.sin(ray_ang)

            closest_t = 2200.0
            hit_u = 0.0
            hit_face = 0  # 0=Bắc, 1=Nam, 2=Tây, 3=Đông

            # Giao điểm mặt ngang
            if dy > 1e-6:
                inv_dy = 1.0 / dy
                for y, x1, x2 in self._h_north:
                    t = (y - py) * inv_dy
                    if 0.1 < t < closest_t:
                        x = px + t * dx
                        if x1 <= x <= x2:
                            closest_t = t
                            hit_u = x % 64.0
                            hit_face = 0
            elif dy < -1e-6:
                inv_dy = 1.0 / dy
                for y, x1, x2 in self._h_south:
                    t = (y - py) * inv_dy
                    if 0.1 < t < closest_t:
                        x = px + t * dx
                        if x1 <= x <= x2:
                            closest_t = t
                            hit_u = x % 64.0
                            hit_face = 1

            # Giao điểm mặt dọc
            if dx > 1e-6:
                inv_dx = 1.0 / dx
                for x, y1, y2 in self._v_west:
                    t = (x - px) * inv_dx
                    if 0.1 < t < closest_t:
                        y = py + t * dy
                        if y1 <= y <= y2:
                            closest_t = t
                            hit_u = y % 64.0
                            hit_face = 2
            elif dx < -1e-6:
                inv_dx = 1.0 / dx
                for x, y1, y2 in self._v_east:
                    t = (x - px) * inv_dx
                    if 0.1 < t < closest_t:
                        y = py + t * dy
                        if y1 <= y <= y2:
                            closest_t = t
                            hit_u = y % 64.0
                            hit_face = 3

            if closest_t >= 2199.0:
                self.z_buffer[i] = 9999.0
                continue

            # Khử hiệu ứng Fish-eye (mắt cá)
            corrected_dist = closest_t * math.cos(ray_ang - player_ang)
            corrected_dist = max(0.1, corrected_dist)
            self.z_buffer[i] = corrected_dist

            # Chiều cao tường theo phối cảnh 3D
            wall_h = int(self.projection_plane * 180.0 / corrected_dist)
            wall_top = horizon - wall_h // 2

            # Ánh sáng định hướng 4 mặt (Directional Lighting Shading)
            face_mult = [1.05, 0.88, 0.78, 1.15][hit_face]
            fog_w = max(0.08, min(1.0, 1.0 - (corrected_dist / 1400.0) ** 1.2))

            br = int(75 * face_mult * fog_w)
            bg = int(82 * face_mult * fog_w)
            bb = int(98 * face_mult * fog_w)

            # Rãnh khớp nối / Cột trụ dọc 3D mỗi 64 đơn vị map
            if hit_u < 4.0 or hit_u > 60.0:
                br = int(br * 0.70)
                bg = int(bg * 0.70)
                bb = int(bb * 0.70)

            rx = int(i * ray_w)
            rw_int = int(ray_w + 1)

            # Thân tường chính
            pygame.draw.rect(screen, (br, bg, bb), (rx, wall_top, rw_int, wall_h))

            # Chân tường gia cố bảo vệ (Baseboard Kickplate)
            base_h = max(2, int(wall_h * 0.12))
            base_col = (int(br * 0.55), int(bg * 0.55), int(bb * 0.60))
            pygame.draw.rect(screen, base_col, (rx, wall_top + wall_h - base_h, rw_int, base_h))

            # Phào trần kim loại bắt sáng (Top Cornice Trim)
            trim_h = max(2, int(wall_h * 0.08))
            trim_col = (min(255, int(br * 1.30)), min(255, int(bg * 1.30)), min(255, int(bb * 1.35)))
            pygame.draw.rect(screen, trim_col, (rx, wall_top, rw_int, trim_h))

            # Vạch neon phản quang phong cách Sci-Fi / Valorant ở độ cao 55%
            stripe_h = max(1, int(wall_h * 0.025))
            stripe_y = wall_top + int(wall_h * 0.55)
            stripe_col = (int(30 * fog_w), int(185 * fog_w), int(225 * fog_w))
            pygame.draw.rect(screen, stripe_col, (rx, stripe_y, rw_int, stripe_h))

        # ======================================================================
        # 4. CỘT MỐC 3D HOLOGRAM ĐỊNH VỊ SITE A, B, C (3D TACTICAL BEACONS)
        # ======================================================================
        if self._font_beacon is None:
            self._font_beacon = pygame.font.SysFont("Arial", 18, bold=True)

        for label, site_rect, col_rgb in [
            ("A", site_A, (60, 220, 130)),
            ("B", site_B, (70, 150, 240)),
            ("C", site_C, (240, 210, 70))
        ]:
            cx, cy = site_rect.centerx, site_rect.centery
            dx, dy = cx - px, cy - py
            dist = math.hypot(dx, dy)
            if dist < 10.0 or dist > 1600.0:
                continue

            ang = math.atan2(dy, dx)
            rel_ang = math.atan2(math.sin(ang - player_ang), math.cos(ang - player_ang))
            if abs(rel_ang) > half_fov + 0.15:
                continue

            sx = int(WIDTH / 2.0 + math.tan(rel_ang) * self.projection_plane)
            col_idx = min(self.num_rays - 1, max(0, int(sx / ray_w)))

            # Kiểm tra nếu nằm trong tầm nhìn hoặc không bị chắn hoàn toàn bởi tường
            is_visible = dist < self.z_buffer[col_idx] + 60.0

            b_h = max(10, int(self.projection_plane * 110.0 / dist))
            by_top = horizon - b_h // 2

            if is_visible:
                # Cột sáng Hologram đứng
                beam_surf = pygame.Surface((28, b_h * 2), pygame.SRCALPHA)
                pygame.draw.rect(beam_surf, (*col_rgb, 45), (6, 0, 16, b_h * 2))
                pygame.draw.rect(beam_surf, (*col_rgb, 140), (10, 0, 8, b_h * 2))
                screen.blit(beam_surf, (sx - 14, by_top - b_h))

            # Biểu tượng Hologram Site lơ lửng trên không
            icon_y = by_top - 32
            pygame.draw.circle(screen, (20, 24, 32), (sx, icon_y), 18)
            pygame.draw.circle(screen, col_rgb, (sx, icon_y), 18, 2)
            lbl_txt = self._font_beacon.render(label, True, col_rgb)
            screen.blit(lbl_txt, (sx - lbl_txt.get_width() // 2, icon_y - lbl_txt.get_height() // 2))

            dist_m = f"{int(dist / 20.0)}m"
            d_txt = self._font_beacon.render(dist_m, True, (215, 225, 235))
            screen.blit(d_txt, (sx - d_txt.get_width() // 2, icon_y + 20))
