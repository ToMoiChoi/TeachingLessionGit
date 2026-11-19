import math
import random
import pygame
from font_vn import get_font
from config import CYBER_BLUE, CYBER_PINK, CYBER_YELLOW, DARK_BG, GREEN, RED, WHITE

ORANGE = (255, 140, 0)
PURPLE = (170, 120, 255)
FLOOR_Y = 380
WORLD_STATES = ("GAME", "LEVEL_CLEAR", "GAME_OVER", "PAUSED")


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width=120, height=15):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, screen, camera_x=0):
        render_rect = self.rect.move(-camera_x, 0)
        pygame.draw.rect(screen, (40, 50, 80), render_rect, border_radius=5)
        pygame.draw.rect(screen, CYBER_BLUE, render_rect, 2, border_radius=5)


def draw_star(screen, cx, cy, r, filled, color=CYBER_YELLOW):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
    if filled:
        pygame.draw.polygon(screen, color, pts)
    pygame.draw.polygon(screen, color if filled else (90, 90, 110), pts, 1 if filled else 2)


class LayoutRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = get_font(18, bold=True)
        self.small = get_font(14, bold=True)
        self.title_font = get_font(36, bold=True)
        self.big_font = get_font(64, bold=True)
        self.sub_font = get_font(20)
        self.num_font = get_font(16, bold=True)
        self.num_big = get_font(22, bold=True)
        # Bầu trời thành phố (vẽ 1 lần)
        self.skyline = self._make_skyline()

    def _make_skyline(self):
        rnd = random.Random(7)
        surf = pygame.Surface((1600, 300), pygame.SRCALPHA)
        x = 0
        while x < 1600:
            w = rnd.randint(40, 90)
            h = rnd.randint(60, 220)
            pygame.draw.rect(surf, (22, 22, 40), (x, 300 - h, w, h))
            for wy in range(300 - h + 8, 296, 14):
                for wx in range(x + 6, x + w - 6, 12):
                    if rnd.random() < 0.25:
                        c = rnd.choice([(0, 120, 140), (120, 0, 70), (120, 110, 0)])
                        pygame.draw.rect(surf, c, (wx, wy, 4, 5))
            x += w + rnd.randint(2, 10)
        return surf

    # ==================================================================
    # VẼ CHÍNH
    # ==================================================================
    def render(self, gameplay):
        gp = gameplay
        if gp.state not in WORLD_STATES:
            gp.menu.render(gp.state, gp)
            return

        if gp.mode == "STORY" and gp.current_level == 8:
            self.screen.fill((70, 5, 15))
        elif gp.mode == "ENDLESS":
            self.screen.fill((20, 8, 30))
        else:
            self.screen.fill(DARK_BG)
        sx = -(gp.camera_x * 0.3) % 800
        self.screen.blit(self.skyline, (sx - 800, FLOOR_Y - 300))

        self.draw_world(gp)

        # Rung màn hình: dịch toàn bộ thế giới (HUD vẽ sau nên không rung)
        if gp.shake > 0:
            s = int(gp.shake)
            self.screen.scroll(random.randint(-s, s), random.randint(-s, s))

        if gp.slow_timer > 0:
            tint = pygame.Surface((800, 500), pygame.SRCALPHA)
            tint.fill((90, 60, 200, 45))
            self.screen.blit(tint, (0, 0))
        if gp.hurt_flash > 0:
            self.draw_vignette((255, 0, 30), int(7 * gp.hurt_flash))

        self.draw_hud(gp)
        if gp.state == "GAME":
            gp.touch.draw(self.screen)

        if gp.state == "PAUSED":
            self.draw_pause(gp)
        elif gp.state == "LEVEL_CLEAR":
            self.draw_level_clear(gp)
        elif gp.state == "GAME_OVER":
            self.draw_game_over(gp)

    def draw_vignette(self, color, alpha):
        edge = pygame.Surface((800, 500), pygame.SRCALPHA)
        for i in range(14):
            a = max(0, alpha - i * alpha // 14)
            pygame.draw.rect(edge, (*color, a), (i * 3, i * 3, 800 - i * 6, 500 - i * 6), 3)
        self.screen.blit(edge, (0, 0))

    def draw_world(self, gp):
        cam_x = gp.camera_x
        scr = self.screen
        pygame.draw.rect(scr, (40, 40, 60), (-cam_x, FLOOR_Y, gp.level_width, 200))
        pygame.draw.line(scr, CYBER_BLUE, (-cam_x, FLOOR_Y), (gp.level_width - cam_x, FLOOR_Y), 2)

        for plat in gp.platforms:
            plat.draw(scr, cam_x)
        if gp.checkpoint:
            gp.checkpoint.draw(scr, cam_x)

        for p in gp.powerups:
            orig = p.rect
            p.rect = orig.move(-cam_x, 0)
            p.draw(scr)
            p.rect = orig
        for c in gp.coin_pickups:
            c.draw(scr, cam_x)

        for enemy in gp.enemies:
            if hasattr(enemy, "draw"):
                enemy.draw(scr, cam_x)
            else:
                scr.blit(enemy.image, enemy.rect.move(-cam_x, 0))

        boss = gp.boss_group.sprite
        if boss:
            if hasattr(boss, "draw"):
                boss.draw(scr, cam_x)
            else:
                scr.blit(boss.image, boss.rect.move(-cam_x, 0))

        for b in gp.player_bullets:
            ren = b.rect.move(-cam_x, 0)
            if getattr(b, "explosive", False):
                pygame.draw.circle(scr, (120, 255, 90), ren.center, 6)
                pygame.draw.circle(scr, (20, 60, 20), ren.center, 6, 2)
                if (b.spin // 4) % 2 == 0:
                    pygame.draw.circle(scr, RED, ren.center, 2)
            elif getattr(b, "image", None) is not None:
                scr.blit(b.image, ren)
            else:
                pygame.draw.rect(scr, getattr(b, "color", CYBER_YELLOW), ren)
        for b in gp.enemy_bullets:
            ren = b.rect.move(-cam_x, 0)
            if getattr(b, "image", None) is not None:
                scr.blit(b.image, ren)
            else:
                pygame.draw.rect(scr, RED, ren)

        # Laser
        for beam in gp.beams:
            a = beam["life"] / 10
            (x1, y1), (x2, y2) = beam["p1"], beam["p2"]
            p1, p2 = (x1 - cam_x, y1), (x2 - cam_x, y2)
            pygame.draw.line(scr, CYBER_BLUE, p1, p2, max(1, int(9 * a)))
            pygame.draw.line(scr, WHITE, p1, p2, max(1, int(3 * a)))

        # Vòng nổ
        for bl in gp.blasts:
            t = 1 - bl["life"] / 18
            r = int(bl["r"] * (0.3 + 0.7 * t))
            ring = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ring, (255, 160, 40, int(140 * (1 - t))), (r + 2, r + 2), r)
            pygame.draw.circle(ring, (255, 240, 180, int(255 * (1 - t))), (r + 2, r + 2), r, 3)
            scr.blit(ring, (bl["x"] - cam_x - r - 2, bl["y"] - r - 2))

        if gp.state != "GAME_OVER":     # đã nổ tung thì không vẽ nhân vật
            gp.player.draw(scr, cam_x)
            if gp.shield_timer > 0:
                pr = gp.player.rect.move(-cam_x, 0)
                blink = gp.shield_timer > 40 or (gp.shield_timer // 4) % 2 == 0
                if blink:
                    bubble = pygame.Surface((90, 90), pygame.SRCALPHA)
                    a = 60 + int(30 * math.sin(gp.frame * 0.2))
                    pygame.draw.circle(bubble, (0, 243, 255, a), (45, 45), 40)
                    pygame.draw.circle(bubble, (180, 250, 255, 200), (45, 45), 40, 2)
                    scr.blit(bubble, (pr.centerx - 45, pr.centery - 45))

        # Hạt hiệu ứng: [x, y, vx, vy, size, life, color]
        for pt in gp.particle_mgr.particles:
            if isinstance(pt, (list, tuple)) and len(pt) >= 7:
                pygame.draw.circle(scr, pt[6], (int(pt[0] - cam_x), int(pt[1])), max(1, int(pt[4])))

        # Số sát thương bay lên
        for f in gp.floaters:
            font = self.num_big if f["big"] else self.num_font
            t = font.render(f["text"], True, f["color"])
            sh = font.render(f["text"], True, (0, 0, 0))
            if f["life"] < 15:
                t.set_alpha(int(255 * f["life"] / 15))
                sh.set_alpha(int(180 * f["life"] / 15))
            x = int(f["x"] - cam_x - t.get_width() // 2)
            scr.blit(sh, (x + 1, int(f["y"]) + 1))
            scr.blit(t, (x, int(f["y"])))

    # ==================================================================
    # HUD
    # ==================================================================
    def draw_hud(self, gp):
        scr = self.screen
        p = gp.player

        # Thanh máu
        ratio = max(0, p.hp) / max(1, p.max_hp)
        pygame.draw.rect(scr, (20, 20, 35), (10, 10, 200, 18), border_radius=4)
        col = GREEN if ratio > 0.5 else (CYBER_YELLOW if ratio > 0.25 else RED)
        pygame.draw.rect(scr, col, (10, 10, int(200 * ratio), 18), border_radius=4)
        pygame.draw.rect(scr, WHITE, (10, 10, 200, 18), 1, border_radius=4)
        hp_t = self.small.render(f"HP {max(0, p.hp)}/{p.max_hp}", True, WHITE)
        scr.blit(hp_t, (16, 10))

        # Súng: các ô theo phím 1-5
        from weapon import WEAPON_KEYS, WEAPON_LIST
        x = 10
        for i, key in enumerate(WEAPON_KEYS):
            if key not in gp.weapons_owned:
                continue
            w = WEAPON_LIST[key]
            active = key == gp.current_weapon_key
            box = pygame.Rect(x, 34, 50, 30)
            pygame.draw.rect(scr, (40, 40, 70) if active else (20, 20, 35), box, border_radius=4)
            pygame.draw.rect(scr, CYBER_YELLOW if active else (70, 70, 90), box, 2 if active else 1, border_radius=4)
            icon = pygame.transform.scale(w.image, (38, max(8, int(38 * w.image.get_height() / w.image.get_width()))))
            scr.blit(icon, (box.centerx - icon.get_width() // 2, box.centery - icon.get_height() // 2 + 2))
            n = self.small.render(str(i + 1), True, CYBER_YELLOW if active else (140, 140, 160))
            scr.blit(n, (box.x + 3, box.y))
            x += 54
        w = gp.current_weapon
        ammo_col = ORANGE if w.ammo > 0 else RED
        scr.blit(self.small.render(f"{w.name}  {w.ammo}/{w.max_ammo}", True, ammo_col), (10, 67))

        # Coins + màn / wave
        scr.blit(self.small.render(f"Coins: {gp.coins}", True, CYBER_YELLOW), (10, 86))
        if gp.mode == "ENDLESS" and gp.endless:
            info = f"WAVE {gp.endless.wave}   ĐIỂM {gp.endless.score}"
            scr.blit(self.small.render(info, True, CYBER_PINK), (10, 104))
        else:
            secs = gp.level_frames // 60
            info = f"Level {gp.current_level}   {secs // 60:02d}:{secs % 60:02d}   Quái còn: {len(gp.enemies) + (1 if gp.boss_group.sprite else 0)}"
            scr.blit(self.small.render(info, True, CYBER_BLUE), (10, 104))

        # Kỹ năng (hồi chiêu)
        from game_engine_gameplay import DASH_CD, SHIELD_CD, SLOW_CD
        skills = [
            ("J", "KIẾM", 1 - p.slash_cooldown / max(1, p.slash_delay), CYBER_BLUE),
            ("Q", "LƯỚT", 1 - gp.dash_cooldown / DASH_CD, CYBER_PINK),
            ("E", "KHIÊN", 1 - gp.shield_cd / SHIELD_CD, CYBER_BLUE),
            ("F", "CHẬM", 1 - gp.slow_cd / SLOW_CD, PURPLE),
        ]
        for i, (key, name, r, c) in enumerate(skills):
            cx, cy = 26 + i * 40, 144
            ready = r >= 1
            pygame.draw.circle(scr, (20, 20, 35), (cx, cy), 16)
            if not ready:
                pygame.draw.arc(scr, c, (cx - 16, cy - 16, 32, 32), math.pi / 2, math.pi / 2 + 2 * math.pi * max(0, r), 3)
            else:
                pygame.draw.circle(scr, c, (cx, cy), 16, 2)
            t = self.small.render(key, True, WHITE if ready else (120, 120, 140))
            scr.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))

        # Thông báo buff bên phải
        buff_y = 10 if not gp.boss_group.sprite else 56
        for buff in gp.active_buffs:
            box_rect = pygame.Rect(600, buff_y, 190, 28)
            bg = pygame.Surface(box_rect.size, pygame.SRCALPHA)
            bg.fill((20, 20, 35, 210))
            scr.blit(bg, box_rect.topleft)
            pygame.draw.rect(scr, buff["color"], box_rect, 2, border_radius=6)
            t = self.small.render(buff["text"], True, buff["color"])
            scr.blit(t, (box_rect.centerx - t.get_width() // 2, box_rect.centery - t.get_height() // 2 - 1))
            r = buff["timer"] / buff["max_timer"]
            pygame.draw.line(scr, buff["color"], (box_rect.left + 4, box_rect.bottom - 3),
                             (box_rect.left + 4 + int(182 * r), box_rect.bottom - 3), 2)
            buff_y += 33

        # Thanh máu boss
        boss = gp.boss_group.sprite
        if boss and hasattr(boss, "draw_health_bar"):
            boss.draw_health_bar(scr, p)

        # Chế độ Vô Tận: banner wave + đếm ngược
        if gp.mode == "ENDLESS" and gp.endless and gp.state == "GAME":
            e = gp.endless
            if e.banner_timer > 0:
                a = min(1.0, e.banner_timer / 30)
                t = self.big_font.render(f"WAVE {e.wave}", True, CYBER_PINK)
                t.set_alpha(int(255 * a))
                scr.blit(t, (400 - t.get_width() // 2, 150))
                if e.wave % 5 == 0:
                    bt = self.font.render("BOSS XUẤT HIỆN!", True, ORANGE)
                    bt.set_alpha(int(255 * a))
                    scr.blit(bt, (400 - bt.get_width() // 2, 225))
            elif e.in_break:
                t = self.font.render(f"Wave tiếp theo sau {e.break_timer // 60 + 1}s", True, CYBER_YELLOW)
                scr.blit(t, (400 - t.get_width() // 2, 160))

    # ==================================================================
    # NÚT DÙNG CHUNG
    # ==================================================================
    def draw_buttons(self, gp, ready=True):
        mouse = pygame.mouse.get_pos()
        for key, rect, text, col in gp.overlay_buttons():
            hover = ready and rect.collidepoint(mouse)
            fill = (col[0] // 4, col[1] // 4, col[2] // 4) if hover else (20, 20, 35)
            pygame.draw.rect(self.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.screen, col if ready else (90, 90, 100), rect, 2, border_radius=8)
            lbl = self.font.render(text, True, col if ready else (110, 110, 120))
            self.screen.blit(lbl, (rect.centerx - lbl.get_width() // 2, rect.centery - lbl.get_height() // 2))

    def _dim(self, color, alpha):
        ov = pygame.Surface((800, 500), pygame.SRCALPHA)
        ov.fill((*color, alpha))
        self.screen.blit(ov, (0, 0))

    # ==================================================================
    # TẠM DỪNG
    # ==================================================================
    def draw_pause(self, gp):
        self._dim((5, 5, 15), 190)
        t = self.big_font.render("TẠM DỪNG", True, CYBER_BLUE)
        self.screen.blit(t, (400 - t.get_width() // 2, 70))
        where = f"Chế độ Vô Tận - Wave {gp.endless.wave}" if gp.mode == "ENDLESS" and gp.endless else f"Level {gp.current_level}"
        s = self.sub_font.render(where, True, (200, 200, 220))
        self.screen.blit(s, (400 - s.get_width() // 2, 150))
        lines = ["A/D chạy  •  W/Space nhảy  •  Chuột trái bắn  •  Chuột phải/J chém (phản đạn)",
                 "Q lướt  •  E khiên  •  F làm chậm thời gian  •  1-5 / lăn chuột đổi súng"]
        for i, line in enumerate(lines):
            l = self.small.render(line, True, (160, 160, 185))
            self.screen.blit(l, (400 - l.get_width() // 2, 200 + i * 24))
        self.draw_buttons(gp)

    # ==================================================================
    # QUA MÀN
    # ==================================================================
    def draw_level_clear(self, gp):
        st = gp.clear_stats
        t = gp.clear_timer
        self._dim((0, 10, 20), min(190, t * 8))
        box = pygame.Rect(170, 50, 460, 330)
        pygame.draw.rect(self.screen, (20, 20, 35), box, border_radius=15)
        pygame.draw.rect(self.screen, CYBER_BLUE, box, 3, border_radius=15)
        title = "PHÁ ĐẢO GAME!" if st.get("final") else "VICTORY!"
        tt = self.title_font.render(title, True, CYBER_YELLOW)
        self.screen.blit(tt, (400 - tt.get_width() // 2, 62))
        sub = self.sub_font.render(f"Màn {st.get('level')} hoàn thành", True, WHITE)
        self.screen.blit(sub, (400 - sub.get_width() // 2, 108))

        # Sao hiện lần lượt
        stars = st.get("stars", 1)
        for i in range(3):
            appear = t - 15 - i * 14
            filled = i < stars and appear > 0
            scale = 1.0 if appear > 8 or not filled else 1.6 - 0.6 * appear / 8
            draw_star(self.screen, 330 + i * 70, 170, int(24 * scale), filled)

        mins, secs = divmod(st.get("seconds", 0), 60)
        rows = [
            ("Hoàn thành màn", "+1 sao", CYBER_YELLOW),
            ("Không chết lần nào", "+1 sao" if st.get("deaths", 0) == 0 else f"chết {st.get('deaths')} lần",
             CYBER_YELLOW if st.get("deaths", 0) == 0 else RED),
            (f"Thời gian {mins:02d}:{secs:02d} (chuẩn {st.get('par')}s)",
             "+1 sao" if st.get("seconds", 999) <= st.get("par", 0) else "chậm",
             CYBER_YELLOW if st.get("seconds", 999) <= st.get("par", 0) else RED),
            ("Coins nhận được", f"+{st.get('earned', 0)}", CYBER_YELLOW),
        ]
        for i, (label, val, col) in enumerate(rows):
            y = 210 + i * 26
            self.screen.blit(self.font.render(label, True, (200, 200, 215)), (200, y))
            v = self.font.render(val, True, col)
            self.screen.blit(v, (600 - v.get_width(), y))
        if st.get("star_bonus"):
            b = self.small.render(f"Sao mới! Thưởng thêm +{st['star_bonus']} coins", True, GREEN)
            self.screen.blit(b, (400 - b.get_width() // 2, 318))
        if st.get("final"):
            b = self.small.render("Bạn đã hạ mọi boss. Thử chế độ Vô Tận hoặc độ khó KHÓ nhé!", True, CYBER_PINK)
            self.screen.blit(b, (400 - b.get_width() // 2, 340))
        self.draw_buttons(gp, gp.overlay_ready())

    # ==================================================================
    # MÀN HÌNH "BẠN ĐÃ CHẾT"
    # ==================================================================
    def draw_game_over(self, gp):
        sw, sh = self.screen.get_size()
        t = gp.death_timer
        fade = min(1.0, t / 40.0)

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((40, 0, 8, int(200 * fade)))
        for y in range(0, sh, 4):
            pygame.draw.line(overlay, (0, 0, 0, int(60 * fade)), (0, y), (sw, y))
        self.screen.blit(overlay, (0, 0))

        pulse = 0.5 + 0.5 * math.sin(t * 0.15)
        self.draw_vignette((255, 30, 50), int(90 * fade * (0.6 + 0.4 * pulse)))

        if t < 12:
            return

        drop = max(0.0, 1.0 - (t - 12) / 20.0)
        title_y = int(75 - 60 * drop * drop)
        title = "BẠN ĐÃ CHẾT"
        jitter = 6 if (t < 40 or random.random() < 0.06) else 0
        cx = sw // 2
        for color, ox in ((CYBER_BLUE, -3), (CYBER_PINK, 3)):
            g = self.big_font.render(title, True, color)
            dx = ox + (random.randint(-jitter, jitter) if jitter else 0)
            self.screen.blit(g, (cx - g.get_width() // 2 + dx, title_y))
        main = self.big_font.render(title, True, (255, 60, 70))
        self.screen.blit(main, (cx - main.get_width() // 2, title_y))

        if gp.death_stats.get("new_record"):
            col = CYBER_YELLOW if (t // 15) % 2 == 0 else ORANGE
            sub = self.title_font.render(f"KỶ LỤC MỚI: {gp.death_stats.get('score', 0)} ĐIỂM!", True, col)
            self.screen.blit(sub, (cx - sub.get_width() // 2, title_y + 72))
        else:
            sub = self.sub_font.render("Kết nối thần kinh bị cắt đứt... Hệ thống đang khởi động lại", True, (255, 170, 175))
            self.screen.blit(sub, (cx - sub.get_width() // 2, title_y + 78))

        if t < 30:
            return

        st = gp.death_stats
        mins, secs = divmod(st.get("seconds", 0), 60)
        if st.get("mode") == "ENDLESS":
            rows = [
                ("Wave đạt được", f"{st.get('wave', 0)}", CYBER_PINK),
                ("Điểm", f"{st.get('score', 0)}", CYBER_YELLOW),
                ("Kỷ lục", f"{st.get('best', 0)}", GREEN),
                ("Quái đã hạ", f"{st.get('kills', 0)}", WHITE),
                ("Coins kiếm được", f"+{st.get('coins', 0)}", CYBER_YELLOW),
            ]
        else:
            rows = [
                ("Màn chơi", f"{st.get('level', 1)}", CYBER_BLUE),
                ("Quái đã hạ", f"{st.get('kills', 0)}", GREEN),
                ("Coins kiếm được", f"+{st.get('coins', 0)}", CYBER_YELLOW),
                ("Thời gian sống", f"{mins:02d}:{secs:02d}", WHITE),
            ]
            if st.get("boss_hp"):
                hp, mx = st["boss_hp"]
                rows.append(("Boss còn lại", f"{int(100 * hp / max(1, mx))}% máu", CYBER_PINK))

        box = pygame.Rect(cx - 210, 195, 420, 30 * len(rows) + 16)
        bg = pygame.Surface(box.size, pygame.SRCALPHA)
        bg.fill((15, 10, 25, 220))
        self.screen.blit(bg, box.topleft)
        pygame.draw.rect(self.screen, (255, 60, 70), box, 2, border_radius=10)
        for i, (label, value, col) in enumerate(rows):
            y = box.top + 10 + i * 30
            self.screen.blit(self.font.render(label, True, (200, 200, 215)), (box.left + 24, y))
            v = self.font.render(value, True, col)
            self.screen.blit(v, (box.right - 24 - v.get_width(), y))


        ready = gp.overlay_ready()
        self.draw_buttons(gp, ready)
        if ready and (t // 30) % 2 == 0:
            keys = [b[0] for b in gp.overlay_buttons()]
            msg = "Nhấn C để hồi sinh ở checkpoint, R để chơi lại" if "checkpoint" in keys else "Nhấn R hoặc Enter để thử lại"
            hint = self.small.render(msg, True, (200, 200, 210))
            self.screen.blit(hint, (cx - hint.get_width() // 2, 458))
