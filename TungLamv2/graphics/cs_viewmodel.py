
import math
import pygame

from graphics import gun3d


# ==============================================================================
# CS:GO / CS2 FIRST PERSON VIEWMODEL
# ==============================================================================

class CSViewModel:

    PISTOLS = {"CLASSIC", "GHOST", "SHERIFF"}
    MELEE = {"KNIFE"}

    def __init__(self, screen_w=1600, screen_h=900):
        self.sw = screen_w
        self.sh = screen_h

        # Vị trí đầu nòng
        self.muzzle_pos = (
            self.sw * 0.58,
            self.sh * 0.52
        )

        # Movement / Bobbing
        self.bob_t = 0.0
        self.bob_x = 0.0
        self.bob_y = 0.0

        self.last_pos = (0.0, 0.0)

        # Mouse sway
        self.sway_x = 0.0
        self.last_angle = 0.0
        self.last_time = 0.0

    # ==========================================================================
    # UPDATE VIEWMODEL
    # ==========================================================================

    def update(self, dt, player):

        now = pygame.time.get_ticks() / 1000.0

        frame_dt = (
            min(0.08, max(0.0, now - self.last_time))
            if self.last_time else 0.016
        )

        self.last_time = now

        # Mouse sway
        dang = (
            player.angle - self.last_angle + math.pi
        ) % (2 * math.pi) - math.pi

        self.last_angle = player.angle

        target_sway = max(
            -8.0,
            min(8.0, -dang * 75.0)
        )

        self.sway_x += (
            target_sway - self.sway_x
        ) * min(1.0, frame_dt * 12.0)

        # Movement bobbing
        dist_moved = math.hypot(
            player.x - self.last_pos[0],
            player.y - self.last_pos[1]
        )

        self.last_pos = (player.x, player.y)

        is_moving = (
            frame_dt > 0 and
            (dist_moved / frame_dt) > 20.0
        )

        if is_moving:

            self.bob_t += frame_dt * 8.0

            self.bob_x = math.sin(self.bob_t) * 2.2
            self.bob_y = abs(math.cos(self.bob_t)) * 1.8

        else:

            self.bob_t += frame_dt * 1.5

            self.bob_x = math.sin(self.bob_t) * 0.5
            self.bob_y = abs(math.cos(self.bob_t)) * 0.6

    # ==========================================================================
    # PIXEL TO WORLD
    # ==========================================================================

    def _px_to_m(self, px, depth):

        f = (self.sw / 2) / math.tan(math.radians(27))

        return px * depth / f

    # ==========================================================================
    # DRAW VIEWMODEL
    # ==========================================================================

    def draw(
        self,
        screen,
        player,
        reload_drop=0,
        side_sway=0,
        bomb_fuse=None
    ):

        cur_w = getattr(player, "weapon", "CLASSIC")

        righthand = getattr(
            player,
            "righthand",
            True
        )

        recoil = max(
            0.0,
            float(getattr(player, "recoil", 0.0))
        )

        # Súng bắn tỉa: khi đã ngắm hẳn thì ống nhòm che màn hình -> ẩn súng
        if cur_w in self.SNIPERS and getattr(player, "ads", 0.0) > 0.85:
            self.muzzle_pos = (self.sw // 2, self.sh // 2)
            return self.muzzle_pos

        # Knife
        if cur_w == "KNIFE":

            return self._draw_knife_viewmodel(
                screen,
                player,
                righthand
            )

        # Throwables
        elif cur_w in (
            "SMOKE",
            "MOLOTOV",
            "BOMB"
        ):

            return self.muzzle_pos

        # Guns
        else:

            return self._draw_gun_viewmodel(
                screen,
                player,
                cur_w,
                righthand,
                recoil,
                reload_drop,
                side_sway
            )

    # ==========================================================================
    # WEAPON POSITIONS: ((x phải, y xuống, z trước), yaw, pitch, roll) - độ
    # ==========================================================================

    POSE_RIFLE = ((0.20, 0.15, 0.80), -12.0, 1.0, -4.0)
    POSE_SNIPER = ((0.20, 0.16, 0.86), -11.0, 1.0, -4.0)
    POSE_PISTOL = ((0.13, 0.085, 0.50), -8.0, 1.0, -3.0)
    POSE_KNIFE = ((0.17, 0.16, 0.32), -28.0, 10.0)

    SNIPERS = {"AWM", "M24"}
    ADS_PITCH = 0.0
    RELOAD_TILT = (-20.0, 6.0, 30.0)   # (yaw, pitch, roll) độ: xoay súng cho lộ băng đạn khi nạp
    NO_MAG = {"SHERIFF", "M014", "M1014"}   # nạp từng viên: không tháo băng đạn

    # ==========================================================================
    # RELOAD ANIMATION
    # ==========================================================================

    @staticmethod
    def _seg(p, a, b):
        """Tiến độ 0..1 của p trong đoạn [a, b]."""
        if b <= a:
            return 1.0 if p >= b else 0.0
        return max(0.0, min(1.0, (p - a) / (b - a)))

    @staticmethod
    def _ease(t):
        return t * t * (3 - 2 * t)

    def _reload_pose(self, p, weapon_id, is_pistol):
        """Trả về (dx, dy, dz, dyaw, dpitch, droll, mag_offset, mag_roll) theo tiến độ nạp đạn p (0..1).

        Các bước: nghiêng súng -> tháo băng cũ (rơi xuống) -> lắp băng mới -> vỗ băng -> kéo khóa nòng.
        """
        e = self._ease
        seg = self._seg
        k = 0.7 if is_pistol else 1.0
        # nghiêng súng vào / ra
        env = e(seg(p, 0.0, 0.14)) * (1.0 - e(seg(p, 0.82, 1.0)))
        dx = -0.03 * env * k
        dy = -0.03 * env * k             # nâng súng lên cho thấy chỗ lắp băng đạn
        dz = 0.0
        tyaw, tpitch, troll = self.RELOAD_TILT
        dyaw = tyaw * env
        dpitch = tpitch * env
        droll = troll * env
        mag_offset, mag_roll = None, 0.0

        if weapon_id in self.NO_MAG:
            # nhét từng viên đạn: súng giật nhẹ theo nhịp
            t = seg(p, 0.16, 0.80)
            if 0.0 < t < 1.0:
                beat = abs(math.sin(t * math.pi * 5))
                dpitch += 5.0 * beat
                dy -= 0.008 * beat
        else:
            drop = seg(p, 0.16, 0.36)        # băng cũ rơi
            insert = seg(p, 0.44, 0.66)      # băng mới đưa lên
            if p < 0.16:
                mag_offset = (0.0, 0.0, 0.0)
            elif p < 0.40:
                mag_offset = (0.0, -0.55 * drop * drop, 0.0)
                mag_roll = -0.5 * drop
            elif p < 0.44:
                mag_offset = (0.0, -0.6, 0.0)      # ngoài màn hình
            else:
                mag_offset = (0.0, -0.32 * (1.0 - e(insert)), 0.0)
                mag_roll = 0.25 * (1.0 - e(insert))
            # vỗ băng đạn vào: súng nảy lên một chút
            slap = seg(p, 0.66, 0.72)
            if 0.0 < slap < 1.0:
                bump = math.sin(slap * math.pi)
                dpitch += 4.0 * bump
                dy -= 0.012 * bump

        # kéo khóa nòng: súng giật về phía sau rồi trở lại
        ch = seg(p, 0.74, 0.88)
        if 0.0 < ch < 1.0:
            pull = math.sin(ch * math.pi)
            dz -= 0.04 * pull * k
            droll -= 8.0 * pull
            dyaw += 4.0 * pull
        return dx, dy, dz, dyaw, dpitch, droll, mag_offset, mag_roll

    # ==========================================================================
    # DRAW GUN
    # ==========================================================================

    def _draw_gun_viewmodel(
        self,
        screen,
        player,
        weapon_id,
        righthand,
        recoil,
        reload_drop,
        side_sway
    ):

        is_pistol = weapon_id in self.PISTOLS
        if is_pistol:
            pose = self.POSE_PISTOL
        elif weapon_id in self.SNIPERS:
            pose = self.POSE_SNIPER
        else:
            pose = self.POSE_RIFLE
        (x, y, z), yaw, pitch, roll = pose

        # Ngắm (ADS): trượt súng vào giữa, thước ngắm trùng tâm màn hình
        model = gun3d.get_model(weapon_id)
        ads = self._ease(max(0.0, min(1.0, float(getattr(player, "ads", 0.0)))))
        if getattr(player, "reloading", False):
            ads = 0.0
        x += (0.0 - x) * ads
        y += (model.sight_y - y) * ads
        z += (model.ads_z - z) * ads
        yaw *= (1.0 - ads)
        pitch += (self.ADS_PITCH - pitch) * ads     # chúc nòng xuống nhẹ để thấy mặt trên súng
        roll *= (1.0 - ads)

        # Recoil (khi ngắm giật ít hơn)
        kick = min(1.0, recoil / 0.14) * (1.0 - 0.5 * ads)

        # Reload animation
        mag_offset, mag_roll = None, 0.0
        if getattr(player, "reloading", False):
            now = pygame.time.get_ticks() / 1000.0
            dur = max(0.1, float(getattr(player, "reload_time", 1.8)))
            p = max(0.0, min(1.0, (now - getattr(player, "reload_start", now)) / dur))
            dx, dy, dz, dyaw, dpitch, droll, mag_offset, mag_roll = self._reload_pose(p, weapon_id, is_pistol)
            x += dx
            y += dy
            z += dz
            yaw += dyaw
            pitch += dpitch
            roll += droll

        # Movement + sway (khi ngắm gần như đứng yên)
        steady = 1.0 - 0.85 * ads
        x += self._px_to_m((self.bob_x + self.sway_x) * steady, z)
        y += self._px_to_m(self.bob_y * steady, z)

        # Recoil kickback
        z -= 0.035 * kick
        pitch += 5.0 * kick

        # Left hand
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
            mag_offset=mag_offset,
            mag_roll=mag_roll,
        )

        return self.muzzle_pos

    # ==========================================================================
    # DRAW KNIFE
    # ==========================================================================

    def _draw_knife_viewmodel(
        self,
        screen,
        player,
        righthand
    ):

        (x, y, z), yaw, pitch = self.POSE_KNIFE

        roll = -20.0

        swing_timer = getattr(
            player,
            "knife_swing",
            0.0
        )

        is_stab = getattr(
            player,
            "knife_is_stab",
            False
        )

        swing_total = 0.28

        if swing_timer > 0:

            p = math.sin(
                (1.0 - swing_timer / swing_total) * math.pi
            )

            if is_stab:

                # Stab
                z += 0.12 * p
                x -= 0.06 * p
                pitch += 6 * p

            else:

                # Slash
                yaw += 40 * p
                roll -= 35 * p
                x -= 0.08 * p
                y -= 0.03 * p

        # Movement bobbing
        x += self._px_to_m(
            self.bob_x + self.sway_x,
            z
        )

        y += self._px_to_m(
            self.bob_y,
            z
        )

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
            fov_deg=68.0
        )

        return self.muzzle_pos
