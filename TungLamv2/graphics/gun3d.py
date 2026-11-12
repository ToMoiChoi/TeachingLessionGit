"""gun3d.py - Vẽ súng 3D trên tay (viewmodel) bằng hình khối, KHÔNG cần ảnh PNG.

Mỗi khẩu súng được ghép từ các khối đơn giản:
    box     : hộp chữ nhật (thân súng, ray, ốp nòng...)
    cyl     : ống tròn nằm dọc nòng (nòng, ống ngắm, giảm thanh...)
    extrude : một hình đa giác 2D (nhìn ngang) được "đùn" ra theo bề dày (báng, tay cầm, băng đạn cong...)
    beam    : thanh nối 2 điểm 3D bất kỳ (cánh tay)

Hệ tọa độ của súng (đơn vị ~ mét):
    x: dọc nòng, đầu nòng ở phía +x      y: lên trên      z: sang phải
    Gốc (0, 0, 0) ở đỉnh tay cầm (chỗ tay phải nắm).

Mỗi khung hình: xoay + dịch các đỉnh -> chiếu phối cảnh -> bỏ mặt quay lưng ->
tô màu theo ánh sáng -> vẽ mặt xa trước, mặt gần sau (thuật toán họa sĩ).
"""
import math
import pygame

# ------------------------------------------------------------------ màu dùng chung
METAL = (62, 66, 74)
METAL_DARK = (36, 38, 44)
STEEL = (120, 126, 136)
GLOVE = (34, 34, 38)
SLEEVE = (58, 72, 92)
LENS = (60, 160, 210)

# Hướng từ mặt súng tới đèn: phía trên (-y), hơi trái (-x), hơi về phía người chơi (-z)
LIGHT = (-0.45, -0.80, -0.40)
_l = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _l for c in LIGHT)
AMBIENT = 0.42


# ================================================================== xây mô hình
class Model:
    def __init__(self):
        self.verts = []   # [(x, y, z)]
        self.faces = []   # [(tuple chỉ số đỉnh, pháp tuyến (nx, ny, nz), màu)]
        self.muzzle = (0.5, 0.0, 0.0)

    def _add(self, pts, faces, color):
        base = len(self.verts)
        self.verts.extend(pts)
        for idx, n in faces:
            self.faces.append((tuple(base + i for i in idx), n, color))

    def box(self, x0, x1, y0, y1, z0, z1, color):
        pts = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
        # chỉ số: x0y0z0=0 x0y0z1=1 x0y1z0=2 x0y1z1=3 x1y0z0=4 x1y0z1=5 x1y1z0=6 x1y1z1=7
        self._add(pts, [
            ((0, 1, 3, 2), (-1, 0, 0)), ((4, 6, 7, 5), (1, 0, 0)),
            ((0, 4, 5, 1), (0, -1, 0)), ((2, 3, 7, 6), (0, 1, 0)),
            ((0, 2, 6, 4), (0, 0, -1)), ((1, 5, 7, 3), (0, 0, 1)),
        ], color)

    def cyl(self, x0, x1, yc, zc, r, color, n=8, r1=None):
        """Ống tròn dọc trục x (n cạnh). r1: bán kính đầu x1 nếu muốn ống thon."""
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
        """poly: các điểm (x, y) của mặt nhìn ngang; đùn từ z0 tới z1."""
        area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))
        if area < 0:
            poly = poly[::-1]            # cho đa giác ngược chiều kim đồng hồ
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
        """Thanh hộp nối p0 -> p1 (dùng cho cánh tay)."""
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
        sides = [(s, (1, 2, 6, 5)), (tuple(-c for c in s), (3, 0, 4, 7)),
                 (u, (2, 3, 7, 6)), (tuple(-c for c in u), (0, 1, 5, 4))]
        for n, idx in sides:
            faces.append((idx, tuple(n)))
        self._add(pts, faces, color)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(v):
    ln = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / ln for c in v)


def _shade(c, k):
    return (min(255, int(c[0] * k)), min(255, int(c[1] * k)), min(255, int(c[2] * k)))


