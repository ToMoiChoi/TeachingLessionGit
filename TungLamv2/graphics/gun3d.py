"""gun3d.py - Hệ thống mô hình súng 3D đồng bộ 100% với bộ ảnh skin súng gốc (assets/skin súng/*.png).

Hỗ trợ:
- Tách rời Khung súng + Khóa nòng/Slide (bolt) + Băng đạn/Ổ đạn (mag) + Đạn rời (shell) + Tay phải + Tay trái động.
- 3 chất liệu tô bóng 3D: MAT_STD (tiêu chuẩn), MAT_GLOW (pha lê/nham thạch/neon tự phát sáng), MAT_METAL (vàng kim/bạc/thép bóng).
- Tự động Cache Sprite tư thế tĩnh (_SPRITE_CACHE) giữ vững 60-120+ FPS trên cả Desktop và Web WASM.
- Kết xuất ảnh mặt ngang độ nét cao (render_side_icon) cho Shop / HUD / Súng rơi đối với các khẩu chưa có PNG riêng.
"""
import math
import pygame

MAT_STD = 0
MAT_GLOW = 1
MAT_METAL = 2

METAL = (62, 66, 74)
METAL_DARK = (32, 34, 40)
STEEL = (148, 154, 166)
SILVER = (214, 220, 232)
GOLD = (232, 186, 62)
CHAMPAGNE = (216, 186, 132)
COPPER = (208, 138, 68)
BRASS = (224, 180, 64)
SHELL_RED = (212, 42, 48)

GLOVE = (28, 31, 38)
GLOVE_PAD = (52, 58, 70)
GLOVE_TRIM = (78, 86, 102)
SLEEVE = (42, 54, 72)
SLEEVE_DARK = (28, 36, 48)
CUFF = (34, 40, 52)

LIGHT = (-0.42, -0.82, -0.38)
_l = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _l for c in LIGHT)
AMBIENT = 0.44


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(v):
    ln = math.sqrt(sum(c * c for c in v)) or 1.0
    return (v[0] / ln, v[1] / ln, v[2] / ln)


def _shade(c, k):
    r = int(c[0] * k)
    g = int(c[1] * k)
    b = int(c[2] * k)
    return (
        255 if r > 255 else (0 if r < 0 else r),
        255 if g > 255 else (0 if g < 0 else g),
        255 if b > 255 else (0 if b < 0 else b),
    )


class Model:
    def __init__(self):
        self.verts = []
        self.faces = []
        self.muzzle = (0.5, 0.0, 0.0)
        self.mag = None
        self.mag_hidden = False
        self.bolt = None
        self.shell = None
        self.right_arm = None
        self.sight_y = 0.06
        self.ads_z = 0.42

        self.fore_grip = (0.26, -0.025, -0.015)
        self.mag_grab = (0.06, -0.13, -0.01)
        self.mag_base = (0.07, -0.21, 0.0)
        self.bolt_grab = (-0.06, 0.055, -0.02)

    def new_mag(self, hidden=False):
        self.mag = Model()
        self.mag_hidden = hidden
        return self.mag

    def new_bolt(self):
        self.bolt = Model()
        return self.bolt

    def new_shell(self):
        self.shell = Model()
        return self.shell

    def new_right_arm(self):
        self.right_arm = Model()
        return self.right_arm

    def _add(self, pts, faces, color, mat=MAT_STD):
        base = len(self.verts)
        self.verts.extend(pts)
        for idx, n in faces:
            self.faces.append((tuple(base + i for i in idx), n, color, mat))

    def box(self, x0, x1, y0, y1, z0, z1, color, mat=MAT_STD):
        pts = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        self._add(pts, [
            ((0, 1, 3, 2), (-1, 0, 0)), ((4, 6, 7, 5), (1, 0, 0)),
            ((0, 4, 5, 1), (0, -1, 0)), ((2, 3, 7, 6), (0, 1, 0)),
            ((0, 2, 6, 4), (0, 0, -1)), ((1, 5, 7, 3), (0, 0, 1)),
        ], color, mat)

    def taper_x(self, x0, x1, y0a, y1a, za, y0b, y1b, zb, color, mat=MAT_STD):
        """Khối lăng trụ vát thuôn dọc theo trục X (dùng cho mũi giáo giảm thanh, đầu rồng, báng vát, gai đá)."""
        pts = [
            (x0, y0a, -za), (x0, y0a, za), (x0, y1a, -za), (x0, y1a, za),
            (x1, y0b, -zb), (x1, y0b, zb), (x1, y1b, -zb), (x1, y1b, zb),
        ]
        dx = max(1e-4, abs(x1 - x0))
        ny_top = _norm((-(y1b - y1a), dx, 0.0))
        ny_bot = _norm(((y0b - y0a), -dx, 0.0))
        nz_side = _norm((-(zb - za), 0.0, dx))
        self._add(pts, [
            ((0, 1, 3, 2), (-1, 0, 0)),
            ((4, 6, 7, 5), (1, 0, 0)),
            ((0, 4, 5, 1), ny_bot),
            ((2, 3, 7, 6), ny_top),
            ((0, 2, 6, 4), (nz_side[0], 0.0, -nz_side[2])),
            ((1, 5, 7, 3), nz_side),
        ], color, mat)

    def cyl(self, x0, x1, yc, zc, r, color, n=8, r1=None, mat=MAT_STD):
        r1 = r if r1 is None else r1
        pts = []
        for i in range(n):
            a = 2 * math.pi * (i + 0.5) / n
            ca, sa = math.cos(a), math.sin(a)
            pts.append((x0, yc + r * sa, zc + r * ca))
            pts.append((x1, yc + r1 * sa, zc + r1 * ca))
        faces = []
        for i in range(n):
            j = (i + 1) % n
            a = 2 * math.pi * (i + 1) / n
            faces.append(((2 * i, 2 * j, 2 * j + 1, 2 * i + 1), (0, math.sin(a), math.cos(a))))
        faces.append((tuple(2 * i for i in range(n)), (-1, 0, 0)))
        faces.append((tuple(2 * i + 1 for i in range(n)), (1, 0, 0)))
        self._add(pts, faces, color, mat)

    def extrude(self, poly, z0, z1, color, mat=MAT_STD):
        area = sum(
            poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
            for i in range(len(poly))
        )
        if area < 0:
            poly = poly[::-1]
        m = len(poly)
        pts = [(x, y, z0) for x, y in poly] + [(x, y, z1) for x, y in poly]
        faces = [(tuple(range(m)), (0, 0, -1)), (tuple(range(m, 2 * m)), (0, 0, 1))]
        for i in range(m):
            j = (i + 1) % m
            dx, dy = poly[j][0] - poly[i][0], poly[j][1] - poly[i][1]
            ln = math.hypot(dx, dy) or 1.0
            faces.append(((i, j, m + j, m + i), (dy / ln, -dx / ln, 0)))
        self._add(pts, faces, color, mat)

    def beam(self, p0, p1, w, h, color, mat=MAT_STD):
        d = [p1[i] - p0[i] for i in range(3)]
        ln = math.sqrt(sum(c * c for c in d)) or 1.0
        d = [c / ln for c in d]
        up = (0, 1, 0) if abs(d[1]) < 0.9 else (1, 0, 0)
        s = _norm(_cross(d, up))
        u = _cross(s, d)
        pts = []
        for p in (p0, p1):
            for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                pts.append(tuple(p[i] + s[i] * a * w / 2 + u[i] * b * h / 2 for i in range(3)))
        neg = tuple(-c for c in d)
        faces = [((0, 3, 2, 1), neg), ((4, 5, 6, 7), tuple(d))]
        for n, idx in ((s, (1, 2, 6, 5)), (tuple(-c for c in s), (3, 0, 4, 7)),
                       (u, (2, 3, 7, 6)), (tuple(-c for c in u), (0, 1, 5, 4))):
            faces.append((idx, tuple(n)))
        self._add(pts, faces, color, mat)


# ================================================================== CHI TIẾT CHUNG & CÁNH TAY TÁC CHIẾN
def _grip(m, color, x=-0.035, slope=0.035, length=0.115, z_half=0.016, mat=MAT_STD):
    m.extrude(
        [(x - 0.034, -0.02), (x + 0.02, -0.02),
         (x + 0.02 - slope, -0.02 - length), (x - 0.034 - slope, -0.02 - length + 0.01)],
        -z_half, z_half, color, mat,
    )


def _trigger_guard(m, guard_col, trig_col=STEEL, x=0.0, guard_mat=MAT_STD, trig_mat=MAT_METAL):
    m.extrude([
        (x - 0.008, -0.022), (x - 0.002, -0.050), (x + 0.044, -0.050),
        (x + 0.054, -0.022), (x + 0.046, -0.022), (x + 0.038, -0.043), (x + 0.004, -0.043),
    ], -0.006, 0.006, guard_col, guard_mat)
    m.extrude([
        (x + 0.012, -0.020), (x + 0.021, -0.020), (x + 0.016, -0.040), (x + 0.009, -0.038),
    ], -0.003, 0.003, trig_col, trig_mat)


def _right_hand(m, pistol=False):
    """Dựng tay phải tác chiến riêng vào m.right_arm (để xuất icon súng không bị dính cánh tay)."""
    ra = m.new_right_arm()
    gx0 = -0.090 if pistol else -0.100
    ra.box(gx0, -0.014, -0.108, -0.030, -0.024, 0.028, GLOVE)
    ra.box(gx0 + 0.008, -0.004, -0.050, -0.026, 0.014, 0.031, GLOVE_PAD, MAT_METAL)
    ra.box(-0.022, 0.018, -0.040, -0.025, 0.005, 0.024, GLOVE)  # Ngón trỏ đặt lên cò
    wrist = (-0.084, -0.102, 0.018)
    shoulder = (-0.38, -0.39, 0.17)
    ra.beam(wrist, (-0.13, -0.15, 0.045), 0.056, 0.052, CUFF)
    ra.beam((-0.12, -0.14, 0.04), shoulder, 0.070, 0.064, SLEEVE)
    ra.beam((-0.14, -0.16, 0.055), (-0.25, -0.27, 0.11), 0.073, 0.030, SLEEVE_DARK)


def _build_left_arm_model(hand_pos):
    """Dựng động cánh tay trái + găng chiến thuật bám theo hand_pos."""
    arm = Model()
    hx, hy, hz = hand_pos
    shoulder = (-0.34, -0.40, -0.27)
    elbow = (
        (hx + shoulder[0]) * 0.5 - 0.05,
        min(hy, shoulder[1]) * 0.55 + (hy + shoulder[1]) * 0.45 - 0.05,
        (hz + shoulder[2]) * 0.5 - 0.04,
    )
    wrist = (hx - 0.032, hy - 0.025, hz - 0.018)
    arm.beam(shoulder, elbow, 0.068, 0.064, SLEEVE)
    arm.beam(elbow, wrist, 0.062, 0.058, SLEEVE)
    arm.beam(wrist, (hx - 0.012, hy - 0.01, hz - 0.008), 0.054, 0.050, CUFF)
    arm.box(hx - 0.036, hx + 0.036, hy - 0.030, hy + 0.024, hz - 0.026, hz + 0.024, GLOVE)
    arm.box(hx - 0.026, hx + 0.028, hy - 0.012, hy + 0.026, hz - 0.031, hz - 0.018, GLOVE_PAD, MAT_METAL)
    arm.box(hx - 0.020, hx + 0.022, hy + 0.002, hy + 0.020, hz - 0.033, hz - 0.026, GLOVE_TRIM)
    return arm


