"""graphics/renderer.py - Bộ dựng hình 3D Raycasting phân tích siêu tốc (cache nền trời-sàn & lọc mặt tường trước vòng tia)."""
import math
import random
import pygame

from settings import WIDTH, HEIGHT, FOV
from font_vn import get_font
from game.map import site_A, site_B, site_C, get_active_map


class Renderer:
    def __init__(self):
        # 320 tia -> mỗi cột rộng đúng 5px trên màn 1600px (không sai số làm tròn, tăng tốc mạnh trên Web)
        self.num_rays = 320
        self.ray_width = WIDTH // self.num_rays
        self.fov = math.radians(FOV)
        self.projection_plane = (WIDTH / 2.0) / math.tan(self.fov / 2.0)

        self.eye_height = 90.0
        self.crouch_height = 50.0
        self.jump_camera_scale = 0.35
        self.pitch_strength = 0.45
        self.max_pitch = 0.75

        self._cached_walls_sig = None
        self._h_north = []
        self._h_south = []
        self._v_west = []
        self._v_east = []

        self.z_buffer = [9999.0] * self.num_rays
        self._ray_offsets = []
        self._last_fov = None
        self._rebuild_ray_table()

        # Cache tấm nền Trời + Sàn phối cảnh kích thước (WIDTH x 3*HEIGHT) theo từng Map -> 1 lần blit/frame!
        self._bg_strip_map_id = None
        self._bg_strip = None
        self._bg_center_y = HEIGHT + HEIGHT // 2

        self._font_beacon = None
        self._beacon_label_cache = {}
        self._beam_cache = {}

        rng = random.Random(1337)
        self._stars = [
            (
                rng.uniform(0.0, math.tau),
                rng.uniform(0.05, 0.45),
                rng.choice((1, 1, 2)),
                rng.choice(((190, 215, 255), (230, 240, 255), (160, 190, 240), (255, 230, 180))),
            )
            for _ in range(64)
        ]

    def _rebuild_ray_table(self):
        if self._last_fov == self.fov:
            return
        self._last_fov = self.fov
        tan_half = math.tan(self.fov * 0.5)
        n = float(self.num_rays)
        self._ray_offsets = [
            (math.atan(((i / n) - 0.5) * 2.0 * tan_half), math.cos(math.atan(((i / n) - 0.5) * 2.0 * tan_half)))
            for i in range(self.num_rays)
        ]

    def _ensure_bg_strip(self, active_map):
        mid = active_map["id"]
        if self._bg_strip_map_id == mid and self._bg_strip is not None:
            return
        self._bg_strip_map_id = mid
        theme = active_map["theme"]
        sky_top = theme["sky_top"]
        sky_bot = theme["sky_bot"]
        floor_far = theme["floor_far"]
        floor_near = theme["floor_near"]

        total_h = HEIGHT * 3
        cy = self._bg_center_y
        col_surf = pygame.Surface((1, total_h))

        # Nửa trên: Bầu trời chuyển sắc tới chân trời cy
        for y in range(cy):
            t = max(0.0, (y - (cy - HEIGHT)) / float(HEIGHT))
            c = (
                int(sky_top[0] + (sky_bot[0] - sky_top[0]) * t),
                int(sky_top[1] + (sky_bot[1] - sky_top[1]) * t),
                int(sky_top[2] + (sky_bot[2] - sky_top[2]) * t),
            )
            col_surf.set_at((0, y), c)

        # Nửa dưới: Sàn nhà phối cảnh sương mù từ chân trời cy xuống đáy
        base_proj = (WIDTH / 2.0) / math.tan(math.radians(FOV) / 2.0)
        num_z = self.eye_height * base_proj
        for y in range(cy, total_h):
            dy = max(1, y - cy)
            z = num_z / dy
            fog = 0.0 if z > 1250.0 else max(0.0, min(1.0, 1.0 - (z / 1250.0) ** 1.3))
            c = (
                int(floor_far[0] + (floor_near[0] - floor_far[0]) * fog),
                int(floor_far[1] + (floor_near[1] - floor_far[1]) * fog),
                int(floor_far[2] + (floor_near[2] - floor_far[2]) * fog),
            )
            col_surf.set_at((0, y), c)

        self._bg_strip = pygame.transform.scale(col_surf, (WIDTH, total_h)).convert()

    def _prepare_walls(self, walls):
        sig = (len(walls), tuple((w.x, w.y, w.w, w.h) for w in walls[:6]))
        if self._cached_walls_sig == sig:
            return
        self._cached_walls_sig = sig
        self._h_north = [(float(w.top), float(w.left), float(w.right)) for w in walls]
        self._h_south = [(float(w.bottom), float(w.left), float(w.right)) for w in walls]
        self._v_west = [(float(w.left), float(w.top), float(w.bottom)) for w in walls]
        self._v_east = [(float(w.right), float(w.top), float(w.bottom)) for w in walls]

    def raycast(self, player, angle, walls):
        self._prepare_walls(walls)
        px, py = player.x, player.y
        dx = math.cos(angle)
        dy = math.sin(angle)
        closest_t = 2500.0

        if dy > 1e-6:
            inv_dy = 1.0 / dy
            for yw, x1, x2 in self._h_north:
                if yw > py:
                    t = (yw - py) * inv_dy
                    if t < closest_t and x1 <= px + t * dx <= x2:
                        closest_t = t
        elif dy < -1e-6:
            inv_dy = 1.0 / dy
            for yw, x1, x2 in self._h_south:
                if yw < py:
                    t = (yw - py) * inv_dy
                    if t < closest_t and x1 <= px + t * dx <= x2:
                        closest_t = t

        if dx > 1e-6:
            inv_dx = 1.0 / dx
            for xw, y1, y2 in self._v_west:
                if xw > px:
                    t = (xw - px) * inv_dx
                    if t < closest_t and y1 <= py + t * dy <= y2:
                        closest_t = t
        elif dx < -1e-6:
            inv_dx = 1.0 / dx
            for xw, y1, y2 in self._v_east:
                if xw < px:
                    t = (xw - px) * inv_dx
                    if t < closest_t and y1 <= py + t * dy <= y2:
                        closest_t = t

        return closest_t

    def get_camera_offset(self, player):
        crouch_offset = (self.crouch_height - self.eye_height) if getattr(player, "crouching", False) else 0.0
        jump_offset = getattr(player, "vertical_offset", 0.0) * self.jump_camera_scale
        return crouch_offset + jump_offset

    def get_pitch(self, player):
        pitch = getattr(player, "pitch", 0.0)
        return max(-self.max_pitch, min(self.max_pitch, pitch))

    def get_horizon(self, player):
        pitch = self.get_pitch(player)
        pitch_offset = math.tan(pitch) * self.projection_plane * self.pitch_strength
        horizon = HEIGHT // 2 + pitch_offset + self.get_camera_offset(player)
        return int(max(-HEIGHT, min(HEIGHT * 2, horizon)))

    def world_to_screen_x(self, player, world_x, world_y):
        dx = world_x - player.x
        dy = world_y - player.y
        distance = math.hypot(dx, dy)
        if distance <= 0.001:
            return WIDTH // 2, distance
        target_angle = math.atan2(dy, dx)
        relative_angle = math.atan2(math.sin(target_angle - player.angle), math.cos(target_angle - player.angle))
        screen_x = WIDTH / 2.0 + math.tan(relative_angle) * self.projection_plane
        return int(screen_x), distance

    def get_object_size(self, distance, world_height=70):
        dist = max(distance, 1.0)
        size = int(self.projection_plane * world_height / dist)
        return max(4, min(HEIGHT * 2, size))

    def render(self, screen, player, walls, show_beacons=True):
        self._prepare_walls(walls)
        self._rebuild_ray_table()

        active_map = get_active_map()
        self._ensure_bg_strip(active_map)
        theme = active_map["theme"]
        wall_r0, wall_g0, wall_b0 = theme["wall_rgb"]
        str_r0, str_g0, str_b0 = theme["stripe_rgb"]

        horizon = self.get_horizon(player)
        px, py = player.x, player.y
        player_ang = player.angle
        half_fov = self.fov * 0.5
        proj_plane = self.projection_plane
        draw_rect = pygame.draw.rect

        # 1 & 2. BẦU TRỜI + SÀN 3D CHỈ BẰNG 1 LỆNH BLIT DUY NHẤT!
        strip_y = max(0, min(HEIGHT * 2, self._bg_center_y - horizon))
        screen.blit(self._bg_strip, (0, 0), (0, strip_y, WIDTH, HEIGHT))

        sky_h = horizon if horizon < HEIGHT else HEIGHT
        if sky_h > 0:
            draw_circle = pygame.draw.circle
            tau = math.tau
            pi = math.pi
            tan = math.tan
            max_diff = half_fov + 0.2
            for star_ang, star_y_f, star_sz, star_col in self._stars:
                diff_ang = (star_ang - player_ang + pi) % tau - pi
                if -max_diff < diff_ang < max_diff:
                    star_sx = int(WIDTH * 0.5 + tan(diff_ang) * proj_plane)
                    star_sy = int(sky_h * star_y_f)
                    if 0 <= star_sx < WIDTH and 0 <= star_sy < sky_h:
                        draw_circle(screen, star_col, (star_sx, star_sy), star_sz)

        # 3. LỌC TRƯỚC CÁC CẠNH TƯỜNG ĐỐI DIỆN NGƯỜI CHƠI (CHỈ CHẠY 1 LẦN / FRAME)
        act_north = [(yw - py, x1, x2) for yw, x1, x2 in self._h_north if yw > py + 0.1]
        act_south = [(yw - py, x1, x2) for yw, x1, x2 in self._h_south if yw < py - 0.1]
        act_west = [(xw - px, y1, y2) for xw, y1, y2 in self._v_west if xw > px + 0.1]
        act_east = [(xw - px, y1, y2) for xw, y1, y2 in self._v_east if xw < px - 0.1]

        ray_w = self.ray_width
        z_buf = self.z_buffer
        cos = math.cos
        sin = math.sin
        face_mults = (1.05, 0.88, 0.78, 1.15)
        wall_scale = proj_plane * 180.0

        for i, (ang_off, cos_off) in enumerate(self._ray_offsets):
            ray_ang = player_ang + ang_off
            dx = cos(ray_ang)
            dy = sin(ray_ang)

            closest_t = 2200.0
            hit_u = 0.0
            hit_face = 0

            if dy > 1e-6:
                inv_dy = 1.0 / dy
                for dy_w, x1, x2 in act_north:
                    t = dy_w * inv_dy
                    if t < closest_t:
                        x = px + t * dx
                        if x1 <= x <= x2:
                            closest_t = t
                            hit_u = x % 64.0
                            hit_face = 0
            elif dy < -1e-6:
                inv_dy = 1.0 / dy
                for dy_w, x1, x2 in act_south:
                    t = dy_w * inv_dy
                    if t < closest_t:
                        x = px + t * dx
                        if x1 <= x <= x2:
                            closest_t = t
                            hit_u = x % 64.0
                            hit_face = 1

            if dx > 1e-6:
                inv_dx = 1.0 / dx
                for dx_w, y1, y2 in act_west:
                    t = dx_w * inv_dx
                    if t < closest_t:
                        y = py + t * dy
                        if y1 <= y <= y2:
                            closest_t = t
                            hit_u = y % 64.0
                            hit_face = 2
            elif dx < -1e-6:
                inv_dx = 1.0 / dx
                for dx_w, y1, y2 in act_east:
                    t = dx_w * inv_dx
                    if t < closest_t:
                        y = py + t * dy
                        if y1 <= y <= y2:
                            closest_t = t
                            hit_u = y % 64.0
                            hit_face = 3

            if closest_t >= 2199.0:
                z_buf[i] = 9999.0
                continue

            corrected_dist = closest_t * cos_off
            if corrected_dist < 0.1:
                corrected_dist = 0.1
            z_buf[i] = corrected_dist

            wall_h = int(wall_scale / corrected_dist)
            wall_top = horizon - (wall_h >> 1)

            fog_w = 1.0 - (corrected_dist * 0.000714)
            if fog_w < 0.08:
                fog_w = 0.08
            shade = face_mults[hit_face] * fog_w
            if hit_u < 4.0 or hit_u > 60.0:
                shade *= 0.70

            br = int(wall_r0 * shade)
            bg = int(wall_g0 * shade)
            bb = int(wall_b0 * shade)
            if br > 255:
                br = 255
            if bg > 255:
                bg = 255
            if bb > 255:
                bb = 255

            rx = i * ray_w
            draw_rect(screen, (br, bg, bb), (rx, wall_top, ray_w, wall_h))

            base_h = wall_h // 8
            if base_h < 2:
                base_h = 2
            draw_rect(
                screen,
                (int(br * 0.55), int(bg * 0.55), int(bb * 0.60)),
                (rx, wall_top + wall_h - base_h, ray_w, base_h),
            )

            trim_h = wall_h // 12
            if trim_h < 2:
                trim_h = 2
            tr = int(br * 1.30)
            tg = int(bg * 1.30)
            tb = int(bb * 1.35)
            draw_rect(
                screen,
                (255 if tr > 255 else tr, 255 if tg > 255 else tg, 255 if tb > 255 else tb),
                (rx, wall_top, ray_w, trim_h),
            )

            stripe_h = wall_h // 40
            if stripe_h < 1:
                stripe_h = 1
            draw_rect(
                screen,
                (int(str_r0 * fog_w), int(str_g0 * fog_w), int(str_b0 * fog_w)),
                (rx, wall_top + int(wall_h * 0.55), ray_w, stripe_h),
            )

        # 4. CỘT MỐC 3D HOLOGRAM SITE A, B, C
        if not show_beacons:
            return
        if self._font_beacon is None:
            self._font_beacon = get_font(17, bold=True)

        for label, site_rect, col_rgb in (
            ("A", site_A, (60, 220, 130)),
            ("B", site_B, (70, 150, 240)),
            ("C", site_C, (240, 210, 70)),
        ):
            cx, cy = site_rect.centerx, site_rect.centery
            dx, dy = cx - px, cy - py
            dist = math.hypot(dx, dy)
            if dist < 10.0 or dist > 1600.0:
                continue

            ang = math.atan2(dy, dx)
            rel_ang = math.atan2(math.sin(ang - player_ang), math.cos(ang - player_ang))
            if abs(rel_ang) > half_fov + 0.15:
                continue

            sx = int(WIDTH * 0.5 + math.tan(rel_ang) * proj_plane)
            col_idx = min(self.num_rays - 1, max(0, sx // ray_w))
            is_visible = dist < z_buf[col_idx] + 60.0

            b_h = max(10, min(320, int(proj_plane * 110.0 / dist)))
            by_top = horizon - (b_h >> 1)

            if is_visible:
                qh = max(20, (b_h * 2 // 16) * 16)
                bkey = (label, qh)
                beam_surf = self._beam_cache.get(bkey)
                if beam_surf is None:
                    if len(self._beam_cache) > 48:
                        self._beam_cache.clear()
                    beam_surf = pygame.Surface((28, qh), pygame.SRCALPHA)
                    draw_rect(beam_surf, (*col_rgb, 45), (6, 0, 16, qh))
                    draw_rect(beam_surf, (*col_rgb, 140), (10, 0, 8, qh))
                    self._beam_cache[bkey] = beam_surf
                screen.blit(beam_surf, (sx - 14, by_top - b_h))

            icon_y = by_top - 32
            pygame.draw.circle(screen, (20, 24, 32), (sx, icon_y), 18)
            pygame.draw.circle(screen, col_rgb, (sx, icon_y), 18, 2)
            lbl_txt = self._beacon_label_cache.get(label)
            if lbl_txt is None:
                lbl_txt = self._font_beacon.render(label, True, col_rgb)
                self._beacon_label_cache[label] = lbl_txt
            screen.blit(lbl_txt, (sx - lbl_txt.get_width() // 2, icon_y - lbl_txt.get_height() // 2))

            d_txt = self._font_beacon.render(f"{int(dist / 20.0)}m", True, (215, 225, 235))
            screen.blit(d_txt, (sx - d_txt.get_width() // 2, icon_y + 20))
