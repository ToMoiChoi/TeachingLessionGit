import pygame
import math
import sys
from bisect import bisect_left, bisect_right

from settings import (
    WIDTH,
    HEIGHT,
    FOV,
    MAP_W,
    MAP_H
)


class Renderer:

    def __init__(self):

        # ==========================================
        # RAYCAST SETTINGS
        # ==========================================

        self.fov = math.radians(FOV)

        self.projection_plane = (
            WIDTH / 2
        ) / math.tan(
            self.fov / 2
        )

        # Nền trời/sàn đơn giản (1 màu) cho máy yếu
        self.simple_background = False

        # Trên web (pygbag) Python chậm hơn nhiều -> dùng ít tia hơn
        self.set_rays(160 if sys.platform == "emscripten" else 240)

        # ==========================================
        # CAMERA
        # ==========================================

        self.eye_height = 90

        self.crouch_height = 50

        self.jump_camera_scale = 0.35

        # Camera pitch strength
        self.pitch_strength = 0.45

        # Giới hạn camera
        self.max_pitch = 0.75

    def set_rays(
        self,
        num_rays
    ):

        # Ít tia hơn = cột tường to hơn, hình thô hơn nhưng nhẹ máy hơn
        self.num_rays = num_rays

        # Tính sẵn góc lệch + hệ số chống mắt cá cho từng tia (không đổi giữa các frame)
        tan_half = math.tan(self.fov / 2)
        self.ray_offsets = [
            math.atan(((i / num_rays) - 0.5) * 2 * tan_half)
            for i in range(num_rays)
        ]
        self.ray_cos = [math.cos(a) for a in self.ray_offsets]

        # Vị trí cột tường trên màn hình. SDL tô hình chữ nhật rộng >= 16px
        # chậm bất thường (cột 20px chậm hơn ~15 lần cột 14px) nên chia cột
        # rộng thành các mảnh <= 15px - hình vẽ ra y hệt.
        ray_width = WIDTH / num_rays
        self.col_pieces = []
        for i in range(num_rays):
            x = int(i * ray_width)
            w = int(ray_width + 1)
            pieces = []
            while w > 0:
                pw = min(15, w)
                pieces.append((x, pw))
                x += pw
                w -= pw
            self.col_pieces.append(pieces)

    # =====================================================
    # RAYCAST
    # =====================================================

    def raycast(
        self,
        player,
        angle,
        walls
    ):

        # Tính thẳng giao điểm tia với từng hình chữ nhật (slab method)
        # thay vì nhích từng 20px rồi dò mọi bức tường -> nhanh hơn ~40 lần,
        # rất quan trọng khi chạy trên web (pygbag chậm hơn desktop nhiều).

        dx = math.cos(angle)
        dy = math.sin(angle)

        px = player.x
        py = player.y

        # Cạnh các bức tường dạng tuple, tính 1 lần (đọc tuple nhanh hơn
        # đọc wall.left/right/... của Rect hàng nghìn lần mỗi frame)
        key = (id(walls), len(walls))
        if getattr(self, "_wall_key", None) != key:
            self._wall_key = key
            self._wall_edges = [(w.left, w.right, w.top, w.bottom) for w in walls]

        best = MAP_W if MAP_W > MAP_H else MAP_H

        if abs(dx) > 1e-9 and abs(dy) > 1e-9:
            ix = 1.0 / dx
            iy = 1.0 / dy
            for left, right, top, bottom in self._wall_edges:
                t1 = (left - px) * ix
                t2 = (right - px) * ix
                if t1 > t2:
                    t1, t2 = t2, t1
                t3 = (top - py) * iy
                t4 = (bottom - py) * iy
                if t3 > t4:
                    t3, t4 = t4, t3
                t_enter = t1 if t1 > t3 else t3
                t_exit = t2 if t2 < t4 else t4
                if t_exit < 0 or t_enter > t_exit:
                    continue
                if t_enter < 0:
                    t_enter = 0
                if t_enter < best:
                    best = t_enter
            return best

        # Tia song song trục X hoặc Y (hiếm gặp)
        for left, right, top, bottom in self._wall_edges:
            if abs(dx) > 1e-9:
                if py < top or py >= bottom:
                    continue
                t1 = (left - px) / dx
                t2 = (right - px) / dx
            else:
                if px < left or px >= right:
                    continue
                t1 = (top - py) / dy
                t2 = (bottom - py) / dy
            if t1 > t2:
                t1, t2 = t2, t1
            if t2 < 0:
                continue
            hit = t1 if t1 > 0 else 0
            if hit < best:
                best = hit
        return best

    # =====================================================
    # RAYCAST TẤT CẢ CÁC TIA (nhanh)
    # =====================================================

    def cast_all(
        self,
        player,
        walls
    ):

        # Thay vì mỗi tia thử MỌI bức tường: mỗi frame tính 1 lần xem tường
        # nào nằm trong góc nhìn của tia nào, xếp tường gần -> xa, rồi mỗi tia
        # chỉ thử các tường của nó và dừng ngay khi tường kế tiếp đã xa hơn
        # điểm chạm hiện tại. Kết quả giống hệt raycast() nhưng nhanh hơn nhiều.

        key = (id(walls), len(walls))
        if getattr(self, "_wall_key", None) != key:
            self._wall_key = key
            self._wall_edges = [(w.left, w.right, w.top, w.bottom) for w in walls]

        px = player.x
        py = player.y
        pa = player.angle
        offs = self.ray_offsets
        n = self.num_rays
        lo_lim = offs[0]
        hi_lim = offs[-1]
        two_pi = 2 * math.pi
        atan2 = math.atan2

        # Khoảng cách gần nhất từ người chơi tới từng tường, sắp xếp gần -> xa
        cand = []
        for left, right, top, bottom in self._wall_edges:
            cx = left if px < left else (right if px > right else px)
            cy = top if py < top else (bottom if py > bottom else py)
            cand.append((math.hypot(px - cx, py - cy), left, right, top, bottom))
        cand.sort()

        buckets = [[] for _ in range(n)]
        for wall in cand:
            d, left, right, top, bottom = wall
            if d < 1:
                # Đứng sát/chạm tường: cho tường này vào mọi tia
                for b in buckets:
                    b.append(wall)
                continue
            angs = [
                (atan2(y - py, x - px) - pa + math.pi) % two_pi - math.pi
                for x, y in ((left, top), (right, top), (left, bottom), (right, bottom))
            ]
            amin = min(angs)
            amax = max(angs)
            if amax - amin > math.pi:
                # Tường vắt qua phía sau lưng (góc ±180°): dồn về khoảng
                # [0, 2π) rồi xét cả phần lùi 2π - phần đó có thể vẫn ở trước mặt
                angs = [a + two_pi if a < 0 else a for a in angs]
                amin = min(angs)
                amax = max(angs)
                spans = ((amin, amax), (amin - two_pi, amax - two_pi))
            else:
                spans = ((amin, amax),)
            # (2 khoảng cách nhau 2π nên tối đa 1 khoảng nằm trong góc nhìn 90°)
            for lo, hi in spans:
                if hi < lo_lim or lo > hi_lim:
                    continue  # ngoài góc nhìn
                i0 = max(0, bisect_left(offs, lo) - 1)
                i1 = min(n, bisect_right(offs, hi) + 1)
                for i in range(i0, i1):
                    buckets[i].append(wall)

        far = MAP_W if MAP_W > MAP_H else MAP_H
        cos = math.cos
        sin = math.sin
        dists = [far] * n

        for i in range(n):
            angle = pa + offs[i]
            dx = cos(angle)
            dy = sin(angle)
            if abs(dx) <= 1e-9 or abs(dy) <= 1e-9:
                dists[i] = self.raycast(player, angle, walls)
                continue
            ix = 1.0 / dx
            iy = 1.0 / dy
            best = far
            for d, left, right, top, bottom in buckets[i]:
                if d >= best:
                    break
                t1 = (left - px) * ix
                t2 = (right - px) * ix
                if t1 > t2:
                    t1, t2 = t2, t1
                t3 = (top - py) * iy
                t4 = (bottom - py) * iy
                if t3 > t4:
                    t3, t4 = t4, t3
                t_enter = t1 if t1 > t3 else t3
                t_exit = t2 if t2 < t4 else t4
                if t_exit < 0 or t_enter > t_exit:
                    continue
                if t_enter < 0:
                    t_enter = 0
                if t_enter < best:
                    best = t_enter
            dists[i] = best

        return dists

    # =====================================================
    # CAMERA HEIGHT
    # =====================================================

    def get_camera_offset(
        self,
        player
    ):

        # ==========================================
        # CROUCH
        # ==========================================

        if getattr(
            player,
            "crouching",
            False
        ):

            crouch_offset = (
                self.crouch_height
                -
                self.eye_height
            )

        else:

            crouch_offset = 0

        # ==========================================
        # JUMP
        # ==========================================

        jump_offset = (
            getattr(
                player,
                "vertical_offset",
                0
            )
            *
            self.jump_camera_scale
        )

        return (
            crouch_offset
            +
            jump_offset
        )

    # =====================================================
    # CAMERA PITCH
    # =====================================================

    def get_pitch(
        self,
        player
    ):

        pitch = getattr(
            player,
            "pitch",
            0.0
        )

        # Giới hạn pitch
        pitch = max(
            -self.max_pitch,
            min(
                self.max_pitch,
                pitch
            )
        )

        return pitch

    # =====================================================
    # HORIZON
    # =====================================================

    def get_horizon(
        self,
        player
    ):

        # ==========================================
        # PITCH
        # ==========================================

        pitch = self.get_pitch(
            player
        )

        # ==========================================
        # PITCH -> PIXEL
        # ==========================================

        pitch_offset = (
            math.tan(pitch)
            *
            self.projection_plane
            *
            self.pitch_strength
        )

        # ==========================================
        # CROUCH / JUMP
        # ==========================================

        camera_height_offset = (
            self.get_camera_offset(
                player
            )
        )

        # ==========================================
        # HORIZON
        # ==========================================

        horizon = (
            HEIGHT // 2
            +
            pitch_offset
            +
            camera_height_offset
        )

        # ==========================================
        # LIMIT
        # ==========================================

        horizon = max(
            -HEIGHT,
            min(
                HEIGHT * 2,
                horizon
            )
        )

        return int(horizon)

    # =====================================================
    # WORLD TO SCREEN X
    # =====================================================

    def world_to_screen_x(
        self,
        player,
        world_x,
        world_y
    ):

        dx = world_x - player.x
        dy = world_y - player.y

        distance = math.hypot(
            dx,
            dy
        )

        if distance <= 0.001:
            return WIDTH // 2, distance

        target_angle = math.atan2(
            dy,
            dx
        )

        relative_angle = math.atan2(
            math.sin(
                target_angle
                -
                player.angle
            ),
            math.cos(
                target_angle
                -
                player.angle
            )
        )

        screen_x = (
            WIDTH / 2
            +
            math.tan(
                relative_angle
            )
            *
            self.projection_plane
        )

        return (
            int(screen_x),
            distance
        )

    # =====================================================
    # OBJECT SIZE
    # =====================================================

    def get_object_size(
        self,
        distance,
        world_height=70
    ):

        distance = max(
            distance,
            1
        )

        size = int(
            self.projection_plane
            *
            world_height
            /
            distance
        )

        size = max(
            4,
            min(
                HEIGHT * 2,
                size
            )
        )

        return size

    # =====================================================
    # RENDER
    # =====================================================

    def render(
        self,
        screen,
        player,
        walls
    ):

        # ==========================================
        # CAMERA HORIZON
        # ==========================================

        horizon = self.get_horizon(
            player
        )

        # ==========================================
        # SKY
        # ==========================================

        # Trần/trời xanh lam, tối dần lên trên
        screen.fill(
            (58, 78, 112)
        )
        sky_h = max(0, min(HEIGHT, horizon))
        floor_top = max(0, min(HEIGHT, horizon))
        if self.simple_background:
            screen.fill((46, 62, 92), (0, 0, WIDTH, sky_h))
            screen.fill((78, 66, 54), (0, floor_top, WIDTH, HEIGHT - floor_top))
        for band in range(0 if self.simple_background else 6):
            t = band / 6
            pygame.draw.rect(
                screen,
                (int(34 + 24 * t), int(46 + 32 * t), int(72 + 40 * t)),
                (0, int(sky_h * band / 6), WIDTH, int(sky_h / 6) + 1)
            )

        # ==========================================
        # GROUND
        # ==========================================

        # Sàn nâu ấm, sáng dần về phía người chơi, tối ở xa (fog)
        floor_h = max(1, HEIGHT - floor_top)
        for band in range(0 if self.simple_background else 8):
            t = band / 7
            y0 = floor_top + int(floor_h * band / 8)
            pygame.draw.rect(
                screen,
                (int(52 + 46 * t), int(46 + 38 * t), int(40 + 28 * t)),
                (0, y0, WIDTH, int(floor_h / 8) + 2)
            )
        pygame.draw.rect(
            screen,
            (98, 84, 68),
            (0, HEIGHT, WIDTH, HEIGHT)
        )

        # ==========================================
        # RAYCAST
        # ==========================================

        all_dists = self.cast_all(
            player,
            walls
        )

        for i in range(
            self.num_rays
        ):

            distance = all_dists[i]

            # ======================================
            # FISH-EYE CORRECTION
            # ======================================

            distance *= self.ray_cos[i]

            distance = max(
                distance,
                0.1
            )

            # ======================================
            # WALL HEIGHT
            # ======================================

            wall_height = int(
                self.projection_plane
                *
                180
                /
                distance
            )

            wall_height = min(
                wall_height,
                HEIGHT * 2
            )

            # ======================================
            # WALL POSITION
            # ======================================

            top = (
                horizon
                -
                wall_height // 2
            )

            # ======================================
            # SHADING
            # ======================================

            shade = max(
                25,
                min(
                    180,
                    int(
                        18000
                        /
                        (
                            distance
                            +
                            100
                        )
                    )
                )
            )

            # Tường tông xám-lạnh nhạt, khác sàn nâu và trần xanh
            color = (
                int(shade * 0.80),
                int(shade * 0.92),
                min(
                    210,
                    int(shade * 1.08) + 8
                )
            )

            # ======================================
            # DRAW WALL
            # ======================================

            # screen.fill nhanh hơn pygame.draw.rect cho hình chữ nhật đặc
            for x, w in self.col_pieces[i]:
                screen.fill(
                    color,
                    (x, top, w, wall_height)
                )