# ================================================================== các bộ phận chung
def _grip(m, color, x=-0.035, slope=0.035, length=0.12):
    m.extrude([(x - 0.035, -0.02), (x + 0.02, -0.02), (x + 0.02 - slope, -0.02 - length),
               (x - 0.035 - slope, -0.02 - length + 0.01)], -0.017, 0.017, color)


def _trigger_guard(m, color, x=0.0):
    m.box(x - 0.005, x + 0.05, -0.05, -0.043, -0.006, 0.006, color)


def _hands_rifle(m, fore_x):
    # tay phải nắm tay cầm, cẳng tay đi về phía người chơi (sau, xuống, phải)
    m.box(-0.11, -0.02, -0.115, -0.03, -0.028, 0.03, GLOVE)
    m.beam((-0.09, -0.11, 0.01), (-0.42, -0.40, 0.16), 0.075, 0.07, SLEEVE)
    # tay trái đỡ ốp nòng, cẳng tay đi về phía sau, xuống, sang trái
    m.box(fore_x - 0.045, fore_x + 0.045, -0.065, 0.02, -0.04, 0.034, GLOVE)
    m.beam((fore_x - 0.01, -0.06, -0.02), (fore_x - 0.38, -0.42, -0.30), 0.07, 0.065, SLEEVE)


def _hands_pistol(m):
    m.box(-0.10, -0.015, -0.12, -0.03, -0.03, 0.03, GLOVE)
    m.box(-0.09, -0.02, -0.11, -0.04, -0.045, -0.028, GLOVE)   # tay trái ôm ngoài
    m.beam((-0.08, -0.11, 0.01), (-0.38, -0.42, 0.14), 0.07, 0.065, SLEEVE)
    m.beam((-0.07, -0.10, -0.04), (-0.34, -0.42, -0.26), 0.065, 0.06, SLEEVE)


# ================================================================== từng khẩu súng
def _pistol(body, slide, suppressor=False, long_barrel=False):
    m = Model()
    L = 0.19 if long_barrel else 0.15
    m.box(-0.05, L, 0.0, 0.035, -0.014, 0.014, slide)              # khối trượt (slide)
    m.box(-0.045, L - 0.02, -0.025, 0.0, -0.012, 0.012, body)       # khung
    m.box(L - 0.015, L, 0.035, 0.045, -0.003, 0.003, METAL_DARK)    # đầu ruồi
    m.box(-0.045, -0.03, 0.035, 0.045, -0.009, 0.009, METAL_DARK)   # thước ngắm
    _grip(m, body, x=-0.02, slope=0.03, length=0.11)
    _trigger_guard(m, body, x=0.0)
    end = L
    if suppressor:
        m.cyl(L, L + 0.16, 0.017, 0.0, 0.017, METAL_DARK)
        end = L + 0.16
    else:
        m.cyl(L, L + 0.008, 0.017, 0.0, 0.007, METAL_DARK)
    _hands_pistol(m)
    m.muzzle = (end, 0.017, 0.0)
    return m


def _revolver(body):
    m = Model()
    m.box(-0.05, 0.04, -0.02, 0.035, -0.013, 0.013, body)           # khung
    m.cyl(-0.005, 0.05, 0.012, 0.0, 0.026, STEEL, n=6)              # ổ đạn
    m.cyl(0.04, 0.24, 0.022, 0.0, 0.010, body)                      # nòng
    m.box(0.04, 0.24, 0.026, 0.038, -0.006, 0.006, body)            # gờ trên nòng
    m.box(0.225, 0.24, 0.038, 0.05, -0.003, 0.003, METAL_DARK)
    m.extrude([(-0.06, 0.035), (-0.045, 0.05), (-0.035, 0.035)], -0.004, 0.004, METAL_DARK)  # búa
    _grip(m, (92, 58, 36), x=-0.03, slope=0.04, length=0.11)
    _trigger_guard(m, body, x=-0.01)
    _hands_pistol(m)
    m.muzzle = (0.24, 0.022, 0.0)
    return m


