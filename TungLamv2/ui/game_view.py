"""ui/game_view.py - Quản lý dựng khung hình 3D (Kẻ địch, Zombie, Hộp tiếp tế, Vũ khí rơi & VFX tối ưu)."""
import math
import pygame

from font_vn import get_font
from game.data import SUPPLY_TYPES
from game.map import line_blocked, check_smoke_blocks
from graphics.weapon_skins import get_dropped_skin
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
        self.tracers = []
        self.tracer_duration = 85

        self.font_big = get_font(42, bold=True)
        self.font_mid = get_font(23, bold=True)
        self.font_small = get_font(18, bold=True)
        self.font_victory = get_font(76, bold=True)
        self.font_hint = get_font(22)

        # Cache sẵn các lớp phủ toàn màn hình (tránh cấp phát 5.7 MB mỗi frame trên Web)
        self._buy_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        self._buy_overlay.fill((0, 0, 0, 75))

        self._match_over_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        self._match_over_overlay.fill((5, 8, 12, 212))

        self._hit_overlay = pygame.Surface((width, height))
        self._hit_overlay.fill((205, 28, 32))

        self._muzzle_cache = {}
        self._shadow_cache = {}

    def spawn_tracer(self, end_pos):
        self.tracers.append({
            "end": end_pos or (self.width // 2, self.height // 2),
            "born": pygame.time.get_ticks(),
            "duration": self.tracer_duration,
        })
        self.muzzle_flash_timer = self.muzzle_flash_duration

    def update_vfx(self, dt):
        if self.muzzle_flash_timer > 0:
            self.muzzle_flash_timer = max(0.0, self.muzzle_flash_timer - dt)

    def _get_drop_shadow(self, w, h):
        qw = max(8, (w // 4) * 4)
        qh = max(4, (h // 2) * 2)
        key = (qw, qh)
        s = self._shadow_cache.get(key)
        if s is None:
            if len(self._shadow_cache) > 48:
                self._shadow_cache.clear()
            s = pygame.Surface((qw, qh), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (10, 12, 16, 170), (0, 0, qw, qh))
            self._shadow_cache[key] = s
        return s

    def render_frame(
        self,
        player,
        enemies,
        walls,
        renderer,
        minimap,
        hud,
        horizon,
        game_state,
        round_timer,
        buy_timer,
        player_score,
        enemy_score,
        dt=1.0 / 60.0,
        hit_flash_timer=0,
        match_winner=None,
        smokes=None,
        fires=None,
        bomb_fuse=None,
        dropped_weapons=None,
        supply_drops=None,
        header_title=None,
        header_sub=None,
        buy_subtitle=None,
        match_summary=None,
    ):
        # 1. Dựng thế giới 3D Raycasting (cập nhật luôn renderer.z_buffer)
        renderer.render(self.screen, player, walls)

        # 2. Thu thập các thực thể 3D trong góc nhìn (dùng z_buffer O(1) thay vì raycast lặp lại)
        vis = []
        px, py = player.x, player.y
        p_ang = player.angle
        half_fov = renderer.fov * 0.5
        proj_plane = renderer.projection_plane
        ray_w = renderer.ray_width
        z_buf = renderer.z_buffer
        n_rays = renderer.num_rays

        for e in enemies:
            if not e.alive:
                continue
            dx, dy = e.x - px, e.y - py
            dist = math.hypot(dx, dy)
            if dist <= 1.0 or dist > 1800.0:
                continue
            ang = math.atan2(dy, dx)
            rel_ang = math.atan2(math.sin(ang - p_ang), math.cos(ang - p_ang))
            if abs(rel_ang) > half_fov + 0.12:
                continue
            if check_smoke_blocks(px, py, e.x, e.y, smokes):
                continue
            sx = self.width * 0.5 + math.tan(rel_ang) * proj_plane
            col_idx = min(n_rays - 1, max(0, int(sx / ray_w)))
            corr_dist = dist * math.cos(rel_ang)
            if corr_dist >= z_buf[col_idx] + 18.0 and line_blocked(px, py, e.x, e.y, walls):
                continue
            w_h = getattr(e, "world_height", 70.0)
            size = max(10, min(460, int(proj_plane * w_h / dist)))
            vis.append(("enemy", dist, sx, size, e))

        if dropped_weapons:
            for dw in dropped_weapons:
                dx, dy = dw["x"] - px, dw["y"] - py
                dist = math.hypot(dx, dy)
                if dist <= 5.0 or dist > 1400.0:
                    continue
                ang = math.atan2(dy, dx)
                rel_ang = math.atan2(math.sin(ang - p_ang), math.cos(ang - p_ang))
                if abs(rel_ang) > half_fov + 0.25:
                    continue
                sx = self.width * 0.5 + math.tan(rel_ang) * proj_plane
                col_idx = min(n_rays - 1, max(0, int(sx / ray_w)))
                if dist * math.cos(rel_ang) >= z_buf[col_idx] + 12.0:
                    continue
                gw = max(18, min(140, int(proj_plane * 48 / dist)))
                gh = max(6, int(gw * 0.32))
                vis.append(("dropped_weapon", dist, sx, gw, gh, dw))

        if supply_drops:
            now_t = pygame.time.get_ticks() * 0.004
            for sd in supply_drops:
                dx, dy = sd["x"] - px, sd["y"] - py
                dist = math.hypot(dx, dy)
                if dist <= 5.0 or dist > 1450.0:
                    continue
                ang = math.atan2(dy, dx)
                rel_ang = math.atan2(math.sin(ang - p_ang), math.cos(ang - p_ang))
                if abs(rel_ang) > half_fov + 0.25:
                    continue
                sx = self.width * 0.5 + math.tan(rel_ang) * proj_plane
                col_idx = min(n_rays - 1, max(0, int(sx / ray_w)))
                if dist * math.cos(rel_ang) >= z_buf[col_idx] + 14.0:
                    continue
                box_sz = max(12, min(92, int(proj_plane * 30 / dist)))
                bob = int(math.sin(now_t + sd["x"] * 0.05) * max(2, box_sz // 6))
                vis.append(("supply", dist, sx, box_sz, bob, sd))

        vis.sort(reverse=True, key=lambda x: x[1])

        for item in vis:
            itype = item[0]
            if itype == "enemy":
                _, dist, sx, size, e = item
                bw, bh = max(8, int(size * 0.45)), size
                foot_y = horizon + int(proj_plane * 35.0 / max(dist, 1.0))
                btop = foot_y - bh
                e.draw_roblox_3d(
                    self.screen, sx, btop, bw, bh, self.font_small,
                    player=player, renderer=renderer, horizon=horizon,
                )

            elif itype == "dropped_weapon":
                _, dist, sx, gw, gh, dw = item
                floor_y = horizon + int(proj_plane * 35 / dist)
                s_surf = self._get_drop_shadow(int(gw * 1.1), max(4, int(gh * 0.75)))
                self.screen.blit(s_surf, (int(sx - s_surf.get_width() // 2), int(floor_y - 2)))

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
                    bw_b = badge_surf.get_width() + 10
                    bh_b = badge_surf.get_height() + 4
                    bx = int(sx - bw_b / 2)
                    by = int(floor_y - gh - bh_b - 6)
                    pygame.draw.rect(self.screen, (18, 22, 28), (bx, by, bw_b, bh_b), border_radius=4)
                    pygame.draw.rect(self.screen, (220, 185, 60), (bx, by, bw_b, bh_b), 1, border_radius=4)
                    self.screen.blit(badge_surf, (bx + 5, by + 2))

            elif itype == "supply":
                _, dist, sx, box_sz, bob, sd = item
                info = SUPPLY_TYPES.get(sd["kind"], SUPPLY_TYPES["MEDKIT"])
                floor_y = horizon + int(proj_plane * 35 / dist)
                s_surf = self._get_drop_shadow(int(box_sz * 1.25), max(4, box_sz // 3))
                self.screen.blit(s_surf, (int(sx - s_surf.get_width() // 2), int(floor_y - 2)))

                bx = int(sx - box_sz // 2)
                by = int(floor_y - box_sz - 6 + bob)
                col = info["color"]
                top_col = (min(255, col[0] + 45), min(255, col[1] + 45), min(255, col[2] + 45))
                lid_h = max(3, box_sz // 4)
                pygame.draw.polygon(self.screen, top_col, [
                    (bx + lid_h, by - lid_h),
                    (bx + box_sz + lid_h, by - lid_h),
                    (bx + box_sz, by),
                    (bx, by),
                ])
                box_rect = pygame.Rect(bx, by, box_sz, box_sz)
                pygame.draw.rect(self.screen, col, box_rect, border_radius=max(2, box_sz // 6))
                pygame.draw.rect(self.screen, info["border"], box_rect, 2, border_radius=max(2, box_sz // 6))

                if sd["kind"] == "MEDKIT" and box_sz >= 14:
                    cw = max(2, box_sz // 5)
                    cl = max(6, int(box_sz * 0.56))
                    ccx, ccy = box_rect.centerx, box_rect.centery
                    pygame.draw.rect(self.screen, (255, 255, 255), (ccx - cw // 2, ccy - cl // 2, cw, cl))
                    pygame.draw.rect(self.screen, (255, 255, 255), (ccx - cl // 2, ccy - cw // 2, cl, cw))

                if dist < 520:
                    lbl = self.font_small.render(info["short"], True, info["border"])
                    self.screen.blit(lbl, (int(sx - lbl.get_width() // 2), by - lid_h - lbl.get_height() - 2))

        # 3. Vũ khí trên tay & hoạt ảnh nạp đạn
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

        self.cs_viewmodel.update(dt, player)
        self.muzzle_x, self.muzzle_y = self.cs_viewmodel.draw(
            self.screen, player, reload_drop, side_sway, bomb_fuse
        )

        # 4. Tia đạn (vẽ trực tiếp, không tạo Surface toàn màn hình!)
        now = pygame.time.get_ticks()
        for t in self.tracers[:]:
            age = now - t["born"]
            if age > t["duration"]:
                self.tracers.remove(t)
                continue
            prog = age / float(t["duration"])
            p0_prog = max(0.0, prog - 0.35)
            x1 = int(self.muzzle_x + (t["end"][0] - self.muzzle_x) * p0_prog)
            y1 = int(self.muzzle_y + (t["end"][1] - self.muzzle_y) * p0_prog)
            x2 = int(self.muzzle_x + (t["end"][0] - self.muzzle_x) * prog)
            y2 = int(self.muzzle_y + (t["end"][1] - self.muzzle_y) * prog)
            pygame.draw.line(self.screen, (255, 232, 145), (x1, y1), (x2, y2), 2)
            pygame.draw.circle(self.screen, (255, 255, 225), (x2, y2), 3)

        # 5. Lửa đầu nòng (cache theo kích thước)
        if self.muzzle_flash_timer > 0:
            dur = max(0.001, self.muzzle_flash_duration)
            ratio = max(0.0, min(1.0, self.muzzle_flash_timer / dur))
            sz = max(8, (int(10 + 22 * ratio) // 2) * 2)
            alpha = max(40, (int(240 * ratio) // 30) * 30)
            mkey = (sz, alpha)
            fl = self._muzzle_cache.get(mkey)
            if fl is None:
                fl = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
                pygame.draw.circle(fl, (255, 225, 140, alpha), (sz, sz), sz)
                self._muzzle_cache[mkey] = fl
            self.screen.blit(fl, (self.muzzle_x - sz, self.muzzle_y - sz))

        # 6. Tâm ngắm & HUD
        cx, cy = self.width // 2, self.height // 2
        gap = 7 + int(player.recoil * 100)
        if getattr(player, "ads", 0.0) < 0.5:
            for p1, p2 in (
                ((cx - gap - 8, cy), (cx - gap, cy)),
                ((cx + gap, cy), (cx + gap + 8, cy)),
                ((cx, cy - gap - 8), (cx, cy - gap)),
                ((cx, cy + gap), (cx, cy + gap + 8)),
            ):
                pygame.draw.line(self.screen, (245, 245, 245), p1, p2, 2)

        hud.draw(
            self.screen, player, player_score, enemy_score, round_timer,
            header_title=header_title, header_sub=header_sub,
        )

        # Thanh tiến trình nạp đạn
        cur_w = getattr(player, "weapon", "")
        if getattr(player, "reloading", False):
            bar_w, bar_h = 160, 10
            bx = cx - bar_w // 2
            by = cy + 45
            pygame.draw.rect(self.screen, (15, 20, 25), (bx - 2, by - 2, bar_w + 4, bar_h + 4), border_radius=5)
            pygame.draw.rect(self.screen, (60, 65, 75), (bx, by, bar_w, bar_h), border_radius=4)
            pygame.draw.rect(self.screen, (0, 230, 255), (bx, by, int(bar_w * reload_progress), bar_h), border_radius=4)
            r_text = self.font_small.render(f"ĐANG NẠP ĐẠN... {int(reload_progress * 100)}%", True, (0, 240, 255))
            self.screen.blit(r_text, (cx - r_text.get_width() // 2, by + 16))
        elif player.magazine == 0 and cur_w not in ("KNIFE", "SMOKE", "MOLOTOV", "BOMB", ""):
            if (pygame.time.get_ticks() // 250) % 2 == 0:
                alert_text = self.font_small.render("HẾT ĐẠN - BẤM [R] ĐỂ NẠP", True, (255, 65, 75))
                self.screen.blit(alert_text, (cx - alert_text.get_width() // 2, cy + 45))

        # Cảnh báo bom hẹn giờ trên tay
        if bomb_fuse is not None and bomb_fuse > 0:
            pulse = (pygame.time.get_ticks() // 180) % 2 == 0
            box_col = (220, 30, 40) if pulse else (140, 15, 20)
            bw_c, bh_c = 340, 44
            bx, by = cx - bw_c // 2, 175
            pygame.draw.rect(self.screen, (10, 5, 5), (bx - 2, by - 2, bw_c + 4, bh_c + 4), border_radius=8)
            pygame.draw.rect(self.screen, box_col, (bx, by, bw_c, bh_c), border_radius=6)
            w_txt = self.font_mid.render(f"BOM NỔ SAU: {max(0.0, bomb_fuse):.1f}s", True, (255, 255, 255))
            self.screen.blit(w_txt, (cx - w_txt.get_width() // 2, by + 10))

        # Màn chờ Mua sắm (Buy Phase)
        if game_state == "BUY":
            self.screen.blit(self._buy_overlay, (0, 0))
            title_str = buy_subtitle or "GIAI ĐOẠN MUA SẮM"
            t1 = self.font_big.render(title_str, True, (245, 245, 245))
            self.screen.blit(t1, (cx - t1.get_width() // 2, 165))
            t2 = self.font_mid.render(f"Bắt đầu sau: {max(0, int(buy_timer))}s", True, (255, 215, 60))
            self.screen.blit(t2, (cx - t2.get_width() // 2, 218))
            t3 = self.font_small.render("Bấm [B] mở Cửa hàng  ·  Bấm [N] vào trận ngay", True, (215, 225, 235))
            self.screen.blit(t3, (cx - t3.get_width() // 2, 252))

        # Chớp đỏ khi dính sát thương (dùng set_alpha trên Surface thường siêu nhẹ)
        if hit_flash_timer > 0:
            self._hit_overlay.set_alpha(min(140, int(125 * (hit_flash_timer / 0.15))))
            self.screen.blit(self._hit_overlay, (0, 0))

        # Minimap
        minimap.draw(
            self.screen, player, enemies, walls,
            smokes=smokes, fires=fires,
            dropped_weapons=dropped_weapons,
            supply_drops=supply_drops,
            game_state=game_state,
        )

        # Màn hình Kết thúc trận đấu
        if game_state == "MATCH_OVER":
            self.screen.blit(self._match_over_overlay, (0, 0))
            won = match_winner == "PLAYER"
            vic = self.font_victory.render(
                "CHIẾN THẮNG!" if won else "THẤT BẠI",
                True,
                (90, 230, 150) if won else (230, 65, 75),
            )
            self.screen.blit(vic, (cx - vic.get_width() // 2, cy - 125))
            summary_str = match_summary or f"Tỉ số: {player_score} - {enemy_score}"
            sc = self.font_hint.render(summary_str, True, (235, 238, 245))
            self.screen.blit(sc, (cx - sc.get_width() // 2, cy - 15))
            h_txt = self.font_hint.render("Bấm ENTER để Chơi lại  |  ESC về Menu chọn Map & Chế độ", True, (175, 185, 200))
            self.screen.blit(h_txt, (cx - h_txt.get_width() // 2, cy + 45))
