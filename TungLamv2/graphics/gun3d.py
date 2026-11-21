"""gun3d.py - Mô hình súng 3D phân tách Khung + Băng đạn (có viên đạn đồng) + Khóa nòng/Slide + Tay trái động.

Hệ tọa độ cục bộ của súng (đơn vị ~ mét):
    x: dọc nòng (+x hướng về đầu nòng)
    y: hướng lên trên (+y)
    z: hướng sang phải (+z)
    Gốc (0, 0, 0) tại đỉnh tay cầm (chỗ tay phải nắm cò).
"""
import math
import pygame

METAL = (62, 66, 74)
METAL_DARK = (34, 36, 42)
STEEL = (132, 138, 148)
BRASS = (222, 178, 62)
COPPER = (198, 118, 58)
SHELL_RED = (196, 42, 46)
GLOVE = (32, 34, 40)
GLOVE_PAD = (52, 56, 66)
SLEEVE = (54, 68, 88)
CUFF = (38, 44, 56)
SKIN_WRIST = (218, 172, 134)
LENS = (55, 175, 225)
RED_DOT = (255, 65, 65)

LIGHT = (-0.42, -0.82, -0.38)
_l = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _l for c in LIGHT)
AMBIENT = 0.42


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(v):
    ln = math.sqrt(sum(c * c for c in v)) or 1.0
    return (v[0] / ln, v[1] / ln, v[2] / ln)


def _shade(c, k):
    r = int(c[0] * k)
    g = int(c[1] * k)
    b = int(c[2] * k)
    return (255 if r > 255 else r, 255 if g > 255 else g, 255 if b > 255 else b)


class Model:
    def __init__(self):
        self.verts = []
        self.faces = []
        self.muzzle = (0.5, 0.0, 0.0)
        self.mag = None              # Băng đạn / ổ quay tháo rời khi nạp
        self.mag_hidden = False      # True: băng nằm khuất trong báng súng lục khi bình thường
        self.bolt = None             # Slide súng lục / khóa nòng / ốp bơm dịch chuyển khi bắn & kéo đạn
        self.shell = None            # Viên đạn lẻ / speedloader đưa vào khi nạp shotgun / revolver
        self.sight_y = 0.06
        self.ads_z = 0.42

        # Các điểm mốc để bàn tay trái bám theo trong hoạt ảnh nạp đạn chân thực
        self.fore_grip = (0.26, -0.025, -0.015)   # Vị trí tay trái đỡ ốp nòng bình thường
        self.mag_grab = (0.06, -0.13, -0.01)      # Vị trí tay trái nắm thân băng đạn
        self.mag_base = (0.07, -0.21, 0.0)        # Đáy băng đạn (để vỗ băng)
        self.bolt_grab = (-0.06, 0.055, -0.02)    # Vị trí tay khóa nòng / slide

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

    def _add(self, pts, faces, color):
        base = len(self.verts)
        self.verts.extend(pts)
        for idx, n in faces:
            self.faces.append((tuple(base + i for i in idx), n, color))

    def box(self, x0, x1, y0, y1, z0, z1, color):
        pts = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        self._add(pts, [
            ((0, 1, 3, 2), (-1, 0, 0)), ((4, 6, 7, 5), (1, 0, 0)),
            ((0, 4, 5, 1), (0, -1, 0)), ((2, 3, 7, 6), (0, 1, 0)),
            ((0, 2, 6, 4), (0, 0, -1)), ((1, 5, 7, 3), (0, 0, 1)),
        ], color)

    def cyl(self, x0, x1, yc, zc, r, color, n=8, r1=None):
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
        self._add(pts, faces, color)

    def extrude(self, poly, z0, z1, color):
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
        self._add(pts, faces, color)

    def beam(self, p0, p1, w, h, color):
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
        self._add(pts, faces, color)


# ================================================================== CHI TIẾT CHUNG & CÁNH TAY
def _grip(m, color, x=-0.035, slope=0.035, length=0.115):
    m.extrude(
        [(x - 0.034, -0.02), (x + 0.02, -0.02),
         (x + 0.02 - slope, -0.02 - length), (x - 0.034 - slope, -0.02 - length + 0.01)],
        -0.016, 0.016, color,
    )


