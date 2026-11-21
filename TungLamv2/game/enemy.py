"""game/enemy.py - Đặc nhiệm AI & 4 chủng loại Zombie khối 3D Roblox (tối ưu dựng hình & dẫn đường)."""
import math
import random
import pygame
from game.data import ZOMBIE_TYPES

# Cache bóng đổ dưới chân theo kích thước lượng tử hóa -> 0 cấp phát Surface mới mỗi khung hình
_SHADOW_CACHE = {}

_CUBOID_FACES = (
    ((2, 6, 7, 3), (0.0, 1.0, 0.0), "front"),
    ((0, 4, 5, 1), (0.0, -1.0, 0.0), "back"),
    ((1, 5, 6, 2), (1.0, 0.0, 0.0), "right"),
    ((3, 7, 4, 0), (-1.0, 0.0, 0.0), "left"),
    ((4, 7, 6, 5), (0.0, 0.0, 1.0), "top"),
    ((0, 1, 2, 3), (0.0, 0.0, -1.0), "bottom"),
)

_LIGHT_LEN = math.hypot(0.25, 0.45, 0.85)
_LIGHT_NORM = (0.25 / _LIGHT_LEN, 0.45 / _LIGHT_LEN, 0.85 / _LIGHT_LEN)


def _get_shadow(w, h):
    qw = max(8, (w // 4) * 4)
    qh = max(3, (h // 2) * 2)
    key = (qw, qh)
    surf = _SHADOW_CACHE.get(key)
    if surf is None:
        if len(_SHADOW_CACHE) > 96:
            _SHADOW_CACHE.clear()
        surf = pygame.Surface((qw, qh), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (15, 18, 24, 110), (0, 0, qw, qh))
        _SHADOW_CACHE[key] = surf
    return surf


class Enemy:
    def __init__(self, x, y, armor=25, is_zombie=False, zombie_type="WALKER", diff_cfg=None):
        self.x = float(x)
        self.y = float(y)
        self.is_zombie = bool(is_zombie)
        self.zombie_type = zombie_type if is_zombie else None

        hp_mult = diff_cfg["hp_mult"] if diff_cfg else 1.0
        spd_mult = diff_cfg["speed_mult"] if diff_cfg else 1.0
        dmg_mult = diff_cfg["dmg_mult"] if diff_cfg else 1.0
        fire_mult = diff_cfg["bot_fire_mult"] if diff_cfg else 1.0

        if self.is_zombie:
            zcfg = ZOMBIE_TYPES.get(zombie_type, ZOMBIE_TYPES["WALKER"])
            self.scale = zcfg["scale"]
            self.radius = int(17 * min(1.25, self.scale))
            self.max_hp = max(30, int(zcfg["hp"] * hp_mult))
            self.hp = self.max_hp
            self.max_armor = max(0, int(zcfg["armor"] * hp_mult))
            self.armor = self.max_armor
            self.speed = zcfg["speed"] * spd_mult
            self.melee_damage = max(5, int(zcfg["melee_damage"] * dmg_mult))
            self.attack_cooldown = zcfg["attack_cooldown"]
            self.attack_range = zcfg["attack_range"]
            self.reward = zcfg["reward"]
            self.drop_chance = zcfg["drop_chance"]
            self.label = zcfg["label"]
            self.colors = zcfg
            self.fire_delay = 999.0
        else:
            self.scale = 1.0
            self.radius = 17
            self.max_hp = max(50, int(100 * hp_mult))
            self.hp = self.max_hp
            self.max_armor = max(50, int(armor))
            self.armor = armor
            self.speed = 98 * spd_mult
            self.melee_damage = 0
            self.attack_cooldown = 1.0
            self.attack_range = 40
            self.reward = 300
            self.drop_chance = 0.15
            self.label = "BOT"
            self.colors = None
            self.fire_delay = random.uniform(0.45, 0.75) * fire_mult

        # Tỉ lệ cơ thể khối Roblox 3D
        self.world_height = 70.0 * self.scale
        self.head_ratio = 0.22
        self.neck_ratio = 0.02
        self.body_ratio = 0.40
        self.leg_ratio = 0.36

        # Hitbox 2D dự phòng
        self.head_radius = int(13 * self.scale)
        self.head_offset_y = int(-32 * self.scale)
        self.body_width = int(30 * self.scale)
        self.body_height = int(55 * self.scale)
        self.body_offset_y = int(10 * self.scale)
        self.leg_width = int(26 * self.scale)
        self.leg_height = int(25 * self.scale)
        self.leg_offset_y = int(48 * self.scale)

        # Trạng thái chuyển động & chiến đấu
        self.angle = random.uniform(0.0, math.tau)
        self.anim_time = random.uniform(0.0, 3.0)
        self.walk_cycle = 0.0
        self.is_moving = False
        self.last_shot = 0.0
        self.last_melee = 0.0
        self.roar_cd = random.uniform(2.0, 7.0)
        self.strafe_dir = random.choice((-1, 1))
        self.strafe_timer = random.uniform(1.0, 2.5)
        self.alive = True
        self.muzzle_flash_timer = 0.0
        self.attack_anim = 0.0

        self.last_hit_part = None
        self.last_hit_damage = 0
        self.last_hit_time = 0

    def update(self, dt):
        self.anim_time += dt
        if self.is_moving:
            rate = 12.5 if (self.is_zombie and self.zombie_type == "RUNNER") else 9.2
            self.walk_cycle += dt * rate
        else:
            self.walk_cycle = 0.0
        self.is_moving = False

        if self.muzzle_flash_timer > 0:
            self.muzzle_flash_timer = max(0.0, self.muzzle_flash_timer - dt)
        if self.attack_anim > 0:
            self.attack_anim = max(0.0, self.attack_anim - dt * 3.5)

    def check_hit_3d(self, sx, btop, bw, bh, screen_x, screen_y):
        half_w = bw * 0.98
        if abs(screen_x - sx) > half_w:
            return None

        head_end_y = btop + bh * self.head_ratio
        body_end_y = btop + bh * (self.head_ratio + self.neck_ratio + self.body_ratio)
        leg_end_y = btop + bh

        if btop - (bh * 0.08) <= screen_y < head_end_y:
            return "head" if abs(screen_x - sx) <= bw * 0.45 else "body"
        if head_end_y <= screen_y < body_end_y:
            return "body"
        if body_end_y <= screen_y <= leg_end_y + (bh * 0.05):
            return "legs"
        return None

    def damage(self, amount, part="body"):
        self.last_hit_part = part
        self.last_hit_damage = amount
        self.last_hit_time = pygame.time.get_ticks()

        actual_damage = float(amount)
        if self.armor > 0:
            absorbed = min(float(self.armor), actual_damage * 0.5)
            self.armor -= absorbed
            actual_damage -= absorbed

        self.hp -= actual_damage
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return actual_damage

    def move(self, dx, dy, walls):
        r = self.radius
        d = r * 2
        test_x = pygame.Rect(int(self.x + dx - r), int(self.y - r), d, d)
        moved = False
        if test_x.collidelist(walls) == -1:
            self.x += dx
            moved = True

        test_y = pygame.Rect(int(self.x - r), int(self.y + dy - r), d, d)
        if test_y.collidelist(walls) == -1:
            self.y += dy
            moved = True
        return moved

    def move_smart(self, target_angle, speed, dt, walls):
        """Di chuyển thông minh: tự động trượt vòng qua góc tường nếu hướng thẳng bị chặn."""
        step = speed * dt
        if step <= 0.001:
            return False
        ox, oy = self.x, self.y
        self.move(math.cos(target_angle) * step, math.sin(target_angle) * step, walls)
        if math.hypot(self.x - ox, self.y - oy) >= step * 0.45:
            self.is_moving = True
            return True

        # Bị kẹt góc tường -> thử các góc trượt trái/phải ưu tiên hướng strafe hiện tại
        s = self.strafe_dir
        for off in (0.62 * s, -0.62 * s, 1.15 * s, -1.15 * s, 1.55 * s, -1.55 * s):
            ang = target_angle + off
            self.move(math.cos(ang) * step * 0.9, math.sin(ang) * step * 0.9, walls)
            if math.hypot(self.x - ox, self.y - oy) >= step * 0.35:
                self.is_moving = True
                return True
        self.strafe_dir = -self.strafe_dir
        return False

    def draw_roblox_3d(self, screen, sx, btop, bw, bh, font_small=None,
                       player=None, renderer=None, horizon=None):
        screen_w = screen.get_width()
        proj_plane = renderer.projection_plane if renderer else 700.0
        horiz = horizon if horizon is not None else btop + bh * 0.5

        if player:
            dx = self.x - player.x
            dy = self.y - player.y
            dist = math.hypot(dx, dy)
            p_ang = player.angle
            cos_p_ang = math.cos(p_ang)
            sin_p_ang = math.sin(p_ang)
        else:
            dist = max(1.0, proj_plane * self.world_height / max(bh, 1))
            cos_p_ang = 1.0
            sin_p_ang = 0.0

        # Bóng đổ dưới chân (dùng cache Surface)
        shadow_surf = _get_shadow(int(bw * 1.5), int(bh * 0.12))
        screen.blit(
            shadow_surf,
            (int(sx - shadow_surf.get_width() // 2), int(btop + bh - shadow_surf.get_height() // 2)),
        )

        # Cấp độ chi tiết theo khoảng cách (LOD) giúp giữ FPS cao khi đông Zombie
        high_detail = dist < 720.0
        sc = self.scale
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        ex, ey = self.x, self.y
        px = player.x if player else 0.0
        py = player.y if player else 0.0
        lx, ly, lz = _LIGHT_NORM

        faces_to_render = []

        def transform_point(loc_x, loc_y, loc_z, pitch=0.0, pivot_y=0.0, pivot_z=0.0):
            loc_x *= sc
            loc_y *= sc
            loc_z *= sc
            pivot_y *= sc
            pivot_z *= sc
            if pitch != 0.0:
                rel_y = loc_y - pivot_y
                rel_z = loc_z - pivot_z
                cp = math.cos(pitch)
                sp = math.sin(pitch)
                rot_y = pivot_y + rel_y * cp - rel_z * sp
                rot_z = pivot_z + rel_y * sp + rel_z * cp
            else:
                rot_y = loc_y
                rot_z = loc_z

            wx = ex - loc_x * sin_a + rot_y * cos_a
            wy = ey + loc_x * cos_a + rot_y * sin_a

            if player:
                pdx = wx - px
                pdy = wy - py
                cam_fwd = pdx * cos_p_ang + pdy * sin_p_ang
                if cam_fwd <= 1.0:
                    return None
                cam_right = -pdx * sin_p_ang + pdy * cos_p_ang
                inv_fwd = proj_plane / cam_fwd
                pt_sx = screen_w * 0.5 + cam_right * inv_fwd
                pt_sy = horiz - (rot_z - 35.0) * inv_fwd
                return (pt_sx, pt_sy, cam_fwd)
            scale_2d = bh / self.world_height
            return (sx + loc_x * scale_2d, horiz - (rot_z - 35.0) * scale_2d, dist)

        def add_cuboid(cx, cy, cz, hx, hy, hz, base_color, pitch=0.0, pivot_y=None, pivot_z=None, tag=None):
            if pivot_y is None:
                pivot_y = cy
            if pivot_z is None:
                pivot_z = cz

            pts = []
            for ox, oy, oz in (
                (-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
                (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz),
            ):
                pt = transform_point(cx + ox, cy + oy, cz + oz, pitch, pivot_y, pivot_z)
                if pt is None:
                    return
                pts.append(pt)

            r0, g0, b0 = base_color
            for indices, (nx, ny, nz), fname in _CUBOID_FACES:
                p0 = pts[indices[0]]
                p1 = pts[indices[1]]
                p2 = pts[indices[2]]
                p3 = pts[indices[3]]

                cross = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])
                if cross <= 0.0:
                    continue

                avg_depth = (p0[2] + p1[2] + p2[2] + p3[2]) * 0.25
                wnx = -nx * sin_a + ny * cos_a
                wny = nx * cos_a + ny * sin_a
                shade = max(0.45, min(1.22, 0.72 + 0.50 * (wnx * lx + wny * ly + nz * lz)))

                shaded_col = (
                    min(255, int(r0 * shade)),
                    min(255, int(g0 * shade)),
                    min(255, int(b0 * shade)),
                )
                poly_2d = ((int(p0[0]), int(p0[1])), (int(p1[0]), int(p1[1])),
                           (int(p2[0]), int(p2[1])), (int(p3[0]), int(p3[1])))
                faces_to_render.append((avg_depth, poly_2d, shaded_col, tag, fname, (p0, p1, p2, p3)))

        walk_swing = math.sin(self.walk_cycle) * 0.44 if self.walk_cycle != 0.0 else 0.0

        if self.is_zombie:
            c = self.colors
            skin_c = c["skin"]
            shirt_c = c["shirt"]
            pants_c = c["pants"]
            eye_c = c["eye"]
            boots_c = (24, 24, 22)

            # Chân Zombie bước khập khiễng
            add_cuboid(-3.8, 0.0, 12.0, 3.4, 3.6, 12.0, pants_c, pitch=walk_swing, pivot_y=0.0, pivot_z=24.0)
            add_cuboid(3.8, 0.0, 12.0, 3.4, 3.6, 12.0, pants_c, pitch=-walk_swing, pivot_y=0.0, pivot_z=24.0)
            if high_detail:
                add_cuboid(-3.8, 0.0, 3.2, 3.5, 3.7, 3.2, boots_c, pitch=walk_swing, pivot_y=0.0, pivot_z=24.0)
                add_cuboid(3.8, 0.0, 3.2, 3.5, 3.7, 3.2, boots_c, pitch=-walk_swing, pivot_y=0.0, pivot_z=24.0)

            # Thân áo rách + xương sườn lộ nhẹ
            add_cuboid(0.0, 0.0, 38.0, 7.8, 4.3, 14.0, shirt_c, tag="zombie_torso")
            if high_detail:
                add_cuboid(0.0, 0.5, 41.0, 5.2, 4.2, 6.0, (125, 35, 40))

            # Đầu Zombie hơi chúi về trước
            add_cuboid(0.0, 0.6, 59.0, 5.2, 5.2, 5.6, skin_c, tag="zombie_head")
            if self.zombie_type in ("BRUTE", "MUTANT"):
                # Gai vai / sừng đột biến cho Zombie khổng lồ & Boss
                horn_c = (165, 45, 210) if self.zombie_type == "BRUTE" else (65, 245, 125)
                add_cuboid(-4.0, 0.5, 66.5, 1.4, 1.4, 3.2, horn_c)
                add_cuboid(4.0, 0.5, 66.5, 1.4, 1.4, 3.2, horn_c)

            # Hai cánh tay Zombie giơ thẳng ra phía trước cào cấu!
            claw_slash = self.attack_anim * 0.75
            arm_l_pitch = 1.38 + math.sin(self.anim_time * 4.5) * 0.14 - claw_slash
            arm_r_pitch = 1.38 - math.sin(self.anim_time * 4.5) * 0.14 - claw_slash
            add_cuboid(-11.4, 0.0, 38.5, 3.2, 3.6, 13.5, shirt_c, pitch=arm_l_pitch, pivot_y=0.0, pivot_z=50.0)
            add_cuboid(11.4, 0.0, 38.5, 3.2, 3.6, 13.5, shirt_c, pitch=arm_r_pitch, pivot_y=0.0, pivot_z=50.0)
            add_cuboid(-11.4, 0.0, 27.5, 3.3, 3.7, 3.0, skin_c, pitch=arm_l_pitch, pivot_y=0.0, pivot_z=50.0)
            add_cuboid(11.4, 0.0, 27.5, 3.3, 3.7, 3.0, skin_c, pitch=arm_r_pitch, pivot_y=0.0, pivot_z=50.0)
        else:
            eye_c = (20, 20, 20)
            skin_c = (252, 215, 65)
            shirt_c = (175, 42, 48)
            vest_c = (38, 44, 54)
            pants_c = (46, 52, 64)
            boots_c = (20, 22, 28)
            gun_c = (30, 32, 38)
            helmet_c = (35, 40, 48)

            add_cuboid(-3.8, 0.0, 12.0, 3.4, 3.6, 12.0, pants_c, pitch=walk_swing, pivot_y=0.0, pivot_z=24.0)
            add_cuboid(3.8, 0.0, 12.0, 3.4, 3.6, 12.0, pants_c, pitch=-walk_swing, pivot_y=0.0, pivot_z=24.0)
            if high_detail:
                add_cuboid(-3.8, 0.0, 3.5, 3.5, 3.7, 3.5, boots_c, pitch=walk_swing, pivot_y=0.0, pivot_z=24.0)
                add_cuboid(3.8, 0.0, 3.5, 3.5, 3.7, 3.5, boots_c, pitch=-walk_swing, pivot_y=0.0, pivot_z=24.0)

            add_cuboid(0.0, 0.0, 38.0, 7.6, 4.2, 14.0, shirt_c)
            add_cuboid(0.0, 0.4, 39.5, 6.8, 4.2, 11.5, vest_c, tag="vest" if high_detail else None)
            if high_detail:
                add_cuboid(0.0, 0.2, 26.5, 7.8, 4.4, 2.2, (22, 24, 30))
                add_cuboid(0.0, 0.0, 52.8, 2.4, 2.4, 1.2, skin_c)

            add_cuboid(0.0, 0.0, 59.5, 5.0, 5.0, 5.5, skin_c, tag="head")
            add_cuboid(0.0, 0.0, 63.2, 5.6, 5.6, 2.6, helmet_c)
            if high_detail:
                add_cuboid(0.0, 3.2, 61.2, 5.8, 3.0, 1.0, (26, 30, 38))

            add_cuboid(-11.4, 0.0, 38.5, 3.2, 3.6, 13.5, shirt_c, pitch=-walk_swing * 0.75, pivot_y=0.0, pivot_z=50.0)
            add_cuboid(-11.4, 0.0, 27.5, 3.3, 3.7, 3.0, skin_c, pitch=-walk_swing * 0.75, pivot_y=0.0, pivot_z=50.0)

            gun_aim_pitch = 0.85 + walk_swing * 0.2
            add_cuboid(11.4, 0.0, 38.5, 3.2, 3.6, 13.5, shirt_c, pitch=gun_aim_pitch, pivot_y=0.0, pivot_z=50.0)
            add_cuboid(11.4, 0.0, 27.5, 3.3, 3.7, 3.0, skin_c, pitch=gun_aim_pitch, pivot_y=0.0, pivot_z=50.0)
            add_cuboid(11.4, 11.0, 36.5, 1.4, 8.5, 2.6, gun_c)
            if high_detail:
                add_cuboid(11.4, 11.5, 30.5, 1.2, 2.6, 3.6, (18, 20, 26))
                add_cuboid(11.4, 23.0, 37.0, 0.9, 6.0, 1.2, (45, 48, 56))

        faces_to_render.sort(key=lambda item: item[0], reverse=True)
        outline_c = (20, 22, 28)
        draw_poly = pygame.draw.polygon

        for _, poly, color, tag, fname, pts4 in faces_to_render:
            draw_poly(screen, color, poly)
            if high_detail:
                draw_poly(screen, outline_c, poly, 1)

            if fname == "front" and tag in ("head", "zombie_head"):
                p0, p1, p2, p3 = pts4
                mcx = (p0[0] + p1[0] + p2[0] + p3[0]) * 0.25
                mcy = (p0[1] + p1[1] + p2[1] + p3[1]) * 0.25
                mw = math.hypot(p0[0] - p3[0], p0[1] - p3[1])
                mh = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
                if mw >= 6 and mh >= 6:
                    ew = max(2, int(mw * 0.16))
                    eh = max(2, int(mh * 0.22))
                    eye_y = int(mcy - mh * 0.08)
                    elx = int(mcx - mw * 0.22 - ew / 2)
                    erx = int(mcx + mw * 0.22 - ew / 2)
                    pygame.draw.rect(screen, eye_c, (elx, eye_y, ew, eh))
                    pygame.draw.rect(screen, eye_c, (erx, eye_y, ew, eh))
                    mouth_w = max(3, int(mw * 0.42))
                    mouth_y = int(mcy + mh * 0.24)
                    m_col = (155, 25, 30) if tag == "zombie_head" else (20, 20, 20)
                    pygame.draw.rect(
                        screen,
                        m_col,
                        (int(mcx - mouth_w / 2), mouth_y, mouth_w, max(2, int(mh * 0.14 if tag == "zombie_head" else mh * 0.06))),
                    )

        # Tia lửa đầu nòng cho Bot bắn súng
        if not self.is_zombie and self.muzzle_flash_timer > 0:
            flash_pt = transform_point(11.4, 30.0, 37.0)
            if flash_pt:
                fx, fy = flash_pt[0], flash_pt[1]
                fr = max(5, int(bh * 0.12))
                draw_poly(screen, (255, 235, 90), [
                    (fx, fy - fr // 3), (fx + fr, fy - fr // 2),
                    (fx + fr * 1.6, fy), (fx + fr, fy + fr // 2), (fx, fy + fr // 3),
                ])

        # Thanh máu + giáp + nhãn chủng loại Zombie
        bar_w = max(28, int(bw * (1.45 if self.scale > 1.1 else 1.3)))
        bx = int(sx - bar_w / 2)
        by = int(btop - 18)
        pygame.draw.rect(screen, (15, 18, 22), (bx - 1, by - 1, bar_w + 2, 7), border_radius=2)
        hp_ratio = max(0.0, min(1.0, self.hp / max(1.0, float(self.max_hp))))
        if self.is_zombie:
            hp_color = (120, 235, 75) if hp_ratio > 0.4 else ((245, 165, 35) if hp_ratio > 0.2 else (235, 55, 55))
        else:
            hp_color = (60, 220, 100) if hp_ratio > 0.4 else ((240, 180, 40) if hp_ratio > 0.2 else (235, 60, 60))
        pygame.draw.rect(screen, hp_color, (bx, by, int(bar_w * hp_ratio), 5), border_radius=1)

        if self.armor > 0:
            ar_ratio = min(1.0, self.armor / max(1.0, float(self.max_armor)))
            pygame.draw.rect(screen, (70, 150, 240), (bx, by - 4, int(bar_w * ar_ratio), 3), border_radius=1)

        if font_small:
            now_ms = pygame.time.get_ticks()
            if self.last_hit_time and now_ms - self.last_hit_time < 850:
                p_text = (self.last_hit_part or "body").upper()
                txt_col = (255, 60, 60) if p_text == "HEAD" else ((240, 200, 70) if p_text == "BODY" else (180, 190, 210))
                hit_surf = font_small.render(f"{p_text} -{int(self.last_hit_damage)}", True, txt_col)
                screen.blit(hit_surf, (int(sx - hit_surf.get_width() // 2), by - 22))
            elif self.is_zombie and self.zombie_type != "WALKER" and dist < 850:
                tag_surf = font_small.render(self.label, True, self.colors["eye"])
                screen.blit(tag_surf, (int(sx - tag_surf.get_width() // 2), by - 21))