def _add_mag_bullet(mg, x_center, y_top, col_case=BRASS, col_tip=COPPER):
    mg.cyl(x_center - 0.024, x_center + 0.008, y_top + 0.006, 0.0, 0.0065, col_case, n=6, mat=MAT_METAL)
    mg.cyl(x_center + 0.008, x_center + 0.024, y_top + 0.006, 0.0, 0.0062, col_tip, n=6, r1=0.002, mat=MAT_METAL)


# ================================================================== 1. PISTOLS (CLASSIC, GHOST, SHERIFF)
def _build_classic():
    """CLASSIC -> classic.png (Prime Classic: Trắng bạc - Vàng hoàng kim - Báng tím - Pha lê xanh băng)."""
    m = Model()
    white_silver = (224, 230, 240)
    prime_gold = (238, 190, 52)
    obsidian = (34, 36, 44)
    royal_purple = (94, 58, 146)
    purple_dark = (68, 40, 108)
    ice_crystal = (146, 212, 255)

    L = 0.165
    # Khung dưới đen mờ vát chéo + chi tiết vàng kim
    m.extrude([(-0.054, 0.004), (L - 0.008, 0.004), (L - 0.022, -0.022), (0.015, -0.026), (-0.054, -0.022)],
              -0.013, 0.013, obsidian)
    m.box(-0.044, -0.008, -0.010, 0.002, -0.015, 0.015, prime_gold, MAT_METAL)
    m.cyl(-0.01, L + 0.005, 0.017, 0.0, 0.0065, prime_gold, n=6, mat=MAT_METAL)  # Nòng vàng lộ khi slide lùi
    # Búa đập vàng phía đuôi súng
    m.extrude([(-0.068, 0.008), (-0.054, 0.024), (-0.048, 0.018), (-0.060, -0.002)], -0.004, 0.004, prime_gold, MAT_METAL)

    # Báng tím có gân ngang + khung tam giác vàng chứa pha lê xanh băng phát sáng!
    _grip(m, royal_purple, x=-0.022, slope=0.036, length=0.112, z_half=0.015)
    for k in range(4):
        gy = -0.042 - k * 0.021
        gx = -0.026 - k * 0.007
        m.box(gx - 0.028, gx + 0.016, gy - 0.006, gy, -0.0165, 0.0165, purple_dark)
    # Đế tam giác vàng + lõi pha lê xanh băng
    m.extrude([(-0.094, -0.136), (-0.036, -0.126), (-0.050, -0.092)], -0.017, 0.017, prime_gold, MAT_METAL)
    m.extrude([(-0.084, -0.130), (-0.045, -0.123), (-0.055, -0.100)], -0.018, 0.018, ice_crystal, MAT_GLOW)
    _trigger_guard(m, prime_gold, trig_col=(132, 92, 188), x=-0.002, guard_mat=MAT_METAL)

    # Slide trắng bạc viền vàng hoàng kim mảnh sắc sảo (m.bolt)
    bl = m.new_bolt()
    bl.box(-0.056, 0.016, 0.004, 0.038, -0.015, 0.015, white_silver, MAT_METAL)
    bl.box(0.056, L, 0.004, 0.038, -0.015, 0.015, white_silver, MAT_METAL)
    bl.box(0.016, 0.056, 0.004, 0.038, -0.015, 0.003, white_silver, MAT_METAL)  # Cửa hất vỏ đạn
    # Ốp đen tam giác phía đuôi slide + tia sáng trắng
    bl.extrude([(-0.054, 0.007), (-0.004, 0.007), (-0.050, 0.030)], -0.0158, 0.0158, obsidian)
    bl.beam((-0.046, 0.013, 0.0165), (-0.014, 0.022, 0.0165), 0.004, 0.004, SILVER, MAT_GLOW)
    bl.beam((-0.046, 0.013, -0.0165), (-0.014, 0.022, -0.0165), 0.004, 0.004, SILVER, MAT_GLOW)
    # Viền vàng kim mảnh dọc hai mép trên & dưới slide (giữ mặt lưng trắng bạc nổi bật đúng classic.png!)
    bl.box(-0.058, 0.020, 0.035, 0.040, -0.0158, -0.009, prime_gold, MAT_METAL)
    bl.box(-0.058, 0.020, 0.035, 0.040, 0.009, 0.0158, prime_gold, MAT_METAL)
    bl.box(0.068, L + 0.003, 0.035, 0.040, -0.0158, 0.0158, prime_gold, MAT_METAL)
    bl.box(-0.056, L + 0.001, 0.002, 0.007, -0.016, 0.016, prime_gold, MAT_METAL)
    bl.extrude([(L - 0.028, 0.040), (L - 0.004, 0.040), (L - 0.012, 0.050)], -0.004, 0.004, prime_gold, MAT_METAL)
    bl.box(-0.056, -0.040, 0.040, 0.048, -0.011, 0.011, prime_gold, MAT_METAL)

    # Băng đạn rời (m.mag)
    mg = m.new_mag(hidden=True)
    mg.extrude([(-0.050, -0.025), (-0.008, -0.025), (-0.040, -0.126), (-0.082, -0.122)], -0.011, 0.011, purple_dark)
    mg.box(-0.088, -0.034, -0.136, -0.123, -0.015, 0.015, prime_gold, MAT_METAL)
    _add_mag_bullet(mg, -0.026, -0.025)

    _right_hand(m, pistol=True)
    m.fore_grip = (-0.042, -0.072, -0.024)
    m.mag_grab = (-0.058, -0.115, -0.008)
    m.mag_base = (-0.062, -0.145, 0.0)
    m.bolt_grab = (-0.025, 0.034, -0.012)
    m.sight_y, m.ads_z = 0.066, 0.35
    m.muzzle = (L + 0.005, 0.020, 0.0)
    return m


def _build_ghost():
    """GHOST -> ghost.png (Sovereign Blade Ghost: Giảm thanh mũi giáo bạc, vỏ bạc-xanh uốn cánh chim, báng đen)."""
    m = Model()
    blade_silver = (176, 188, 206)
    blade_edge = (218, 226, 240)
    dark_core = (26, 28, 34)
    slate_mid = (118, 128, 144)

    L = 0.165
    # Khung trong & báng đen công thái học
    m.box(-0.062, L, -0.018, 0.016, -0.012, 0.012, dark_core)
    _grip(m, dark_core, x=-0.026, slope=0.038, length=0.114, z_half=0.015)
    m.extrude([(-0.052, -0.042), (-0.024, -0.042), (-0.052, -0.118), (-0.076, -0.112)], -0.016, 0.016, (40, 44, 52))
    # Cánh bảo vệ bạc-xanh uốn từ thân trước bọc vòng xuống dưới cò súng (đúng dáng ghost.png!)
    m.extrude([
        (0.088, 0.012), (0.042, 0.012), (0.012, -0.052), (-0.018, -0.054),
        (-0.014, -0.044), (0.018, -0.040), (0.048, 0.004),
    ], -0.014, 0.014, blade_silver, MAT_METAL)
    m.box(0.018, 0.078, -0.048, -0.036, -0.011, 0.011, dark_core)
    m.box(-0.002, 0.006, -0.038, -0.018, -0.003, 0.003, dark_core)  # Cò súng đen sắc cạnh

    # Ống giảm thanh vát nhọn hình lưỡi giáo bạc (x = 0.165 -> 0.365)
    m.taper_x(L - 0.005, L + 0.045, 0.004, 0.030, 0.012, -0.002, 0.034, 0.016, slate_mid, MAT_METAL)
    m.taper_x(L + 0.045, L + 0.205, -0.002, 0.034, 0.016, 0.014, 0.022, 0.004, blade_silver, MAT_METAL)
    m.beam((L + 0.04, 0.018, 0.0), (L + 0.205, 0.018, 0.0), 0.034, 0.004, blade_edge, MAT_METAL)

    # Khối trượt trên bạc-xanh có mỏ nhọn phía đầu (m.bolt)
    bl = m.new_bolt()
    bl.extrude([
        (-0.058, 0.014), (L + 0.012, 0.014), (L + 0.024, 0.038),
        (L - 0.010, 0.036), (-0.048, 0.038), (-0.064, 0.024),
    ], -0.015, 0.015, blade_silver, MAT_METAL)
    bl.box(-0.066, -0.046, 0.012, 0.032, -0.014, 0.014, dark_core)
    bl.box(-0.058, -0.048, 0.020, 0.024, -0.015, 0.015, (230, 242, 255), MAT_GLOW)  # Đèn trắng nhỏ bên hông

    mg = m.new_mag(hidden=True)
    mg.extrude([(-0.052, -0.025), (-0.010, -0.025), (-0.044, -0.128), (-0.084, -0.124)], -0.011, 0.011, dark_core)
    _add_mag_bullet(mg, -0.028, -0.025, col_case=SILVER, col_tip=blade_silver)

    _right_hand(m, pistol=True)
    m.fore_grip = (-0.042, -0.072, -0.024)
    m.mag_grab = (-0.058, -0.115, -0.008)
    m.mag_base = (-0.062, -0.145, 0.0)
    m.bolt_grab = (-0.025, 0.032, -0.012)
    m.sight_y, m.ads_z = 0.058, 0.35
    m.muzzle = (L + 0.205, 0.018, 0.0)
    return m