def _trigger_guard(m, color, x=0.0):
    m.box(x - 0.005, x + 0.05, -0.05, -0.043, -0.006, 0.006, color)
    m.box(x + 0.012, x + 0.020, -0.042, -0.022, -0.003, 0.003, STEEL)  # Cò súng


def _right_hand(m, pistol=False):
    """Tay phải nắm cò súng cố định theo khung súng (có găng chiến thuật & cổ tay áo)."""
    gx0 = -0.092 if pistol else -0.102
    m.box(gx0, -0.012, -0.108, -0.032, -0.024, 0.028, GLOVE)
    m.box(gx0 + 0.01, -0.002, -0.048, -0.026, 0.014, 0.030, GLOVE_PAD)  # Ngón cái & đệm găng
    wrist = (-0.085, -0.102, 0.018)
    shoulder = (-0.38, -0.39, 0.17)
    m.beam(wrist, (-0.13, -0.15, 0.045), 0.056, 0.052, CUFF)
    m.beam((-0.12, -0.14, 0.04), shoulder, 0.068, 0.064, SLEEVE)


def _build_left_arm_model(hand_pos):
    """Dựng động cánh tay trái + bàn tay găng từ vai trái tới đúng vị trí hand_pos (ốp nòng / băng đạn / khóa nòng)."""
    arm = Model()
    hx, hy, hz = hand_pos
    shoulder = (-0.34, -0.40, -0.27)
    # Khuỷu tay hơi khuỵu tự nhiên xuống dưới & ra ngoài
    elbow = (
        (hx + shoulder[0]) * 0.5 - 0.05,
        min(hy, shoulder[1]) * 0.55 + (hy + shoulder[1]) * 0.45 - 0.05,
        (hz + shoulder[2]) * 0.5 - 0.04,
    )
    wrist = (hx - 0.032, hy - 0.025, hz - 0.018)
    arm.beam(shoulder, elbow, 0.068, 0.064, SLEEVE)
    arm.beam(elbow, wrist, 0.062, 0.058, SLEEVE)
    arm.beam(wrist, (hx - 0.012, hy - 0.01, hz - 0.008), 0.054, 0.050, CUFF)
    # Bàn tay găng chiến thuật + các đốt ngón ôm vào vật thể
    arm.box(hx - 0.036, hx + 0.036, hy - 0.030, hy + 0.024, hz - 0.026, hz + 0.024, GLOVE)
    arm.box(hx - 0.026, hx + 0.028, hy - 0.012, hy + 0.026, hz - 0.030, hz - 0.018, GLOVE_PAD)
    return arm


def _add_mag_bullet(mg, x_center, y_top):
    """Thêm viên đạn đồng sáng bóng trên miệng băng đạn để khi tháo/lắp băng nhìn cực thật."""
    mg.cyl(x_center - 0.024, x_center + 0.008, y_top + 0.006, 0.0, 0.0065, BRASS, n=6)
    mg.cyl(x_center + 0.008, x_center + 0.024, y_top + 0.006, 0.0, 0.0062, COPPER, n=6, r1=0.002)


