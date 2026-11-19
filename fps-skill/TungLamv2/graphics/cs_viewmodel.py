
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

        f = (self.sw / 2) / math.tan(math.radians(34))

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

        # Hide weapon when scoped
        if (
            getattr(player, "scoped", False)
            and cur_w in (
                "AWM",
                "M24",
                "AK-47",
                "M416",
                "UMP",
                "MP5"
            )
        ):

            self.muzzle_pos = (
                self.sw // 2,
                self.sh // 2
            )

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
    # WEAPON POSITIONS
    # ==========================================================================

    POSE_RIFLE = (
        (0.25, 0.19, 0.62),
        -17.0,
        3.0
    )

    POSE_PISTOL = (
        (0.17, 0.13, 0.42),
        -14.0,
        3.0
    )

    POSE_KNIFE = (
        (0.17, 0.16, 0.32),
        -28.0,
        10.0
    )

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

        (x, y, z), yaw, pitch = (
            self.POSE_PISTOL
            if is_pistol
            else self.POSE_RIFLE
        )

        # Recoil
        kick = min(1.0, recoil / 0.14)

        # Reload animation
        reload_p = min(
            1.0,
            max(0.0, reload_drop / 110.0)
        )

        # Movement + sway
        x += self._px_to_m(
            self.bob_x + self.sway_x + side_sway,
            z
        )

        y += self._px_to_m(
            self.bob_y + reload_drop * 0.6,
            z
        )

        # Recoil kickback
        z -= 0.035 * kick

        pitch += 5.0 * kick

        # Reload tilt
        roll = -22.0 * reload_p

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
            mirror=not righthand
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
            mirror=not righthand
        )

        return self.muzzle_pos