def _build_sheriff():
    """SHERIFF -> sheriff.png (Neo Frontier Western Revolver: Thép đen ánh đồng, búa bạc, báng gỗ óc chó cong)."""
    m = Model()
    blued_steel = (46, 50, 58)
    bronze_frame = (78, 72, 68)
    nickel = (192, 196, 204)
    walnut = (102, 56, 38)
    walnut_hi = (132, 78, 52)

    # Khung ổ quay bằng thép pha đồng cổ + nòng dài thép đen bóng
    m.box(-0.052, 0.050, -0.022, 0.038, -0.012, 0.012, bronze_frame, MAT_METAL)
    m.cyl(0.050, 0.258, 0.024, 0.0, 0.0105, blued_steel, n=8, mat=MAT_METAL)
    m.box(0.048, 0.256, 0.032, 0.041, -0.006, 0.006, blued_steel, MAT_METAL)   # Sống nòng trên
    m.box(0.050, 0.195, 0.004, 0.015, -0.007, 0.007, bronze_frame, MAT_METAL)  # Ốp cần đẩy vỏ đạn dưới nòng
    m.box(0.238, 0.252, 0.041, 0.049, -0.0025, 0.0025, nickel, MAT_METAL)      # Đầu ruồi thép bạc cổ điển
    m.box(-0.046, 0.046, 0.038, 0.045, -0.009, 0.009, nickel, MAT_METAL)       # Thanh ngắm trên ổ quay

    # Ổ quay 6 viên thép đen bóng + viền đồng mảnh (m.mag bật ngang khi nạp)
    cyl_mag = m.new_mag(hidden=False)
    cyl_mag.cyl(-0.008, 0.048, 0.013, 0.0, 0.024, blued_steel, n=8, mat=MAT_METAL)
    cyl_mag.box(0.002, 0.036, 0.010, 0.022, -0.0252, 0.0252, (74, 78, 88), MAT_METAL)  # Rãnh khía ổ quay
    cyl_mag.cyl(-0.005, -0.002, 0.013, 0.0, 0.0246, BRASS, n=8, mat=MAT_METAL)          # Viền đồng mảnh quanh ổ quay

    # Búa đập mạ bạc uốn cong cổ điển Viễn Tây (m.bolt)
    bl = m.new_bolt()
    bl.extrude([(-0.072, 0.030), (-0.056, 0.052), (-0.044, 0.048), (-0.048, 0.026)], -0.004, 0.004, nickel, MAT_METAL)

    # Speedloader 6 viên đồng khi nạp
    sh = m.new_shell()
    sh.cyl(-0.035, -0.010, 0.013, -0.052, 0.020, METAL_DARK, n=6)
    sh.cyl(-0.010, 0.025, 0.013, -0.052, 0.016, BRASS, n=6, mat=MAT_METAL)

    # Báng gỗ óc chó loe cong kiểu cao bồi + đinh ốc bạc
    m.extrude([
        (-0.054, -0.008), (-0.018, -0.020), (-0.046, -0.082),
        (-0.062, -0.138), (-0.114, -0.132), (-0.092, -0.068),
    ], -0.016, 0.016, walnut)
    m.extrude([(-0.056, -0.014), (-0.028, -0.024), (-0.046, -0.052), (-0.068, -0.042)], -0.017, 0.017, walnut_hi)
    m.box(-0.074, -0.068, -0.076, -0.070, -0.018, 0.018, nickel, MAT_METAL)
    _trigger_guard(m, nickel, trig_col=blued_steel, x=-0.012, guard_mat=MAT_METAL)

    _right_hand(m, pistol=True)
    m.fore_grip = (-0.048, -0.076, -0.024)
    m.mag_grab = (0.015, 0.005, -0.052)
    m.bolt_grab = (-0.056, 0.044, 0.0)
    m.sight_y, m.ads_z = 0.068, 0.35
    m.muzzle = (0.258, 0.024, 0.0)
    return m


# ================================================================== 2. SMGS (MP5, UMP)
def _build_mp5():
    """MP5 -> mp5.png (Jade Crystal Spectre: Giảm thanh pha lê ngọc lục bảo, thân trắng ngọc trai viền vàng kim)."""
    m = Model()
    jade = (88, 232, 132)
    jade_deep = (46, 178, 96)
    pearl = (230, 234, 240)
    gold = (212, 180, 124)

    # Thân trắng ngọc trai viền vàng champagne + ngọc lục bảo ở giữa
    m.extrude([(-0.12, -0.024), (0.14, -0.024), (0.18, 0.042), (-0.08, 0.046)], -0.020, 0.020, pearl, MAT_METAL)
    m.box(-0.11, 0.16, 0.040, 0.050, -0.021, 0.021, gold, MAT_METAL)
    m.extrude([(0.02, 0.012), (0.055, 0.028), (0.02, 0.042), (-0.015, 0.028)], -0.022, 0.022, jade, MAT_GLOW)

    # Ốp nòng lõi ngọc lục bảo phát sáng bọc khung móng vàng trên & dưới
    m.box(0.14, 0.33, -0.018, 0.036, -0.022, 0.022, jade, MAT_GLOW)
    m.extrude([(0.14, 0.036), (0.34, 0.036), (0.355, 0.052), (0.13, 0.048)], -0.024, 0.024, gold, MAT_METAL)
    m.extrude([(0.13, -0.018), (0.33, -0.018), (0.35, -0.038), (0.31, -0.030), (0.14, -0.030)],
              -0.024, 0.024, gold, MAT_METAL)

    # Ống giảm thanh tinh thể ngọc lục bảo vát nhọn + con mắt vàng ở giữa (đúng mp5.png!)
    m.taper_x(0.35, 0.43, -0.006, 0.034, 0.020, -0.010, 0.038, 0.024, jade_deep, MAT_GLOW)
    m.taper_x(0.43, 0.57, -0.010, 0.038, 0.024, 0.008, 0.022, 0.006, jade, MAT_GLOW)
    m.extrude([(0.40, 0.014), (0.435, 0.028), (0.47, 0.014), (0.435, 0.000)], -0.026, 0.026, gold, MAT_METAL)

    # Khóa nòng vàng (m.bolt)
    bl = m.new_bolt()
    bl.box(0.20, 0.24, 0.028, 0.046, -0.032, -0.014, gold, MAT_METAL)

    # Băng đạn cong pha lê ngọc lục bảo viền vàng champagne (m.mag)
    mg = m.new_mag()
    mg.extrude([(0.045, -0.022), (0.105, -0.022), (0.158, -0.195), (0.094, -0.208)], -0.014, 0.014, jade, MAT_GLOW)
    mg.extrude([(0.042, -0.022), (0.064, -0.022), (0.114, -0.205), (0.090, -0.212)], -0.016, 0.016, gold, MAT_METAL)
    mg.box(0.092, 0.162, -0.218, -0.196, -0.017, 0.017, gold, MAT_METAL)
    _add_mag_bullet(mg, 0.075, -0.022, col_case=gold, col_tip=jade)

    # Tay cầm trắng ngọc trai viền vàng + báng thanh xanh đuôi vàng uốn cong
    _grip(m, pearl, x=-0.035, slope=0.042, length=0.112, z_half=0.016, mat=MAT_METAL)
    m.box(-0.112, -0.052, -0.138, -0.124, -0.018, 0.018, gold, MAT_METAL)
    _trigger_guard(m, gold, trig_col=jade, guard_mat=MAT_METAL, trig_mat=MAT_GLOW)
    m.cyl(-0.27, -0.11, 0.024, 0.0, 0.008, jade_deep, n=6, mat=MAT_GLOW)
    m.extrude([(-0.26, 0.042), (-0.34, 0.036), (-0.36, -0.078), (-0.31, -0.082), (-0.28, -0.010)],
              -0.019, 0.019, gold, MAT_METAL)
    m.extrude([(-0.27, 0.034), (-0.32, 0.028), (-0.33, -0.056), (-0.29, -0.012)], -0.020, 0.020, pearl, MAT_METAL)

    # Thước ngắm vàng đính ngọc xanh
    m.box(-0.04, 0.03, 0.050, 0.068, -0.012, 0.012, gold, MAT_METAL)
    m.box(-0.01, 0.005, 0.062, 0.074, -0.004, 0.004, jade, MAT_GLOW)

    _right_hand(m)
    m.fore_grip = (0.235, -0.022, -0.018)
    m.mag_grab = (0.095, -0.130, -0.010)
    m.mag_base = (0.125, -0.212, 0.0)
    m.bolt_grab = (0.218, 0.038, -0.028)
    m.sight_y, m.ads_z = 0.088, 0.38
    m.muzzle = (0.57, 0.015, 0.0)
    return m


def _build_ump():
    """UMP -> ump.png (ARC Obsidian-Violet & Copper SMG: Đen tím than, cuộn đồng, băng thẳng 6 vạch tím sáng)."""
    m = Model()
    obsidian = (34, 32, 44)
    slate_violet = (54, 48, 68)
    arc_copper = (218, 152, 72)
    neon_violet = (206, 102, 255)
    olive_pad = (76, 72, 66)

    # Thân sci-fi dài liền mạch + cầu ngắm trên (carry handle)
    m.box(-0.18, 0.34, -0.018, 0.040, -0.021, 0.021, obsidian)
    m.box(0.14, 0.36, -0.036, -0.016, -0.019, 0.019, olive_pad)
    m.taper_x(0.34, 0.41, 0.005, 0.034, 0.015, 0.012, 0.032, 0.011, slate_violet, MAT_METAL)
    # Quai xách / cầu ngắm trên
    m.extrude([(0.02, 0.040), (0.31, 0.040), (0.28, 0.066), (0.05, 0.066)], -0.013, 0.013, slate_violet)
    m.box(0.08, 0.25, 0.042, 0.054, -0.015, 0.015, (18, 18, 24))  # Khe rỗng dưới cầu ngắm
    m.box(0.26, 0.30, 0.066, 0.076, -0.008, 0.008, arc_copper, MAT_METAL)
    m.box(0.12, 0.19, 0.066, 0.078, -0.012, 0.012, obsidian)

    # Cụm cuộn dây đồng ARC ở giữa thân + rãnh năng lượng tím mảnh chạy dọc hông (đúng ump.png!)
    m.cyl(0.08, 0.16, 0.020, 0.0, 0.025, obsidian, n=8)
    m.cyl(0.09, 0.11, 0.020, 0.0, 0.0268, arc_copper, n=8, mat=MAT_METAL)
    m.cyl(0.13, 0.15, 0.020, 0.0, 0.0268, arc_copper, n=8, mat=MAT_METAL)
    for zs in (-0.0216, 0.0216):
        m.beam((-0.14, 0.020, zs), (0.07, 0.020, zs), 0.005, 0.002, neon_violet, MAT_GLOW)
        m.beam((0.17, 0.020, zs), (0.32, 0.020, zs), 0.005, 0.002, neon_violet, MAT_GLOW)

    # Khóa nòng đồng (m.bolt)
    bl = m.new_bolt()
    bl.box(0.18, 0.22, 0.028, 0.044, -0.032, -0.015, arc_copper, MAT_METAL)

    # Băng đạn thẳng đứng (90 độ) có 6 vạch đèn tím neon phát sáng (đúng ump.png!)
    mg = m.new_mag()
    mg.box(0.068, 0.116, -0.228, -0.020, -0.014, 0.014, obsidian)
    for k in range(6):
        vy = -0.048 - k * 0.026
        mg.box(0.084, 0.102, vy - 0.004, vy, -0.0155, 0.0155, neon_violet, MAT_GLOW)
    mg.box(0.065, 0.119, -0.240, -0.226, -0.016, 0.016, arc_copper, MAT_METAL)
    _add_mag_bullet(mg, 0.092, -0.020, col_case=arc_copper, col_tip=neon_violet)

    # Tay cầm vát + cò đồng + báng khung tam giác rỗng
    _grip(m, olive_pad, x=-0.036, slope=0.040, length=0.112, z_half=0.016)
    _trigger_guard(m, obsidian, trig_col=arc_copper, trig_mat=MAT_METAL)
    m.box(-0.36, -0.18, 0.005, 0.042, -0.020, 0.020, obsidian)
    m.beam((-0.16, -0.018, 0.0), (-0.35, -0.065, 0.0), 0.032, 0.022, obsidian)
    m.box(-0.37, -0.33, -0.075, 0.044, -0.021, 0.021, olive_pad)

    _right_hand(m)
    m.fore_grip = (0.235, -0.026, -0.018)
    m.mag_grab = (0.092, -0.135, -0.010)
    m.mag_base = (0.092, -0.242, 0.0)
    m.bolt_grab = (0.200, 0.036, -0.028)
    m.sight_y, m.ads_z = 0.108, 0.38
    m.muzzle = (0.41, 0.022, 0.0)
    return m