# ================================================================== TỪNG KHẨU SÚNG CHI TIẾT
def _pistol(body, slide_col, suppressor=False, long_barrel=False):
    m = Model()
    L = 0.19 if long_barrel else 0.155
    # Khung dưới cố định
    m.box(-0.048, L - 0.018, -0.024, 0.002, -0.013, 0.013, body)
    m.cyl(-0.01, L + 0.006, 0.016, 0.0, 0.0065, STEEL, n=6)  # Nòng thép lộ ra khi slide lùi!
    _grip(m, body, x=-0.022, slope=0.032, length=0.108)
    _trigger_guard(m, body, x=0.0)

    # Khối trượt (Slide) tách riêng vào m.bolt để giật lùi khi bắn & kéo nạp đạn!
    bl = m.new_bolt()
    bl.box(-0.052, 0.015, 0.002, 0.036, -0.015, 0.015, slide_col)          # Phần sau slide
    bl.box(0.055, L, 0.002, 0.036, -0.015, 0.015, slide_col)               # Phần trước slide
    bl.box(0.015, 0.055, 0.002, 0.036, -0.015, 0.003, slide_col)           # Khe hất vỏ đạn bên phải!
    bl.box(L - 0.015, L - 0.003, 0.036, 0.046, -0.003, 0.003, METAL_DARK)  # Đầu ruồi
    bl.box(-0.046, -0.032, 0.036, 0.046, -0.010, 0.010, METAL_DARK)        # Thước ngắm sau
    bl.box(-0.047, -0.045, 0.039, 0.044, -0.007, 0.007, (90, 250, 120))    # Chấm dạ quang thước ngắm

    # Băng đạn nằm trong báng (chỉ lộ ra khi tháo/lắp) + viên đạn đồng trên đỉnh
    mg = m.new_mag(hidden=True)
    mg.extrude([(-0.050, -0.025), (-0.006, -0.025), (-0.036, -0.125), (-0.080, -0.120)], -0.011, 0.011, METAL_DARK)
    mg.box(-0.088, -0.030, -0.136, -0.123, -0.015, 0.015, body)
    _add_mag_bullet(mg, -0.026, -0.025)

    end = L
    if suppressor:
        m.cyl(L, L + 0.155, 0.017, 0.0, 0.016, METAL_DARK, n=8)
        end = L + 0.155
    _right_hand(m, pistol=True)
    m.fore_grip = (-0.042, -0.072, -0.024)
    m.mag_grab = (-0.058, -0.115, -0.008)
    m.mag_base = (-0.062, -0.145, 0.0)
    m.bolt_grab = (-0.025, 0.032, -0.012)
    m.sight_y, m.ads_z = 0.052, 0.34
    m.muzzle = (end, 0.017, 0.0)
    return m


def _revolver(body):
    m = Model()
    m.box(-0.052, 0.042, -0.022, 0.036, -0.012, 0.012, body)
    m.cyl(0.042, 0.245, 0.022, 0.0, 0.010, body, n=8)
    m.box(0.042, 0.245, 0.028, 0.040, -0.006, 0.006, body)
    m.box(0.228, 0.242, 0.040, 0.052, -0.003, 0.003, RED_DOT)
    m.box(-0.045, -0.030, 0.036, 0.046, -0.009, 0.009, METAL_DARK)
    # Ổ quay 6 viên tách vào m.mag để bật ngang sang trái khi nạp đạn!
    cyl_mag = m.new_mag(hidden=False)
    cyl_mag.cyl(-0.006, 0.048, 0.012, 0.0, 0.025, STEEL, n=6)
    cyl_mag.cyl(-0.008, -0.005, 0.012, 0.0, 0.018, BRASS, n=6)
    # Búa đập tách vào m.bolt
    bl = m.new_bolt()
    bl.extrude([(-0.064, 0.034), (-0.048, 0.052), (-0.036, 0.034)], -0.004, 0.004, METAL_DARK)
    # Speedloader 6 viên đồng đưa vào khi nạp
    sh = m.new_shell()
    sh.cyl(-0.035, -0.010, 0.012, -0.052, 0.020, METAL_DARK, n=6)
    sh.cyl(-0.010, 0.025, 0.012, -0.052, 0.016, BRASS, n=6)

    _grip(m, (96, 58, 34), x=-0.030, slope=0.040, length=0.112)
    _trigger_guard(m, body, x=-0.01)
    _right_hand(m, pistol=True)
    m.fore_grip = (-0.045, -0.074, -0.024)
    m.mag_grab = (0.015, 0.005, -0.052)
    m.bolt_grab = (-0.052, 0.042, 0.0)
    m.sight_y, m.ads_z = 0.056, 0.34
    m.muzzle = (0.245, 0.022, 0.0)
    return m


