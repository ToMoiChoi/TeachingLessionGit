import pygame
from config import CYBER_BLUE, CYBER_PINK, CYBER_YELLOW, DARK_BG, GREEN, RED, WHITE

ORANGE = (255, 140, 0)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width=120, height=15):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, screen, camera_x=0):
        render_rect = self.rect.move(-camera_x, 0)
        pygame.draw.rect(screen, (40, 50, 80), render_rect, border_radius=5)
        pygame.draw.rect(screen, CYBER_BLUE, render_rect, 2, border_radius=5)


class LayoutRenderer:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("Arial", 18, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)

    def render(self, gameplay):
        if gameplay.current_level == 8 and gameplay.state in ["GAME", "LEVEL_CLEAR"]:
            self.screen.fill((200, 10, 30))
        else:
            self.screen.fill(DARK_BG)

        if gameplay.state in ["GAME", "LEVEL_CLEAR"]:
            cam_x = gameplay.camera_x

            pygame.draw.rect(self.screen, (40, 40, 60), (-cam_x, 380, gameplay.level_width, 200))
            pygame.draw.line(self.screen, CYBER_BLUE, (-cam_x, 380), (gameplay.level_width - cam_x, 380), 2)

            for plat in gameplay.platforms:
                plat.draw(self.screen, cam_x)

            for p in gameplay.powerups:
                ren_rect = p.rect.move(-cam_x, 0)
                if hasattr(p, 'draw'):
                    orig_rect = p.rect
                    p.rect = ren_rect
                    p.draw(self.screen)
                    p.rect = orig_rect

            for enemy in gameplay.enemies:
                if hasattr(enemy, 'draw'):
                    enemy.draw(self.screen, cam_x)
                else:
                    ren_rect = enemy.rect.move(-cam_x, 0)
                    if hasattr(enemy, 'image') and enemy.image:
                        self.screen.blit(enemy.image, ren_rect)
                    else:
                        pygame.draw.rect(self.screen, RED, ren_rect, border_radius=4)
                    hp_ratio = max(0, enemy.hp / getattr(enemy, 'max_hp', 50))
                    pygame.draw.rect(self.screen, RED, (ren_rect.x, ren_rect.top - 8, 35, 4))
                    pygame.draw.rect(self.screen, GREEN, (ren_rect.x, ren_rect.top - 8, int(35 * hp_ratio), 4))

            boss = gameplay.boss_group.sprite
            if boss:
                ren_rect = boss.rect.move(-cam_x, 0)
                if hasattr(boss, 'image') and boss.image:
                    self.screen.blit(boss.image, ren_rect)
                else:
                    boss_color = (255, 60, 0) if getattr(boss, 'phase', 1) == 2 else CYBER_PINK
                    pygame.draw.rect(self.screen, boss_color, ren_rect, border_radius=6)
                if hasattr(boss, 'draw_health_bar'):
                    boss.draw_health_bar(self.screen, gameplay.player)

            for b in gameplay.player_bullets:
                ren_rect = b.rect.move(-cam_x, 0)
                if hasattr(b, 'image') and b.image:
                    self.screen.blit(b.image, ren_rect)
                else:
                    pygame.draw.rect(self.screen, getattr(b, 'color', CYBER_YELLOW), ren_rect)

            for b in gameplay.enemy_bullets:
                ren_rect = b.rect.move(-cam_x, 0)
                if hasattr(b, 'image') and b.image:
                    self.screen.blit(b.image, ren_rect)
                else:
                    pygame.draw.rect(self.screen, RED, ren_rect)

            gameplay.player.draw(self.screen, cam_x)

            for pt in gameplay.particle_mgr.particles:
                if isinstance(pt, dict):
                    px, py = int(pt['x'] - cam_x), int(pt['y'])
                    col = pt.get('color', WHITE)
                    sz = int(pt.get('size', 3))
                elif isinstance(pt, (list, tuple)):
                    px, py = int(pt[0] - cam_x), int(pt[1])
                    col = pt[2] if len(pt) > 2 and isinstance(pt[2], (tuple, list)) else WHITE
                    sz = int(pt[3]) if len(pt) > 3 and isinstance(pt[3], (int, float)) else 3
                elif hasattr(pt, 'x') and hasattr(pt, 'y'):
                    px, py = int(pt.x - cam_x), int(pt.y)
                    col = getattr(pt, 'color', WHITE)
                    sz = int(getattr(pt, 'size', 3))
                else:
                    continue
                pygame.draw.circle(self.screen, col, (px, py), max(1, sz))

            # UI BẢNG THÔNG TIN
            hp_txt = self.font.render(f"HP: {max(0, gameplay.player.hp)}/{gameplay.player.max_hp}", True, WHITE)
            ammo_txt = self.font.render(f"AMMO: {gameplay.current_weapon.ammo}/{gameplay.current_weapon.max_ammo}", True, ORANGE)
            gun_label = self.font.render("GUN [1,2,3]:", True, CYBER_YELLOW)
            coin_txt = self.font.render(f"Coins: {gameplay.coins}", True, CYBER_YELLOW)
            disp_lvl = gameplay.current_level - 1 if gameplay.state == 'LEVEL_CLEAR' else gameplay.current_level
            lvl_txt = self.font.render(f"Level: {disp_lvl}", True, CYBER_BLUE)

            self.screen.blit(hp_txt, (10, 10))
            self.screen.blit(ammo_txt, (10, 32))
            self.screen.blit(gun_label, (10, 54))

            # HIỂN THỊ HÌNH ẢNH SÚNG TRỰC TIẾP
            gun_obj = gameplay.current_weapon
            gun_img = getattr(gun_obj, 'image', getattr(gun_obj, 'surface', None))
            if gun_img:
                gun_icon = pygame.transform.scale(gun_img, (40, 20))
                self.screen.blit(gun_icon, (125, 52))
            else:
                gun_name_txt = self.font.render(gun_obj.name, True, CYBER_YELLOW)
                self.screen.blit(gun_name_txt, (125, 54))

            self.screen.blit(coin_txt, (10, 76))
            self.screen.blit(lvl_txt, (10, 98))

            pygame.draw.rect(self.screen, (30, 30, 50), (10, 124, 100, 12), border_radius=3)
            slash_ratio = 1 - (gameplay.player.slash_cooldown / gameplay.player.slash_delay)
            pygame.draw.rect(self.screen, CYBER_BLUE, (10, 124, int(100 * max(0, slash_ratio)), 12), border_radius=3)
            self.screen.blit(self.font.render("SWORD", True, WHITE), (115, 120))

            buff_y = 10
            for buff in gameplay.active_buffs:
                box_rect = pygame.Rect(620, buff_y, 170, 30)
                bg_surf = pygame.Surface((170, 30), pygame.SRCALPHA)
                bg_surf.fill((20, 20, 35, 210))
                self.screen.blit(bg_surf, (620, buff_y))
                pygame.draw.rect(self.screen, buff["color"], box_rect, 2, border_radius=6)
                txt_surf = self.font.render(buff["text"], True, buff["color"])
                self.screen.blit(txt_surf, (box_rect.centerx - txt_surf.get_width() // 2, box_rect.centery - txt_surf.get_height() // 2))
                ratio = buff["timer"] / buff["max_timer"]
                pygame.draw.line(self.screen, buff["color"], (box_rect.left + 4, box_rect.bottom - 3), (box_rect.left + int(162 * ratio), box_rect.bottom - 3), 2)
                buff_y += 36

            if gameplay.state == "LEVEL_CLEAR":
                overlay = pygame.Surface((800, 500), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (0, 0))
                box_rect = pygame.Rect(200, 120, 400, 260)
                pygame.draw.rect(self.screen, (20, 20, 35), box_rect, border_radius=15)
                pygame.draw.rect(self.screen, CYBER_BLUE, box_rect, 3, border_radius=15)
                win_title = self.title_font.render("VICTORY!", True, CYBER_YELLOW)
                self.screen.blit(win_title, (box_rect.centerx - win_title.get_width() // 2, 140))
                info_txt = self.font.render(f"Màn chơi {gameplay.current_level - 1} Hoàn Thành!", True, WHITE)
                self.screen.blit(info_txt, (box_rect.centerx - info_txt.get_width() // 2, 200))
                sec_left = max(1, gameplay.clear_timer // 60 + 1)
                time_txt = self.font.render(f"Tự động về Menu sau {sec_left}s...", True, CYBER_BLUE)
                self.screen.blit(time_txt, (box_rect.centerx - time_txt.get_width() // 2, 250))
        else:
            gameplay.menu.render(gameplay.state, gameplay)

        pygame.display.flip()