# ================================================================== 3. SHOTGUNS (M014 GAIA, MAG-7 ELDERFLAME DRAGON)
def _build_m1014():
    """M014 -> m1014.png (Gaia's Vengeance: Cành cây trắng bạc uốn xoắn ôm lõi pha lê đỏ Ruby + lá đỏ)."""
    m = Model()
    bark_light = (192, 200, 214)
    bark_mid = (146, 156, 174)
    ruby = (238, 38, 56)
    ruby_deep = (176, 20, 36)
    leaf_red = (196, 34, 42)

    # Lõi pha lê đỏ Ruby phát sáng chạy xuyên từ thân ra mũi nhọn pha lê!
    m.cyl(-0.08, 0.52, 0.020, 0.0, 0.016, ruby_deep, n=6, mat=MAT_GLOW)
    m.taper_x(0.48, 0.62, 0.006, 0.034, 0.015, 0.016, 0.026, 0.004, ruby, MAT_GLOW)

    # Hệ thống cành cây cổ thụ trắng bạc đan chéo ôm quanh lõi Ruby (đúng m1014.png!)
    m.beam((-0.14, 0.036, 0.0), (0.48, 0.038, 0.0), 0.034, 0.016, bark_light)
    m.beam((-0.12, -0.012, 0.016), (0.22, 0.026, 0.020), 0.016, 0.018, bark_light)
    m.beam((-0.12, -0.012, -0.016), (0.22, 0.026, -0.020), 0.016, 0.018, bark_light)
    m.beam((0.10, 0.032, 0.018), (0.46, -0.006, 0.014), 0.015, 0.016, bark_mid)
    m.beam((0.10, 0.032, -0.018), (0.46, -0.006, -0.014), 0.015, 0.016, bark_mid)
    m.beam((0.02, -0.024, 0.0), (0.42, -0.018, 0.0), 0.030, 0.016, bark_mid)
    # Nhánh gai nhọn vươn ra ở đầu nòng & ốp tay
    m.beam((0.38, 0.034, 0.0), (0.50, 0.054, 0.0), 0.012, 0.010, bark_light)
    m.beam((0.16, -0.022, 0.0), (0.28, -0.046, 0.0), 0.016, 0.012, bark_light)

    # Báng rễ cây uốn vòng hở nghệ thuật + tay cầm rễ cây liền khối
    m.beam((-0.10, 0.028, 0.0), (-0.44, -0.024, 0.0), 0.028, 0.020, bark_light)
    m.beam((-0.16, 0.018, 0.0), (-0.42, 0.034, 0.0), 0.020, 0.014, bark_mid)
    m.beam((-0.06, -0.020, 0.0), (-0.22, -0.098, 0.0), 0.026, 0.018, bark_mid)   # Tay cầm rễ cây
    m.beam((-0.22, -0.098, 0.0), (-0.44, -0.088, 0.0), 0.022, 0.015, bark_light)
    m.beam((-0.44, -0.024, 0.0), (-0.45, -0.095, 0.0), 0.024, 0.018, bark_mid)

    # Lá phong đỏ rủ xuống dưới nòng, ốp tay và trong hốc báng
    for lx, ly in ((0.50, -0.006), (0.24, -0.052), (-0.24, -0.112), (-0.36, 0.012)):
        m.extrude([(lx, ly), (lx + 0.022, ly - 0.014), (lx + 0.006, ly - 0.028), (lx - 0.012, ly - 0.012)],
                  -0.003, 0.003, leaf_red, MAT_GLOW)

    _trigger_guard(m, bark_mid, trig_col=ruby, trig_mat=MAT_GLOW)

    # Khóa nòng cành bạc & đạn pha lê đỏ khi nhét đạn dưới bụng
    bl = m.new_bolt()
    bl.box(0.02, 0.11, 0.014, 0.032, 0.016, 0.024, bark_light, MAT_METAL)
    sh = m.new_shell()
    sh.cyl(0.012, 0.068, -0.038, 0.0, 0.010, ruby, n=6, mat=MAT_GLOW)
    sh.cyl(0.000, 0.014, -0.038, 0.0, 0.0105, bark_light, n=6, mat=MAT_METAL)

    _right_hand(m)
    m.fore_grip = (0.285, -0.022, -0.018)
    m.mag_grab = (0.045, -0.048, -0.010)
    m.bolt_grab = (0.075, 0.026, 0.028)
    m.sight_y, m.ads_z = 0.078, 0.45
    m.muzzle = (0.62, 0.020, 0.0)
    return m


def _build_mag7():
    """MAG-7 -> mag-7.png (Elderflame Dragon Judge: Súng Rồng Lửa Hắc Ám quắp cầu đá dung nham!)."""
    m = Model()
    scale_dark = (62, 58, 78)
    scale_hi = (88, 82, 108)
    belly_brown = (96, 78, 68)
    horn_bone = (182, 164, 142)
    lava_fire = (255, 192, 42)
    lava_deep = (242, 112, 24)
    rock_dark = (52, 48, 52)

    # Thân rồng bọc vảy giáp tím than + bụng nâu sẫm
    m.box(-0.14, 0.36, -0.008, 0.040, -0.025, 0.025, scale_dark)
    m.box(-0.08, 0.38, -0.028, -0.005, -0.022, 0.022, belly_brown)
    # 5 lớp vảy giáp xếp chồng dọc sống lưng + khe lửa nham thạch vàng cam!
    for i in range(5):
        sx = -0.08 + i * 0.085
        m.extrude([(sx, 0.036), (sx + 0.075, 0.036), (sx + 0.055, 0.055), (sx - 0.010, 0.048)],
                  -0.022, 0.022, scale_hi, MAT_METAL)
        if i in (2, 3):
            m.box(sx + 0.015, sx + 0.045, 0.022, 0.042, -0.026, 0.026, lava_fire, MAT_GLOW)
    # Gai xương trên sống lưng rồng
    for gx in (0.02, 0.20):
        m.extrude([(gx, 0.052), (gx + 0.045, 0.052), (gx + 0.010, 0.078)], -0.006, 0.006, horn_bone)

    # ĐẦU RỒNG HẮC ÁM PHUN LỬA Ở ĐẦU NÒNG (x = 0.36 -> 0.54)!
    # Sọ trên + sừng mũi + 2 sừng chóp đầu quặp ra sau + mắt rồng rực sáng
    m.taper_x(0.36, 0.53, 0.016, 0.052, 0.028, 0.020, 0.044, 0.018, scale_dark, MAT_METAL)
    m.extrude([(0.49, 0.042), (0.53, 0.040), (0.515, 0.072)], -0.006, 0.006, horn_bone)  # Sừng mũi rồng!
    m.beam((0.40, 0.048, 0.018), (0.33, 0.074, 0.030), 0.014, 0.012, horn_bone)            # Sừng phải
    m.beam((0.40, 0.048, -0.018), (0.33, 0.074, -0.030), 0.014, 0.012, horn_bone)          # Sừng trái
    m.box(0.43, 0.46, 0.034, 0.042, -0.026, 0.026, lava_fire, MAT_GLOW)                    # Đôi mắt lửa!
    # Hàm dưới há rộng + lõi lửa & răng nanh nham thạch rực cháy!
    m.taper_x(0.36, 0.51, -0.032, 0.002, 0.024, -0.046, -0.014, 0.016, belly_brown)
    m.box(0.41, 0.50, -0.018, 0.022, -0.016, 0.016, lava_deep, MAT_GLOW)
    for fx in (0.44, 0.48, 0.51):
        m.box(fx, fx + 0.014, 0.008, 0.022, -0.015, 0.015, lava_fire, MAT_GLOW)
        m.box(fx, fx + 0.014, -0.024, -0.008, -0.014, 0.014, lava_fire, MAT_GLOW)

    # Hai chân trước của rồng quắp xuống ổ đạn (m.bolt trượt nhẹ khi kéo đạn)
    bl = m.new_bolt()
    bl.beam((0.18, 0.008, 0.024), (0.12, -0.055, 0.032), 0.022, 0.018, scale_hi)
    bl.beam((0.18, 0.008, -0.024), (0.12, -0.055, -0.032), 0.022, 0.018, scale_hi)

    # QUẢ CẦU ĐÁ DUNG NHAM NỨT SÁNG LÀM Ổ ĐẠN (m.mag tháo/lắp khi nạp đạn!)
    mg = m.new_mag()
    mg.cyl(0.02, 0.16, -0.092, 0.0, 0.068, rock_dark, n=8)
    mg.cyl(0.00, 0.18, -0.092, 0.0, 0.052, rock_dark, n=8)
    # Vết nứt dung nham chữ Z phát sáng rực rỡ hai bên quả cầu đá!
    mg.beam((0.05, -0.062, 0.054), (0.11, -0.105, 0.054), 0.012, 0.010, lava_fire, MAT_GLOW)
    mg.beam((0.11, -0.105, 0.054), (0.07, -0.132, 0.054), 0.012, 0.010, lava_fire, MAT_GLOW)
    mg.beam((0.05, -0.062, -0.054), (0.11, -0.105, -0.054), 0.012, 0.010, lava_fire, MAT_GLOW)
    mg.beam((0.11, -0.105, -0.054), (0.07, -0.132, -0.054), 0.012, 0.010, lava_fire, MAT_GLOW)
    mg.cyl(0.06, 0.12, -0.026, 0.0, 0.014, lava_deep, n=6, mat=MAT_GLOW)

    # Chân sau rồng làm tay cầm cò + Đuôi rồng uốn cong đầy gai làm báng súng!
    _grip(m, scale_dark, x=-0.040, slope=0.042, length=0.112, z_half=0.017)
    m.beam((-0.02, -0.025, 0.0), (0.05, -0.035, 0.0), 0.014, 0.012, horn_bone)
    m.extrude([
        (-0.14, 0.036), (-0.34, 0.028), (-0.42, -0.015), (-0.40, -0.072),
        (-0.36, -0.042), (-0.30, -0.010), (-0.14, -0.018),
    ], -0.020, 0.020, scale_dark)

    _right_hand(m)
    m.fore_grip = (0.245, -0.028, -0.024)
    m.mag_grab = (0.090, -0.105, -0.020)
    m.mag_base = (0.090, -0.165, 0.0)
    m.bolt_grab = (0.155, -0.030, -0.030)
    m.sight_y, m.ads_z = 0.096, 0.44
    m.muzzle = (0.52, 0.008, 0.0)
    return m


