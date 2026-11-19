import pygame
import math
import random


class Enemy:

    def __init__(self, x, y, armor=25):

        # =========================
        # POSITION & HITBOX
        # =========================

        self.x = x
        self.y = y

        # Bán kính va chạm di chuyển trên bản đồ 2D
        self.radius = 17

        # =========================
        # TỈ LỆ CƠ THỂ KHỐI ROBLOX 3D (ĐẦU - THÂN - CHÂN)
        # =========================
        # Tổng chiều cao 70 đơn vị trong không gian thế giới
        self.head_ratio = 0.22
        self.neck_ratio = 0.02
        self.body_ratio = 0.40
        self.leg_ratio = 0.36

        # Hitbox 2D (phụ trợ)
        self.head_radius = 13
        self.head_offset_y = -32

        self.body_width = 30
        self.body_height = 55
        self.body_offset_y = 10

        self.leg_width = 26
        self.leg_height = 25
        self.leg_offset_y = 48

        # =========================
        # HP / ARMOR
        # =========================

        self.hp = 100
        self.armor = armor

        # =========================
        # MOVEMENT & ANIMATION
        # =========================

        self.speed = 95
        self.angle = 0.0
        self.anim_time = 0.0
        self.walk_cycle = 0.0
        self.is_moving = False

        # =========================
        # SHOOTING & EFFECTS
        # =========================

        self.last_shot = 0
        self.fire_delay = random.uniform(0.45, 0.75)
        self.alive = True
        self.muzzle_flash_timer = 0.0

        # Trạng thái trúng đòn gần nhất (dùng cho hiệu ứng hiển thị)
        self.last_hit_part = None
        self.last_hit_damage = 0
        self.last_hit_time = 0

    # =========================================================
    # UPDATE ANIMATION & TIMERS
    # =========================================================

    def update(self, dt):
        self.anim_time += dt
        if self.is_moving:
            self.walk_cycle += dt * 9.0
        else:
            self.walk_cycle = 0.0
        self.is_moving = False

        if self.muzzle_flash_timer > 0:
            self.muzzle_flash_timer = max(0.0, self.muzzle_flash_timer - dt)

    # =========================================================
    # XÁC ĐỊNH BỘ PHẬN TRÚNG ĐẠN TRÊN MÀN HÌNH 3D (ROBLOX HUMANOID)
    # =========================================================

    def check_hit_3d(self, sx, btop, bw, bh, screen_x, screen_y):
        """
        Kiểm tra điểm bắn (screen_x, screen_y) có trúng vào kẻ địch không.
        Khối người Roblox bao gồm cả 2 cánh tay ở 2 bên nên chiều rộng tổng thể ~ bw * 0.95.
        Nếu trúng, trả về tên bộ phận ('head', 'body', 'legs').
        Nếu không trúng, trả về None.
        """
        half_w = bw * 0.95
        if abs(screen_x - sx) > half_w:
            return None

        head_end_y = btop + bh * self.head_ratio
        body_end_y = btop + bh * (self.head_ratio + self.neck_ratio + self.body_ratio)
        leg_end_y = btop + bh

        # Đỉnh đầu có mũ khối nhô cao hơn một chút
        if btop - (bh * 0.06) <= screen_y < head_end_y:
            head_half_w = bw * 0.42
            if abs(screen_x - sx) <= head_half_w:
                return "head"
            else:
                return "body"
        elif head_end_y <= screen_y < body_end_y:
            return "body"
        elif body_end_y <= screen_y <= leg_end_y + (bh * 0.05):
            return "legs"

        return None

    # =========================================================
    # DAMAGE
    # =========================================================

    def damage(self, amount, part="body"):
        self.last_hit_part = part
        self.last_hit_damage = amount
        self.last_hit_time = pygame.time.get_ticks()

        actual_damage = amount
        if self.armor > 0:
            absorbed = min(self.armor, actual_damage * 0.5)
            self.armor -= absorbed
            actual_damage -= absorbed

        self.hp -= actual_damage

        if self.hp <= 0:
            self.hp = 0
            self.alive = False

        return actual_damage

    # =========================================================
    # HITBOX 2D (DỰ PHÒNG)
    # =========================================================

    def get_hitboxes(self):
        head = {
            "type": "head",
            "x": self.x,
            "y": self.y + self.head_offset_y,
            "radius": self.head_radius
        }

        body = pygame.Rect(
            int(self.x - self.body_width / 2),
            int(self.y + self.body_offset_y - self.body_height / 2),
            self.body_width,
            self.body_height
        )

        legs = pygame.Rect(
            int(self.x - self.leg_width / 2),
            int(self.y + self.leg_offset_y - self.leg_height / 2),
            self.leg_width,
            self.leg_height
        )

        return {"head": head, "body": body, "legs": legs}

    def check_hit(self, hit_x, hit_y):
        hitboxes = self.get_hitboxes()
        head = hitboxes["head"]
        dist = math.hypot(hit_x - head["x"], hit_y - head["y"])
        if dist <= head["radius"]:
            return "head"
        if hitboxes["body"].collidepoint(int(hit_x), int(hit_y)):
            return "body"
        if hitboxes["legs"].collidepoint(int(hit_x), int(hit_y)):
            return "legs"
        return None

    # =========================================================
    # MOVEMENT & COLLISION
    # =========================================================

    def move(self, dx, dy, walls):
        # Trục X
        test_x = pygame.Rect(
            int(self.x + dx - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2
        )
        if not any(test_x.colliderect(w) for w in walls):
            self.x += dx

        # Trục Y
        test_y = pygame.Rect(
            int(self.x - self.radius),
            int(self.y + dy - self.radius),
            self.radius * 2,
            self.radius * 2
        )
        if not any(test_y.colliderect(w) for w in walls):
            self.y += dy

    # =========================================================
    # VẼ KẺ ĐỊCH DẠNG HÌNH KHỐI 3D ROBLOX THỰC THỤ (TRUE 3D POLYGONAL MESH)
    # =========================================================

    def draw_roblox_3d(self, screen, sx, btop, bw, bh, font_small=None,
                       player=None, renderer=None, horizon=None):
        """
        Dựng hình kẻ địch thành các khối hộp 3D (3D Cuboids) hoàn chỉnh:
        - Sử dụng ma trận biến đổi tọa độ 3D và phép chiếu phối cảnh (Perspective Projection).
        - Khi người chơi di chuyển xung quanh, nhân vật xoay mọi góc nhìn 3D (thấy mặt trước,
          mặt bên, mặt sau, mặt trên và mặt dưới của các khối hộp).
        - Chiếu sáng đa giác 3D (Directional 3D Shading) và viền nét sắc sảo (Cel-shading).
        - Hoạt ảnh bước đi đung đưa chân và tay trong không gian 3D.
        - Khẩu súng khối Roblox 3D trên tay và tia lửa nòng súng 3D khi khai hỏa.
        """
        screen_w = screen.get_width()
        screen_h = screen.get_height()

        # Nếu không truyền player / renderer thì suy luận từ sx, btop, bw, bh
        proj_plane = (renderer.projection_plane if renderer else 700.0)
        horiz = (horizon if horizon is not None else btop + bh * 0.5)

        # Tính khoảng cách và góc nhìn từ Player
        if player:
            dx = self.x - player.x
            dy = self.y - player.y
            dist = math.hypot(dx, dy)
            p_ang = player.angle
        else:
            dist = max(1.0, proj_plane * 70.0 / max(bh, 1))
            p_ang = 0.0

        # Vector ánh sáng từ trên cao chếch trước
        light_dir = (0.25, 0.45, 0.85)
        l_len = math.hypot(light_dir[0], light_dir[1], light_dir[2])
        light_norm = (light_dir[0] / l_len, light_dir[1] / l_len, light_dir[2] / l_len)

        # --- 0. BÓNG ĐỔ DƯỚI SÀN 3D (GROUND SHADOW) ---
        shadow_w = int(bw * 1.5)
        shadow_h = max(3, int(bh * 0.12))
        shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (15, 18, 24, 110), (0, 0, shadow_w, shadow_h))
        screen.blit(shadow_surf, (int(sx - shadow_w / 2), int(btop + bh - shadow_h // 2)))

        # Danh sách chứa tất cả các mặt đa giác 3D để sắp xếp theo chiều sâu (Z-sorting)
        faces_to_render = []

        # Hàm chuyển đổi đỉnh 3D cục bộ của Enemy sang màn hình 2D
        def transform_point(lx, ly, lz, pitch=0.0, pivot_y=0.0, pivot_z=0.0):
            # Xoay pitch cục bộ (nếu có) quanh pivot
            if pitch != 0.0:
                rel_y = ly - pivot_y
                rel_z = lz - pivot_z
                cos_p = math.cos(pitch)
                sin_p = math.sin(pitch)
                rot_y = pivot_y + rel_y * cos_p - rel_z * sin_p
                rot_z = pivot_z + rel_y * sin_p + rel_z * cos_p
            else:
                rot_y = ly
                rot_z = lz
            rot_x = lx

            # Xoay theo góc hướng mặt của Enemy (self.angle) sang World Space
            cos_a = math.cos(self.angle)
            sin_a = math.sin(self.angle)
            wx = self.x - rot_x * sin_a + rot_y * cos_a
            wy = self.y + rot_x * cos_a + rot_y * sin_a
            wz = rot_z

            # Chiếu sang Camera Space của Player
            if player:
                pdx = wx - player.x
                pdy = wy - player.y
                cam_fwd = pdx * math.cos(p_ang) + pdy * math.sin(p_ang)
                if cam_fwd <= 1.0:
                    return None
                cam_right = -pdx * math.sin(p_ang) + pdy * math.cos(p_ang)
                cam_up = wz - 35.0  # Mắt player ở độ cao tâm người (35 đơn vị)

                pt_sx = screen_w / 2.0 + (cam_right / cam_fwd) * proj_plane
                pt_sy = horiz - (cam_up / cam_fwd) * proj_plane
                return (pt_sx, pt_sy, cam_fwd, wx, wy, wz)
            else:
                # Dự phòng 3D dựa trên sx, btop
                yaw = self.angle
                rx = rot_x * math.cos(yaw) - rot_y * math.sin(yaw)
                ry = rot_x * math.sin(yaw) + rot_y * math.cos(yaw)
                scale = bh / 70.0
                pt_sx = sx + rx * scale
                pt_sy = horiz - (rot_z - 35.0) * scale - ry * scale * 0.15
                return (pt_sx, pt_sy, dist + ry, wx, wy, wz)

        # Hàm thêm 1 khối hộp 3D (Cuboid) vào danh sách vẽ
        def add_cuboid(cx, cy, cz, hx, hy, hz, base_color,
                       pitch=0.0, pivot_y=None, pivot_z=None,
                       tag=None, custom_colors=None):
            if pivot_y is None:
                pivot_y = cy
            if pivot_z is None:
                pivot_z = cz

            # 8 đỉnh khối hộp
            offsets = [
                (-hx, -hy, -hz),  # 0: Sau, Trái, Dưới
                ( hx, -hy, -hz),  # 1: Sau, Phải, Dưới
                ( hx,  hy, -hz),  # 2: Trước, Phải, Dưới
                (-hx,  hy, -hz),  # 3: Trước, Trái, Dưới
                (-hx, -hy,  hz),  # 4: Sau, Trái, Trên
                ( hx, -hy,  hz),  # 5: Sau, Phải, Trên
                ( hx,  hy,  hz),  # 6: Trước, Phải, Trên
                (-hx,  hy,  hz),  # 7: Trước, Trái, Trên
            ]

            pts = []
            for ox, oy, oz in offsets:
                pt = transform_point(cx + ox, cy + oy, cz + oz, pitch, pivot_y, pivot_z)
                if pt is None:
                    return
                pts.append(pt)

            # 6 mặt của khối hộp (định nghĩa theo thứ tự CCW nhìn từ bên ngoài)
            # Mỗi mặt gồm: (danh sách index đỉnh, normal vector cục bộ, tên mặt)
            faces_def = [
                ([2, 6, 7, 3], ( 0.0,  1.0,  0.0), "front"),   # Mặt trước (+Y)
                ([0, 4, 5, 1], ( 0.0, -1.0,  0.0), "back"),    # Mặt sau (-Y)
                ([1, 5, 6, 2], ( 1.0,  0.0,  0.0), "right"),   # Mặt bên phải (+X)
                ([3, 7, 4, 0], (-1.0,  0.0,  0.0), "left"),    # Mặt bên trái (-X)
                ([4, 7, 6, 5], ( 0.0,  0.0,  1.0), "top"),     # Mặt đỉnh trên (+Z)
                ([0, 1, 2, 3], ( 0.0,  0.0, -1.0), "bottom"),  # Mặt đáy dưới (-Z)
            ]

            cos_a = math.cos(self.angle)
            sin_a = math.sin(self.angle)

            for indices, (nx, ny, nz), fname in faces_def:
                p0, p1, p2, p3 = [pts[i] for i in indices]

                # Back-face culling dùng tích có hướng 2D (Shoelace cross product)
                # Trên Pygame, trục Y hướng xuống dưới nên cross > 0 là mặt hướng về phía người xem
                cross = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0])
                if cross <= 0:
                    continue  # Mặt quay vào trong hoặc quay ra sau -> loại bỏ

                # Độ sâu trung bình để sắp xếp Z-sorting
                avg_depth = (p0[2] + p1[2] + p2[2] + p3[2]) * 0.25

                # Vector pháp tuyến sang World Space để tính ánh sáng 3D
                wnx = -nx * sin_a + ny * cos_a
                wny =  nx * cos_a + ny * sin_a
                wnz = nz

                # Tính độ sáng Shading (từ 0.45 đến 1.25)
                dot_light = wnx * light_norm[0] + wny * light_norm[1] + wnz * light_norm[2]
                shade = max(0.45, min(1.22, 0.72 + 0.50 * dot_light))

                face_col = (custom_colors.get(fname, base_color) if custom_colors else base_color)
                shaded_col = (
                    max(0, min(255, int(face_col[0] * shade))),
                    max(0, min(255, int(face_col[1] * shade))),
                    max(0, min(255, int(face_col[2] * shade)))
                )

                poly_2d = [(int(p[0]), int(p[1])) for p in (p0, p1, p2, p3)]

                faces_to_render.append({
                    "depth": avg_depth,
                    "poly": poly_2d,
                    "color": shaded_col,
                    "tag": tag,
                    "fname": fname,
                    "pts": [p0, p1, p2, p3]
                })

        # =========================================================
        # DỰNG TẤT CẢ CÁC BỘ PHẬN HÌNH KHỐI ROBLOX 3D
        # =========================================================

        # Màu sắc phong cách nhân vật Roblox đặc nhiệm (Roblox Tactical Humanoid)
        skin_c = (252, 215, 65)         # Màu vàng da Roblox kinh điển
        shirt_c = (175, 42, 48)         # Áo đặc nhiệm đỏ sẫm Roblox
        vest_c = (38, 44, 54)           # Áo giáp chống đạn xám đen
        pants_c = (46, 52, 64)          # Quần chiến thuật xanh than
        boots_c = (20, 22, 28)          # Bốt quân sự đen khối
        gun_c = (30, 32, 38)            # Súng khối đen kim loại
        helmet_c = (35, 40, 48)         # Mũ bảo hiểm đặc nhiệm khối

        # Góc dao động chân & tay theo hoạt ảnh bước đi Roblox (Walking Animation)
        walk_swing = math.sin(self.walk_cycle) * 0.42 if self.walk_cycle != 0.0 else 0.0

        # --- 1. HAI CHÂN KHỐI 3D (LEGS) ---
        # Chân trái (xoay pitch quanh hông Z=24)
        add_cuboid(-3.8, 0.0, 12.0, 3.4, 3.6, 12.0, pants_c,
                   pitch=walk_swing, pivot_y=0.0, pivot_z=24.0, tag="leg_left")
        # Bốt trái
        add_cuboid(-3.8, 0.0, 3.5, 3.5, 3.7, 3.5, boots_c,
                   pitch=walk_swing, pivot_y=0.0, pivot_z=24.0, tag="boot_left")

        # Chân phải (ngược pha)
        add_cuboid(3.8, 0.0, 12.0, 3.4, 3.6, 12.0, pants_c,
                   pitch=-walk_swing, pivot_y=0.0, pivot_z=24.0, tag="leg_right")
        # Bốt phải
        add_cuboid(3.8, 0.0, 3.5, 3.5, 3.7, 3.5, boots_c,
                   pitch=-walk_swing, pivot_y=0.0, pivot_z=24.0, tag="boot_right")

        # --- 2. THÂN KHỐI 3D (TORSO) ---
        add_cuboid(0.0, 0.0, 38.0, 7.6, 4.2, 14.0, shirt_c, tag="torso")
        # Áo giáp chống đạn khối hộp (Tactical Armor Vest) đè ở ngực
        add_cuboid(0.0, 0.4, 39.5, 6.8, 4.2, 11.5, vest_c, tag="vest")
        # Thắt lưng khối đen có khóa bạc
        add_cuboid(0.0, 0.2, 26.5, 7.8, 4.4, 2.2, (22, 24, 30), tag="belt")

        # --- 3. CỔ (NECK) ---
        add_cuboid(0.0, 0.0, 52.8, 2.4, 2.4, 1.2, skin_c, tag="neck")

        # --- 4. ĐẦU KHỐI 3D (HEAD) ---
        add_cuboid(0.0, 0.0, 59.5, 5.0, 5.0, 5.5, skin_c, tag="head")

        # Mũ bảo hiểm đặc nhiệm khối 3D (Tactical Helmet)
        add_cuboid(0.0, 0.0, 63.2, 5.6, 5.6, 2.6, helmet_c, tag="helmet")
        # Vành mũ nhô ra phía trước
        add_cuboid(0.0, 3.2, 61.2, 5.8, 3.0, 1.0, (26, 30, 38), tag="visor")

        # --- 5. CÁNH TAY TRÁI KHỐI 3D (LEFT ARM) ---
        # Đung đưa ngược pha với chân trái
        add_cuboid(-11.4, 0.0, 38.5, 3.2, 3.6, 13.5, shirt_c,
                   pitch=-walk_swing * 0.75, pivot_y=0.0, pivot_z=50.0, tag="arm_left")
        # Bàn tay trái khối vàng Roblox
        add_cuboid(-11.4, 0.0, 27.5, 3.3, 3.7, 3.0, skin_c,
                   pitch=-walk_swing * 0.75, pivot_y=0.0, pivot_z=50.0, tag="hand_left")

        # --- 6. CÁNH TAY PHẢI CẦM SÚNG KHỐI 3D (RIGHT ARM & BLOCKY GUN) ---
        # Tay phải đưa ra phía trước tư thế cầm súng chĩa thẳng về phía trước
        gun_aim_pitch = 0.85 + walk_swing * 0.2
        add_cuboid(11.4, 0.0, 38.5, 3.2, 3.6, 13.5, shirt_c,
                   pitch=gun_aim_pitch, pivot_y=0.0, pivot_z=50.0, tag="arm_right")
        # Bàn tay phải
        add_cuboid(11.4, 0.0, 27.5, 3.3, 3.7, 3.0, skin_c,
                   pitch=gun_aim_pitch, pivot_y=0.0, pivot_z=50.0, tag="hand_right")

        # Khẩu súng trường khối Roblox (Blocky Rifle) gắn vào tay phải
        # Thân súng (Receiver)
        add_cuboid(11.4, 11.0, 36.5, 1.4, 8.5, 2.6, gun_c, tag="gun_body")
        # Băng đạn hộp vuông (Magazine)
        add_cuboid(11.4, 11.5, 30.5, 1.2, 2.6, 3.6, (18, 20, 26), tag="gun_mag")
        # Nòng súng khối (Barrel)
        add_cuboid(11.4, 23.0, 37.0, 0.9, 6.0, 1.2, (45, 48, 56), tag="gun_barrel")

        # =========================================================
        # SẮP XẾP Z-DEPTH (PAINTER'S ALGORITHM) VÀ VẼ CÁC MẶT ĐA GIÁC
        # =========================================================

        # Mặt xa vẽ trước, mặt gần vẽ sau
        faces_to_render.sort(key=lambda f: f["depth"], reverse=True)

        outline_c = (20, 22, 28)

        for f in faces_to_render:
            poly = f["poly"]
            color = f["color"]
            tag = f["tag"]
            fname = f["fname"]

            # Vẽ mặt đa giác 3D
            pygame.draw.polygon(screen, color, poly)
            # Viền nét cel-shading đen sắc nét chuẩn phong cách Roblox
            pygame.draw.polygon(screen, outline_c, poly, 1)

            # --- CHI TIẾT ĐẶC TRƯNG TRÊN CÁC MẶT ---

            # 1. Khuôn mặt Roblox kinh điển trên mặt Front của Đầu (Head)
            if tag == "head" and fname == "front":
                p0, p1, p2, p3 = f["pts"]
                # 4 đỉnh của mặt trước đầu: p0(dưới-phải), p1(trên-phải), p2(trên-trái), p3(dưới-trái)
                # Tính tâm và kích thước mặt trước
                mcx = (p0[0] + p1[0] + p2[0] + p3[0]) * 0.25
                mcy = (p0[1] + p1[1] + p2[1] + p3[1]) * 0.25
                mw = math.hypot(p0[0] - p3[0], p0[1] - p3[1])
                mh = math.hypot(p1[0] - p0[0], p1[1] - p0[1])

                if mw >= 6 and mh >= 6:
                    ew = max(1, int(mw * 0.14))
                    eh = max(2, int(mh * 0.22))
                    eye_y = int(mcy - mh * 0.08)

                    # Mắt trái Roblox (hình chữ nhật có chấm sáng trắng)
                    elx = int(mcx - mw * 0.22 - ew / 2)
                    pygame.draw.rect(screen, (20, 20, 20), (elx, eye_y, ew, eh))
                    if ew >= 2 and eh >= 2:
                        pygame.draw.rect(screen, (255, 255, 255), (elx, eye_y, max(1, ew // 2), max(1, eh // 2)))

                    # Mắt phải Roblox
                    erx = int(mcx + mw * 0.22 - ew / 2)
                    pygame.draw.rect(screen, (20, 20, 20), (erx, eye_y, ew, eh))
                    if ew >= 2 and eh >= 2:
                        pygame.draw.rect(screen, (255, 255, 255), (erx, eye_y, max(1, ew // 2), max(1, eh // 2)))

                    # Miệng Roblox (đường thẳng mím môi nghiêm nghị)
                    mouth_w = max(3, int(mw * 0.36))
                    mouth_y = int(mcy + mh * 0.24)
                    pygame.draw.line(screen, (20, 20, 20),
                                     (int(mcx - mouth_w / 2), mouth_y),
                                     (int(mcx + mouth_w / 2), mouth_y), max(1, int(mh * 0.06)))

            # 2. Huy hiệu áo giáp trên mặt Front của Vest
            elif tag == "vest" and fname == "front":
                p0, p1, p2, p3 = f["pts"]
                vc_x = (p0[0] + p1[0] + p2[0] + p3[0]) * 0.25
                vc_y = (p0[1] + p1[1] + p2[1] + p3[1]) * 0.25
                vw = math.hypot(p0[0] - p3[0], p0[1] - p3[1])
                vh = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
                if vw >= 8 and vh >= 8:
                    # 2 túi đạn khối hộp ở ngực
                    pw = max(2, int(vw * 0.30))
                    ph = max(2, int(vh * 0.35))
                    pygame.draw.rect(screen, (25, 28, 35),
                                     (int(vc_x - vw * 0.32), int(vc_y), pw, ph))
                    pygame.draw.rect(screen, (25, 28, 35),
                                     (int(vc_x + vw * 0.32 - pw), int(vc_y), pw, ph))

        # --- 7. TIA LỬ ĐẦU NÒNG SÚNG 3D (MUZZLE FLASH) ---
        if self.muzzle_flash_timer > 0:
            flash_pt = transform_point(11.4, 30.0, 37.0)
            if flash_pt:
                fx, fy = flash_pt[0], flash_pt[1]
                fr = max(5, int(bh * 0.12))
                # Ngọn lửa khối đa giác sắc cạnh 3D
                pygame.draw.polygon(screen, (255, 235, 90), [
                    (fx, fy - fr // 3),
                    (fx + fr, fy - fr // 2),
                    (fx + fr * 1.6, fy),
                    (fx + fr, fy + fr // 2),
                    (fx, fy + fr // 3)
                ])
                pygame.draw.polygon(screen, (255, 120, 20), [
                    (fx, fy - fr // 5),
                    (fx + fr * 0.9, fy),
                    (fx, fy + fr // 5)
                ])

        # --- 8. THANH MÁU VÀ GIÁP (HEALTH & ARMOR BAR) ---
        bar_w = max(28, int(bw * 1.3))
        bx = int(sx - bar_w / 2)
        by = int(btop - 18)
        # Nền thanh máu
        pygame.draw.rect(screen, (15, 18, 22), (bx - 1, by - 1, bar_w + 2, 7), border_radius=2)
        # Máu HP
        hp_ratio = max(0, self.hp) / 100.0
        hp_color = (60, 220, 100) if hp_ratio > 0.4 else ((240, 180, 40) if hp_ratio > 0.2 else (235, 60, 60))
        pygame.draw.rect(screen, hp_color, (bx, by, int(bar_w * hp_ratio), 5), border_radius=1)

        # Giáp Armor
        if self.armor > 0:
            pygame.draw.rect(screen, (70, 150, 240), (bx, by - 4, int(bar_w * min(1.0, self.armor / 50.0)), 3), border_radius=1)

        # Thông báo sát thương vừa nhận (HEAD / BODY / LEGS)
        now_ms = pygame.time.get_ticks()
        if font_small and hasattr(self, "last_hit_time") and now_ms - self.last_hit_time < 900:
            p_text = getattr(self, "last_hit_part", "body").upper()
            dmg_val = getattr(self, "last_hit_damage", 0)
            txt_col = (255, 60, 60) if p_text == "HEAD" else ((240, 200, 70) if p_text == "BODY" else (180, 190, 210))
            hit_surf = font_small.render(f"{p_text} -{int(dmg_val)}", True, txt_col)
            screen.blit(hit_surf, (sx - hit_surf.get_width() // 2, by - 20))