def _rifle_ak(wood, metal, accent=None):
    m = Model()
    accent = accent or wood
    m.box(-0.13, 0.18, -0.03, 0.040, -0.021, 0.021, metal)
    m.box(-0.12, 0.15, 0.040, 0.056, -0.017, 0.017, metal)
    m.box(0.18, 0.37, -0.028, 0.034, -0.025, 0.025, wood)
    m.cyl(0.17, 0.40, 0.050, 0.0, 0.012, accent)
    m.cyl(0.36, 0.60, 0.012, 0.0, 0.011, METAL_DARK)
    m.box(0.54, 0.556, 0.020, 0.064, -0.004, 0.004, METAL_DARK)
    m.cyl(0.58, 0.64, 0.012, 0.0, 0.016, accent)
    m.box(0.05, 0.085, 0.056, 0.070, -0.008, 0.008, METAL_DARK)

    # Cụm khóa nòng + tay kéo đạn AK
    bl = m.new_bolt()
    bl.box(0.03, 0.12, 0.024, 0.042, 0.016, 0.023, STEEL)
    bl.cyl(0.09, 0.115, 0.033, 0.023, 0.006, METAL_DARK, n=6)
    bl.box(0.09, 0.11, 0.030, 0.038, 0.022, 0.044, METAL_DARK)

    # Băng đạn cong đặc trưng + viên đạn đồng trên đỉnh
    mg = m.new_mag()
    mg.extrude([(0.04, -0.028), (0.12, -0.028), (0.172, -0.212), (0.086, -0.226)], -0.015, 0.015, METAL_DARK)
    mg.box(0.084, 0.174, -0.232, -0.214, -0.017, 0.017, accent)
    _add_mag_bullet(mg, 0.082, -0.028)

    _grip(m, METAL_DARK)
    _trigger_guard(m, metal)
    m.extrude([(-0.13, 0.04), (-0.13, -0.03), (-0.43, -0.095), (-0.45, 0.015)], -0.020, 0.020, wood)
    _right_hand(m)
    m.fore_grip = (0.265, -0.022, -0.016)
    m.mag_grab = (0.115, -0.145, -0.010)
    m.mag_base = (0.130, -0.235, 0.0)
    m.bolt_grab = (0.095, 0.036, 0.035)
    m.sight_y, m.ads_z = 0.076, 0.46
    m.muzzle = (0.64, 0.012, 0.0)
    return m


def _rifle_ar(body, accent, suppressor=False):
    m = Model()
    m.box(-0.14, 0.16, -0.02, 0.050, -0.021, 0.021, body)
    m.box(-0.10, 0.105, -0.052, -0.02, -0.019, 0.019, body)
    m.box(-0.13, 0.36, 0.050, 0.063, -0.013, 0.013, METAL_DARK)
    for i in range(8):
        x = -0.11 + i * 0.058
        m.box(x, x + 0.022, 0.063, 0.070, -0.013, 0.013, METAL_DARK)
    m.box(0.16, 0.37, -0.030, 0.048, -0.026, 0.026, accent)
    # Kính ngắm Holographic / Red-dot sắc nét
    m.box(-0.025, 0.070, 0.070, 0.118, -0.020, 0.020, METAL_DARK)
    m.box(-0.012, 0.002, 0.078, 0.110, -0.014, 0.014, LENS)
    m.box(-0.005, 0.005, 0.092, 0.098, -0.003, 0.003, RED_DOT)

    if suppressor:
        m.cyl(0.37, 0.47, 0.012, 0.0, 0.011, METAL_DARK)
        m.cyl(0.46, 0.69, 0.012, 0.0, 0.022, (46, 50, 58), n=8)
        end = 0.69
    else:
        m.cyl(0.37, 0.56, 0.012, 0.0, 0.011, METAL_DARK)
        m.cyl(0.55, 0.61, 0.012, 0.0, 0.016, METAL_DARK)
        end = 0.61

    # Khóa nòng chữ T phía sau + cửa hất vỏ đạn
    bl = m.new_bolt()
    bl.box(-0.155, -0.125, 0.042, 0.054, -0.024, 0.024, STEEL)
    bl.box(0.01, 0.08, 0.016, 0.036, 0.019, 0.023, STEEL)

    mg = m.new_mag()
    mg.extrude([(0.018, -0.048), (0.092, -0.048), (0.116, -0.202), (0.042, -0.212)], -0.015, 0.015, METAL_DARK)
    mg.box(0.038, 0.118, -0.220, -0.202, -0.017, 0.017, accent)
    _add_mag_bullet(mg, 0.056, -0.048)

    _grip(m, METAL_DARK)
    _trigger_guard(m, body)
    m.cyl(-0.34, -0.14, 0.022, 0.0, 0.016, METAL_DARK)
    m.extrude([(-0.42, 0.055), (-0.27, 0.055), (-0.27, 0.0), (-0.31, -0.07), (-0.42, -0.075)],
              -0.021, 0.021, accent)
    _right_hand(m)
    m.fore_grip = (0.265, -0.020, -0.018)
    m.mag_grab = (0.068, -0.145, -0.010)
    m.mag_base = (0.078, -0.225, 0.0)
    m.bolt_grab = (-0.145, 0.048, -0.015)
    m.sight_y, m.ads_z = 0.102, 0.44
    m.muzzle = (end, 0.012, 0.0)
    return m