# ================================================================== 4. RIFLES (VANDAL, AK-47, M416, PHANTOM, GUARDIAN)
def _build_vandal():
    """VANDAL -> vandal.png (RGX 11z Pro Vandal: Xanh chuối Neon + Khung xương đen chữ X + Băng xám trong)."""
    m = Model()
    rgx_lime = (146, 214, 58)
    rgx_lime_glow = (176, 244, 78)
    exo_black = (32, 36, 42)
    smoked_poly = (76, 82, 88)

    # Thân bán trong suốt màu xám khói + lõi cơ khí sáng bên trong
    m.box(-0.14, 0.18, -0.026, 0.042, -0.020, 0.020, smoked_poly)
    m.cyl(-0.06, 0.16, 0.016, 0.0, 0.011, SILVER, n=6, mat=MAT_METAL)
    # Ốp nòng dưới & nòng ngoài bọc màu Xanh Chuối Neon RGX!
    m.extrude([(0.16, 0.024), (0.39, 0.018), (0.38, -0.028), (0.15, -0.030)], -0.024, 0.024, rgx_lime, MAT_GLOW)
    m.box(0.18, 0.38, 0.018, 0.044, -0.020, 0.020, smoked_poly)
    m.cyl(0.38, 0.60, 0.010, 0.0, 0.012, rgx_lime, n=8, mat=MAT_GLOW)
    m.cyl(0.58, 0.63, 0.010, 0.0, 0.015, rgx_lime_glow, n=8, mat=MAT_GLOW)
    m.cyl(0.38, 0.50, 0.034, 0.0, 0.009, exo_black, n=6)
    m.extrude([(0.47, 0.042), (0.50, 0.042), (0.49, 0.064)], -0.004, 0.004, rgx_lime_glow, MAT_GLOW)

    # KHUNG XƯƠNG GIÀN GIÁO ĐEN (EXOSKELETON TRUSS) đan chéo quanh thân (đúng chuẩn vandal.png!)
    m.box(-0.11, 0.36, 0.044, 0.054, -0.022, 0.022, exo_black, MAT_METAL)
    for z_side in (-0.022, 0.022):
        m.beam((-0.09, 0.046, z_side), (0.04, -0.028, z_side), 0.010, 0.010, exo_black, MAT_METAL)
        m.beam((0.04, -0.028, z_side), (0.18, 0.046, z_side), 0.010, 0.010, exo_black, MAT_METAL)
        m.beam((0.18, 0.046, z_side), (0.32, 0.018, z_side), 0.009, 0.009, exo_black, MAT_METAL)
    m.box(0.01, 0.09, 0.054, 0.064, -0.014, 0.014, rgx_lime_glow, MAT_GLOW)

    # Khóa nòng thép (m.bolt)
    bl = m.new_bolt()
    bl.box(0.03, 0.12, 0.022, 0.040, 0.016, 0.024, SILVER, MAT_METAL)
    bl.box(0.09, 0.11, 0.028, 0.038, 0.022, 0.044, exo_black)

    # Băng đạn cong xám khói lộ hàng đạn sáng + nẹp sống lưng xanh chuối neon (m.mag)
    mg = m.new_mag()
    mg.extrude([(0.04, -0.026), (0.12, -0.026), (0.172, -0.212), (0.086, -0.226)], -0.014, 0.014, smoked_poly)
    mg.extrude([(0.038, -0.026), (0.060, -0.026), (0.110, -0.224), (0.084, -0.228)], -0.016, 0.016, rgx_lime, MAT_GLOW)
    for k in range(5):
        by = -0.058 - k * 0.030
        bx = 0.072 + k * 0.011
        mg.box(bx, bx + 0.032, by - 0.006, by, -0.0155, 0.0155, rgx_lime_glow, MAT_GLOW)
    mg.box(0.084, 0.176, -0.236, -0.214, -0.017, 0.017, exo_black)
    _add_mag_bullet(mg, 0.082, -0.026, col_case=SILVER, col_tip=rgx_lime_glow)

    # Tay cầm xám khói ốp lưng xanh neon + Báng tam giác xanh neon hở khung
    _grip(m, smoked_poly, x=-0.035, slope=0.038, length=0.114)
    m.extrude([(-0.068, -0.022), (-0.052, -0.022), (-0.090, -0.132), (-0.106, -0.126)], -0.017, 0.017, rgx_lime, MAT_GLOW)
    _trigger_guard(m, smoked_poly, trig_col=rgx_lime_glow, trig_mat=MAT_GLOW)
    m.box(-0.44, -0.14, 0.012, 0.046, -0.020, 0.020, rgx_lime, MAT_GLOW)
    m.beam((-0.14, -0.012, 0.0), (-0.41, -0.088, 0.0), 0.026, 0.020, smoked_poly)
    m.beam((-0.43, 0.040, 0.0), (-0.40, -0.092, 0.0), 0.030, 0.022, rgx_lime, MAT_GLOW)

    _right_hand(m)
    m.fore_grip = (0.265, -0.022, -0.016)
    m.mag_grab = (0.115, -0.145, -0.010)
    m.mag_base = (0.130, -0.235, 0.0)
    m.bolt_grab = (0.095, 0.034, 0.035)
    m.sight_y, m.ads_z = 0.098, 0.45
    m.muzzle = (0.63, 0.010, 0.0)
    return m


def _build_ak47():
    """AK-47 Chiến Thuật Cổ Điển: Gỗ gụ đỏ sẫm vân đẹp + Thép đen dập gân + Băng đạn thép khía (có Icon riêng)."""
    m = Model()
    redwood = (146, 62, 34)
    redwood_hi = (176, 84, 46)
    gunmetal = (44, 48, 56)
    bakelite = (168, 76, 32)

    m.box(-0.13, 0.18, -0.030, 0.038, -0.021, 0.021, gunmetal, MAT_METAL)
    m.box(-0.12, 0.16, 0.038, 0.056, -0.018, 0.018, (56, 60, 70), MAT_METAL)
    # Ốp lót tay gỗ gụ đỏ 2 tầng có khe thoát nhiệt đen
    m.box(0.18, 0.38, -0.028, 0.018, -0.025, 0.025, redwood)
    m.box(0.18, 0.36, 0.024, 0.050, -0.021, 0.021, redwood_hi)
    m.box(0.22, 0.32, 0.016, 0.025, -0.026, 0.026, METAL_DARK)
    # Nòng thép + ống trích khí + đầu ngắm chữ A + chụp bù giật vát chéo đặc trưng AK-47
    m.cyl(0.38, 0.61, 0.010, 0.0, 0.0105, METAL_DARK, mat=MAT_METAL)
    m.cyl(0.36, 0.48, 0.038, 0.0, 0.009, gunmetal, mat=MAT_METAL)
    m.extrude([(0.55, 0.016), (0.58, 0.016), (0.57, 0.066), (0.555, 0.066)], -0.004, 0.004, METAL_DARK)
    m.taper_x(0.60, 0.65, 0.000, 0.020, 0.013, -0.002, 0.014, 0.012, gunmetal, MAT_METAL)
    m.box(0.12, 0.165, 0.056, 0.068, -0.008, 0.008, STEEL, MAT_METAL)

    bl = m.new_bolt()
    bl.box(0.03, 0.12, 0.024, 0.042, 0.016, 0.023, SILVER, MAT_METAL)
    bl.box(0.09, 0.11, 0.030, 0.038, 0.022, 0.045, METAL_DARK)

    mg = m.new_mag()
    mg.extrude([(0.04, -0.028), (0.12, -0.028), (0.176, -0.214), (0.090, -0.228)], -0.015, 0.015, bakelite)
    mg.box(0.088, 0.178, -0.235, -0.215, -0.017, 0.017, gunmetal, MAT_METAL)
    _add_mag_bullet(mg, 0.082, -0.028)

    _grip(m, redwood, x=-0.035, slope=0.036, length=0.112)
    _trigger_guard(m, gunmetal)
    m.extrude([(-0.13, 0.038), (-0.13, -0.030), (-0.43, -0.098), (-0.45, 0.016)], -0.020, 0.020, redwood)
    m.box(-0.458, -0.442, -0.098, 0.016, -0.021, 0.021, METAL_DARK)

    _right_hand(m)
    m.fore_grip = (0.265, -0.022, -0.016)
    m.mag_grab = (0.115, -0.145, -0.010)
    m.mag_base = (0.132, -0.235, 0.0)
    m.bolt_grab = (0.095, 0.036, 0.035)
    m.sight_y, m.ads_z = 0.098, 0.45
    m.muzzle = (0.65, 0.010, 0.0)
    return m


def _build_m416():
    """M416 -> m416.png (Obsidian Demon Rifle: Giáp hắc diện thạch viền đồng cổ, mắt quỷ cam lửa, giảm thanh vát)."""
    m = Model()
    obsidian = (44, 44, 52)
    slate_plate = (64, 64, 74)
    bone_bronze = (152, 132, 110)
    hellfire = (255, 86, 26)
    ember_deep = (196, 42, 22)

    # Thân giáp hắc diện thạch xếp lớp + viền xương đồng cổ chạy mảnh hai bên hông
    m.box(-0.16, 0.18, -0.024, 0.048, -0.022, 0.022, obsidian)
    m.box(-0.14, 0.36, 0.046, 0.056, -0.016, 0.016, obsidian, MAT_METAL)
    for zs in (-0.022, 0.022):
        m.beam((-0.12, 0.044, zs), (0.36, 0.044, zs), 0.008, 0.006, bone_bronze, MAT_METAL)
    # Sọ quỷ đen viền đồng trên thân sau có đôi mắt lửa đỏ cam rực sáng (đúng m416.png!)
    m.extrude([(-0.08, 0.048), (0.03, 0.048), (0.01, 0.078), (-0.06, 0.082)], -0.021, 0.021, obsidian, MAT_METAL)
    m.beam((-0.07, 0.078, 0.0), (0.02, 0.072, 0.0), 0.044, 0.007, bone_bronze, MAT_METAL)
    m.box(-0.05, -0.01, 0.056, 0.070, -0.023, 0.023, hellfire, MAT_GLOW)
    # Khe lửa đỏ âm ỉ bên hông súng
    m.box(-0.08, 0.14, 0.008, 0.016, -0.0235, 0.0235, ember_deep, MAT_GLOW)

    # Ốp nòng vảy giáp xéo + ngạnh nhọn dưới gầm
    for i in range(4):
        px = 0.16 + i * 0.052
        m.extrude([(px, -0.026), (px + 0.048, -0.022), (px + 0.056, 0.044), (px + 0.008, 0.044)],
                  -0.025, 0.025, slate_plate, MAT_METAL)
    m.extrude([(0.06, -0.022), (0.15, -0.022), (0.14, -0.052), (0.04, -0.046)], -0.024, 0.024, bone_bronze, MAT_METAL)

    # Ống giảm thanh hắc diện thạch vát cạnh sắc lẹm + mắt lửa đỏ ở gốc giảm thanh!
    m.taper_x(0.37, 0.46, -0.022, 0.040, 0.022, -0.028, 0.036, 0.020, bone_bronze, MAT_METAL)
    m.box(0.39, 0.43, 0.014, 0.030, -0.023, 0.023, hellfire, MAT_GLOW)
    m.taper_x(0.46, 0.68, -0.024, 0.036, 0.020, -0.008, 0.034, 0.014, obsidian, MAT_METAL)

    # Khóa nòng (m.bolt)
    bl = m.new_bolt()
    bl.box(-0.165, -0.125, 0.040, 0.054, -0.024, 0.024, bone_bronze, MAT_METAL)
    bl.box(0.02, 0.09, 0.018, 0.038, 0.019, 0.024, slate_plate, MAT_METAL)

    # Băng đạn cong bọc giáp vảy gai có khe lửa đỏ (m.mag)
    mg = m.new_mag()
    mg.extrude([(0.03, -0.028), (0.11, -0.028), (0.132, -0.198), (0.048, -0.208)], -0.015, 0.015, obsidian)
    for k in range(4):
        sy = -0.055 - k * 0.036
        mg.box(0.042, 0.124, sy - 0.012, sy, -0.017, 0.017, slate_plate, MAT_METAL)
    mg.box(0.095, 0.122, -0.175, -0.055, -0.016, 0.016, ember_deep, MAT_GLOW)
    _add_mag_bullet(mg, 0.070, -0.028, col_case=bone_bronze, col_tip=hellfire)

    # Tay cầm vảy gai + báng vuốt quỷ hở lõi đỏ
    _grip(m, obsidian, x=-0.036, slope=0.040, length=0.114)
    _trigger_guard(m, bone_bronze, trig_col=obsidian, guard_mat=MAT_METAL)
    m.extrude([
        (-0.16, 0.044), (-0.42, 0.040), (-0.45, -0.015), (-0.42, -0.088),
        (-0.34, -0.080), (-0.28, -0.015), (-0.16, -0.020),
    ], -0.021, 0.021, obsidian)
    m.beam((-0.18, 0.038, 0.0), (-0.41, 0.034, 0.0), 0.044, 0.014, bone_bronze, MAT_METAL)
    m.box(-0.39, -0.33, -0.052, 0.016, -0.022, 0.022, ember_deep, MAT_GLOW)

    _right_hand(m)
    m.fore_grip = (0.265, -0.020, -0.018)
    m.mag_grab = (0.078, -0.135, -0.010)
    m.mag_base = (0.088, -0.215, 0.0)
    m.bolt_grab = (-0.145, 0.048, -0.015)
    m.sight_y, m.ads_z = 0.114, 0.44
    m.muzzle = (0.68, 0.014, 0.0)
    return m


