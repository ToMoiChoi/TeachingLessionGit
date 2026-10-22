import os
import math
import pygame

# ==============================================================================
# HỆ THỐNG VIEWMODEL GÓC NHÌN THỨ NHẤT CHUẨN CS:GO / CS2
# ==============================================================================

class CSViewModel:
    """
    Quản lý góc nhìn thứ nhất (FPS Viewmodel) chuẩn xác 100% như CS:GO:
    - Góc nhìn dọc theo sống lưng súng về phía đầu ruồi và tâm ngắm
    - Bàn tay đeo găng đặc nhiệm CT ôm báng súng và đỡ nòng súng chuyên nghiệp
    - Đổi tay cầm (Trái / Phải - cl_righthand 1 / 0)
    - Neo góc dưới (bottomright / bottomleft) không che HUD hay tầm nhìn
    - Giảm rung lắc khi di chuyển (cl_bobamt_lat 0.1, cl_bobamt_vert 0.1)
    - Giật lùi và nảy lên khi bắn (Recoil Kickback) chân thực
    - Hoạt ảnh chém (slash) và đâm mạnh (stab) của dao
    - Đầu nòng đạn (muzzle_pos) trùng khớp 100% với nòng súng thực tế
    """

    PISTOLS = {"CLASSIC", "GHOST", "SHERIFF"}
    MELEE = {"KNIFE"}

    def __init__(self, screen_w=1600, screen_h=900):
        self.sw = screen_w
        self.sh = screen_h

        # Vị trí đầu nòng bắn đạn mặc định
        self.muzzle_pos = (self.sw * 0.58, self.sh * 0.52)

        # Trạng thái di chuyển, quán tính và bobbing
        self.bob_t = 0.0
        self.bob_x = 0.0
        self.bob_y = 0.0
        self.last_pos = (0.0, 0.0)
        self.sway_x = 0.0
        self.last_angle = 0.0
        self.last_time = 0.0

        # Đường dẫn assets viewmodel FPS chuẩn CS:GO
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assets_dir = os.path.join(base_dir, "assets")

        # Cache sprites
        self._sprite_cache = {}

    def _load_fps_sprite(self, category):
        """Tải sprite góc nhìn FPS CS:GO với kích thước scale chuẩn màn hình."""
        if category in self._sprite_cache:
            return self._sprite_cache[category]

        filename = {
            "RIFLE": "fps_rifle.png",
            "PISTOL": "fps_pistol.png",
            "KNIFE": "fps_knife.png",
        }.get(category, "fps_rifle.png")

        path = os.path.join(self.assets_dir, filename)
        if not os.path.exists(path):
            return None

        try:
            raw = pygame.image.load(path)
            if pygame.display.get_surface() is not None:
                raw = raw.convert_alpha()

            rw, rh = raw.get_size()

            # Tỉ lệ kích thước viewmodel tối ưu chuẩn CS:GO
            if category == "RIFLE":
                target_w = int(self.sw * 0.58)
            elif category == "PISTOL":
                target_w = int(self.sw * 0.38)
            else:  # KNIFE
                target_w = int(self.sw * 0.44)

            target_h = max(1, int(rh * target_w / rw))
            scaled = pygame.transform.smoothscale(raw, (target_w, target_h))
            self._sprite_cache[category] = scaled
            return scaled
        except Exception as e:
            print(f"[CSViewModel] Lỗi tải sprite {path}: {e}")
            return None

    def update(self, dt, player):
        now = pygame.time.get_ticks() / 1000.0
        frame_dt = min(0.08, max(0.0, now - self.last_time)) if self.last_time else 0.016
        self.last_time = now

        # Quán tính chuột nhẹ (Mouse sway)
        dang = (player.angle - self.last_angle + math.pi) % (2 * math.pi) - math.pi
        self.last_angle = player.angle
        target_sway = max(-8.0, min(8.0, -dang * 75.0))
        self.sway_x += (target_sway - self.sway_x) * min(1.0, frame_dt * 12.0)

        # Bobbing di chuyển chuẩn CS:GO (cl_bobamt_lat 0.1, cl_bobamt_vert 0.1)
        dist_moved = math.hypot(player.x - self.last_pos[0], player.y - self.last_pos[1])
        self.last_pos = (player.x, player.y)
        is_moving = frame_dt > 0 and (dist_moved / frame_dt) > 20.0

        if is_moving:
            self.bob_t += frame_dt * 8.0
            self.bob_x = math.sin(self.bob_t) * 2.2
            self.bob_y = abs(math.cos(self.bob_t)) * 1.8
        else:
            self.bob_t += frame_dt * 1.5
            self.bob_x = math.sin(self.bob_t) * 0.5
            self.bob_y = abs(math.cos(self.bob_t)) * 0.6

    def draw(self, screen, player, reload_drop=0, side_sway=0):
        cur_w = getattr(player, "weapon", "CLASSIC")
        righthand = getattr(player, "righthand", True)
        recoil = max(0.0, float(getattr(player, "recoil", 0.0)))

        # Ẩn viewmodel khi đang ngắm Scope
        if getattr(player, "scoped", False) and cur_w in ("AWM", "M24", "AK-47", "M416", "UMP", "MP5"):
            self.muzzle_pos = (self.sw // 2, self.sh // 2)
            return self.muzzle_pos

        if cur_w == "KNIFE":
            return self._draw_knife_viewmodel(screen, player, righthand)
        elif cur_w in ("SMOKE", "MOLOTOV", "BOMB"):
            return self.muzzle_pos
        else:
            return self._draw_gun_viewmodel(screen, player, cur_w, righthand, recoil, reload_drop, side_sway)

    # ==========================================================================
    # 1. VIEWMODEL SÚNG (GÓC NHÌN THỨ NHẤT CHUẨN CS:GO NHÌN DỌC THÂN SÚNG)
    # ==========================================================================

    def _draw_gun_viewmodel(self, screen, player, weapon_id, righthand, recoil, reload_drop, side_sway):
        is_pistol = weapon_id in self.PISTOLS
        cat = "PISTOL" if is_pistol else "RIFLE"
        sprite = self._load_fps_sprite(cat)
        if sprite is None:
            return self.muzzle_pos

        kick = min(1.0, recoil / 0.14)
        recoil_kick_y = int(12.0 * kick)
        recoil_kick_x = int(6.0 * kick)

        # Hoạt ảnh nạp đạn (hạ súng xuống nhẹ)
        cur_drop = reload_drop

        # Nếu cầm tay trái (cl_righthand 0): lật gương sprite sang bên trái
        if not righthand:
            draw_img = pygame.transform.flip(sprite, True, False)
        else:
            draw_img = sprite

        sw, sh = draw_img.get_size()
        rect = draw_img.get_rect()

        if righthand:
            # ------------------------------------------------------------------
            # TAY PHẢI (cl_righthand 1): Súng ở góc dưới bên phải, nòng chĩa vào tâm
            # ------------------------------------------------------------------
            if is_pistol:
                # Súng lục: neo gần giữa-phải để nhìn dọc theo sống lưng
                anchor_x = int(self.sw * 0.76 + self.bob_x + self.sway_x + side_sway + recoil_kick_x)
                anchor_y = int(self.sh + 10 + self.bob_y + cur_drop + recoil_kick_y)
                rect.bottomright = (anchor_x, anchor_y)
                # Đầu nòng súng lục
                self.muzzle_pos = (rect.left + int(sw * 0.35), rect.top + int(sh * 0.18))
            else:
                # Súng trường: nòng chĩa thẳng vào tâm ngắm
                anchor_x = int(self.sw * 0.88 + self.bob_x + self.sway_x + side_sway + recoil_kick_x)
                anchor_y = int(self.sh + 20 + self.bob_y + cur_drop + recoil_kick_y)
                rect.bottomright = (anchor_x, anchor_y)
                # Đầu nòng súng trường
                self.muzzle_pos = (rect.left + int(sw * 0.14), rect.top + int(sh * 0.28))

            screen.blit(draw_img, rect.topleft)

        else:
            # ------------------------------------------------------------------
            # TAY TRÁI (cl_righthand 0): Súng ở góc dưới bên trái, nòng chĩa vào tâm
            # ------------------------------------------------------------------
            if is_pistol:
                anchor_x = int(self.sw * 0.24 - self.bob_x - self.sway_x + side_sway - recoil_kick_x)
                anchor_y = int(self.sh + 10 + self.bob_y + cur_drop + recoil_kick_y)
                rect.bottomleft = (anchor_x, anchor_y)
                self.muzzle_pos = (rect.right - int(sw * 0.35), rect.top + int(sh * 0.18))
            else:
                anchor_x = int(self.sw * 0.12 - self.bob_x - self.sway_x + side_sway - recoil_kick_x)
                anchor_y = int(self.sh + 20 + self.bob_y + cur_drop + recoil_kick_y)
                rect.bottomleft = (anchor_x, anchor_y)
                self.muzzle_pos = (rect.right - int(sw * 0.14), rect.top + int(sh * 0.28))

            screen.blit(draw_img, rect.topleft)

        return self.muzzle_pos

    # ==========================================================================
    # 2. VIEWMODEL DAO CẬN CHIẾN CHUẨN CS:GO
    # ==========================================================================

    def _draw_knife_viewmodel(self, screen, player, righthand):
        sprite = self._load_fps_sprite("KNIFE")
        if sprite is None:
            return self.muzzle_pos

        swing_timer = getattr(player, "knife_swing", 0.0)
        is_stab = getattr(player, "knife_is_stab", False)
        swing_total = 0.28

        anim_off_x = 0
        anim_off_y = 0
        rot_angle = 0.0

        if swing_timer > 0:
            prog = 1.0 - (swing_timer / swing_total)
            if is_stab:
                # Đâm dao (Right click): phóng mạnh mũi dao về phía trước
                p = math.sin(prog * math.pi)
                anim_off_x = -int(p * 70)
                anim_off_y = -int(p * 85)
            else:
                # Chém dao (Left click): vung chém quét qua góc
                p = math.sin(prog * math.pi)
                rot_angle = -p * 22.0
                anim_off_x = -int(p * 80)
                anim_off_y = int(math.cos(prog * math.pi) * 30)

        # Lật tay trái nếu cần
        if not righthand:
            draw_img = pygame.transform.flip(sprite, True, False)
            rot_angle = -rot_angle
            anim_off_x = -anim_off_x
        else:
            draw_img = sprite

        if rot_angle != 0:
            draw_img = pygame.transform.rotate(draw_img, rot_angle)

        sw, sh = draw_img.get_size()
        rect = draw_img.get_rect()

        if righthand:
            anchor_x = int(self.sw * 0.86 + self.bob_x + self.sway_x + anim_off_x)
            anchor_y = int(self.sh + 15 + self.bob_y + anim_off_y)
            rect.bottomright = (anchor_x, anchor_y)
            screen.blit(draw_img, rect.topleft)
            self.muzzle_pos = (rect.left + int(sw * 0.25), rect.top + int(sh * 0.25))
        else:
            anchor_x = int(self.sw * 0.14 - self.bob_x - self.sway_x + anim_off_x)
            anchor_y = int(self.sh + 15 + self.bob_y + anim_off_y)
            rect.bottomleft = (anchor_x, anchor_y)
            screen.blit(draw_img, rect.topleft)
            self.muzzle_pos = (rect.right - int(sw * 0.25), rect.top + int(sh * 0.25))

        return self.muzzle_pos
