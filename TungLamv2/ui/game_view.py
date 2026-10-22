import pygame
import math
from game.map import line_blocked
from graphics.weapon_skins import get_viewmodel_parts, get_dropped_skin
from graphics.cs_viewmodel import CSViewModel

class GameView:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height
        self.cs_viewmodel = CSViewModel(width, height)
        self.muzzle_x = width // 2 + 80
        self.muzzle_y = height - 145
        self.muzzle_flash_timer = 0.0
        self.muzzle_flash_duration = 0.06
        self._vm_last = 0.0
        self._vm_last_angle = 0.0
        self._vm_last_pos = (0.0, 0.0)
        self._vm_sway = pygame.math.Vector2()
        self._vm_t = 0.0
        self.tracers = []
        self.tracer_duration = 90
        font_family = "segoeui,tahoma,arial"
        self.font_big = pygame.font.SysFont(font_family, 44, bold=True)
        self.font_mid = pygame.font.SysFont(font_family, 24, bold=True)
        self.font_small = pygame.font.SysFont(font_family, 20)
        self.font_victory = pygame.font.SysFont(font_family, 84, bold=True)
        self.font_hint = pygame.font.SysFont(font_family, 22)

    def spawn_tracer(self, end_pos):
        self.tracers.append({
            "end": end_pos or (self.width // 2, self.height // 2),
            "born": pygame.time.get_ticks(),
            "duration": self.tracer_duration
        })
        self.muzzle_flash_timer = self.muzzle_flash_duration

    def _draw_viewmodel(self, parts, player, reload_drop, side_sway):
        """Vẽ súng xoay quanh đầu nòng, neo ở dưới-phải tâm ngắm. Trả về vị trí đầu nòng trên màn hình."""
        img, pivot, base_angle, (ax, ay) = parts
        now = pygame.time.get_ticks() / 1000.0
        dt = min(0.1, max(0.0, now - self._vm_last)) if self._vm_last else 0.0
        self._vm_last = now

        # Sway trễ theo hướng xoay chuột
        dang = (player.angle - self._vm_last_angle + math.pi) % (2 * math.pi) - math.pi
        self._vm_last_angle = player.angle
        target = pygame.math.Vector2(-dang * 160, 0)
        target.x = max(-15, min(15, target.x))
        self._vm_sway = self._vm_sway.lerp(target, min(1.0, dt * 10))

        # Bob khi di chuyển
        moved = math.hypot(player.x - self._vm_last_pos[0], player.y - self._vm_last_pos[1])
        self._vm_last_pos = (player.x, player.y)
        moving = dt > 0 and moved / dt > 20
        if moving:
            self._vm_t += dt * 9
        bob = (pygame.math.Vector2(math.sin(self._vm_t) * 3, abs(math.cos(self._vm_t)) * 4)
               if moving else pygame.math.Vector2())

        # Giật theo recoil của player (0..0.14) -> 0..1
        kick = min(1.0, max(0.0, getattr(player, "recoil", 0.0)) / 0.14)
        recoil = pygame.math.Vector2(8, 12) * kick

        anchor = (pygame.math.Vector2(self.width * ax, self.height * ay)
                  + bob + self._vm_sway + recoil + (side_sway, reload_drop))
        angle = base_angle - 4 * kick  # âm = cùng chiều kim đồng hồ, tăng độ hếch nòng khi bắn

        rot = pygame.transform.rotozoom(img, angle, 1)
        # Xoay vector (tâm ảnh -> đầu nòng) giống cách pygame xoay ảnh (CCW, trục y hướng xuống)
        ox, oy = pivot[0] - img.get_width() / 2, pivot[1] - img.get_height() / 2
        a = math.radians(angle)
        rx = ox * math.cos(a) + oy * math.sin(a)
        ry = -ox * math.sin(a) + oy * math.cos(a)
        rect = rot.get_rect(center=(anchor.x - rx, anchor.y - ry))
        self.screen.blit(rot, rect)
        return int(anchor.x), int(anchor.y)

    def update_vfx(self, dt):
        if self.muzzle_flash_timer > 0:
            self.muzzle_flash_timer = max(0.0, self.muzzle_flash_timer - dt)

    def render_frame(self, player, enemies, walls, renderer, minimap, hud, horizon,
                     game_state, round_timer, buy_timer, player_score, enemy_score,
                     spike_carried, spike_planted, spike_timer, spike_max_time, hit_flash_timer, match_winner,
                     smokes=None, fires=None, bomb_fuse=None, dropped_weapons=None):
        # 1. Thế giới 3D Raycasting
        renderer.render(self.screen, player, walls)

        # 2. Danh sách đối tượng 3D (Địch, Vùng khói Smoke, Vùng lửa Bom xăng)
        vis = []
        for e in enemies:
            if not e.alive:
                continue
            dx, dy = e.x - player.x, e.y - player.y
            dist = math.hypot(dx, dy)
            if dist <= 0 or dist > 1800:
                continue
            ang = math.atan2(dy, dx)
            rel_ang = math.atan2(math.sin(ang - player.angle), math.cos(ang - player.angle))
            if abs(rel_ang) > renderer.fov / 2:
                continue
            if line_blocked(player.x, player.y, e.x, e.y):
                continue
            wall_dist = renderer.raycast(player, ang, walls)
            if dist >= wall_dist:
                continue
            sx = self.width / 2 + math.tan(rel_ang) * renderer.projection_plane
            size = max(10, min(400, int(renderer.projection_plane * 70 / dist)))
            vis.append(("enemy", dist, sx, size, e))

        # Thêm các vùng khói Smoke vào tầm nhìn 3D
        if smokes:
            for s in smokes:
                dx, dy = s["x"] - player.x, s["y"] - player.y
                dist = math.hypot(dx, dy)
                if dist <= 5 or dist > 1800:
                    continue
                ang = math.atan2(dy, dx)
                rel_ang = math.atan2(math.sin(ang - player.angle), math.cos(ang - player.angle))
                if abs(rel_ang) > renderer.fov / 2 + 0.4:
                    continue
                wall_dist = renderer.raycast(player, ang, walls)
                if dist >= wall_dist + 50:
                    continue
                sx = self.width / 2 + math.tan(rel_ang) * renderer.projection_plane
                rad = max(15, int(renderer.projection_plane * s.get("radius", 130) / dist))
                vis.append(("smoke", dist, sx, rad, s))

        # Thêm các vùng lửa Bom xăng vào tầm nhìn 3D
        if fires:
            for f in fires:
                dx, dy = f["x"] - player.x, f["y"] - player.y
                dist = math.hypot(dx, dy)
                if dist <= 5 or dist > 1800:
                    continue
                ang = math.atan2(dy, dx)
                rel_ang = math.atan2(math.sin(ang - player.angle), math.cos(ang - player.angle))
                if abs(rel_ang) > renderer.fov / 2 + 0.4:
                    continue
                wall_dist = renderer.raycast(player, ang, walls)
                if dist >= wall_dist + 50:
                    continue
                sx = self.width / 2 + math.tan(rel_ang) * renderer.projection_plane
                rad = max(12, int(renderer.projection_plane * f.get("radius", 95) / dist))
                vis.append(("fire", dist, sx, rad, f))

        # Thêm các vũ khí rơi trên sàn vào tầm nhìn 3D
        if dropped_weapons:
            for dw in dropped_weapons:
                dx, dy = dw["x"] - player.x, dw["y"] - player.y
                dist = math.hypot(dx, dy)
                if dist <= 5 or dist > 1400:
                    continue
                ang = math.atan2(dy, dx)
                rel_ang = math.atan2(math.sin(ang - player.angle), math.cos(ang - player.angle))
                if abs(rel_ang) > renderer.fov / 2 + 0.3:
                    continue
                wall_dist = renderer.raycast(player, ang, walls)
                if dist >= wall_dist:
                    continue
                sx = self.width / 2 + math.tan(rel_ang) * renderer.projection_plane
                gw = max(18, min(140, int(renderer.projection_plane * 48 / dist)))
                gh = max(6, int(gw * 0.32))
                vis.append(("dropped_weapon", dist, sx, gw, gh, dw))

        # Sắp xếp từ xa đến gần
        vis.sort(reverse=True, key=lambda x: x[1])

        for item in vis:
            itype = item[0]
            if itype == "enemy":
                _, dist, sx, size, e = item
                bw, bh = max(8, int(size * 0.45)), size
                btop = horizon + int(bh * 0.5) - bh

                head_h = max(3, int(bh * 0.22))
                body_h = max(4, int(bh * 0.43))
                leg_h = max(3, bh - head_h - body_h)

                head_y = btop
                body_y = btop + head_h
                leg_y = body_y + body_h

                # --- 1. CHÂN (LEGS) ---
                leg_w = max(2, int(bw * 0.38))
                gap = max(1, int(bw * 0.08))
                pygame.draw.rect(self.screen, (40, 44, 52), (int(sx - leg_w - gap // 2), int(leg_y), leg_w, leg_h))
                pygame.draw.rect(self.screen, (40, 44, 52), (int(sx + gap // 2), int(leg_y), leg_w, leg_h))
                boot_h = max(2, int(leg_h * 0.25))
                pygame.draw.rect(self.screen, (20, 20, 25), (int(sx - leg_w - gap // 2), int(leg_y + leg_h - boot_h), leg_w, boot_h))
                pygame.draw.rect(self.screen, (20, 20, 25), (int(sx + gap // 2), int(leg_y + leg_h - boot_h), leg_w, boot_h))

                # --- 2. THÂN / NGƯỜI (BODY) ---
                pygame.draw.rect(self.screen, (185, 45, 55), (int(sx - bw / 2), int(body_y), bw, body_h), border_radius=max(1, int(bw * 0.1)))
                vest_w = max(4, int(bw * 0.72))
                vest_h = max(3, int(body_h * 0.68))
                pygame.draw.rect(self.screen, (55, 60, 72), (int(sx - vest_w / 2), int(body_y + 2), vest_w, vest_h), border_radius=2)

                # --- 3. ĐẦU (HEAD) ---
                hr = max(4, int(head_h * 0.48))
                head_cx = int(sx)
                head_cy = int(head_y + hr)
                pygame.draw.circle(self.screen, (230, 185, 145), (head_cx, head_cy), hr)
                pygame.draw.circle(self.screen, (45, 50, 60), (head_cx, head_cy - 1), hr, draw_top_left=True, draw_top_right=True)
                visor_w = max(3, int(hr * 1.2))
                visor_h = max(2, int(hr * 0.35))
                pygame.draw.rect(self.screen, (30, 30, 35), (head_cx - visor_w // 2, head_cy - visor_h // 2, visor_w, visor_h))
                pygame.draw.circle(self.screen, (240, 60, 60), (head_cx, head_cy), max(1, int(hr * 0.2)))

                # --- THANH MÁU & GIÁP ---
                bar_w = max(25, int(size * 0.8))
                bx = int(sx - bar_w / 2)
                by = int(btop - 18)
                pygame.draw.rect(self.screen, (15, 18, 22), (bx - 1, by - 1, bar_w + 2, 7), border_radius=2)
                pygame.draw.rect(self.screen, (60, 220, 100), (bx, by, int(bar_w * max(0, e.hp) / 100), 5), border_radius=1)
                if getattr(e, "armor", 0) > 0:
                    pygame.draw.rect(self.screen, (70, 150, 240), (bx, by - 4, int(bar_w * min(1.0, e.armor / 50)), 3), border_radius=1)

                now_ms = pygame.time.get_ticks()
                if hasattr(e, "last_hit_time") and now_ms - e.last_hit_time < 900:
                    p_text = getattr(e, "last_hit_part", "body").upper()
                    dmg_val = getattr(e, "last_hit_damage", 0)
                    txt_col = (255, 60, 60) if p_text == "HEAD" else ((240, 200, 70) if p_text == "BODY" else (180, 190, 210))
                    hit_surf = self.font_small.render(f"{p_text} -{int(dmg_val)}", True, txt_col)
                    self.screen.blit(hit_surf, (sx - hit_surf.get_width() // 2, by - 20))

            elif itype == "smoke":
                _, dist, sx, rad, s = item
                s_rad = min(self.width // 2, rad)
                smoke_surf = pygame.Surface((s_rad * 2, s_rad * 2), pygame.SRCALPHA)
                for ox_f, oy_f, r_f, col in [
                    (0.0, 0.0, 0.95, (135, 140, 150, 175)),
                    (-0.35, -0.2, 0.75, (160, 165, 175, 155)),
                    (0.35, -0.2, 0.75, (115, 120, 130, 165)),
                    (-0.2, 0.25, 0.70, (140, 145, 155, 150)),
                    (0.2, 0.25, 0.70, (125, 130, 140, 160)),
                ]:
                    px = int(s_rad + ox_f * s_rad * 0.4)
                    py = int(s_rad + oy_f * s_rad * 0.4)
                    pr = max(4, int(s_rad * r_f))
                    pygame.draw.circle(smoke_surf, col, (px, py), pr)
                sy = horizon - s_rad // 3
                self.screen.blit(smoke_surf, (int(sx - s_rad), int(sy - s_rad)))

            elif itype == "fire":
                _, dist, sx, rad, f = item
                f_rad = min(self.width // 3, rad)
                t_ms = pygame.time.get_ticks()
                f_surf = pygame.Surface((f_rad * 2, f_rad * 2), pygame.SRCALPHA)
                for flame_i in range(5):
                    fx_off = int((flame_i - 2) * f_rad * 0.35)
                    f_h = int(f_rad * (0.6 + 0.4 * math.sin(t_ms * 0.018 + flame_i * 1.5)))
                    flame_pts = [
                        (f_rad + fx_off - f_rad // 4, f_rad * 2 - 4),
                        (f_rad + fx_off + f_rad // 4, f_rad * 2 - 4),
                        (f_rad + fx_off, max(2, f_rad * 2 - 4 - f_h))
                    ]
                    col = (255, 180, 30, 220) if flame_i % 2 == 0 else (240, 60, 20, 200)
                    pygame.draw.polygon(f_surf, col, flame_pts)
                    pygame.draw.circle(f_surf, (255, 230, 70, 230), (f_rad + fx_off, f_rad * 2 - 8), max(2, f_rad // 6))
                sy = horizon + f_rad // 3
                self.screen.blit(f_surf, (int(sx - f_rad), int(sy - f_rad * 2)))

            elif itype == "dropped_weapon":
                _, dist, sx, gw, gh, dw = item
                floor_y = horizon + int(renderer.projection_plane * 35 / dist)
                sw, sh = int(gw * 1.1), max(4, int(gh * 0.75))
                s_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
                pygame.draw.ellipse(s_surf, (10, 12, 16, 170), (0, 0, sw, sh))
                self.screen.blit(s_surf, (int(sx - sw / 2), int(floor_y - 2)))

                d_skin = get_dropped_skin(dw.get("id"), gw, gh)
                if d_skin is not None:
                    self.screen.blit(d_skin, (int(sx - gw / 2), int(floor_y - gh)))
                else:
                    w_rect = pygame.Rect(int(sx - gw / 2), int(floor_y - gh), gw, gh)
                    pygame.draw.rect(self.screen, (32, 35, 42), w_rect, border_radius=max(1, gh // 4))
                    pygame.draw.rect(self.screen, (220, 185, 60), w_rect, max(1, gh // 6), border_radius=max(1, gh // 4))

                if dist < 450:
                    badge_text = f"{dw.get('id', '')} ({dw.get('magazine', 0)}/{dw.get('reserve', 0)})"
                    badge_surf = self.font_small.render(badge_text, True, (255, 255, 255))
                    bw = badge_surf.get_width() + 10
                    bh = badge_surf.get_height() + 2
                    bx = int(sx - bw / 2)
                    by = int(floor_y - gh - bh - 6)
                    bg_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
                    bg_surf.fill((18, 22, 28, 210))
                    pygame.draw.rect(bg_surf, (220, 185, 60, 220), (0, 0, bw, bh), 1, border_radius=3)
                    self.screen.blit(bg_surf, (bx, by))
                    self.screen.blit(badge_surf, (bx + 5, by + 1))

        # 3. Vũ khí, Trang bị ném & Hoạt ảnh Nạp đạn
        now_sec = pygame.time.get_ticks() / 1000.0
        reload_drop = 0
        reload_progress = 0.0

        if getattr(player, "reloading", False):
            elapsed = now_sec - getattr(player, "reload_start", 0)
            reload_progress = min(1.0, elapsed / max(0.1, getattr(player, "reload_time", 1.8)))
            reload_drop = int(math.sin(reload_progress * math.pi) * 110)
            side_sway = int(math.sin(reload_progress * math.pi * 2) * 18)
        else:
            side_sway = 0

        wy = self.height - 145 + reload_drop
        gun_x = self.width // 2 + 80 + side_sway

        # Cập nhật chuyển động quán tính và bobbing viewmodel
        self.cs_viewmodel.update(1.0 / 60.0, player)
        righthand = getattr(player, "righthand", True)

        # Vẽ Viewmodel trên tay theo loại vũ khí / trang bị
        cur_w = getattr(player, "weapon", "")
        is_scoped = getattr(player, "scoped", False)

        if cur_w not in ("SMOKE", "MOLOTOV", "BOMB"):
            if is_scoped:
                # Khi đang bật kính ngắm (ADS / Scope), ẩn thân súng để tầm nhìn ngắm chuẩn xác
                self.muzzle_x = self.width // 2
                self.muzzle_y = self.height // 2
            else:
                self.muzzle_x, self.muzzle_y = self.cs_viewmodel.draw(
                    self.screen, player, reload_drop, side_sway
                )

        elif cur_w == "SMOKE":
            # Quả Smoke trên tay (bên phải hoặc trái theo righthand)
            gx = (self.width // 2 + 120) if righthand else (self.width // 2 - 166)
            gy = self.height - 130
            pygame.draw.rect(self.screen, (75, 80, 90), (gx, gy, 46, 75), border_radius=6)
            pygame.draw.rect(self.screen, (240, 210, 50), (gx, gy + 20, 46, 12))
            pygame.draw.rect(self.screen, (50, 55, 62), (gx + 14, gy - 16, 18, 18), border_radius=3)
            pygame.draw.circle(self.screen, (200, 200, 210), (gx + 10, gy - 8), 7, 2)
            lbl = self.font_small.render("SMOKE", True, (240, 240, 245))
            self.screen.blit(lbl, (gx - 5, gy + 36))

        elif cur_w == "MOLOTOV":
            # Chai Bom xăng trên tay
            gx = (self.width // 2 + 120) if righthand else (self.width // 2 - 166)
            gy = self.height - 140
            pygame.draw.rect(self.screen, (40, 110, 70), (gx + 6, gy + 25, 42, 70), border_radius=8)
            pygame.draw.rect(self.screen, (40, 110, 70), (gx + 20, gy, 14, 28))
            pygame.draw.rect(self.screen, (200, 190, 170), (gx + 18, gy - 8, 18, 12))
            fl_sz = int(12 + 5 * math.sin(pygame.time.get_ticks() * 0.02))
            pygame.draw.circle(self.screen, (255, 120, 20), (gx + 27, gy - 16), fl_sz)
            pygame.draw.circle(self.screen, (255, 230, 40), (gx + 27, gy - 16), max(2, fl_sz // 2))
            lbl = self.font_small.render("MOLOTOV", True, (255, 200, 60))
            self.screen.blit(lbl, (gx - 12, gy + 45))

        elif cur_w == "BOMB":
            # Quả bom hẹn giờ trên tay
            gx = (self.width // 2 + 130) if righthand else (self.width // 2 - 170)
            gy = self.height - 110
            pygame.draw.circle(self.screen, (32, 35, 42), (gx + 20, gy + 20), 40)
            pygame.draw.circle(self.screen, (60, 65, 75), (gx + 12, gy + 12), 12)
            pygame.draw.rect(self.screen, (10, 12, 16), (gx - 2, gy + 8, 44, 22), border_radius=4)
            f_val = f"{max(0.0, bomb_fuse):.1f}s" if (bomb_fuse is not None and bomb_fuse > 0) else "5.0s"
            t_col = (255, 40, 40) if (pygame.time.get_ticks() // 200) % 2 == 0 else (255, 180, 40)
            digi = self.font_small.render(f_val, True, t_col)
            self.screen.blit(digi, (gx + 20 - digi.get_width() // 2, gy + 11))

        # 4. Tia đạn (Tracers)
        now = pygame.time.get_ticks()
        for t in self.tracers[:]:
            age = now - t["born"]
            if age > t["duration"]: self.tracers.remove(t); continue
            prog = age / t["duration"]
            bx = self.muzzle_x + (t["end"][0] - self.muzzle_x) * prog
            by = self.muzzle_y + (t["end"][1] - self.muzzle_y) * prog
            trail = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.line(trail, (255, 235, 160, max(0, 255 - int(255 * prog))), (self.muzzle_x, self.muzzle_y), (bx, by), 2)
            self.screen.blit(trail, (0, 0))
            pygame.draw.circle(self.screen, (255, 255, 225), (int(bx), int(by)), 3)

        # 5. Lửa đầu nòng (Muzzle flash)
        if self.muzzle_flash_timer > 0:
            dur = max(0.001, getattr(self, "muzzle_flash_duration", 0.06))
            ratio = max(0.0, min(1.0, self.muzzle_flash_timer / dur))
            sz = int(10 + 22 * ratio)
            fl = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
            alpha = max(0, min(255, int(255 * ratio)))
            pygame.draw.circle(fl, (255, 225, 140, alpha), (sz, sz), sz)
            self.screen.blit(fl, (self.muzzle_x - sz, self.muzzle_y - sz))

        # 6. Tâm ngắm (Crosshair) & HUD
        cx, cy, gap = self.width // 2, self.height // 2, 7 + int(player.recoil * 100)
        for p1, p2 in [((cx - gap - 8, cy), (cx - gap, cy)), ((cx + gap, cy), (cx + gap + 8, cy)), ((cx, cy - gap - 8), (cx, cy - gap)), ((cx, cy + gap), (cx, cy + gap + 8))]:
            pygame.draw.line(self.screen, (245, 245, 245), p1, p2, 2)
        hud.draw(self.screen, player, player_score, enemy_score, round_timer)

        # Hiển thị Thanh tiến trình Nạp đạn (Reload Progress Bar)
        if getattr(player, "reloading", False):
            bar_w, bar_h = 160, 10
            bx = self.width // 2 - bar_w // 2
            by = cy + 45
            pygame.draw.rect(self.screen, (15, 20, 25), (bx - 2, by - 2, bar_w + 4, bar_h + 4), border_radius=5)
            pygame.draw.rect(self.screen, (60, 65, 75), (bx, by, bar_w, bar_h), border_radius=4)
            fill_w = int(bar_w * reload_progress)
            pygame.draw.rect(self.screen, (0, 230, 255), (bx, by, fill_w, bar_h), border_radius=4)
            r_text = self.font_small.render(f"RELOADING... {int(reload_progress * 100)}%", True, (0, 240, 255))
            self.screen.blit(r_text, (self.width // 2 - r_text.get_width() // 2, by + 16))
        elif player.magazine == 0 and cur_w in ("CLASSIC", "GHOST", "SHERIFF", "MP5", "UMP", "M014", "MAG-7", "AK-47", "VANDAL", "M416", "GUARDIAN", "M24", "AWM"):
            pulse = (pygame.time.get_ticks() // 250) % 2 == 0
            if pulse:
                alert_text = self.font_small.render("NO AMMO - PRESS [R] TO RELOAD", True, (255, 60, 70))
                self.screen.blit(alert_text, (self.width // 2 - alert_text.get_width() // 2, cy + 45))

        # Cảnh báo quả bom hẹn giờ 5s đếm ngược
        if bomb_fuse is not None and bomb_fuse > 0:
            pulse = (pygame.time.get_ticks() // 180) % 2 == 0
            box_col = (220, 30, 40) if pulse else (140, 15, 20)
            bw, bh = 340, 44
            bx = self.width // 2 - bw // 2
            by = 175
            pygame.draw.rect(self.screen, (10, 5, 5), (bx - 2, by - 2, bw + 4, bh + 4), border_radius=8)
            pygame.draw.rect(self.screen, box_col, (bx, by, bw, bh), border_radius=6)
            w_txt = self.font_mid.render(f"BOM SẼ NỔ TRONG: {max(0.0, bomb_fuse):.1f}s", True, (255, 255, 255))
            self.screen.blit(w_txt, (self.width // 2 - w_txt.get_width() // 2, by + 10))

        # 7. Giao diện Spike
        if spike_carried:
            self.screen.blit(self.font_mid.render("ĐANG GIỮ SPIKE", True, (240, 210, 70)), (24, 85))
        elif spike_planted:
            s_txt = self.font_mid.render(f"SPIKE NỔ SAU {max(0, spike_max_time - spike_timer):.1f}s", True, (220, 60, 70))
            self.screen.blit(s_txt, (self.width // 2 - s_txt.get_width() // 2, 130))

        # 8. Giao diện Mua sắm (Buy Phase) - Đặt ở tầng y=170 tách biệt khỏi Header tỷ số
        if game_state == "BUY":
            ov = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 75))
            self.screen.blit(ov, (0, 0))

            t1 = self.font_big.render("GIAI ĐOẠN MUA SẮM", True, (245, 245, 245))
            self.screen.blit(t1, (self.width // 2 - t1.get_width() // 2, 170))

            t2 = self.font_mid.render(f"Bắt đầu sau: {max(0, int(buy_timer))} giây", True, (255, 215, 60))
            self.screen.blit(t2, (self.width // 2 - t2.get_width() // 2, 225))

            t3 = self.font_small.render("Ấn [B] để mở Cửa hàng mua vũ khí & trang bị", True, (215, 220, 230))
            self.screen.blit(t3, (self.width // 2 - t3.get_width() // 2, 260))

        # 9. Màn hình nhấp nháy đỏ khi bị bắn trúng
        if hit_flash_timer > 0:
            hov = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            hov.fill((200, 30, 30, int(120 * (hit_flash_timer / 0.15))))
            self.screen.blit(hov, (0, 0))

        # 10. Minimap (truyền game_state để ẩn kẻ địch trong Buy Phase hoặc khi bị khuất tường)
        minimap.draw(
            self.screen, player, enemies, walls,
            smokes=smokes, fires=fires, dropped_weapons=dropped_weapons,
            game_state=game_state
        )

        # 11. Màn hình Kết thúc trận đấu (Match Over)
        if game_state == "MATCH_OVER":
            mov = pygame.Surface((self.width, self.height), pygame.SRCALPHA); mov.fill((5, 8, 12, 210)); self.screen.blit(mov, (0, 0))
            vic = self.font_victory.render("VICTORY" if match_winner == "PLAYER" else "DEFEAT", True, (90, 230, 150) if match_winner == "PLAYER" else (220, 60, 70))
            self.screen.blit(vic, (self.width // 2 - vic.get_width() // 2, self.height // 2 - 120))
            sc = self.font_hint.render(f"{player_score} - {enemy_score}", True, (235, 235, 235))
            self.screen.blit(sc, (self.width // 2 - sc.get_width() // 2, self.height // 2))
            h_txt = self.font_hint.render("Nhấn F12 để chụp ảnh | Nhấn ENTER để chơi lại", True, (170, 175, 180))
            self.screen.blit(h_txt, (self.width // 2 - h_txt.get_width() // 2, self.height // 2 + 60))