def _build_phantom():
    """PHANTOM Spec-Ops Cyber: Thép Titan đen + Vỏ trắng bạc + Rãnh năng lượng Xanh Băng + Kính Holo (có Icon riêng)."""
    m = Model()
    titan_dark = (36, 42, 52)
    aero_silver = (196, 206, 220)
    cyber_cyan = (64, 218, 255)

    m.box(-0.14, 0.16, -0.022, 0.048, -0.021, 0.021, titan_dark, MAT_METAL)
    m.box(-0.12, 0.36, 0.026, 0.052, -0.022, 0.022, aero_silver, MAT_METAL)
    m.box(0.16, 0.38, -0.028, 0.026, -0.024, 0.024, titan_dark)
    m.box(-0.08, 0.34, 0.020, 0.027, -0.025, 0.025, cyber_cyan, MAT_GLOW)  # Dải đèn xanh băng dọc thân
    # Đế gắn kính ngắm gọn trên lưng súng (khi bật Scope sẽ hiện kính ngắm Holographic xanh băng xuyên thấu!)
    m.box(-0.03, 0.065, 0.052, 0.060, -0.019, 0.019, titan_dark, MAT_METAL)
    m.box(-0.02, 0.055, 0.060, 0.065, -0.015, 0.015, cyber_cyan, MAT_GLOW)
    # Ống giảm thanh Spec-Ops dài có khía tản nhiệt
    m.cyl(0.38, 0.45, 0.012, 0.0, 0.012, STEEL, n=8, mat=MAT_METAL)
    m.cyl(0.44, 0.69, 0.012, 0.0, 0.021, titan_dark, n=10, mat=MAT_METAL)
    m.cyl(0.50, 0.52, 0.012, 0.0, 0.0225, cyber_cyan, n=10, mat=MAT_GLOW)

    bl = m.new_bolt()
    bl.box(-0.155, -0.125, 0.040, 0.054, -0.024, 0.024, aero_silver, MAT_METAL)
    bl.box(0.01, 0.08, 0.014, 0.034, 0.019, 0.023, aero_silver, MAT_METAL)

    mg = m.new_mag()
    mg.extrude([(0.022, -0.024), (0.092, -0.024), (0.114, -0.200), (0.044, -0.210)], -0.015, 0.015, titan_dark)
    mg.box(0.062, 0.082, -0.180, -0.055, -0.016, 0.016, cyber_cyan, MAT_GLOW)
    mg.box(0.040, 0.116, -0.220, -0.200, -0.017, 0.017, aero_silver, MAT_METAL)
    _add_mag_bullet(mg, 0.058, -0.024, col_case=SILVER, col_tip=cyber_cyan)

    _grip(m, titan_dark)
    _trigger_guard(m, aero_silver, trig_col=cyber_cyan, guard_mat=MAT_METAL, trig_mat=MAT_GLOW)
    m.cyl(-0.34, -0.14, 0.024, 0.0, 0.015, titan_dark)
    m.extrude([(-0.42, 0.052), (-0.27, 0.052), (-0.27, 0.0), (-0.31, -0.072), (-0.42, -0.076)],
              -0.020, 0.020, aero_silver, MAT_METAL)

    _right_hand(m)
    m.fore_grip = (0.265, -0.020, -0.018)
    m.mag_grab = (0.068, -0.145, -0.010)
    m.mag_base = (0.078, -0.225, 0.0)
    m.bolt_grab = (-0.145, 0.048, -0.015)
    m.sight_y, m.ads_z = 0.094, 0.44
    m.muzzle = (0.69, 0.012, 0.0)
    return m


def _build_guardian():
    """GUARDIAN -> guardian.png (Basalt & Amethyst Crystal: Đá bazan đen nứt gãy ôm nòng & băng pha lê tím hồng)."""
    m = Model()
    basalt = (58, 58, 66)
    basalt_hi = (86, 86, 96)
    amethyst = (226, 82, 246)
    amethyst_deep = (164, 46, 198)

    # Lõi & Nòng pha lê Thạch Anh Tím (Amethyst) dài rực sáng!
    m.taper_x(-0.16, 0.75, 0.008, 0.036, 0.016, 0.014, 0.032, 0.009, amethyst, MAT_GLOW)
    m.taper_x(0.42, 0.66, -0.016, 0.004, 0.012, -0.006, 0.006, 0.005, amethyst_deep, MAT_GLOW)  # Thanh pha lê dưới nòng

    # Các tảng đá Bazan đen xám vát cạnh kẹp rời rạc quanh lõi pha lê tím (đúng guardian.png!)
    m.extrude([(0.16, -0.026), (0.48, -0.018), (0.45, 0.022), (0.14, 0.026)], -0.025, 0.025, basalt)
    m.extrude([(0.20, 0.030), (0.50, 0.028), (0.47, 0.050), (0.24, 0.052)], -0.020, 0.020, basalt_hi, MAT_METAL)
    m.extrude([(-0.16, -0.022), (0.12, -0.028), (0.14, 0.024), (-0.14, 0.042)], -0.024, 0.024, basalt)
    m.box(-0.08, 0.14, 0.038, 0.056, -0.018, 0.018, basalt_hi, MAT_METAL)
    # Thước ngắm đá sau + mảnh pha lê tím bay lơ lửng đầu nòng
    m.extrude([(-0.06, 0.054), (-0.02, 0.054), (-0.035, 0.076)], -0.012, 0.012, basalt_hi)
    m.box(0.66, 0.70, 0.042, 0.054, -0.006, 0.006, amethyst, MAT_GLOW)

    # Khóa nòng pha lê & đá (m.bolt)
    bl = m.new_bolt()
    bl.box(0.03, 0.12, 0.020, 0.040, 0.018, 0.026, amethyst, MAT_GLOW)
    bl.box(0.09, 0.115, 0.026, 0.038, 0.022, 0.044, basalt_hi)

    # Băng đạn khối tinh thể pha lê tím hồng phát sáng (m.mag)
    mg = m.new_mag()
    mg.extrude([(0.025, -0.022), (0.102, -0.022), (0.092, -0.156), (0.012, -0.148)], -0.015, 0.015, amethyst, MAT_GLOW)
    mg.extrude([(0.045, -0.030), (0.075, -0.030), (0.068, -0.148), (0.038, -0.144)], -0.017, 0.017, (250, 165, 255), MAT_GLOW)
    _add_mag_bullet(mg, 0.062, -0.022, col_case=basalt_hi, col_tip=amethyst)

    # Tay cầm đá bazan + cò pha lê tím + báng đá móc câu cắm 3 gai pha lê tím!
    _grip(m, basalt, x=-0.042, slope=0.040, length=0.112)
    _trigger_guard(m, basalt_hi, trig_col=amethyst, trig_mat=MAT_GLOW)
    m.extrude([
        (-0.16, 0.040), (-0.44, 0.036), (-0.47, -0.015), (-0.44, -0.096),
        (-0.38, -0.092), (-0.40, -0.030), (-0.28, 0.005), (-0.16, -0.015),
    ], -0.022, 0.022, basalt)
    for sx, sy in ((-0.32, 0.002), (-0.37, -0.015), (-0.41, -0.035)):
        m.beam((sx, sy, 0.0), (sx - 0.055, sy - 0.042, 0.0), 0.016, 0.014, amethyst, MAT_GLOW)

    _right_hand(m)
    m.fore_grip = (0.295, -0.018, -0.018)
    m.mag_grab = (0.060, -0.105, -0.010)
    m.mag_base = (0.055, -0.160, 0.0)
    m.bolt_grab = (0.102, 0.034, 0.034)
    m.sight_y, m.ads_z = 0.112, 0.48
    m.muzzle = (0.75, 0.022, 0.0)
    return m