def _rifle_ak(wood, metal, accent=None):
    m = Model()
    accent = accent or wood
    m.box(-0.13, 0.18, -0.03, 0.04, -0.022, 0.022, metal)           # thân
    m.box(-0.12, 0.15, 0.04, 0.056, -0.018, 0.018, metal)           # nắp che bụi
    m.box(0.18, 0.37, -0.028, 0.034, -0.026, 0.026, wood)           # ốp nòng
    m.cyl(0.17, 0.40, 0.052, 0.0, 0.012, accent)                    # ống trích khí
    m.cyl(0.36, 0.60, 0.012, 0.0, 0.011, METAL_DARK)                # nòng
    m.box(0.54, 0.555, 0.02, 0.062, -0.005, 0.005, METAL_DARK)      # đầu ruồi
    m.cyl(0.58, 0.64, 0.012, 0.0, 0.016, METAL_DARK)                # chống giật đầu nòng
    m.box(0.06, 0.09, 0.056, 0.07, -0.008, 0.008, METAL_DARK)       # thước ngắm
    m.extrude([(0.04, -0.03), (0.12, -0.03), (0.17, -0.21), (0.085, -0.225)], -0.016, 0.016, METAL_DARK)
    _grip(m, METAL_DARK)
    _trigger_guard(m, metal)
    m.extrude([(-0.13, 0.04), (-0.13, -0.03), (-0.43, -0.095), (-0.45, 0.015)], -0.02, 0.02, wood)
    _hands_rifle(m, 0.27)
    m.muzzle = (0.64, 0.012, 0.0)
    return m


def _rifle_ar(body, accent, suppressor=False):
    m = Model()
    m.box(-0.14, 0.16, -0.02, 0.05, -0.022, 0.022, body)            # thân trên
    m.box(-0.10, 0.10, -0.05, -0.02, -0.02, 0.02, body)             # thân dưới (ổ băng đạn)
    m.box(-0.13, 0.36, 0.05, 0.064, -0.014, 0.014, METAL_DARK)      # ray Picatinny
    for i in range(10):                                            # khía ray
        x = -0.12 + i * 0.048
        m.box(x, x + 0.018, 0.064, 0.072, -0.014, 0.014, METAL_DARK)
    m.box(0.16, 0.37, -0.032, 0.05, -0.028, 0.028, accent)          # ốp nòng
    m.box(-0.02, 0.07, 0.072, 0.12, -0.02, 0.02, METAL_DARK)        # ống ngắm red dot
    m.box(-0.01, 0.0, 0.08, 0.112, -0.014, 0.014, LENS)
    if suppressor:
        m.cyl(0.37, 0.48, 0.012, 0.0, 0.011, METAL_DARK)
        m.cyl(0.47, 0.70, 0.012, 0.0, 0.024, (48, 50, 56), n=10)
        end = 0.70
    else:
        m.cyl(0.37, 0.56, 0.012, 0.0, 0.011, METAL_DARK)
        m.cyl(0.55, 0.61, 0.012, 0.0, 0.016, METAL_DARK)
        end = 0.61
    m.extrude([(0.015, -0.05), (0.09, -0.05), (0.115, -0.2), (0.04, -0.21)], -0.016, 0.016, METAL_DARK)
    _grip(m, METAL_DARK)
    _trigger_guard(m, body)
    m.cyl(-0.34, -0.14, 0.022, 0.0, 0.016, METAL_DARK)              # ống đệm báng
    m.extrude([(-0.42, 0.055), (-0.27, 0.055), (-0.27, 0.0), (-0.31, -0.07), (-0.42, -0.075)],
              -0.022, 0.022, accent)
    _hands_rifle(m, 0.27)
    m.muzzle = (end, 0.012, 0.0)
    return m


def _guardian(body, accent):
    m = Model()
    m.box(-0.16, 0.20, -0.025, 0.05, -0.024, 0.024, body)
    m.box(0.20, 0.42, -0.02, 0.045, -0.026, 0.026, accent)
    m.box(-0.12, 0.40, 0.05, 0.066, -0.012, 0.012, METAL_DARK)
    m.cyl(0.42, 0.72, 0.012, 0.0, 0.012, METAL_DARK)
    m.cyl(0.70, 0.76, 0.012, 0.0, 0.018, METAL_DARK)
    m.cyl(-0.04, 0.12, 0.095, 0.0, 0.02, METAL_DARK)                # ống ngắm nhỏ
    m.box(0.02, 0.05, 0.066, 0.078, -0.008, 0.008, METAL_DARK)
    m.extrude([(0.02, -0.025), (0.09, -0.025), (0.10, -0.15), (0.03, -0.155)], -0.015, 0.015, METAL_DARK)
    _grip(m, METAL_DARK)
    _trigger_guard(m, body)
    m.extrude([(-0.16, 0.05), (-0.16, -0.025), (-0.46, -0.08), (-0.47, 0.02), (-0.30, 0.03)],
              -0.021, 0.021, accent)
    _hands_rifle(m, 0.30)
    m.muzzle = (0.76, 0.012, 0.0)
    return m