def _guardian(body, accent):
    m = Model()
    m.box(-0.16, 0.20, -0.025, 0.050, -0.023, 0.023, body)
    m.box(0.20, 0.42, -0.020, 0.044, -0.025, 0.025, accent)
    m.box(-0.12, 0.40, 0.050, 0.065, -0.012, 0.012, METAL_DARK)
    m.cyl(0.42, 0.72, 0.012, 0.0, 0.012, METAL_DARK)
    m.cyl(0.70, 0.76, 0.012, 0.0, 0.018, METAL_DARK)
    m.cyl(-0.04, 0.12, 0.095, 0.0, 0.020, METAL_DARK, n=8)
    m.box(0.02, 0.05, 0.065, 0.078, -0.008, 0.008, METAL_DARK)

    bl = m.new_bolt()
    bl.box(0.04, 0.13, 0.024, 0.044, 0.018, 0.025, STEEL)
    bl.box(0.10, 0.12, 0.030, 0.042, 0.022, 0.044, STEEL)

    mg = m.new_mag()
    mg.extrude([(0.02, -0.025), (0.09, -0.025), (0.10, -0.155), (0.03, -0.160)], -0.015, 0.015, METAL_DARK)
    _add_mag_bullet(mg, 0.056, -0.025)

    _grip(m, METAL_DARK)
    _trigger_guard(m, body)
    m.extrude([(-0.16, 0.05), (-0.16, -0.025), (-0.46, -0.08), (-0.47, 0.02), (-0.30, 0.03)],
              -0.021, 0.021, accent)
    _right_hand(m)
    m.fore_grip = (0.295, -0.018, -0.018)
    m.mag_grab = (0.062, -0.115, -0.010)
    m.mag_base = (0.065, -0.170, 0.0)
    m.bolt_grab = (0.105, 0.036, 0.034)
    m.sight_y, m.ads_z = 0.115, 0.48
    m.muzzle = (0.76, 0.012, 0.0)
    return m