# ================================================================== 5. SNIPERS (M24 DARK RAVEN, AWM IMPERIUM JADE DRAGON)
def _build_m24():
    """M24 -> m24.png (Dark Raven Marshal: Gỗ đen xoắn, giáp xám đêm, mũ sọ quạ & lông vũ xanh trên kính ngắm, cần gạt)."""
    m = Model()
    dark_wood = (66, 48, 42)
    raven_slate = (68, 74, 92)
    feather_indigo = (42, 68, 118)
    claw_gold = (224, 184, 88)

    # Nòng & thân gỗ nâu đen xoắn kết hợp giáp xám đêm thuôn dài
    m.cyl(0.18, 0.85, 0.014, 0.0, 0.012, dark_wood, r1=0.009)
    m.box(0.32, 0.64, 0.020, 0.032, -0.014, 0.014, raven_slate, MAT_METAL)
    m.extrude([(0.78, 0.022), (0.83, 0.022), (0.80, 0.042)], -0.003, 0.003, claw_gold, MAT_METAL)  # Vuốt vàng đầu nòng!
    m.extrude([(-0.14, -0.024), (0.36, -0.020), (0.32, 0.030), (-0.12, 0.038)], -0.022, 0.022, raven_slate, MAT_METAL)
    m.extrude([(0.24, -0.020), (0.35, -0.020), (0.31, -0.052), (0.27, -0.044)], -0.020, 0.020, raven_slate, MAT_METAL)
    m.box(0.28, 0.31, -0.058, -0.046, -0.008, 0.008, claw_gold, MAT_METAL)

    # Ống ngắm trùm giáp Sọ Quạ phía trên + Chùm Lông Vũ Xanh Đêm rủ xuống (đúng m24.png!)
    m.cyl(-0.08, 0.20, 0.088, 0.0, 0.019, raven_slate, n=8, mat=MAT_METAL)
    m.extrude([(-0.10, 0.098), (0.16, 0.102), (0.04, 0.128), (-0.12, 0.112)], -0.022, 0.022, (88, 96, 116), MAT_METAL)
    for fx, fy in ((0.06, 0.072), (0.01, 0.062), (-0.04, 0.054), (-0.28, -0.038)):
        m.extrude([(fx, fy), (fx + 0.075, fy + 0.012), (fx + 0.045, fy - 0.018), (fx - 0.015, fy - 0.012)],
                  -0.024, 0.024, feather_indigo, MAT_METAL)

    # Cần quy-lát (m.bolt) & Vòng cần gạt Lever-Action uốn dưới cò súng!
    bl = m.new_bolt()
    bl.cyl(-0.08, 0.03, 0.026, 0.005, 0.009, raven_slate, n=6, mat=MAT_METAL)
    bl.beam((-0.045, 0.026, 0.014), (-0.055, 0.005, 0.052), 0.010, 0.010, claw_gold, MAT_METAL)

    mg = m.new_mag(hidden=True)
    mg.box(0.02, 0.09, -0.095, -0.024, -0.013, 0.013, raven_slate)
    _add_mag_bullet(mg, 0.055, -0.024, col_case=claw_gold, col_tip=SILVER)

    # Vòng cần gạt đặc trưng của Marshal dưới cò + báng gỗ đen bọc đế giáp xám
    m.extrude([
        (-0.01, -0.022), (0.05, -0.022), (-0.05, -0.108), (-0.13, -0.138),
        (-0.15, -0.126), (-0.07, -0.092),
    ], -0.007, 0.007, raven_slate, MAT_METAL)
    m.box(0.010, 0.020, -0.045, -0.022, -0.003, 0.003, claw_gold, MAT_METAL)
    m.extrude([(-0.12, 0.028), (-0.14, -0.036), (-0.45, -0.068), (-0.46, 0.018)], -0.020, 0.020, dark_wood)
    m.extrude([(-0.34, 0.032), (-0.48, 0.030), (-0.49, -0.092), (-0.44, -0.088), (-0.44, 0.010)],
              -0.022, 0.022, raven_slate, MAT_METAL)

    _right_hand(m)
    m.fore_grip = (0.305, -0.022, -0.018)
    m.mag_grab = (0.055, -0.085, -0.010)
    m.mag_base = (0.055, -0.115, 0.0)
    m.bolt_grab = (-0.055, 0.010, 0.048)
    m.sight_y, m.ads_z = 0.092, 0.50
    m.muzzle = (0.85, 0.014, 0.0)
    return m


def _build_awm():
    """AWM -> awm.png (Imperium Jade Dragon Operator: Ngọc bích xanh lục bảo + Rồng Vàng Hoàng Kim + Lụa Đỏ)."""
    m = Model()
    jade_bright = (42, 198, 152)
    jade_deep = (24, 132, 104)
    imp_gold = (232, 190, 88)
    silk_red = (192, 34, 44)

    # Nòng dài Ngọc Bích + Đầu nòng vát Vàng Hoàng Kim + Dải lụa đỏ quấn quanh nòng!
    m.cyl(0.20, 0.82, 0.018, 0.0, 0.013, jade_bright, r1=0.011, mat=MAT_GLOW)
    m.taper_x(0.76, 0.94, 0.006, 0.030, 0.016, 0.010, 0.026, 0.010, imp_gold, MAT_METAL)
    m.cyl(0.70, 0.75, 0.018, 0.0, 0.0145, silk_red, n=8)  # Dải lụa đỏ quấn nòng!

    # Thân trên Ngọc Bích uốn lượn + Hoa văn mây rồng Vàng Hoàng Kim đỡ dưới bụng súng
    m.extrude([(-0.18, 0.002), (0.34, 0.006), (0.30, 0.046), (-0.16, 0.042)], -0.023, 0.023, jade_bright, MAT_GLOW)
    m.box(-0.16, 0.24, -0.016, 0.012, -0.024, 0.024, jade_deep)
    m.extrude([
        (-0.08, -0.012), (0.32, 0.004), (0.35, -0.036), (0.16, -0.032),
        (0.10, -0.072), (-0.04, -0.056),
    ], -0.022, 0.022, imp_gold, MAT_METAL)
    m.box(0.02, 0.055, -0.010, 0.048, -0.025, 0.025, silk_red)  # Đai lụa đỏ giữa thân!

    # ỐNG NGẮM NGỌC BÍCH QUẤN ĐAI VÀNG MẢNH + ĐẦU RỒNG VÀNG CHẦU PHÍA SAU (đúng awm.png!)
    m.cyl(-0.14, 0.23, 0.102, 0.0, 0.020, jade_bright, n=10, mat=MAT_GLOW)
    m.cyl(0.19, 0.24, 0.102, 0.0, 0.025, imp_gold, n=10, r1=0.027, mat=MAT_METAL)
    m.cyl(-0.15, -0.12, 0.102, 0.0, 0.024, imp_gold, n=10, mat=MAT_METAL)
    m.cyl(0.02, 0.045, 0.102, 0.0, 0.023, imp_gold, n=10, mat=MAT_METAL)
    # Thanh rồng vàng uốn từ thân lên kính ngắm + Đầu rồng vàng có sừng ở x = -0.17
    m.beam((0.14, 0.042, 0.0), (0.04, 0.096, 0.0), 0.015, 0.015, imp_gold, MAT_METAL)
    m.beam((-0.05, 0.042, 0.0), (-0.08, 0.096, 0.0), 0.015, 0.015, imp_gold, MAT_METAL)
    m.extrude([(-0.19, 0.044), (-0.11, 0.044), (-0.13, 0.072), (-0.21, 0.068)], -0.012, 0.012, imp_gold, MAT_METAL)

    # Tay quy-lát vàng kim (m.bolt)
    bl = m.new_bolt()
    bl.cyl(-0.08, 0.03, 0.026, 0.005, 0.009, imp_gold, n=6, mat=MAT_METAL)
    bl.beam((-0.045, 0.026, 0.014), (-0.055, 0.005, 0.054), 0.010, 0.010, imp_gold, MAT_METAL)
    bl.box(-0.065, -0.045, -0.004, 0.014, 0.048, 0.064, jade_bright, MAT_GLOW)

    # Băng đạn Ngọc Bích bọc viền vàng (m.mag)
    mg = m.new_mag()
    mg.extrude([(0.025, -0.042), (0.105, -0.042), (0.100, -0.126), (0.020, -0.118)], -0.014, 0.014, jade_bright, MAT_GLOW)
    mg.box(0.018, 0.104, -0.134, -0.118, -0.016, 0.016, imp_gold, MAT_METAL)
    _add_mag_bullet(mg, 0.062, -0.042, col_case=imp_gold, col_tip=jade_bright)

    # Tay cầm vàng quấn lụa đỏ + Báng Ngọc Bích viền mây vàng uốn cong!
    _grip(m, imp_gold, x=-0.042, slope=0.038, length=0.112, mat=MAT_METAL)
    m.box(-0.082, -0.024, -0.095, -0.052, -0.0175, 0.0175, silk_red)  # Lụa đỏ quấn tay cầm!
    _trigger_guard(m, imp_gold, trig_col=imp_gold, guard_mat=MAT_METAL, trig_mat=MAT_METAL)
    m.extrude([
        (-0.16, 0.042), (-0.48, 0.048), (-0.51, -0.015), (-0.48, -0.098),
        (-0.36, -0.088), (-0.30, -0.022), (-0.16, -0.018),
    ], -0.022, 0.022, jade_bright, MAT_GLOW)
    m.extrude([(-0.32, -0.018), (-0.49, -0.010), (-0.50, -0.104), (-0.38, -0.095)], -0.024, 0.024, imp_gold, MAT_METAL)
    m.box(-0.46, -0.42, 0.018, 0.052, -0.024, 0.024, silk_red)

    _right_hand(m)
    m.fore_grip = (0.305, -0.020, -0.018)
    m.mag_grab = (0.062, -0.098, -0.010)
    m.mag_base = (0.060, -0.136, 0.0)
    m.bolt_grab = (-0.055, 0.010, 0.048)
    m.sight_y, m.ads_z = 0.104, 0.52
    m.muzzle = (0.94, 0.018, 0.0)
    return m


# ================================================================== 6. DAO CẬN CHIẾN RĂNG CƯA (KNIFE)
def _knife():
    """KNIFE khớp chuẩn với icon build_knife_sprite(): Lưỡi bạc vát nhọn, rãnh đen, 6 răng cưa, cán khía & khuyên tròn."""
    m = Model()
    # Lưỡi dao thép bạc sáng bóng + rãnh đen giữa lưỡi
    m.extrude([
        (0.030, -0.010), (0.160, -0.012), (0.245, 0.004),
        (0.290, 0.022), (0.195, 0.030), (0.030, 0.028),
    ], -0.0032, 0.0032, SILVER, MAT_METAL)
    m.extrude([(0.045, 0.006), (0.205, 0.010), (0.235, 0.020), (0.045, 0.022)], -0.0042, 0.0042, (24, 26, 32))
    # 6 răng cưa sắc nhọn trên sống dao
    for i in range(6):
        tx = 0.055 + i * 0.021
        m.extrude([(tx, 0.028), (tx + 0.015, 0.028), (tx + 0.007, 0.037)], -0.003, 0.003, SILVER, MAT_METAL)
    # Chắn tay thép (crossguard) + Cán đen khía rãnh ngón tay + Khuyên tròn ở chuôi
    m.box(0.014, 0.032, -0.026, 0.046, -0.013, 0.013, STEEL, MAT_METAL)
    m.extrude([
        (-0.115, 0.024), (0.014, 0.028), (0.014, -0.008),
        (-0.025, -0.014), (-0.065, -0.010), (-0.115, -0.018),
    ], -0.013, 0.013, (40, 42, 50))
    m.cyl(-0.138, -0.114, 0.004, 0.0, 0.014, SILVER, n=8, mat=MAT_METAL)

    ra = m.new_right_arm()
    ra.box(-0.105, -0.005, -0.036, 0.012, -0.026, 0.026, GLOVE)
    ra.box(-0.085, -0.015, -0.012, 0.018, 0.016, 0.030, GLOVE_PAD, MAT_METAL)
    ra.beam((-0.075, -0.02, 0.0), (-0.40, -0.32, 0.14), 0.072, 0.066, SLEEVE)

    m.fore_grip = None
    m.muzzle = (0.290, 0.022, 0.0)
    return m