def _smg(body, accent, kind):
    m = Model()
    m.box(-0.10, 0.17, -0.025, 0.045, -0.022, 0.022, body)
    if kind == "MP5":
        m.cyl(0.0, 0.26, 0.03, 0.0, 0.018, body)                     # ống trên MP5
        m.box(0.17, 0.30, -0.035, 0.03, -0.028, 0.028, accent)       # ốp tay to
        m.cyl(0.30, 0.38, 0.012, 0.0, 0.012, METAL_DARK)
        m.extrude([(0.03, -0.025), (0.09, -0.025), (0.13, -0.18), (0.075, -0.19)], -0.013, 0.013, METAL_DARK)
        end = 0.38
    else:  # UMP: thân vuông, băng đạn thẳng
        m.box(0.17, 0.32, -0.03, 0.045, -0.026, 0.026, accent)
        m.box(-0.08, 0.30, 0.045, 0.058, -0.012, 0.012, METAL_DARK)
        m.cyl(0.32, 0.37, 0.012, 0.0, 0.013, METAL_DARK)
        m.extrude([(0.03, -0.025), (0.095, -0.025), (0.10, -0.19), (0.035, -0.19)], -0.015, 0.015, METAL_DARK)
        end = 0.37
    m.box(-0.02, 0.06, 0.058, 0.09, -0.016, 0.016, METAL_DARK)
    _grip(m, METAL_DARK)
    _trigger_guard(m, body)
    m.extrude([(-0.10, 0.04), (-0.10, -0.02), (-0.30, -0.06), (-0.32, 0.03)], -0.018, 0.018, accent)
    _hands_rifle(m, 0.235)
    m.muzzle = (end, 0.012, 0.0)
    return m


def _shotgun(body, accent, kind):
    m = Model()
    m.box(-0.12, 0.15, -0.03, 0.045, -0.024, 0.024, body)           # thân
    m.cyl(0.15, 0.58, 0.022, 0.0, 0.015, METAL_DARK)                # nòng
    m.cyl(0.15, 0.50, -0.012, 0.0, 0.014, METAL)                    # ống tiếp đạn dưới nòng
    m.box(0.56, 0.57, 0.035, 0.05, -0.004, 0.004, STEEL)            # đầu ruồi
    if kind == "MAG-7":
        m.box(0.22, 0.36, -0.04, 0.01, -0.03, 0.03, accent)          # ốp bơm (pump)
        m.extrude([(0.03, -0.03), (0.09, -0.03), (0.09, -0.17), (0.03, -0.17)], -0.018, 0.018, METAL_DARK)
        m.extrude([(-0.12, 0.04), (-0.12, -0.03), (-0.20, -0.05), (-0.20, 0.035)], -0.02, 0.02, accent)
        fore = 0.29
    else:  # M1014: báng dài, ốp tay dài
        m.box(0.17, 0.40, -0.035, 0.005, -0.027, 0.027, accent)
        m.box(-0.10, 0.12, 0.045, 0.058, -0.012, 0.012, METAL_DARK)
        m.extrude([(-0.12, 0.04), (-0.12, -0.03), (-0.44, -0.095), (-0.45, 0.02)], -0.021, 0.021, accent)
        fore = 0.30
    _grip(m, METAL_DARK)
    _trigger_guard(m, body)
    _hands_rifle(m, fore)
    m.muzzle = (0.58, 0.022, 0.0)
    return m


