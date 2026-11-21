"""graphics/minimap.py - Bản đồ radar tối ưu (cache nền tường tĩnh, hiển thị Zombie & hộp tiếp tế)."""
import math
import pygame

import sys
from settings import MAP_W, MAP_H, GREEN, RED, WHITE
from font_vn import get_font
from game.map import line_blocked, check_smoke_blocks, get_active_map


class Minimap:
    def __init__(self):
        self.scale = 0.105 if sys.platform == "emscripten" else 0.15
        self.width = int(MAP_W * self.scale)
        self.height = int(MAP_H * self.scale)
        self.margin = 14 if sys.platform == "emscripten" else 20
        self._bg_cache_key = None
        self._bg_surf = None
        self._circle_cache = {}
        self._font = None

    def _get_circle_surf(self, radius, fill_rgba, border_rgba=None):
        key = (radius, fill_rgba, border_rgba)
        surf = self._circle_cache.get(key)
        if surf is None:
            if len(self._circle_cache) > 32:
                self._circle_cache.clear()
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, fill_rgba, (radius, radius), radius)
            if border_rgba:
                pygame.draw.circle(surf, border_rgba, (radius, radius), radius, 1)
            self._circle_cache[key] = surf
        return surf

    def _ensure_bg(self, walls):
        active_map = get_active_map()
        key = (active_map["id"], len(walls))
        if self._bg_cache_key == key and self._bg_surf is not None:
            return
        self._bg_cache_key = key
        surf = pygame.Surface((self.width, self.height))
        surf.fill((12, 14, 18))

        # Vẽ vùng Site A/B/C mờ trên radar
        sites = active_map.get("sites", {})
        for s_col, s_key in (((30, 85, 55), "A"), ((30, 60, 95), "B"), ((85, 75, 30), "C")):
            sr = sites.get(s_key)
            if sr:
                r = pygame.Rect(
                    int(sr.x * self.scale),
                    int(sr.y * self.scale),
                    max(4, int(sr.w * self.scale)),
                    max(4, int(sr.h * self.scale)),
                )
                pygame.draw.rect(surf, s_col, r)

        wall_col = active_map["theme"]["wall_rgb"]
        for wall in walls:
            rect = pygame.Rect(
                int(wall.x * self.scale),
                int(wall.y * self.scale),
                max(2, int(wall.width * self.scale)),
                max(2, int(wall.height * self.scale)),
            )
            pygame.draw.rect(surf, wall_col, rect)

        pygame.draw.rect(surf, WHITE, (0, 0, self.width, self.height), 2)
        self._bg_surf = surf

    def draw(
        self,
        screen,
        player,
        enemies,
        walls,
        smokes=None,
        fires=None,
        dropped_weapons=None,
        supply_drops=None,
        game_state=None,
    ):
        self._ensure_bg(walls)
        x0 = screen.get_width() - self.width - self.margin
        y0 = self.margin
        screen.blit(self._bg_surf, (x0, y0))

        # Khói & Lửa trên radar
        if smokes:
            for s in smokes:
                sx = x0 + int(s["x"] * self.scale)
                sy = y0 + int(s["y"] * self.scale)
                sr = max(3, int(s.get("r", s.get("radius", 130)) * self.scale))
                screen.blit(
                    self._get_circle_surf(sr, (170, 175, 185, 140), (220, 225, 235, 180)),
                    (sx - sr, sy - sr),
                )

        if fires:
            for f in fires:
                fx = x0 + int(f["x"] * self.scale)
                fy = y0 + int(f["y"] * self.scale)
                fr = max(3, int(f.get("r", f.get("radius", 95)) * self.scale))
                screen.blit(
                    self._get_circle_surf(fr, (255, 90, 20, 165), (255, 220, 40, 200)),
                    (fx - fr, fy - fr),
                )

        # Súng rơi & Hộp tiếp tế
        if dropped_weapons:
            for dw in dropped_weapons:
                wx = x0 + int(dw["x"] * self.scale)
                wy = y0 + int(dw["y"] * self.scale)
                pygame.draw.rect(screen, (255, 215, 60), (wx - 2, wy - 2, 4, 4))

        if supply_drops:
            for sd in supply_drops:
                dx = x0 + int(sd["x"] * self.scale)
                dy = y0 + int(sd["y"] * self.scale)
                pygame.draw.circle(screen, (80, 240, 255), (dx, dy), 3)

        # Kẻ địch & Zombie
        if game_state != "BUY":
            for enemy in enemies:
                if not enemy.alive:
                    continue
                # Zombie áp sát gần (< 320) phát tiếng động nên hiện chấm cảnh báo trên radar
                is_z = getattr(enemy, "is_zombie", False)
                near_alert = is_z and math.hypot(enemy.x - player.x, enemy.y - player.y) < 320
                if not near_alert:
                    if line_blocked(player.x, player.y, enemy.x, enemy.y, walls):
                        continue
                    if check_smoke_blocks(player.x, player.y, enemy.x, enemy.y, smokes):
                        continue

                ex = x0 + int(enemy.x * self.scale)
                ey = y0 + int(enemy.y * self.scale)
                if is_z:
                    z_col = (195, 85, 255) if enemy.zombie_type in ("BRUTE", "MUTANT") else (140, 245, 75)
                    rad = 5 if enemy.zombie_type == "MUTANT" else 4
                    pygame.draw.circle(screen, z_col, (ex, ey), rad)
                else:
                    pygame.draw.circle(screen, RED, (ex, ey), 4)

        # Người chơi & hướng nhìn
        px = x0 + int(player.x * self.scale)
        py = y0 + int(player.y * self.scale)
        pygame.draw.circle(screen, GREEN, (px, py), 5)
        dx = math.cos(player.angle) * 18
        dy = math.sin(player.angle) * 18
        pygame.draw.line(screen, GREEN, (px, py), (int(px + dx), int(py + dy)), 2)

        # Tên bản đồ hiện gọn phía dưới minimap
        if self._font is None:
            self._font = get_font(14, bold=True)
        m_name = get_active_map()["name"]
        lbl = self._font.render(m_name, True, (195, 205, 220))
        screen.blit(lbl, (x0 + self.width - lbl.get_width(), y0 + self.height + 4))