_BUILDERS = {
    "CLASSIC": _build_classic,
    "GHOST": _build_ghost,
    "SHERIFF": _build_sheriff,
    "MP5": _build_mp5,
    "UMP": _build_ump,
    "M014": _build_m1014,
    "MAG-7": _build_mag7,
    "AK-47": _build_ak47,
    "VANDAL": _build_vandal,
    "M416": _build_m416,
    "PHANTOM": _build_phantom,
    "GUARDIAN": _build_guardian,
    "M24": _build_m24,
    "AWM": _build_awm,
    "KNIFE": _knife,
}
_ALIAS = {"M1014": "M014", "MAG7": "MAG-7", "AK47": "AK-47"}
_cache = {}
_idle_arm_cache = {}
_SPRITE_CACHE = {}

PISTOL_IDS = {"CLASSIC", "GHOST", "SHERIFF"}


def get_model(weapon_id):
    key = _ALIAS.get(str(weapon_id).upper(), str(weapon_id).upper())
    if key not in _BUILDERS:
        key = "VANDAL"
    if key not in _cache:
        _cache[key] = _BUILDERS[key]()
    return _cache[key]


def _get_idle_left_arm(weapon_id, model):
    if model.fore_grip is None:
        return None
    key = _ALIAS.get(str(weapon_id).upper(), str(weapon_id).upper())
    if key not in _idle_arm_cache:
        _idle_arm_cache[key] = _build_left_arm_model(model.fore_grip)
    return _idle_arm_cache[key]


def _matrix(yaw, pitch, roll):
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    rz = ((cr, -sr, 0), (sr, cr, 0), (0, 0, 1))
    rx = ((1, 0, 0), (0, cp, -sp), (0, sp, cp))
    ry = ((cy, 0, sy), (0, 1, 0), (-sy, 0, cy))

    def mul(a, b):
        return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))
    return mul(ry, mul(rx, rz))


def _shade_material(col, mat, lam, nz, outline):
    if mat == MAT_GLOW:
        rim = ((-nz) ** 3 * 0.16) if nz < 0.0 else 0.0
        fill_c = _shade(col, 0.90 + 0.24 * lam + rim)
        line_c = _shade(fill_c, 0.72) if outline else None
    elif mat == MAT_METAL:
        rim = ((-nz) ** 4 * 0.34) if nz < 0.0 else 0.0
        fill_c = _shade(col, 0.38 + 0.76 * lam + rim)
        line_c = _shade(fill_c, 0.56) if outline else None
    else:
        rim = ((-nz) ** 6 * 0.15) if nz < 0.0 else 0.0
        fill_c = _shade(col, AMBIENT + 0.68 * lam + rim)
        line_c = _shade(fill_c, 0.55) if outline else None
    return fill_c, line_c


def _render_uncached(target_w, target_h, weapon_id, pos, yaw, pitch, roll, mirror, fov_deg,
                     outline, mag_offset, mag_roll, bolt_back, left_hand_pos, shell_offset, include_arms=True):
    model = get_model(weapon_id)
    cx, cy = target_w * 0.5, target_h * 0.5
    f = cx / math.tan(math.radians(fov_deg) * 0.5)
    (a, b, c), (d, e, g), (h, i, j) = _matrix(yaw, pitch, roll)
    px, py, pz = pos
    sx = -1.0 if mirror else 1.0
    lx0, ly0, lz0 = LIGHT

    def to_cam(v):
        bx, by, bz = v[2], -v[1], v[0]
        return (
            sx * (a * bx + b * by + c * bz) + px,
            d * bx + e * by + g * bz + py,
            h * bx + i * by + j * bz + pz,
        )

    parts = [(model, None, 0.0)]
    if model.bolt is not None:
        b_off = (-bolt_back, 0.0, 0.0) if abs(bolt_back) > 1e-4 else None
        parts.append((model.bolt, b_off, 0.0))
    if model.mag is not None and not (model.mag_hidden and mag_offset is None):
        parts.append((model.mag, mag_offset, mag_roll))
    if shell_offset is not None and model.shell is not None:
        parts.append((model.shell, shell_offset, 0.0))

    if include_arms:
        if model.right_arm is not None:
            parts.append((model.right_arm, None, 0.0))
        if model.fore_grip is not None:
            if left_hand_pos is None:
                idle_arm = _get_idle_left_arm(weapon_id, model)
                if idle_arm is not None:
                    parts.append((idle_arm, None, 0.0))
            else:
                parts.append((_build_left_arm_model(left_hand_pos), None, 0.0))

    polys = []
    min_x, min_y = target_w, target_h
    max_x, max_y = 0, 0

    for part, off, mr in parts:
        verts = part.verts
        if off is not None:
            cr, sr = math.cos(mr), math.sin(mr)
            ox, oy, oz = off
            if abs(mr) > 1e-4:
                verts = [(x * cr - y * sr + ox, x * sr + y * cr + oy, z + oz) for x, y, z in verts]
            else:
                verts = [(x + ox, y + oy, z + oz) for x, y, z in verts]
        else:
            cr, sr = 1.0, 0.0

        cam = [to_cam(v) for v in verts]
        proj = [(int(cx + x / z * f), int(cy + y / z * f)) if z > 0.02 else None for x, y, z in cam]
        for idx, n, col, mat in part.faces:
            n0, n1 = (n[0] * cr - n[1] * sr, n[0] * sr + n[1] * cr) if abs(mr) > 1e-4 else (n[0], n[1])
            bx, by, bz = n[2], -n1, n0
            nx = sx * (a * bx + b * by + c * bz)
            ny = d * bx + e * by + g * bz
            nz = h * bx + i * by + j * bz
            c0, c1 = cam[idx[0]], cam[idx[2]]
            if nx * (c0[0] + c1[0]) + ny * (c0[1] + c1[1]) + nz * (c0[2] + c1[2]) >= 0.0:
                continue
            pts = [proj[t] for t in idx]
            if None in pts:
                continue
            for vx, vy in pts:
                if vx < min_x:
                    min_x = vx
                if vx > max_x:
                    max_x = vx
                if vy < min_y:
                    min_y = vy
                if vy > max_y:
                    max_y = vy
            lam = nx * lx0 + ny * ly0 + nz * lz0
            if lam < 0.0:
                lam = 0.0
            fill_c, line_c = _shade_material(col, mat, lam, nz, outline)
            avg_z = sum(cam[t][2] for t in idx) / len(idx)
            polys.append((avg_z, pts, fill_c, line_c))

    polys.sort(key=lambda p: -p[0])
    mx, my, mz = to_cam(model.muzzle)
    muz = (int(cx), int(cy)) if mz <= 0.02 else (int(cx + mx / mz * f), int(cy + my / mz * f))
    return polys, (min_x, min_y, max_x, max_y), muz


def render_side_icon(weapon_id, canvas_w=640, canvas_h=240):
    """Kết xuất ảnh mặt ngang của khẩu súng 3D (không kèm cánh tay) để làm Icon Shop/HUD/Súng rơi sắc nét."""
    polys, (min_x, min_y, max_x, max_y), _ = _render_uncached(
        canvas_w, canvas_h, weapon_id,
        pos=(0.08, -0.02, 2.35),
        yaw=math.radians(-88.0),
        pitch=math.radians(3.0),
        roll=math.radians(-2.0),
        mirror=False,
        fov_deg=28.0,
        outline=True,
        mag_offset=None,
        mag_roll=0.0,
        bolt_back=0.0,
        left_hand_pos=None,
        shell_offset=None,
        include_arms=False,
    )
    if not polys or max_x <= min_x or max_y <= min_y:
        return None
    pad = 6
    bx0, by0 = max(0, min_x - pad), max(0, min_y - pad)
    bx1, by1 = min(canvas_w, max_x + pad), min(canvas_h, max_y + pad)
    surf = pygame.Surface((bx1 - bx0, by1 - by0), pygame.SRCALPHA)
    draw_poly = pygame.draw.polygon
    for _, pts, fill_c, line_c in polys:
        shifted = [(vx - bx0, vy - by0) for vx, vy in pts]
        draw_poly(surf, fill_c, shifted)
        if line_c is not None:
            draw_poly(surf, line_c, shifted, 1)
    return surf


def render(screen, weapon_id, pos, yaw=0.0, pitch=0.0, roll=0.0, mirror=False, fov_deg=58.0,
           outline=True, mag_offset=None, mag_roll=0.0, bolt_back=0.0,
           left_hand_pos=None, shell_offset=None, offset_px=(0, 0)):
    """Vẽ súng 3D với tự động Cache Sprite tư thế tĩnh (đạt 60-120+ FPS)."""
    sw, sh = screen.get_size()
    ox_px, oy_px = int(offset_px[0]), int(offset_px[1])

    is_static_parts = (
        mag_offset is None
        and left_hand_pos is None
        and shell_offset is None
        and abs(bolt_back) < 0.002
    )

    if is_static_parts:
        key = (
            sw, sh, str(weapon_id).upper(), mirror, round(fov_deg, 1), outline,
            round(pos[0], 3), round(pos[1], 3), round(pos[2], 3),
            round(yaw, 2), round(pitch, 2), round(roll, 2),
        )
        cached = _SPRITE_CACHE.get(key)
        if cached is None:
            if len(_SPRITE_CACHE) > 96:
                _SPRITE_CACHE.clear()
            polys, (min_x, min_y, max_x, max_y), muz = _render_uncached(
                sw, sh, weapon_id, pos, yaw, pitch, roll, mirror, fov_deg,
                outline, None, 0.0, 0.0, None, None, include_arms=True,
            )
            pad = 4
            bx0 = max(0, min_x - pad)
            by0 = max(0, min_y - pad)
            bx1 = min(sw, max_x + pad)
            by1 = min(sh, max_y + pad)
            if bx1 > bx0 and by1 > by0 and polys:
                surf = pygame.Surface((bx1 - bx0, by1 - by0), pygame.SRCALPHA)
                draw_poly = pygame.draw.polygon
                for _, pts, fill_c, line_c in polys:
                    shifted = [(vx - bx0, vy - by0) for vx, vy in pts]
                    draw_poly(surf, fill_c, shifted)
                    if line_c is not None:
                        draw_poly(surf, line_c, shifted, 1)
                cached = (surf, bx0, by0, muz)
            else:
                cached = (None, 0, 0, muz)
            _SPRITE_CACHE[key] = cached

        surf, bx0, by0, muz = cached
        if surf is not None:
            screen.blit(surf, (bx0 + ox_px, by0 + oy_px))
        return (muz[0] + ox_px, muz[1] + oy_px)

    polys, _, muz = _render_uncached(
        sw, sh, weapon_id, pos, yaw, pitch, roll, mirror, fov_deg,
        outline, mag_offset, mag_roll, bolt_back, left_hand_pos, shell_offset, include_arms=True,
    )
    draw_poly = pygame.draw.polygon
    for _, pts, fill_c, line_c in polys:
        shifted = [(vx + ox_px, vy + oy_px) for vx, vy in pts] if (ox_px or oy_px) else pts
        draw_poly(screen, fill_c, shifted)
        if line_c is not None:
            draw_poly(screen, line_c, shifted, 1)
    return (muz[0] + ox_px, muz[1] + oy_px)