def _smg(body, accent, kind):
    m = Model()
    m.box(-0.10, 0.17, -0.025, 0.045, -0.021, 0.021, body)
    bl = m.new_bolt()
    mg = m.new_mag()

    if kind == "MP5":
        m.cyl(0.0, 0.27, 0.032, 0.0, 0.017, body)
        m.box(0.17, 0.30, -0.034, 0.028, -0.027, 0.027, accent)
        m.cyl(0.30, 0.39, 0.012, 0.0, 0.012, METAL_DARK)
        bl.box(0.20, 0.235, 0.032, 0.050, -0.032, -0.014, STEEL)  # Tay kéo HK-slap phía trước!
        mg.extrude([(0.03, -0.025), (0.088, -0.025), (0.128, -0.182), (0.074, -0.192)], -0.013, 0.013, METAL_DARK)
        _add_mag_bullet(mg, 0.058, -0.025)
        m.bolt_grab = (0.215, 0.042, -0.028)
        end = 0.39
    else:
        m.box(0.17, 0.32, -0.030, 0.045, -0.025, 0.025, accent)
        m.box(-0.08, 0.30, 0.045, 0.058, -0.012, 0.012, METAL_DARK)
        m.cyl(0.32, 0.38, 0.012, 0.0, 0.013, METAL_DARK)
        bl.box(0.19, 0.225, 0.034, 0.048, -0.034, -0.016, STEEL)
        mg.extrude([(0.03, -0.025), (0.092, -0.025), (0.098, -0.192), (0.036, -0.192)], -0.014, 0.014, METAL_DARK)
        _add_mag_bullet(mg, 0.062, -0.025)
        m.bolt_grab = (0.205, 0.040, -0.028)
        end = 0.38

    m.box(-0.02, 0.06, 0.056, 0.088, -0.016, 0.016, METAL_DARK)
    m.box(0.01, 0.02, 0.068, 0.078, -0.004, 0.004, RED_DOT)
    _grip(m, METAL_DARK)
    _trigger_guard(m, body)
    m.extrude([(-0.10, 0.04), (-0.10, -0.02), (-0.30, -0.06), (-0.32, 0.03)], -0.018, 0.018, accent)
    _right_hand(m)
    m.fore_grip = (0.235, -0.022, -0.018)
    m.mag_grab = (0.075, -0.130, -0.010)
    m.mag_base = (0.088, -0.202, 0.0)
    m.sight_y, m.ads_z = 0.092, 0.36
    m.muzzle = (end, 0.012, 0.0)
    return m


def _shotgun(body, accent, kind):
    m = Model()
    m.box(-0.12, 0.15, -0.030, 0.045, -0.023, 0.023, body)
    m.cyl(0.15, 0.58, 0.022, 0.0, 0.015, METAL_DARK)
    m.cyl(0.15, 0.50, -0.012, 0.0, 0.014, METAL)
    m.box(0.555, 0.572, 0.036, 0.052, -0.004, 0.004, RED_DOT)

    bl = m.new_bolt()
    if kind == "MAG-7":
        bl.box(0.21, 0.36, -0.042, 0.008, -0.030, 0.030, accent)  # Ốp bơm trượt
        mg = m.new_mag()
        mg.extrude([(0.03, -0.03), (0.09, -0.03), (0.09, -0.175), (0.03, -0.175)], -0.017, 0.017, METAL_DARK)
        mg.cyl(0.042, 0.082, -0.024, 0.0, 0.009, SHELL_RED, n=6)
        m.extrude([(-0.12, 0.04), (-0.12, -0.03), (-0.22, -0.05), (-0.22, 0.035)], -0.020, 0.020, accent)
        m.fore_grip = (0.285, -0.022, -0.018)
        m.mag_grab = (0.060, -0.120, -0.010)
        m.mag_base = (0.060, -0.185, 0.0)
        m.bolt_grab = (0.285, -0.020, -0.018)
    else:
        # M1014 nạp từng viên đạn đỏ vào cổng dưới thân!
        m.box(0.17, 0.40, -0.035, 0.005, -0.026, 0.026, accent)
        m.box(-0.10, 0.12, 0.045, 0.058, -0.012, 0.012, METAL_DARK)
        bl.box(0.02, 0.10, 0.016, 0.036, 0.018, 0.025, STEEL)
        bl.cyl(0.07, 0.09, 0.026, 0.034, 0.006, STEEL, n=6)
        sh = m.new_shell()
        sh.cyl(0.015, 0.068, -0.038, 0.0, 0.010, SHELL_RED, n=6)
        sh.cyl(0.002, 0.016, -0.038, 0.0, 0.0105, BRASS, n=6)
        m.extrude([(-0.12, 0.04), (-0.12, -0.03), (-0.44, -0.095), (-0.45, 0.02)], -0.021, 0.021, accent)
        m.fore_grip = (0.295, -0.020, -0.018)
        m.mag_grab = (0.045, -0.048, -0.010)   # Cổng nhét đạn dưới bụng súng!
        m.bolt_grab = (0.075, 0.026, 0.030)

    _grip(m, METAL_DARK)
    _trigger_guard(m, body)
    _right_hand(m)
    m.sight_y, m.ads_z = 0.065, 0.45
    m.muzzle = (0.58, 0.022, 0.0)
    return m


