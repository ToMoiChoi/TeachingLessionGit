import pygame
import math

from settings import MAP_W, MAP_H
from settings import WALL, GREEN, RED, WHITE
from game.map import line_blocked


class Minimap:

    def __init__(self):

        self.scale = 0.15

        self.width = int(MAP_W * self.scale)
        self.height = int(MAP_H * self.scale)

        self.margin = 20

    def draw(self, screen, player, enemies, walls, smokes=None, fires=None, dropped_weapons=None, game_state=None):

        x0 = screen.get_width() - self.width - self.margin
        y0 = self.margin

        # Khung minimap
        pygame.draw.rect(
            screen,
            (12, 14, 18),
            (
                x0,
                y0,
                self.width,
                self.height
            )
        )

        # Viền
        pygame.draw.rect(
            screen,
            WHITE,
            (
                x0,
                y0,
                self.width,
                self.height
            ),
            2
        )

        # -----------------------------
        # Vẽ tường
        # -----------------------------

        for wall in walls:

            rect = pygame.Rect(
                x0 + int(wall.x * self.scale),
                y0 + int(wall.y * self.scale),
                max(2, int(wall.width * self.scale)),
                max(2, int(wall.height * self.scale))
            )

            pygame.draw.rect(
                screen,
                WALL,
                rect
            )

        # -----------------------------
        # Vẽ Smoke & Vùng lửa Bom xăng
        # -----------------------------
        if smokes:
            for s in smokes:
                sx = x0 + int(s["x"] * self.scale)
                sy = y0 + int(s["y"] * self.scale)
                sr = max(3, int(s.get("radius", 130) * self.scale))
                s_surf = pygame.Surface((sr * 2, sr * 2), pygame.SRCALPHA)
                pygame.draw.circle(s_surf, (170, 175, 185, 140), (sr, sr), sr)
                pygame.draw.circle(s_surf, (220, 225, 235, 180), (sr, sr), sr, 1)
                screen.blit(s_surf, (sx - sr, sy - sr))

        if fires:
            for f in fires:
                fx = x0 + int(f["x"] * self.scale)
                fy = y0 + int(f["y"] * self.scale)
                fr = max(3, int(f.get("radius", 95) * self.scale))
                f_surf = pygame.Surface((fr * 2, fr * 2), pygame.SRCALPHA)
                pygame.draw.circle(f_surf, (255, 90, 20, 160), (fr, fr), fr)
                pygame.draw.circle(f_surf, (255, 220, 40, 200), (fr, fr), max(1, fr // 2))
                screen.blit(f_surf, (fx - fr, fy - fr))

        # -----------------------------
        # Vẽ Vũ khí rơi trên bản đồ
        # -----------------------------
        if dropped_weapons:
            for dw in dropped_weapons:
                wx = x0 + int(dw["x"] * self.scale)
                wy = y0 + int(dw["y"] * self.scale)
                pygame.draw.rect(screen, (255, 215, 60), (wx - 2, wy - 2, 4, 4))

        # -----------------------------
        # Vẽ Enemy
        # -----------------------------

        for enemy in enemies:

            if not enemy.alive:
                continue

            # Ẩn kẻ địch trong Buy Phase hoặc khi bị tường che khuất
            if game_state == "BUY":
                continue
            if line_blocked(player.x, player.y, enemy.x, enemy.y):
                continue

            ex = x0 + int(
                enemy.x * self.scale
            )

            ey = y0 + int(
                enemy.y * self.scale
            )

            pygame.draw.circle(
                screen,
                RED,
                (ex, ey),
                4
            )

        # -----------------------------
        # Vẽ Player
        # -----------------------------

        px = x0 + int(
            player.x * self.scale
        )

        py = y0 + int(
            player.y * self.scale
        )

        pygame.draw.circle(
            screen,
            GREEN,
            (px, py),
            5
        )

        # -----------------------------
        # Hướng nhìn của Player
        # -----------------------------

        direction_length = 18

        dx = math.cos(
            player.angle
        ) * direction_length

        dy = math.sin(
            player.angle
        ) * direction_length

        pygame.draw.line(
            screen,
            GREEN,
            (px, py),
            (
                int(px + dx),
                int(py + dy)
            ),
            2
        )