def _sniper(body, accent, kind):
    m = Model()
    m.box(-0.14, 0.18, -0.03, 0.04, -0.024, 0.024, body)
    m.cyl(0.18, 0.86, 0.012, 0.0, 0.013, METAL_DARK, r1=0.010)      # nòng dài, thon dần
    m.cyl(-0.10, 0.18, 0.105, 0.0, 0.022, METAL_DARK, n=10)         # ống ngắm
    m.cyl(0.14, 0.22, 0.105, 0.0, 0.03, METAL_DARK, n=10, r1=0.032) # loa ống ngắm trước
    m.cyl(-0.14, -0.09, 0.105, 0.0, 0.027, METAL_DARK, n=10)        # thị kính
    m.box(-0.06, -0.03, 0.04, 0.085, -0.008, 0.008, METAL)          # chân ống ngắm
    m.box(0.09, 0.12, 0.04, 0.085, -0.008, 0.008, METAL)
    m.cyl(-0.06, -0.03, 0.03, 0.05, 0.007, STEEL)                   # tay khóa nòng (bolt)
    if kind == "AWM":
        m.cyl(0.84, 0.92, 0.012, 0.0, 0.017, METAL_DARK)
        m.box(0.18, 0.46, -0.04, 0.03, -0.03, 0.03, accent)
        m.extrude([(-0.14, 0.045), (-0.14, -0.03), (-0.26, -0.03), (-0.30, -0.10), (-0.50, -0.09),
                   (-0.50, 0.04)], -0.024, 0.024, accent)
        end = 0.92
    else:  # M24: báng gỗ/nhựa liền
        m.extrude([(0.18, 0.03), (0.52, 0.02), (0.52, -0.02), (0.18, -0.05)], -0.026, 0.026, accent)
        m.extrude([(-0.14, 0.04), (-0.14, -0.04), (-0.48, -0.10), (-0.49, 0.03)], -0.024, 0.024, accent)
        end = 0.86
    m.extrude([(0.03, -0.03), (0.09, -0.03), (0.09, -0.11), (0.03, -0.11)], -0.014, 0.014, METAL_DARK)
    _grip(m, accent)
    _trigger_guard(m, body)
    _hands_rifle(m, 0.32)
    m.muzzle = (end, 0.012, 0.0)
    return m


def _knife():
    m = Model()
    m.extrude([(0.03, -0.006), (0.20, -0.004), (0.26, 0.02), (0.19, 0.026), (0.03, 0.022)],
              -0.003, 0.003, (190, 196, 206))                       # lưỡi dao
    m.extrude([(0.03, 0.022), (0.19, 0.026), (0.19, 0.03), (0.03, 0.028)], -0.0045, 0.0045, (90, 96, 106))
    m.box(0.015, 0.03, -0.022, 0.05, -0.012, 0.012, METAL_DARK)     # chắn tay
    m.box(-0.11, 0.015, -0.005, 0.03, -0.014, 0.014, (40, 40, 46))  # cán
    m.box(-0.10, -0.01, -0.035, 0.0, -0.03, 0.03, GLOVE)            # nắm tay
    m.beam((-0.07, -0.02, 0.0), (-0.40, -0.30, 0.12), 0.075, 0.07, SLEEVE)
    m.muzzle = (0.26, 0.02, 0.0)
    return m


# Màu "skin" cho từng súng: (màu thân, màu điểm nhấn)
_BUILDERS = {
    "CLASSIC": lambda: _pistol((54, 58, 66), (78, 84, 94)),
    "GHOST": lambda: _pistol((52, 56, 62), (150, 156, 166), suppressor=True),
    "SHERIFF": lambda: _revolver((112, 116, 124)),
    "MP5": lambda: _smg((44, 46, 52), (60, 64, 72), "MP5"),
    "UMP": lambda: _smg((70, 74, 66), (88, 92, 80), "UMP"),
    "M014": lambda: _shotgun((50, 52, 58), (66, 70, 78), "M1014"),
    "MAG-7": lambda: _shotgun((60, 64, 72), (196, 120, 40), "MAG-7"),
    "AK-47": lambda: _rifle_ak((120, 70, 38), (58, 60, 66)),
    "VANDAL": lambda: _rifle_ak((168, 52, 48), (54, 56, 64), accent=(220, 180, 70)),
    "M416": lambda: _rifle_ar((52, 54, 60), (176, 150, 104)),
    "PHANTOM": lambda: _rifle_ar((44, 46, 54), (70, 120, 170), suppressor=True),
    "GUARDIAN": lambda: _guardian((58, 62, 70), (196, 186, 160)),
    "M24": lambda: _sniper((56, 58, 64), (104, 72, 44), "M24"),
    "AWM": lambda: _sniper((52, 56, 50), (84, 104, 62), "AWM"),
    "KNIFE": _knife,
}
_ALIAS = {"M1014": "M014", "MAG7": "MAG-7", "AK47": "AK-47"}
_cache = {}