def _sniper(body, accent, kind):
    m = Model()
    m.box(-0.14, 0.18, -0.03, 0.040, -0.023, 0.023, body)
    m.cyl(0.18, 0.86, 0.012, 0.0, 0.013, METAL_DARK, r1=0.010)
    m.cyl(-0.10, 0.18, 0.105, 0.0, 0.021, METAL_DARK, n=10)
    m.cyl(0.14, 0.22, 0.105, 0.0, 0.029, METAL_DARK, n=10, r1=0.031)
    m.cyl(-0.14, -0.09, 0.105, 0.0, 0.026, METAL_DARK, n=10)
    m.box(-0.06, -0.03, 0.040, 0.085, -0.008, 0.008, METAL)
    m.box(0.09, 0.12, 0.040, 0.085, -0.008, 0.008, METAL)

    # Tay quy-lát bắn tỉa tách riêng vào m.bolt
    bl = m.new_bolt()
    bl.cyl(-0.08, 0.03, 0.026, 0.005, 0.009, STEEL, n=6)
    bl.beam((-0.045, 0.026, 0.014), (-0.055, 0.005, 0.054), 0.010, 0.010, STEEL)
    bl.box(-0.065, -0.045, -0.004, 0.014, 0.048, 0.064, METAL_DARK)

    if kind == "AWM":
        m.cyl(0.84, 0.92, 0.012, 0.0, 0.017, METAL_DARK)
        m.box(0.18, 0.46, -0.04, 0.03, -0.029, 0.029, accent)
        m.extrude([(-0.14, 0.045), (-0.14, -0.03), (-0.26, -0.03), (-0.30, -0.10), (-0.50, -0.09),
                   (-0.50, 0.04)], -0.023, 0.023, accent)
        end = 0.92
    else:
        m.extrude([(0.18, 0.03), (0.52, 0.02), (0.52, -0.02), (0.18, -0.05)], -0.025, 0.025, accent)
        m.extrude([(-0.14, 0.04), (-0.14, -0.04), (-0.48, -0.10), (-0.49, 0.03)], -0.023, 0.023, accent)
        end = 0.86

    mg = m.new_mag()
    mg.extrude([(0.025, -0.03), (0.095, -0.03), (0.095, -0.125), (0.025, -0.125)], -0.014, 0.014, METAL_DARK)
    _add_mag_bullet(mg, 0.060, -0.030)

    _grip(m, accent)
    _trigger_guard(m, body)
    _right_hand(m)
    m.fore_grip = (0.315, -0.020, -0.018)
    m.mag_grab = (0.060, -0.095, -0.010)
    m.mag_base = (0.060, -0.135, 0.0)
    m.bolt_grab = (-0.055, 0.010, 0.048)
    m.sight_y, m.ads_z = 0.105, 0.52
    m.muzzle = (end, 0.012, 0.0)
    return m


def _knife():
    m = Model()
    m.extrude([(0.03, -0.006), (0.20, -0.004), (0.26, 0.02), (0.19, 0.026), (0.03, 0.022)],
              -0.003, 0.003, (195, 202, 214))
    m.extrude([(0.03, 0.022), (0.19, 0.026), (0.19, 0.03), (0.03, 0.028)], -0.0045, 0.0045, (90, 96, 106))
    m.box(0.015, 0.03, -0.022, 0.05, -0.012, 0.012, METAL_DARK)
    m.box(-0.11, 0.015, -0.005, 0.03, -0.014, 0.014, (40, 40, 46))
    m.box(-0.10, -0.01, -0.035, 0.0, -0.028, 0.028, GLOVE)
    m.beam((-0.07, -0.02, 0.0), (-0.40, -0.32, 0.14), 0.072, 0.066, SLEEVE)
    m.fore_grip = None
    m.muzzle = (0.26, 0.02, 0.0)
    return m


