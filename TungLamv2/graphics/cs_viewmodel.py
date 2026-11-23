"""graphics/cs_viewmodel.py - Góc cầm súng chuẩn CS2/Valorant & Hoạt ảnh nạp đạn 6 pha có tay trái thật."""
import math
import pygame

from graphics import gun3d


def _lerp3(a, b, t):
    return (
        a[0] + (b[0] - a[0]) * t,
        a[1] + (b[1] - a[1]) * t,
        a[2] + (b[2] - a[2]) * t,
    )


class CSViewModel:
    PISTOLS = {"CLASSIC", "GHOST", "SHERIFF"}
    SMGS = {"MP5", "UMP"}
    SHOTGUNS = {"M014", "M1014", "MAG-7", "MAG7"}
    SNIPERS = {"AWM", "M24"}
    AK_STYLE = {"AK-47", "AK47", "VANDAL"}

    # Góc cầm súng chuẩn FPS chiến thuật (CS2 / Valorant viewmodel_fov 60):
    # ((x sang phải, y xuống dưới, z ra trước), yaw chĩa về tâm, pitch nâng mũi, roll nghiêng tự nhiên)
    POSE_PISTOL = ((0.182, 0.126, 0.58), -10.5, 2.5, -4.0)
    POSE_SMG = ((0.215, 0.152, 0.68), -11.0, 2.2, -3.8)
    POSE_SHOTGUN = ((0.220, 0.148, 0.74), -11.0, 2.4, -3.5)
    POSE_RIFLE = ((0.225, 0.156, 0.78), -11.2, 2.2, -3.8)
    POSE_SNIPER = ((0.230, 0.160, 0.84), -10.5, 2.0, -3.2)
    POSE_KNIFE = ((0.175, 0.142, 0.36), -26.0, 9.0)

    ADS_PITCH = 0.0

    def __init__(self, screen_w=1600, screen_h=900):
        self.sw = screen_w
        self.sh = screen_h
        self.muzzle_pos = (int(screen_w * 0.58), int(screen_h * 0.52))

        self.bob_t = 0.0
        self.bob_x = 0.0
        self.bob_y = 0.0
        self.last_pos = (0.0, 0.0)

        self.sway_x = 0.0
        self.sway_y = 0.0
        self.last_angle = 0.0
        self.last_pitch = 0.0
        self.last_time = 0.0

        # Hiệu ứng rút súng (Equip Raise) khi đổi vũ khí
        self._last_weapon = None
        self._equip_t = 1.0

    def update(self, dt, player):
        now = pygame.time.get_ticks() / 1000.0
        frame_dt = min(0.08, max(0.0, now - self.last_time)) if self.last_time else 0.016
        self.last_time = now

        cur_w = getattr(player, "weapon", "CLASSIC")
        if cur_w != self._last_weapon:
            self._last_weapon = cur_w
            self._equip_t = 0.0
        elif self._equip_t < 1.0:
            self._equip_t = min(1.0, self._equip_t + frame_dt * 4.6)

        # Quán tính lắc súng mượt theo hướng lia chuột ngang & dọc
        dang = (player.angle - self.last_angle + math.pi) % math.tau - math.pi
        dpitch = getattr(player, "pitch", 0.0) - self.last_pitch
        self.last_angle = player.angle
        self.last_pitch = getattr(player, "pitch", 0.0)

        target_sx = max(-10.0, min(10.0, -dang * 85.0))
        target_sy = max(-7.0, min(7.0, dpitch * 65.0))
        k_lerp = min(1.0, frame_dt * 12.0)
        self.sway_x += (target_sx - self.sway_x) * k_lerp
        self.sway_y += (target_sy - self.sway_y) * k_lerp

        dist_moved = math.hypot(player.x - self.last_pos[0], player.y - self.last_pos[1])
        self.last_pos = (player.x, player.y)
        is_moving = frame_dt > 0 and (dist_moved / frame_dt) > 20.0

        if is_moving:
            self.bob_t += frame_dt * 8.6
            self.bob_x = math.sin(self.bob_t) * 2.8
            self.bob_y = abs(math.cos(self.bob_t)) * 2.4
        else:
            self.bob_t += frame_dt * 1.6
            self.bob_x = math.sin(self.bob_t) * 0.45
            self.bob_y = abs(math.cos(self.bob_t)) * 0.55

    @staticmethod
    def _seg(p, a, b):
        if b <= a:
            return 1.0 if p >= b else 0.0
        return max(0.0, min(1.0, (p - a) / (b - a)))

    @staticmethod
    def _ease(t):
        return t * t * (3.0 - 2.0 * t)

    def _get_base_pose(self, weapon_id):
        if weapon_id in self.PISTOLS:
            return self.POSE_PISTOL
        if weapon_id in self.SMGS:
            return self.POSE_SMG
        if weapon_id in self.SHOTGUNS:
            return self.POSE_SHOTGUN
        if weapon_id in self.SNIPERS:
            return self.POSE_SNIPER
        return self.POSE_RIFLE

    def _reload_choreography(self, p, weapon_id, model):
        """Trả về đầy đủ chuyển động 6 pha:
        (dx, dy, dz, dyaw, dpitch, droll, mag_offset, mag_roll, bolt_back, left_hand_pos, shell_offset)
        """
        e = self._ease
        seg = self._seg
        is_pistol = weapon_id in self.PISTOLS
        pouch = (-0.14, -0.34, -0.14)  # Túi đạn trước ngực/hông người chơi
        fore = model.fore_grip
        m_grab = model.mag_grab
        m_base = model.mag_base
        b_grab = model.bolt_grab

        # ------------------------------------------------------------------
        # KIỂU 1: SÚNG LỤC Ổ QUAY SHERIFF (Bật ổ quay sang trái -> Đổ vỏ -> Speedloader -> Hất cổ tay đóng ổ)
        # ------------------------------------------------------------------
        if weapon_id == "SHERIFF":
            env = e(seg(p, 0.0, 0.14)) * (1.0 - e(seg(p, 0.86, 1.0)))
            dx = -0.085 * env
            dy = -0.115 * env   # Nâng cao ổ quay lên giữa tầm mắt!
            dz = 0.03 * env
            dyaw = -16.0 * env
            dpitch = 6.0 * env
            droll = 28.0 * env

            swing_open = e(seg(p, 0.10, 0.22)) * (1.0 - e(seg(p, 0.74, 0.84)))
            mag_offset = (0.0, -0.008 * swing_open, -0.048 * swing_open)
            mag_roll = 0.0
            bolt_back = 0.0
            shell_offset = None

            # Hất ngược mũi súng đổ vỏ đạn cũ (0.22 -> 0.36)
            dump = math.sin(seg(p, 0.22, 0.38) * math.pi)
            dpitch += 16.0 * dump
            dy -= 0.018 * dump

            if p < 0.16:
                lh = _lerp3(fore, m_grab, e(seg(p, 0.0, 0.16)))
            elif p < 0.36:
                lh = _lerp3(m_grab, pouch, e(seg(p, 0.20, 0.36)))
            elif p < 0.66:
                ins = e(seg(p, 0.38, 0.62))
                sh_x = -0.09 * (1.0 - ins)
                sh_y = -0.08 * (1.0 - ins)
                shell_offset = (sh_x, sh_y, 0.0)
                lh = (m_grab[0] + sh_x - 0.03, m_grab[1] + sh_y - 0.01, m_grab[2])
                if p > 0.60:
                    bump = math.sin(seg(p, 0.60, 0.66) * math.pi)
                    dz -= 0.018 * bump
            elif p < 0.84:
                lh = _lerp3(m_grab, fore, e(seg(p, 0.68, 0.84)))
                # Hất nhẹ cổ tay đóng ổ quay cái "cạch"!
                snap = math.sin(seg(p, 0.74, 0.84) * math.pi)
                droll -= 28.0 * snap
                dyaw += 6.0 * snap
            else:
                lh = fore

            return dx, dy, dz, dyaw, dpitch, droll, mag_offset, mag_roll, bolt_back, lh, shell_offset

        # ------------------------------------------------------------------
        # KIỂU 2: SHOTGUN ỐNG M014 (Lật bụng súng -> Nhét từng viên đạn đỏ -> Kéo khóa nòng)
        # ------------------------------------------------------------------
        if weapon_id in ("M014", "M1014"):
            env = e(seg(p, 0.0, 0.14)) * (1.0 - e(seg(p, 0.88, 1.0)))
            dx = -0.105 * env
            dy = -0.135 * env   # Nâng cao bụng súng lên giữa màn hình để thấy rõ viên đạn đỏ chui vào!
            dz = 0.04 * env
            dyaw = -22.0 * env
            dpitch = 8.0 * env
            droll = 48.0 * env  # Lật nghiêng lộ cổng tiếp đạn dưới bụng súng!
            bolt_back = 0.0
            shell_offset = None

            if p < 0.14:
                lh = _lerp3(fore, pouch, e(seg(p, 0.0, 0.14)))
            elif p < 0.74:
                # 3 nhịp nhét 3 viên đạn đỏ liên hoàn
                cyc = ((p - 0.14) / 0.60) * 3.0
                sub = cyc - int(cyc)
                if sub < 0.58:
                    up_t = e(sub / 0.58)
                    cur = _lerp3(pouch, m_grab, up_t)
                    shell_offset = (cur[0] - m_grab[0], cur[1] - m_grab[1], cur[2] - m_grab[2])
                    lh = (cur[0] - 0.015, cur[1] - 0.02, cur[2])
                else:
                    push_t = (sub - 0.58) / 0.42
                    bump = math.sin(push_t * math.pi)
                    dpitch += 4.5 * bump
                    dy -= 0.010 * bump
                    shell_offset = (0.025 * push_t, 0.018 * push_t, 0.0) if push_t < 0.55 else None
                    lh = _lerp3(m_grab, pouch, e(push_t))
            elif p < 0.90:
                # Tay phải/trái kéo khóa nòng cái "xoạch"!
                rack = seg(p, 0.76, 0.88)
                pull = math.sin(rack * math.pi)
                bolt_back = 0.065 * pull
                dz -= 0.032 * pull
                dpitch += 3.5 * pull
                droll -= 14.0 * pull
                lh = _lerp3(b_grab, fore, e(seg(p, 0.84, 0.92))) if p > 0.84 else _lerp3(pouch, b_grab, e(seg(p, 0.74, 0.79)))
            else:
                lh = _lerp3(b_grab, fore, e(seg(p, 0.88, 1.0)))

            return dx, dy, dz, dyaw, dpitch, droll, None, 0.0, bolt_back, lh, shell_offset

        # ------------------------------------------------------------------
        # KIỂU 3 & 4: SÚNG TRƯỜNG / SMG / SÚNG TỈA / SÚNG LỤC BĂNG ĐẠN RỜI
        # 6 PHA: Nghiêng súng -> Rút băng cũ -> Lấy băng mới có đạn đồng -> Đút khớp ổ -> Vỗ đáy băng -> Kéo Slide/Khóa nòng!
        # ------------------------------------------------------------------
        k = 0.82 if is_pistol else 1.0
        is_ak = weapon_id in self.AK_STYLE
        env = e(seg(p, 0.0, 0.14)) * (1.0 - e(seg(p, 0.88, 1.0)))

        # Nâng cao súng lên tầm ngực/mắt (dy âm trong hệ camera) & xích vào tâm để thấy trọn vẹn cả băng đạn & bàn tay trái!
        dx = (-0.085 if is_pistol else -0.105) * env
        dy = (-0.125 if is_pistol else -0.148) * env
        dz = (0.045 if is_pistol else 0.050) * env
        dyaw = (-18.0 if is_pistol else -24.0) * env
        dpitch = (7.0 if is_pistol else 6.5) * env
        droll = (38.0 if is_pistol else 36.0) * env

        mag_offset = None
        mag_roll = 0.0
        bolt_back = 0.0

        # Súng lục khi hết đạn khóa trượt giữ mở nhẹ cho tới lúc kéo thả slide (pha 5)
        if is_pistol and p < 0.82:
            bolt_back = 0.032 * env

        if p < 0.13:
            # Pha 1: Tay trái rời ốp nòng chụp lấy thân băng đạn
            mag_offset = (0.0, 0.0, 0.0)
            lh = _lerp3(fore, m_grab, e(seg(p, 0.0, 0.13)))

        elif p < 0.35:
            # Pha 2: Tay trái bẻ lẫy (AK cong ra trước, súng khác rút dọc trục) tháo băng đạn cũ ném xuống
            pull_t = e(seg(p, 0.13, 0.32))
            ox = (0.045 * pull_t if is_ak else -0.02 * pull_t)
            oy = -0.34 * pull_t * pull_t - 0.06 * pull_t
            mag_offset = (ox, oy, -0.015 * pull_t)
            mag_roll = (-0.42 if is_ak else -0.22) * pull_t
            # Giật nhẹ súng xuống khi bứt băng đạn ra khỏi lẫy
            yank = math.sin(seg(p, 0.14, 0.24) * math.pi)
            dpitch -= 3.5 * yank
            dy += 0.008 * yank
            lh = (m_grab[0] + ox, m_grab[1] + oy, m_grab[2] - 0.015 * pull_t)

        elif p < 0.42:
            # Pha 3: Tay trái thò xuống túi đạn lấy băng đạn mới
            mag_offset = (0.0, -0.75, 0.0)
            lh = _lerp3((m_grab[0], m_grab[1] - 0.28, m_grab[2]), pouch, math.sin(seg(p, 0.35, 0.42) * math.pi))

        elif p < 0.64:
            # Pha 4: Tay trái cầm băng đạn mới (có viên đạn đồng sáng ở đỉnh) lắp khớp vào ổ đạn
            ins_t = e(seg(p, 0.42, 0.63))
            rem = 1.0 - ins_t
            ox = (0.038 if is_ak else -0.015) * rem
            oy = -0.28 * rem
            oz = -0.018 * rem
            mag_offset = (ox, oy, oz)
            mag_roll = (-0.32 if is_ak else 0.16) * rem
            lh = (m_grab[0] + ox, m_grab[1] + oy, m_grab[2] + oz)
            # Nảy nhẹ khi băng đạn chạm cá giữ
            if p > 0.59:
                seat = math.sin(seg(p, 0.59, 0.64) * math.pi)
                dpitch += 3.0 * seat
                dy -= 0.008 * seat

        elif p < 0.73:
            # Pha 5: Vỗ đáy băng đạn (Tactical Mag Slap!) cho chắc chắn vào khớp
            mag_offset = (0.0, 0.0, 0.0)
            slap_t = seg(p, 0.64, 0.73)
            if slap_t < 0.45:
                # Hạ nhẹ lòng bàn tay xuống dưới đáy băng
                lh = _lerp3(m_grab, (m_base[0], m_base[1] - 0.045, m_base[2]), e(slap_t / 0.45))
            else:
                # Vỗ mạnh từ dưới lên đáy băng -> súng nảy lên cực đầm tay!
                hit_t = (slap_t - 0.45) / 0.55
                bump = math.sin(hit_t * math.pi)
                lh = _lerp3((m_base[0], m_base[1] - 0.045, m_base[2]), m_base, min(1.0, hit_t * 2.0))
                dpitch += 5.5 * bump
                dy -= 0.015 * bump
                droll -= 4.5 * bump

        elif p < 0.91:
            # Pha 6: Đưa tay lên kéo Khóa nòng / Slide / Ốp bơm (Rack Slide / Charging Handle!)
            mag_offset = (0.0, 0.0, 0.0)
            # Xoay nhẹ súng sang phía đối diện để lộ rõ khóa nòng & khe hất đạn!
            rack_env = math.sin(seg(p, 0.73, 0.91) * math.pi)
            droll -= (22.0 if not is_pistol else 18.0) * rack_env
            dyaw += 5.0 * rack_env

            if p < 0.78:
                lh = _lerp3(m_base, b_grab, e(seg(p, 0.73, 0.78)))
            elif p < 0.86:
                pull = math.sin(seg(p, 0.78, 0.86) * math.pi)
                travel = 0.045 if is_pistol else 0.068
                bolt_back = max(bolt_back, travel * pull)
                lh = (b_grab[0] - bolt_back, b_grab[1], b_grab[2])
                dz -= 0.038 * pull * k
                dpitch += 4.2 * pull
            else:
                # Buông tay cho lò xo đẩy khóa nòng đóng sập về trước!
                snap = math.sin(seg(p, 0.86, 0.91) * math.pi)
                dz += 0.014 * snap * k
                dpitch -= 2.5 * snap
                lh = _lerp3(b_grab, fore, e(seg(p, 0.86, 0.91)))

        else:
            # Pha cuối: Thu súng mượt mà về tư thế ngắm bắn chuẩn
            mag_offset = (0.0, 0.0, 0.0)
            lh = _lerp3(fore, fore, 1.0)

        return dx, dy, dz, dyaw, dpitch, droll, mag_offset, mag_roll, bolt_back, lh, None

    def draw(self, screen, player, reload_drop=0, side_sway=0, bomb_fuse=None):
        self.sw, self.sh = screen.get_size()
        cur_w = getattr(player, "weapon", "CLASSIC")
        righthand = getattr(player, "righthand", True)
        recoil = max(0.0, float(getattr(player, "recoil", 0.0)))

        if cur_w in self.SNIPERS and getattr(player, "ads", 0.0) > 0.78:
            self.muzzle_pos = (self.sw // 2, self.sh // 2)
            return self.muzzle_pos

        if cur_w == "KNIFE":
            return self._draw_knife_viewmodel(screen, player, righthand)
        if cur_w in ("SMOKE", "MOLOTOV", "BOMB"):
            return self.muzzle_pos

        return self._draw_gun_viewmodel(screen, player, cur_w, righthand, recoil)

    def _draw_gun_viewmodel(self, screen, player, weapon_id, righthand, recoil):
        (x, y, z), yaw, pitch, roll = self._get_base_pose(weapon_id)
        model = gun3d.get_model(weapon_id)

        # Hiệu ứng rút súng lên khi vừa đổi vũ khí
        if self._equip_t < 1.0:
            eq = 1.0 - self._ease(self._equip_t)
            y += 0.14 * eq
            pitch -= 18.0 * eq
            roll += 12.0 * eq

        # Ngắm qua thước ngắm (ADS)
        ads = self._ease(max(0.0, min(1.0, float(getattr(player, "ads", 0.0)))))
        if getattr(player, "reloading", False):
            ads = 0.0
        if ads > 0.0:
            x += (0.0 - x) * ads
            y += (model.sight_y - y) * ads
            z += (model.ads_z - z) * ads
            yaw *= 1.0 - ads
            pitch += (self.ADS_PITCH - pitch) * ads
            roll *= 1.0 - ads

        # Độ giật khi bắn (Blowback lùi khóa nòng + hếch mũi súng thật!)
        kick = min(1.0, recoil / 0.14) * (1.0 - 0.45 * ads)
        bolt_back = (0.038 * kick) if kick > 0.18 else 0.0

        mag_offset, mag_roll = None, 0.0
        left_hand_pos, shell_offset = None, None

        if getattr(player, "reloading", False):
            now = pygame.time.get_ticks() / 1000.0
            dur = max(0.1, float(getattr(player, "reload_time", 1.8)))
            p = max(0.0, min(1.0, (now - getattr(player, "reload_start", now)) / dur))
            (
                dx, dy, dz, dyaw, dpitch, droll,
                mag_offset, mag_roll, r_bolt, left_hand_pos, shell_offset,
            ) = self._reload_choreography(p, weapon_id, model)
            x += dx
            y += dy
            z += dz
            yaw += dyaw
            pitch += dpitch
            roll += droll
            bolt_back = max(bolt_back, r_bolt)

        steady = 1.0 - 0.85 * ads
        shift_px = (
            int((self.bob_x + self.sway_x) * steady),
            int((self.bob_y + self.sway_y) * steady),
        )

        # Recoil kickback
        z -= 0.038 * kick
        pitch += 6.2 * kick
        roll -= 1.8 * kick

        if not righthand:
            x = -x

        self.muzzle_pos = gun3d.render(
            screen,
            weapon_id,
            (x, y, z),
            math.radians(yaw),
            math.radians(pitch),
            math.radians(roll),
            mirror=not righthand,
            fov_deg=58.0,
            mag_offset=mag_offset,
            mag_roll=mag_roll,
            bolt_back=bolt_back,
            left_hand_pos=left_hand_pos,
            shell_offset=shell_offset,
            offset_px=shift_px,
        )
        return self.muzzle_pos

    def _draw_knife_viewmodel(self, screen, player, righthand):
        (x, y, z), yaw, pitch = self.POSE_KNIFE
        roll = -20.0
        if self._equip_t < 1.0:
            eq = 1.0 - self._ease(self._equip_t)
            y += 0.12 * eq
            roll -= 25.0 * eq

        swing_timer = getattr(player, "knife_swing", 0.0)
        is_stab = getattr(player, "knife_is_stab", False)
        if swing_timer > 0:
            p = math.sin((1.0 - swing_timer / 0.28) * math.pi)
            if is_stab:
                z += 0.13 * p
                x -= 0.06 * p
                pitch += 7.0 * p
            else:
                yaw += 42.0 * p
                roll -= 36.0 * p
                x -= 0.08 * p
                y -= 0.03 * p

        shift_px = (int(self.bob_x + self.sway_x), int(self.bob_y + self.sway_y))
        if not righthand:
            x = -x

        self.muzzle_pos = gun3d.render(
            screen,
            "KNIFE",
            (x, y, z),
            math.radians(yaw),
            math.radians(pitch),
            math.radians(roll),
            mirror=not righthand,
            fov_deg=66.0,
            offset_px=shift_px,
        )
        return self.muzzle_pos