PISTOL_IDS = {"CLASSIC", "GHOST", "SHERIFF"}


def get_model(weapon_id):
    key = _ALIAS.get(str(weapon_id).upper(), str(weapon_id).upper())
    if key not in _BUILDERS:
        key = "VANDAL"
    if key not in _cache:
        _cache[key] = _BUILDERS[key]()
    return _cache[key]


# ================================================================== vẽ
def _matrix(yaw, pitch, roll):
    """Ma trận xoay R = Ry(yaw) . Rx(pitch) . Rz(roll) trong hệ tọa độ camera."""
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    rz = ((cr, -sr, 0), (sr, cr, 0), (0, 0, 1))
    rx = ((1, 0, 0), (0, cp, -sp), (0, sp, cp))
    ry = ((cy, 0, sy), (0, 1, 0), (-sy, 0, cy))

    def mul(a, b):
        return tuple(tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3))
    return mul(ry, mul(rx, rz))


def render(screen, weapon_id, pos, yaw=0.0, pitch=0.0, roll=0.0, mirror=False, fov_deg=68.0,
           outline=True):
    """Vẽ súng lên screen.
    pos: (x, y, z) vị trí gốc súng trong hệ camera (x phải, y xuống, z vào trong màn hình).
    Trả về tọa độ màn hình của đầu nòng (để vẽ tia đạn / lửa đầu nòng)."""
    model = get_model(weapon_id)
    sw, sh = screen.get_size()
    cx, cy = sw / 2, sh / 2
    f = (sw / 2) / math.tan(math.radians(fov_deg) / 2)
    R = _matrix(yaw, pitch, roll)
    (a, b, c), (d, e, g), (h, i, j) = R
    px, py, pz = pos
    sx = -1.0 if mirror else 1.0

    def to_cam(v):
        # súng (x trước, y lên, z phải) -> camera (x phải, y xuống, z trước)
        bx, by, bz = v[2], -v[1], v[0]
        return (sx * (a * bx + b * by + c * bz) + px,
                d * bx + e * by + g * bz + py,
                h * bx + i * by + j * bz + pz)

    cam = [to_cam(v) for v in model.verts]
    proj = [(cx + x / z * f, cy + y / z * f) if z > 0.02 else None for x, y, z in cam]

    polys = []
    for idx, n, col in model.faces:
        bx, by, bz = n[2], -n[1], n[0]
        nx = sx * (a * bx + b * by + c * bz)
        ny = d * bx + e * by + g * bz
        nz = h * bx + i * by + j * bz
        k = len(idx)
        fx = sum(cam[t][0] for t in idx) / k
        fy = sum(cam[t][1] for t in idx) / k
        fz = sum(cam[t][2] for t in idx) / k
        if nx * fx + ny * fy + nz * fz >= 0:      # mặt quay lưng về camera -> bỏ
            continue
        pts = [proj[t] for t in idx]
        if None in pts:
            continue
        lam = max(0.0, nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2])
        rim = max(0.0, -nz) ** 6 * 0.15                       # viền sáng nhẹ ở mặt hướng thẳng camera
        polys.append((fz, pts, _shade(col, AMBIENT + 0.68 * lam + rim)))

    polys.sort(key=lambda p: -p[0])
    for _, pts, col in polys:
        pygame.draw.polygon(screen, col, pts)
        if outline:
            pygame.draw.polygon(screen, _shade(col, 0.55), pts, 1)

    mx, my, mz = to_cam(model.muzzle)
    if mz <= 0.02:
        return (int(cx), int(cy))
    return (int(cx + mx / mz * f), int(cy + my / mz * f))