_BUILDERS = {
    "CLASSIC": lambda: _pistol((54, 58, 66), (86, 92, 104)),
    "GHOST": lambda: _pistol((52, 56, 62), (152, 158, 168), suppressor=True),
    "SHERIFF": lambda: _revolver((118, 122, 132)),
    "MP5": lambda: _smg((44, 46, 52), (62, 66, 76), "MP5"),
    "UMP": lambda: _smg((70, 74, 66), (92, 96, 84), "UMP"),
    "M014": lambda: _shotgun((50, 52, 58), (68, 72, 82), "M1014"),
    "MAG-7": lambda: _shotgun((60, 64, 72), (202, 124, 42), "MAG-7"),
    "AK-47": lambda: _rifle_ak((124, 72, 38), (58, 60, 66)),
    "VANDAL": lambda: _rifle_ak((172, 50, 46), (54, 56, 64), accent=(224, 184, 68)),
    "M416": lambda: _rifle_ar((52, 54, 60), (180, 154, 106)),
    "PHANTOM": lambda: _rifle_ar((44, 46, 54), (72, 126, 178), suppressor=True),
    "GUARDIAN": lambda: _guardian((58, 62, 70), (198, 188, 162)),
    "M24": lambda: _sniper((56, 58, 64), (108, 74, 44), "M24"),
    "AWM": lambda: _sniper((52, 56, 50), (88, 108, 64), "AWM"),
    "KNIFE": _knife,
}
_ALIAS = {"M1014": "M014", "MAG7": "MAG-7", "AK47": "AK-47"}
_cache = {}
_idle_arm_cache = {}

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


_SPRITE_CACHE = {}


def _render_uncached(target_w, target_h, weapon_id, pos, yaw, pitch, roll, mirror, fov_deg,
                     outline, mag_offset, mag_roll, bolt_back, left_hand_pos, shell_offset):
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

    # Danh sách bộ phận cần vẽ: (sub_model, offset_xyz, roll_rad)
    parts = [(model, None, 0.0)]
    if model.bolt is not None:
        b_off = (-bolt_back, 0.0, 0.0) if abs(bolt_back) > 1e-4 else None
        parts.append((model.bolt, b_off, 0.0))
    if model.mag is not None and not (model.mag_hidden and mag_offset is None):
        parts.append((model.mag, mag_offset, mag_roll))
    if shell_offset is not None and model.shell is not None:
        parts.append((model.shell, shell_offset, 0.0))

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
        for idx, n, col in part.faces:
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
            rim = ((-nz) ** 6 * 0.15) if nz < 0.0 else 0.0
            fill_c = _shade(col, AMBIENT + 0.68 * lam + rim)
            line_c = _shade(fill_c, 0.55) if outline else None
            polys.append(((c0[2] + c1[2]) * 0.5, pts, fill_c, line_c))

    polys.sort(key=lambda p: -p[0])
    mx, my, mz = to_cam(model.muzzle)
    muz = (int(cx), int(cy)) if mz <= 0.02 else (int(cx + mx / mz * f), int(cy + my / mz * f))
    return polys, (min_x, min_y, max_x, max_y), muz


def render(screen, weapon_id, pos, yaw=0.0, pitch=0.0, roll=0.0, mirror=False, fov_deg=58.0,
           outline=True, mag_offset=None, mag_roll=0.0, bolt_back=0.0,
           left_hand_pos=None, shell_offset=None, offset_px=(0, 0)):
    """Vẽ súng 3D với cơ chế tự động Cache Sprite khi ở tư thế cầm súng chuẩn (giữ vững 60-120 FPS)."""
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
                outline, None, 0.0, 0.0, None, None,
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
        outline, mag_offset, mag_roll, bolt_back, left_hand_pos, shell_offset,
    )
    draw_poly = pygame.draw.polygon
    for _, pts, fill_c, line_c in polys:
        shifted = [(vx + ox_px, vy + oy_px) for vx, vy in pts] if (ox_px or oy_px) else pts
        draw_poly(screen, fill_c, shifted)
        if line_c is not None:
            draw_poly(screen, line_c, shifted, 1)
    return (muz[0] + ox_px, muz[1] + oy_px)
