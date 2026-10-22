import pygame
import math

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

        self.num_rays = 240

        self.fov = math.radians(FOV)

        self.projection_plane = (
            WIDTH / 2
        ) / math.tan(
            self.fov / 2
        )

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

    # =====================================================
    # RAYCAST
    # =====================================================

    def raycast(
        self,
        player,
        angle,
        walls
    ):

        dx = math.cos(angle)
        dy = math.sin(angle)

        depth = 0

        max_depth = max(
            MAP_W,
            MAP_H
        )

        while depth < max_depth:

            x = player.x + dx * depth
            y = player.y + dy * depth

            # Ra ngoài map
            if x < 0 or y < 0:
                return depth

            if x >= MAP_W or y >= MAP_H:
                return depth

            # Kiểm tra tường
            for wall in walls:

                if wall.collidepoint(
                    int(x),
                    int(y)
                ):
                    return depth

            depth += 20

        return depth

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
        for band in range(6):
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
        floor_top = max(0, min(HEIGHT, horizon))
        floor_h = max(1, HEIGHT - floor_top)
        for band in range(8):
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

        ray_width = (
            WIDTH
            /
            self.num_rays
        )

        for i in range(
            self.num_rays
        ):

            # ======================================
            # CAMERA X
            # ======================================

            camera_x = (
                i
                /
                self.num_rays
            ) - 0.5

            # ======================================
            # RAY ANGLE
            # ======================================

            ray_angle = (
                player.angle
                +
                math.atan(
                    camera_x
                    *
                    2
                    *
                    math.tan(
                        self.fov / 2
                    )
                )
            )

            # ======================================
            # RAYCAST
            # ======================================

            distance = self.raycast(
                player,
                ray_angle,
                walls
            )

            # ======================================
            # FISH-EYE CORRECTION
            # ======================================

            distance *= math.cos(
                ray_angle
                -
                player.angle
            )

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

            pygame.draw.rect(
                screen,
                color,
                (
                    int(
                        i
                        *
                        ray_width
                    ),
                    top,
                    int(
                        ray_width
                        +
                        1
                    ),
                    wall_height
                )
            )