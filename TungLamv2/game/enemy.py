"""game/enemy.py - Hệ thống Mô hình 3D Giải Phẫu Chân Thực cho Đặc Nhiệm AI & 4 Chủng Loại Zombie.

Đặc điểm kỹ thuật:
- Khung xương 3D giải phẫu có khớp vai, khuỷu tay, cổ tay, hông, khớp gối, cổ chân, cột sống gù/nghiêng.
- Lưới đa diện vát thuôn (Tapered Anatomical Frustums) tô bóng định hướng + ánh sáng viền (Rim Light) mượt mà, loại bỏ hoàn toàn khối hộp Lego và mắt vuông 2D thô.
- 5 thiết kế 3D riêng biệt:
    1. BOT (Đặc nhiệm Spec-Ops): Mũ chống đạn FAST, kính chiến thuật phát sáng, mặt nạ Balaclava, giáp Plate Carrier 3 túi đạn, cầm súng trường bằng CẢ 2 TAY.
    2. WALKER (Zombie xác sống): Lưng gù lệch, bước khập khiễng gập gối, hốc mắt sâu đỏ rực, hàm dưới trễ lộ răng & vết máu, áo rách lộ xương sườn trắng.
    3. RUNNER (Zombie cuồng tốc): Thân gân máu lao rạp 28 độ về trước, mắt cam rực lửa, vuốt xương dài vung chém tốc độ cao.
    4. BRUTE (Zombie khổng lồ): Cơ bắp chữ V khổng lồ, vai đóng giáp sắt chống bạo động vỡ, mạch năng lượng tím phát sáng, nắm đấm bọc thép.
    5. MUTANT (Boss đột biến): Giáp sinh học đen nứt lộ lõi tim xanh độc phát quang, hàng gai tinh thể ngọc lục bảo mọc dọc sống lưng, hai tay biến dị thành lưỡi hái xương.
- Bộ nhớ đệm tư thế 3D khử răng cưa 2 tầng (_BASE_POSE_CACHE & _SCALED_POSE_CACHE) giữ vững 60-120+ FPS kể cả khi đông 14 Zombie trên màn hình.
"""
import math
import random
import pygame
from game.data import ZOMBIE_TYPES

MAT_BODY = 0
MAT_GLOW = 1
MAT_METAL = 2

_SHADOW_CACHE = {}
_BASE_POSE_CACHE = {}
_SCALED_POSE_CACHE = {}

# Ánh sáng 3D trong không gian Camera (x sang phải, y hướng xuống, z hướng vào màn hình)
_L_RAW = (-0.38, -0.68, -0.62)
_L_LEN = math.sqrt(sum(c * c for c in _L_RAW))
_LIGHT_CAM = tuple(c / _L_LEN for c in _L_RAW)


def _norm3(v):
    ln = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / ln, v[1] / ln, v[2] / ln)


def _cross3(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _shade_rgb(c, k):
    r = int(c[0] * k)
    g = int(c[1] * k)
    b = int(c[2] * k)
    return (
        255 if r > 255 else (0 if r < 0 else r),
        255 if g > 255 else (0 if g < 0 else g),
        255 if b > 255 else (0 if b < 0 else b),
    )


def _get_shadow(w, h):
    qw = max(8, (w // 4) * 4)
    qh = max(3, (h // 2) * 2)
    key = (qw, qh)
    surf = _SHADOW_CACHE.get(key)
    if surf is None:
        if len(_SHADOW_CACHE) > 96:
            _SHADOW_CACHE.clear()
        surf = pygame.Surface((qw, qh), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (10, 13, 18, 135), (0, 0, qw, qh))
        if qw > 14 and qh > 5:
            pygame.draw.ellipse(surf, (8, 10, 14, 75), (qw // 6, qh // 6, (qw * 2) // 3, (qh * 2) // 3))
        _SHADOW_CACHE[key] = surf
    return surf


class _CharMesh:
    """Bộ dựng lưới đa diện 3D giải phẫu cơ thể trong hệ tọa độ nhân vật:
    x: sang phải (+x = tay phải), y: hướng tới trước (+y = mặt trước), z: chiều cao từ mặt đất (0 -> ~70).
    """
    def __init__(self):
        self.verts = []
        self.faces = []  # (indices_tuple, normal_xyz, color_rgb, mat_type)

    def _add(self, pts, face_specs, color, mat=MAT_BODY):
        base = len(self.verts)
        self.verts.extend(pts)
        for idx, n in face_specs:
            self.faces.append((tuple(base + i for i in idx), n, color, mat))

    def limb(self, p0, p1, rx0, ry0, rx1, ry1, color, sides=8, mat=MAT_BODY, cap0=True, cap1=True):
        """Ống cơ thể giải phẫu thuôn mượt nối từ khớp p0 tới khớp p1 (đùi, bắp chân, bắp tay, cẳng tay, ngực, cổ, đầu)."""
        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        dz = p1[2] - p0[2]
        ln = math.sqrt(dx * dx + dy * dy + dz * dz)
        if ln < 1e-4:
            return
        axis = (dx / ln, dy / ln, dz / ln)
        ref = (0.0, 1.0, 0.0) if abs(axis[1]) < 0.88 else (1.0, 0.0, 0.0)
        right = _norm3(_cross3(ref, axis))
        fwd = _norm3(_cross3(axis, right))

        pts = []
        for i in range(sides):
            ang = math.tau * (i + 0.5) / sides
            ca, sa = math.cos(ang), math.sin(ang)
            pts.append((
                p0[0] + right[0] * ca * rx0 + fwd[0] * sa * ry0,
                p0[1] + right[1] * ca * rx0 + fwd[1] * sa * ry0,
                p0[2] + right[2] * ca * rx0 + fwd[2] * sa * ry0,
            ))
            pts.append((
                p1[0] + right[0] * ca * rx1 + fwd[0] * sa * ry1,
                p1[1] + right[1] * ca * rx1 + fwd[1] * sa * ry1,
                p1[2] + right[2] * ca * rx1 + fwd[2] * sa * ry1,
            ))

        faces = []
        for i in range(sides):
            j = (i + 1) % sides
            ang_m = math.tau * (i + 1.0) / sides
            ca, sa = math.cos(ang_m), math.sin(ang_m)
            nx = right[0] * ca + fwd[0] * sa
            ny = right[1] * ca + fwd[1] * sa
            nz = right[2] * ca + fwd[2] * sa
            # Đảm bảo pháp tuyến hướng ra ngoài khối cơ thể
            faces.append(((2 * i, 2 * j, 2 * j + 1, 2 * i + 1), _norm3((nx, ny, nz))))
        if cap0:
            faces.append((tuple(2 * (sides - 1 - i) for i in range(sides)), (-axis[0], -axis[1], -axis[2])))
        if cap1:
            faces.append((tuple(2 * i + 1 for i in range(sides)), axis))
        self._add(pts, faces, color, mat)

    def spike(self, base_pt, tip_pt, rx, ry, color, sides=5, mat=MAT_BODY):
        """Gai xương / sừng / móng vuốt / tinh thể nhọn thuôn về đỉnh tip_pt."""
        self.limb(base_pt, tip_pt, rx, ry, 0.18, 0.18, color, sides=sides, mat=mat, cap0=True, cap1=False)

    def box_oriented(self, p0, p1, w, h, color, mat=MAT_BODY):
        """Thanh hộp định hướng 3D (dùng cho súng trường, túi đạn, mảnh giáp, xương sườn, lưỡi hái)."""
        self.limb(p0, p1, w * 0.5, h * 0.5, w * 0.5, h * 0.5, color, sides=4, mat=mat)


def _fk_point(origin, length, pitch, roll=0.0, yaw=0.0):
    """Tính vị trí khớp con hướng từ origin xuống dưới (-z) rồi xoay theo pitch (+y tới trước), roll (+x ngang), yaw."""
    # Gốc mặc định duỗi xuống (0, 0, -length)
    x = length * math.sin(roll)
    y0 = length * math.sin(pitch) * math.cos(roll)
    z = -length * math.cos(pitch) * math.cos(roll)
    if abs(yaw) > 1e-4:
        cy, sy = math.cos(yaw), math.sin(yaw)
        rx = x * cy - y0 * sy
        ry = x * sy + y0 * cy
        x, y0 = rx, ry
    return (origin[0] + x, origin[1] + y0, origin[2] + z)


def _add_sculpted_skull(m, base_pt, tilt_x, fwd_lean, skin_col, jaw_col, eye_col, mouth_col, scale_w=1.0, dome_col=None):
    """Dựng hộp sọ giải phẫu người/quái vật 3 tầng bo vòm tự nhiên + gò má + cung mày + sống mũi + hàm răng hở."""
    bx, by, bz = base_pt
    dc = dome_col or skin_col
    # Tầng 1: Quai hàm dưới & cằm thuôn nhọn
    chin = (bx + tilt_x * 0.2, by + 1.8 * scale_w + fwd_lean * 0.2, bz - 2.2)
    cheek = (bx + tilt_x * 0.5, by + 0.6 + fwd_lean * 0.5, bz + 3.4)
    brow = (bx + tilt_x * 0.8, by + 0.8 + fwd_lean * 0.8, bz + 6.8)
    crown = (bx + tilt_x * 1.0, by - 0.2 + fwd_lean * 0.9, bz + 9.8)
    top_dome = (bx + tilt_x * 1.1, by - 0.6 + fwd_lean * 0.9, bz + 11.4)

    m.limb(chin, cheek, 2.5 * scale_w, 2.8 * scale_w, 4.3 * scale_w, 4.7 * scale_w, jaw_col, sides=10)
    m.limb(cheek, brow, 4.3 * scale_w, 4.7 * scale_w, 4.6 * scale_w, 5.1 * scale_w, skin_col, sides=10)
    # Vòm sọ bo tròn thuôn lên đỉnh đầu (loại bỏ hoàn toàn đỉnh đầu phẳng kiểu hình trụ!)
    m.limb(brow, crown, 4.6 * scale_w, 5.1 * scale_w, 3.8 * scale_w, 4.3 * scale_w, dc, sides=10)
    m.limb(crown, top_dome, 3.8 * scale_w, 4.3 * scale_w, 1.9 * scale_w, 2.2 * scale_w, dc, sides=8)

    # Gờ xương chân mày nhô ra trước che hốc mắt sâu + sống mũi 3D
    brow_y = brow[1] + 4.8 * scale_w
    m.box_oriented(
        (brow[0] - 3.3 * scale_w, brow_y, brow[2] - 0.2),
        (brow[0] + 3.3 * scale_w, brow_y, brow[2] - 0.2),
        1.5 * scale_w, 1.4, dc,
    )
    m.spike(
        (cheek[0], cheek[1] + 4.4 * scale_w, cheek[2] + 1.8),
        (cheek[0], cheek[1] + 5.7 * scale_w, cheek[2] + 0.2),
        0.95 * scale_w, 0.95, skin_col,
    )

    # Hốc mắt sâu tối + đồng tử phát sáng nằm sâu dưới chân mày
    for side in (-1.0, 1.0):
        ex = brow[0] + side * 1.85 * scale_w
        ey = brow[1] + 4.45 * scale_w
        ez = brow[2] - 1.35
        m.box_oriented((ex - 0.85, ey, ez), (ex + 0.85, ey, ez), 1.4, 1.4, (16, 12, 14))
        m.box_oriented((ex - 0.45, ey + 0.45, ez), (ex + 0.45, ey + 0.45, ez), 0.85, 0.85, eye_col, MAT_GLOW)

    # Khoang miệng tối đẫm máu + hàm răng nanh nhọn trên/dưới
    mx, my, mz = cheek[0], cheek[1] + 4.35 * scale_w, cheek[2] - 1.1
    m.box_oriented((mx - 1.9 * scale_w, my, mz), (mx + 1.9 * scale_w, my, mz), 2.2, 2.4, mouth_col)
    for tx in (-1.15 * scale_w, 0.0, 1.15 * scale_w):
        m.spike((mx + tx, my + 0.35, mz + 0.95), (mx + tx, my + 0.45, mz + 0.05), 0.42, 0.42, (222, 212, 192))


# ==============================================================================
# DỰNG HÌNH 5 CHỦNG LOẠI KẺ ĐỊCH & ZOMBIE CHÂN THỰC
# ==============================================================================
def _build_tactical_bot_mesh(walk_phase, atk_phase):
    """1. ĐẶC NHIỆM AI (Spec-Ops Operator): Quân phục Urban-Slate, giáp đen túi Khaki, mũ FAST bo vòm, cầm súng chéo ngực 2 tay."""
    m = _CharMesh()
    jacket_slate = (68, 78, 94)
    pants_slate = (52, 60, 74)
    vest_black = (30, 34, 42)
    khaki_rig = (138, 122, 92)
    helmet_col = (44, 52, 62)
    balaclava = (24, 26, 32)
    skin_brow = (206, 158, 128)
    visor_glow = (255, 76, 48)
    team_red = (204, 38, 46)
    boot_col = (20, 22, 28)
    gun_metal = (26, 30, 36)
    gun_steel = (134, 142, 156)

    stride = math.sin(walk_phase) if walk_phase >= 0.0 else 0.0
    bob_z = abs(math.cos(walk_phase)) * 1.1 if walk_phase >= 0.0 else 0.0

    # --- ĐÔI CHÂN CHIẾN THUẬT CÓ KHỚP GỐI, BỌC GỐI & BAO SÚNG ĐÙI ---
    for side, s_mult in ((-1.0, 1.0), (1.0, -1.0)):
        sw = stride * s_mult
        hip = (side * 4.4, 0.0, 33.5 + bob_z)
        thigh_pitch = sw * 0.42 + 0.06
        knee_bend = max(0.10, -sw * 0.48 + 0.16)
        knee = _fk_point(hip, 15.5, thigh_pitch, roll=side * 0.04)
        ankle = _fk_point(knee, 14.5, thigh_pitch - knee_bend, roll=side * 0.02)

        m.limb(hip, knee, 3.7, 4.0, 2.8, 3.0, pants_slate, sides=8)
        if side > 0:
            # Bao súng ngắn chiến thuật đeo bên đùi phải
            hx_p = (hip[0] + knee[0]) * 0.5 + 3.1
            hy_p = (hip[1] + knee[1]) * 0.5
            hz_p = (hip[2] + knee[2]) * 0.5 + 1.0
            m.box_oriented((hx_p, hy_p, hz_p + 2.2), (hx_p, hy_p, hz_p - 2.2), 1.8, 3.0, vest_black, MAT_METAL)
        m.limb(
            (knee[0], knee[1] + 0.9, knee[2] + 1.5),
            (knee[0], knee[1] + 0.9, knee[2] - 1.6),
            2.9, 2.7, 2.7, 2.5, vest_black, sides=6, mat=MAT_METAL,
        )
        m.limb(knee, ankle, 2.8, 3.0, 2.2, 2.4, pants_slate, sides=8)
        foot_base = (ankle[0], ankle[1] + 0.4, max(0.0, ankle[2] - 3.4))
        toe = (ankle[0], ankle[1] + 5.8, max(0.2, ankle[2] - 3.2))
        m.limb(ankle, foot_base, 2.5, 2.7, 2.8, 3.2, boot_col, sides=6)
        m.limb((foot_base[0], foot_base[1] - 1.2, foot_base[2] + 1.5), toe, 2.7, 1.9, 2.1, 1.4, boot_col, sides=6)

    # --- HÔNG, THẮT LƯNG KHAKI, ÁO KHOÁC SLATE & GIÁP CHỐNG ĐẠN PLATE CARRIER + BA LÔ ---
    pelvis_b = (0.0, 0.0, 31.5 + bob_z)
    waist = (0.0, 0.4, 37.5 + bob_z)
    chest_top = (0.0, 1.2, 53.2 + bob_z)
    m.limb(pelvis_b, waist, 7.3, 4.5, 6.5, 4.1, pants_slate, sides=8)
    m.limb((0.0, 0.2, 34.6 + bob_z), (0.0, 0.3, 37.3 + bob_z), 7.7, 4.9, 7.6, 4.8, khaki_rig, sides=8)
    m.limb(waist, chest_top, 6.6, 4.3, 8.9, 5.3, jacket_slate, sides=10)

    # Áo giáp đen Plate Carrier + 3 túi đạn Khaki nổi khối rõ ràng + Ba lô tác chiến sau lưng
    m.limb((0.0, 0.9, 38.8 + bob_z), (0.0, 1.6, 51.6 + bob_z), 7.3, 5.4, 7.9, 5.9, vest_black, sides=8, mat=MAT_METAL)
    for px in (-3.6, 0.0, 3.6):
        m.box_oriented((px, 6.0, 39.4 + bob_z), (px, 6.3, 45.0 + bob_z), 2.5, 2.2, khaki_rig)
    m.box_oriented((-4.6, 5.8, 47.6 + bob_z), (4.6, 5.8, 49.4 + bob_z), 9.2, 1.8, team_red)
    m.box_oriented((0.0, -5.2, 40.2 + bob_z), (0.0, -4.8, 50.8 + bob_z), 8.2, 4.2, vest_black)

    # --- ĐẦU BALACLAVA LỘ MẮT/SỐNG MŨI NGƯỜI THẬT + KÍNH CHIẾN THUẬT + MŨ CHỐNG ĐẠN FAST BO VÒM ---
    neck_b = (0.0, 1.2, 53.0 + bob_z)
    m.limb(neck_b, (0.0, 1.5, 56.2 + bob_z), 3.2, 3.2, 3.0, 3.0, balaclava, sides=8)
    m.limb((0.0, 1.6, 55.2 + bob_z), (0.0, 1.7, 60.5 + bob_z), 4.2, 4.6, 4.6, 5.1, balaclava, sides=10)
    # Vùng da mặt thật quanh sống mũi/mắt dưới kính chiến thuật
    m.limb((0.0, 2.1, 59.4 + bob_z), (0.0, 2.1, 61.6 + bob_z), 4.4, 4.8, 4.5, 4.9, skin_brow, sides=10)
    # Mũ chống đạn FAST bo tròn 2 tầng lên đỉnh vòm + chụp tai nghe ComTac + NVG Mount
    m.limb((0.0, 1.3, 61.0 + bob_z), (0.0, 1.1, 66.2 + bob_z), 5.6, 6.1, 4.9, 5.4, helmet_col, sides=10, mat=MAT_METAL)
    m.limb((0.0, 1.1, 66.2 + bob_z), (0.0, 0.9, 68.8 + bob_z), 4.9, 5.4, 2.4, 2.8, helmet_col, sides=10, mat=MAT_METAL)
    m.box_oriented((-5.4, 1.4, 58.2 + bob_z), (-5.4, 1.4, 62.2 + bob_z), 1.8, 3.4, khaki_rig, MAT_METAL)
    m.box_oriented((5.4, 1.4, 58.2 + bob_z), (5.4, 1.4, 62.2 + bob_z), 1.8, 3.4, khaki_rig, MAT_METAL)
    m.box_oriented((-3.8, 6.0, 60.4 + bob_z), (3.8, 6.0, 60.4 + bob_z), 2.4, 2.2, visor_glow, MAT_GLOW)
    m.box_oriented((0.0, 6.4, 64.5 + bob_z), (0.0, 7.8, 63.8 + bob_z), 3.4, 2.0, gun_metal, MAT_METAL)

    # --- HAI CÁNH TAY ÁO XÁM SLATE + ĐỆM VAI ĐỎ CẦM SÚNG TRƯỜNG HƠI CHÉO QUA NGỰC (NHÌN RÕ TỪ CHÍNH DIỆN!) ---
    kick = atk_phase * 1.4
    sh_r = (9.6, 1.0, 50.6 + bob_z)
    sh_l = (-9.6, 1.0, 50.6 + bob_z)
    m.limb(sh_r, (10.6, 1.4, 46.5 + bob_z), 3.5, 3.7, 3.1, 3.2, team_red, sides=8)
    m.limb(sh_l, (-10.6, 1.4, 46.5 + bob_z), 3.5, 3.7, 3.1, 3.2, team_red, sides=8)

    elbow_r = (10.4, 4.5 - kick * 0.5, 41.2 + bob_z)
    hand_r = (5.4, 10.2 - kick, 43.8 + bob_z)
    elbow_l = (-8.8, 7.6 - kick * 0.5, 41.0 + bob_z)
    hand_l = (-0.8, 17.6 - kick, 44.5 + bob_z)

    m.limb(sh_r, elbow_r, 3.0, 3.1, 2.5, 2.6, jacket_slate, sides=8)
    m.limb(elbow_r, hand_r, 2.5, 2.6, 2.0, 2.1, jacket_slate, sides=8)
    m.limb(hand_r, (hand_r[0], hand_r[1] + 1.8, hand_r[2]), 2.1, 2.2, 1.9, 2.0, balaclava, sides=6)

    m.limb(sh_l, elbow_l, 3.0, 3.1, 2.5, 2.6, jacket_slate, sides=8)
    m.limb(elbow_l, hand_l, 2.5, 2.6, 2.0, 2.1, jacket_slate, sides=8)
    m.limb(hand_l, (hand_l[0], hand_l[1] + 1.8, hand_l[2]), 2.1, 2.2, 1.9, 2.0, balaclava, sides=6)

    # --- KHẨU SÚNG TRƯỜNG ASSAULT CARBINE CẦM HƠI CHÉO TRƯỚC NGỰC RẤT CHÂN THỰC ---
    stock_pt = (7.4, 4.0 - kick, 45.2 + bob_z)
    recv_pt = (3.4, 12.8 - kick, 45.8 + bob_z)
    hg_pt = (-1.2, 21.2 - kick, 46.2 + bob_z)
    muz_pt = (-4.2, 29.2 - kick, 46.5 + bob_z)
    m.box_oriented(stock_pt, recv_pt, 2.1, 3.5, gun_metal, MAT_METAL)
    m.box_oriented(recv_pt, hg_pt, 2.4, 3.7, gun_metal, MAT_METAL)
    m.limb(hg_pt, muz_pt, 0.95, 0.95, 0.85, 0.85, gun_steel, sides=6, mat=MAT_METAL)
    m.box_oriented((2.2, 14.5 - kick, 44.8 + bob_z), (1.4, 16.2 - kick, 37.2 + bob_z), 1.7, 2.5, khaki_rig)
    m.box_oriented((3.0, 12.5 - kick, 48.3 + bob_z), (1.6, 16.0 - kick, 48.5 + bob_z), 1.9, 2.1, gun_steel, MAT_METAL)
    return m


def _build_walker_zombie_mesh(walk_phase, atk_phase):
    """2. ZOMBIE THƯỜNG (WALKER): Sọ giải phẫu bo tròn ngoẹo lệch, sườn cong 3D, tay khuỳnh khuỷu vồ mồi kinh dị."""
    m = _CharMesh()
    rot_skin = (118, 138, 104)
    bruise_skin = (82, 94, 76)
    blood_dark = (124, 22, 28)
    bone_rib = (218, 208, 188)
    coat_torn = (58, 64, 56)
    coat_rag = (44, 48, 42)
    pants_torn = (42, 46, 52)
    eye_red = (255, 48, 44)

    limp = math.sin(walk_phase) if walk_phase >= 0.0 else 0.0
    lurch_z = abs(math.sin(walk_phase * 0.5)) * 1.4 if walk_phase >= 0.0 else 0.0

    # Chân trái bước gập gối, chân phải rách quần lộ cẳng chân xương xẩu kéo lê
    hip_l = (-4.3, -0.5, 31.5 + lurch_z)
    knee_l = _fk_point(hip_l, 15.0, limp * 0.46 + 0.18, roll=-0.07)
    ank_l = _fk_point(knee_l, 14.5, limp * 0.46 - 0.24, roll=-0.03)
    m.limb(hip_l, knee_l, 3.4, 3.6, 2.6, 2.8, pants_torn, sides=8)
    m.limb(knee_l, ank_l, 2.5, 2.7, 2.0, 2.2, pants_torn, sides=8)
    m.limb(ank_l, (ank_l[0], ank_l[1] + 4.8, max(0.2, ank_l[2] - 2.6)), 2.3, 1.8, 1.9, 1.2, (26, 26, 24), sides=6)

    hip_r = (4.3, -1.0, 31.0 + lurch_z)
    knee_r = _fk_point(hip_r, 14.8, -limp * 0.34 - 0.05, roll=0.09)
    ank_r = _fk_point(knee_r, 14.2, -limp * 0.34 - 0.32, roll=0.05)
    m.limb(hip_r, knee_r, 3.3, 3.5, 2.5, 2.7, pants_torn, sides=8)
    m.limb(knee_r, ank_r, 2.2, 2.4, 1.7, 1.8, rot_skin, sides=8)
    m.box_oriented((knee_r[0], knee_r[1] + 1.8, knee_r[2] - 3.2), (knee_r[0], knee_r[1] + 1.5, knee_r[2] - 7.5), 1.1, 1.1, blood_dark)
    m.limb(ank_r, (ank_r[0], ank_r[1] + 4.6, max(0.2, ank_r[2] - 2.6)), 2.2, 1.7, 1.8, 1.2, bruise_skin, sides=6)

    # Cột sống gù chúi về trước + Vạt áo khoác rách tả tơi rủ lệch bên hông
    pelvis = (0.0, -0.8, 30.0 + lurch_z)
    mid_spine = (-0.6, 2.4, 39.5 + lurch_z)
    chest = (-1.0, 6.4, 50.2 + lurch_z)
    m.limb(pelvis, mid_spine, 6.6, 4.0, 6.1, 4.0, coat_torn, sides=8)
    m.limb(mid_spine, chest, 6.3, 4.2, 8.4, 4.9, coat_torn, sides=9)
    m.spike((-5.2, 0.8, 34.5 + lurch_z), (-6.2, -0.5, 24.5 + lurch_z), 2.4, 1.6, coat_rag)
    m.spike((4.8, 0.5, 34.0 + lurch_z), (5.6, -0.8, 26.2 + lurch_z), 2.1, 1.5, coat_rag)

    # Hốc ngực rách đẫm máu + 3 cặp xương sườn cong chữ V ôm quanh lồng ngực!
    m.limb((0.4, 5.5, 40.0 + lurch_z), (0.2, 7.8, 48.6 + lurch_z), 4.6, 3.7, 5.0, 3.9, blood_dark, sides=8)
    for rz, ry in ((42.0, 8.2), (44.8, 8.9), (47.5, 9.5)):
        m.box_oriented((-3.8, ry - 0.9, rz + 0.4 + lurch_z), (-0.5, ry + 0.5, rz - 0.2 + lurch_z), 0.95, 0.95, bone_rib)
        m.box_oriented((0.5, ry + 0.5, rz - 0.2 + lurch_z), (3.9, ry - 0.9, rz + 0.4 + lurch_z), 0.95, 0.95, bone_rib)

    # Sọ người hoại tử bo vòm tự nhiên, nghiêng ngoẹo sang phải!
    m.limb((-1.0, 6.8, 50.4 + lurch_z), (0.4, 8.8, 54.4 + lurch_z), 2.9, 2.9, 2.6, 2.8, bruise_skin, sides=8)
    _add_sculpted_skull(
        m, (0.5, 8.8, 54.4 + lurch_z),
        tilt_x=1.5, fwd_lean=1.4,
        skin_col=rot_skin, jaw_col=bruise_skin, eye_col=eye_red, mouth_col=blood_dark,
        scale_w=1.0, dome_col=bruise_skin,
    )

    # Hai cánh tay KHUỲNH KHUỶU RA NGOÀI rồi quặp bàn tay móng máu vào trong (nhìn từ chính diện cực kỳ thật & đáng sợ!)
    slash = atk_phase * 0.68
    sh_l = (-8.8, 5.8, 49.2 + lurch_z)
    elb_l = (-12.2, 12.8, 43.2 + slash * 3.0 + lurch_z)
    wr_l = (-6.8, 21.2, 42.5 - slash * 6.5 + limp * 1.4 + lurch_z)
    m.limb(sh_l, elb_l, 2.8, 2.9, 2.2, 2.3, coat_torn, sides=7)
    m.limb(elb_l, wr_l, 2.1, 2.2, 1.7, 1.8, rot_skin, sides=7)
    for cx_off, cz_off in ((-1.2, -1.8), (0.0, -2.5), (1.2, -1.8)):
        m.spike(wr_l, (wr_l[0] + cx_off + 1.0, wr_l[1] + 4.2, wr_l[2] + cz_off), 0.65, 0.65, blood_dark)

    sh_r = (7.8, 5.6, 47.4 + lurch_z)
    elb_r = (11.6, 11.8, 40.8 + slash * 3.0 + lurch_z)
    wr_r = (6.4, 20.0, 39.2 - slash * 6.5 - limp * 1.4 + lurch_z)
    m.limb(sh_r, elb_r, 2.7, 2.8, 2.1, 2.2, rot_skin, sides=7)
    m.limb(elb_r, wr_r, 2.1, 2.2, 1.7, 1.8, bruise_skin, sides=7)
    for cx_off, cz_off in ((-1.2, -1.8), (0.0, -2.5), (1.2, -1.8)):
        m.spike(wr_r, (wr_r[0] + cx_off - 1.0, wr_r[1] + 4.2, wr_r[2] + cz_off), 0.65, 0.65, blood_dark)
    return m


def _build_runner_zombie_mesh(walk_phase, atk_phase):
    """3. ZOMBIE CUỒNG TỐC (RUNNER): Hộp sọ bo vòm gân máu, lao rạp 28 độ, hai tay khuỳnh rộng giương vuốt xương dài."""
    m = _CharMesh()
    flayed_red = (164, 64, 60)
    sinew_pale = (198, 128, 114)
    dark_rags = (42, 34, 38)
    bone_claw = (226, 210, 188)
    eye_amber = (255, 196, 34)

    run_s = math.sin(walk_phase) if walk_phase >= 0.0 else 0.35
    leap_z = abs(math.cos(walk_phase)) * 2.2 if walk_phase >= 0.0 else 0.0

    for side, s_mult in ((-1.0, 1.0), (1.0, -1.0)):
        sw = run_s * s_mult
        hip = (side * 3.9, -2.0, 30.5 + leap_z)
        knee = _fk_point(hip, 15.2, sw * 0.68 + 0.25, roll=side * 0.07)
        ank = _fk_point(knee, 15.0, sw * 0.68 - 0.52, roll=side * 0.04)
        m.limb(hip, knee, 3.0, 3.3, 2.1, 2.3, dark_rags, sides=7)
        m.limb(knee, ank, 2.1, 2.3, 1.5, 1.7, flayed_red, sides=7)
        m.spike(ank, (ank[0], ank[1] + 5.2, max(0.2, ank[2] - 2.2)), 1.7, 1.4, sinew_pale)

    pelvis = (0.0, -2.2, 29.5 + leap_z)
    waist = (0.0, 2.5, 37.5 + leap_z)
    chest = (0.0, 9.8, 47.8 + leap_z)
    m.limb(pelvis, waist, 5.6, 3.6, 4.8, 3.2, dark_rags, sides=8)
    m.limb(waist, chest, 5.0, 3.4, 7.8, 4.5, flayed_red, sides=9)
    for k in range(4):
        t = k / 3.0
        sy = 2.0 + t * 7.2 - 3.6
        sz = 37.5 + t * 10.0 + leap_z
        m.spike((0.0, sy, sz), (0.0, sy - 3.4, sz + 2.4), 1.15, 1.15, bone_claw)

    # Sọ quái thú săn mồi bo vòm tự nhiên rướn sát về trước
    m.limb((0.0, 10.2, 47.8 + leap_z), (0.0, 13.0, 50.6 + leap_z), 2.6, 2.6, 2.4, 2.5, flayed_red, sides=8)
    _add_sculpted_skull(
        m, (0.0, 13.0, 50.6 + leap_z),
        tilt_x=0.0, fwd_lean=2.2,
        skin_col=sinew_pale, jaw_col=flayed_red, eye_col=eye_amber, mouth_col=(96, 14, 18),
        scale_w=0.94, dome_col=flayed_red,
    )

    # Hai cánh tay mở rộng khuỷu sang hai bên như thú săn mồi vồ mồi + móng xương dài!
    slash = atk_phase * 0.85
    for side in (-1.0, 1.0):
        sh = (side * 8.2, 9.4, 46.8 + leap_z)
        elb = (side * 12.6, 14.5 - side * run_s * 2.0, 41.5 + slash * 3.5 + leap_z)
        wr = (side * 7.2, 22.8, 38.8 - slash * 7.5 + leap_z)
        m.limb(sh, elb, 2.5, 2.7, 2.0, 2.1, flayed_red, sides=7)
        m.limb(elb, wr, 2.1, 2.2, 1.7, 1.8, sinew_pale, sides=7)
        for c_off in (-1.3, 0.0, 1.3):
            m.spike(wr, (wr[0] + c_off - side * 1.2, wr[1] + 6.4, wr[2] - 3.2), 0.75, 0.75, bone_claw)
    return m


def _build_brute_zombie_mesh(walk_phase, atk_phase):
    """4. ZOMBIE KHỔNG LỒ (BRUTE): Hộp sọ bo vòm bọc giáp hàm sắt, vai hộ pháp chữ V, giáp bạo động & mạch tím."""
    m = _CharMesh()
    hulk_skin = (88, 102, 116)
    hulk_dark = (62, 72, 86)
    armor_steel = (46, 50, 62)
    pants_heavy = (34, 34, 48)
    bio_violet = (204, 88, 255)

    stomp = math.sin(walk_phase) if walk_phase >= 0.0 else 0.0
    sway_x = stomp * 1.2
    bob_z = abs(math.cos(walk_phase)) * 1.2 if walk_phase >= 0.0 else 0.0

    for side, s_mult in ((-1.0, 1.0), (1.0, -1.0)):
        sw = stomp * s_mult
        hip = (side * 5.6 + sway_x * 0.4, 0.0, 30.0 + bob_z)
        knee = _fk_point(hip, 14.2, sw * 0.35 + 0.12, roll=side * 0.08)
        ank = _fk_point(knee, 13.8, sw * 0.35 - 0.16, roll=side * 0.04)
        m.limb(hip, knee, 4.8, 5.0, 3.8, 4.0, pants_heavy, sides=8)
        m.limb(knee, ank, 3.9, 4.1, 3.2, 3.4, armor_steel, sides=8, mat=MAT_METAL)
        m.limb(ank, (ank[0], ank[1] + 5.2, max(0.2, ank[2] - 2.8)), 3.5, 2.6, 3.0, 1.8, (22, 22, 28), sides=6)

    pelvis = (sway_x * 0.4, 0.0, 28.5 + bob_z)
    waist = (sway_x * 0.6, 1.2, 36.5 + bob_z)
    chest = (sway_x, 4.2, 52.5 + bob_z)
    traps = (sway_x, 3.5, 58.2 + bob_z)
    m.limb(pelvis, waist, 8.8, 5.6, 8.0, 5.2, pants_heavy, sides=8)
    m.limb(waist, chest, 8.2, 5.5, 13.4, 8.4, hulk_skin, sides=10)
    m.limb((sway_x, 3.2, 50.5 + bob_z), traps, 11.6, 7.2, 6.8, 5.2, hulk_dark, sides=9)
    m.box_oriented((-6.5 + sway_x, 9.2, 41.5 + bob_z), (5.5 + sway_x, 9.5, 49.5 + bob_z), 12.0, 3.2, armor_steel, MAT_METAL)
    m.box_oriented((-3.5 + sway_x, 10.6, 44.0 + bob_z), (3.5 + sway_x, 10.6, 48.0 + bob_z), 2.2, 1.8, bio_violet, MAT_GLOW)

    # Đầu khổng lồ bo vòm tự nhiên + giáp sắt bọc quai hàm dưới!
    _add_sculpted_skull(
        m, (sway_x, 6.8, 53.6 + bob_z),
        tilt_x=0.0, fwd_lean=0.8,
        skin_col=hulk_skin, jaw_col=armor_steel, eye_col=bio_violet, mouth_col=(48, 22, 58),
        scale_w=1.12, dome_col=hulk_dark,
    )

    smash = atk_phase * 0.95
    for side in (-1.0, 1.0):
        sh = (side * 13.6 + sway_x, 3.8, 50.8 + bob_z)
        m.limb((sh[0], sh[1], sh[2] + 3.2), (sh[0] + side * 1.5, sh[1], sh[2] - 2.5), 4.8, 5.0, 4.4, 4.6, armor_steel, sides=8, mat=MAT_METAL)
        m.spike((sh[0] + side * 1.2, sh[1], sh[2] + 2.8), (sh[0] + side * 4.8, sh[1] - 0.5, sh[2] + 8.5), 1.8, 1.8, bio_violet, mat=MAT_GLOW)

        elb = _fk_point(sh, 13.5, 0.65 + smash * 0.55 - side * stomp * 0.18, roll=side * 0.28)
        fist = _fk_point(elb, 13.8, 1.25 - smash * 1.15, roll=-side * 0.16)
        m.limb(sh, elb, 4.4, 4.6, 3.8, 4.0, hulk_skin, sides=8)
        m.limb(elb, fist, 4.2, 4.4, 3.6, 3.8, hulk_dark, sides=8)
        m.box_oriented((elb[0] + side * 2.2, elb[1] + 2.0, elb[2]), (fist[0] + side * 1.8, fist[1] + 1.8, fist[2]), 1.3, 1.3, bio_violet, MAT_GLOW)
        m.limb(fist, (fist[0], fist[1] + 3.5, fist[2] - 2.0), 4.4, 4.6, 4.0, 4.2, armor_steel, sides=8, mat=MAT_METAL)
    return m


def _build_mutant_boss_mesh(walk_phase, atk_phase):
    """5. BOSS ĐỘT BIẾN (MUTANT): Giáp sinh học đen, lõi tim & 6 gai lưng ngọc lục bảo phát sáng, tay lưỡi hái xương!"""
    m = _CharMesh()
    chitin_dark = (24, 42, 34)
    chitin_plate = (38, 68, 52)
    toxic_glow = (72, 255, 132)
    toxic_core = (155, 255, 185)
    bone_scythe = (196, 224, 198)

    stride = math.sin(walk_phase) if walk_phase >= 0.0 else 0.2
    bob_z = abs(math.cos(walk_phase)) * 1.5 if walk_phase >= 0.0 else 0.0

    # Chân quái thú khớp ngược (digitigrade) bọc vỏ giáp sinh học
    for side, s_mult in ((-1.0, 1.0), (1.0, -1.0)):
        sw = stride * s_mult
        hip = (side * 5.0, -1.0, 31.5 + bob_z)
        knee = _fk_point(hip, 14.5, sw * 0.45 + 0.32, roll=side * 0.08)
        hock = _fk_point(knee, 10.5, sw * 0.45 - 0.55, roll=side * 0.05)
        foot = (hock[0], hock[1] + 5.8, max(0.2, hock[2] - 6.5))
        m.limb(hip, knee, 4.2, 4.5, 3.0, 3.2, chitin_dark, sides=8, mat=MAT_METAL)
        m.limb(knee, hock, 3.0, 3.2, 2.3, 2.5, chitin_plate, sides=7)
        m.limb(hock, foot, 2.4, 2.6, 2.8, 2.2, chitin_dark, sides=6, mat=MAT_METAL)
        m.spike(foot, (foot[0], foot[1] + 4.5, 0.4), 1.6, 1.2, toxic_glow, mat=MAT_GLOW)

    # Thân giáp sinh học vạm vỡ + Lõi tim sinh học phát quang xanh ngọc lục bảo rực rỡ trước ngực!
    pelvis = (0.0, -1.0, 30.0 + bob_z)
    waist = (0.0, 1.5, 38.0 + bob_z)
    chest = (0.0, 6.0, 53.0 + bob_z)
    m.limb(pelvis, waist, 7.4, 4.8, 6.6, 4.4, chitin_dark, sides=8, mat=MAT_METAL)
    m.limb(waist, chest, 6.8, 4.8, 11.8, 7.2, chitin_plate, sides=10, mat=MAT_METAL)
    # Lõi ngực phát sáng độc lục bảo + xương sườn giáp đen ôm quanh
    m.limb((0.0, 7.2, 41.5 + bob_z), (0.0, 9.6, 50.8 + bob_z), 4.6, 3.8, 5.4, 4.2, toxic_glow, sides=8, mat=MAT_GLOW)
    m.limb((0.0, 8.8, 44.2 + bob_z), (0.0, 10.4, 48.5 + bob_z), 2.6, 2.4, 2.8, 2.6, toxic_core, sides=6, mat=MAT_GLOW)

    # 6 GAI TINH THỂ ĐỘC LỤC BẢO PHÁT SÁNG MỌC TỪ LƯNG VÀ HAI VAI!
    for side in (-1.0, 1.0):
        m.spike((side * 5.2, 2.2, 52.5 + bob_z), (side * 11.5, -5.5, 66.5 + bob_z), 2.4, 2.4, toxic_glow, mat=MAT_GLOW)
        m.spike((side * 3.8, 0.2, 46.5 + bob_z), (side * 8.2, -7.2, 58.0 + bob_z), 1.9, 1.9, toxic_glow, mat=MAT_GLOW)
        m.spike((side * 2.6, -1.2, 40.5 + bob_z), (side * 5.5, -7.8, 49.5 + bob_z), 1.5, 1.5, toxic_glow, mat=MAT_GLOW)

    # Đầu Chúa Tể Đột Biến bo vòm sọ giáp + cặp sừng quặp + 4 con mắt xanh độc + hàm quái thú!
    skull_b = (0.0, 8.8, 54.0 + bob_z)
    skull_m = (0.0, 10.2, 61.2 + bob_z)
    skull_t = (0.0, 9.5, 65.4 + bob_z)
    m.limb(skull_b, skull_m, 4.6, 5.2, 4.8, 5.6, chitin_dark, sides=10, mat=MAT_METAL)
    m.limb(skull_m, skull_t, 4.8, 5.6, 2.2, 2.6, chitin_plate, sides=10, mat=MAT_METAL)
    for side in (-1.0, 1.0):
        m.spike((side * 3.4, 9.8, 61.8 + bob_z), (side * 8.2, 4.2, 70.6 + bob_z), 1.9, 1.9, bone_scythe)
        m.box_oriented((side * 2.0 - 0.6, 15.2, 59.8 + bob_z), (side * 2.0 + 0.6, 15.2, 59.8 + bob_z), 1.3, 1.3, toxic_core, MAT_GLOW)
        m.box_oriented((side * 3.3 - 0.5, 14.5, 61.2 + bob_z), (side * 3.3 + 0.5, 14.5, 61.2 + bob_z), 1.0, 1.0, toxic_glow, MAT_GLOW)
        m.spike((side * 2.2, 13.8, 55.6 + bob_z), (side * 1.2, 16.8, 51.8 + bob_z), 1.1, 1.1, bone_scythe)
    m.limb((0.0, 12.2, 55.2 + bob_z), (0.0, 15.6, 50.8 + bob_z), 3.4, 2.8, 2.2, 1.8, chitin_plate, sides=6)

    # HAI CẲNG TAY BIẾN DỊ THÀNH LƯỠI HÁI SINH HỌC KHỔNG LỒ PHÁT SÁNG!
    slash = atk_phase * 0.95
    for side in (-1.0, 1.0):
        sh = (side * 11.8, 5.5, 51.2 + bob_z)
        elb = _fk_point(sh, 12.5, 0.85 - slash * 0.45 - side * stride * 0.18, roll=side * 0.30)
        wr = _fk_point(elb, 12.0, 1.45 - slash * 0.85, roll=-side * 0.16)
        m.limb(sh, elb, 3.6, 3.8, 2.8, 3.0, chitin_dark, sides=8, mat=MAT_METAL)
        m.limb(elb, wr, 3.0, 3.2, 2.4, 2.6, chitin_plate, sides=7)
        # Lưỡi hái xương dài phát quang xanh độc quặp xuống từ cổ tay!
        scythe_tip = (wr[0] - side * 3.5, wr[1] + 9.5, wr[2] - 10.5)
        m.spike(wr, scythe_tip, 2.6, 1.2, bone_scythe)
        m.box_oriented((wr[0], wr[1] + 1.5, wr[2] - 1.0), scythe_tip, 0.9, 1.8, toxic_glow, MAT_GLOW)
    return m


# ==============================================================================
# BỘ KẾT XUẤT & CACHE TƯ THẾ 3D SIÊU TỐC (KHỬ RĂNG CƯA SUPERSAMPLING)
# ==============================================================================
_CANON_W = 240
_CANON_H = 260
_CANON_DIST = 235.0
_CANON_FOCAL = 620.0  # Chiều cao 70 đơn vị -> ~198 px sắc nét


def _render_base_pose(kind, yaw_step, anim_step, atk_step):
    """Kết xuất mô hình 3D ở độ phân giải gốc 200px cho góc nhìn rel_yaw = yaw_step * 15 độ."""
    key = (kind, yaw_step, anim_step, atk_step)
    cached = _BASE_POSE_CACHE.get(key)
    if cached is not None:
        return cached

    if len(_BASE_POSE_CACHE) > 280:
        _BASE_POSE_CACHE.clear()

    walk_phase = -1.0 if anim_step < 0 else (anim_step / 8.0) * math.tau
    atk_phase = atk_step * 0.5

    if kind == "BOT":
        mesh = _build_tactical_bot_mesh(walk_phase, atk_phase)
    elif kind == "RUNNER":
        mesh = _build_runner_zombie_mesh(walk_phase, atk_phase)
    elif kind == "BRUTE":
        mesh = _build_brute_zombie_mesh(walk_phase, atk_phase)
    elif kind == "MUTANT":
        mesh = _build_mutant_boss_mesh(walk_phase, atk_phase)
    else:
        mesh = _build_walker_zombie_mesh(walk_phase, atk_phase)

    # Góc xoay tương đối: yaw_step = 12 (pi rad) nghĩa là kẻ địch quay thẳng mặt về phía người chơi (+y -> -cam_z)
    theta = (yaw_step / 24.0) * math.tau
    ct, st = math.cos(theta), math.sin(theta)
    cx = _CANON_W * 0.5
    cy = _CANON_H * 0.52
    z_mid = 35.0
    lx, ly, lz = _LIGHT_CAM

    # Biến đổi từ không gian nhân vật (x phải, y trước, z lên) sang Camera (X phải, Y xuống, Z sâu vào màn hình)
    # Khi theta = pi (ct = -1, st = 0):
    #    mặt trước (+y) -> cam_z nhỏ hơn _CANON_DIST (gần người chơi hơn!)
    #    tay phải nhân vật (+x) -> nằm bên trái màn hình người chơi (-cam_x), chuẩn gương đối diện thật!
    cam_verts = []
    proj_verts = []
    for vx, vy, vz in mesh.verts:
        cam_x = vx * ct + vy * st
        cam_z = _CANON_DIST - vx * st + vy * ct
        cam_y = -(vz - z_mid)
        cam_verts.append((cam_x, cam_y, cam_z))
        inv_z = _CANON_FOCAL / max(20.0, cam_z)
        proj_verts.append((int(round(cx + cam_x * inv_z)), int(round(cy + cam_y * inv_z))))

    polys = []
    min_x, min_y = _CANON_W, _CANON_H
    max_x, max_y = 0, 0

    for idx, (nx0, ny0, nz0), col, mat in mesh.faces:
        cnx = nx0 * ct + ny0 * st
        cnz = -nx0 * st + ny0 * ct
        cny = -nz0

        c0 = cam_verts[idx[0]]
        # Loại bỏ mặt khuất phía sau (Backface Culling)
        if cnx * c0[0] + cny * c0[1] + cnz * c0[2] >= 0.0:
            continue

        pts = [proj_verts[i] for i in idx]
        for px_i, py_i in pts:
            if px_i < min_x:
                min_x = px_i
            if px_i > max_x:
                max_x = px_i
            if py_i < min_y:
                min_y = py_i
            if py_i > max_y:
                max_y = py_i

        lam = cnx * lx + cny * ly + cnz * lz
        if lam < 0.0:
            lam = 0.0
        # Ánh sáng viền (Rim Light) giúp tách khối cơ thể 3D nổi bật khỏi nền tối mà không cần viền đen hoạt hình!
        rim = ((1.0 - min(1.0, abs(cnz))) ** 3) * 0.22

        if mat == MAT_GLOW:
            fill_c = _shade_rgb(col, 0.94 + 0.25 * lam + rim)
            edge_c = _shade_rgb(fill_c, 0.88)
        elif mat == MAT_METAL:
            spec = ((-cnz) ** 5 * 0.26) if cnz < 0.0 else 0.0
            fill_c = _shade_rgb(col, 0.40 + 0.72 * lam + rim + spec)
            edge_c = _shade_rgb(fill_c, 0.78)
        else:
            fill_c = _shade_rgb(col, 0.44 + 0.66 * lam + rim)
            edge_c = _shade_rgb(fill_c, 0.82)

        avg_z = sum(cam_verts[i][2] for i in idx) / len(idx)
        polys.append((avg_z, pts, fill_c, edge_c))

    polys.sort(key=lambda item: -item[0])

    foot_sy = cy + z_mid * (_CANON_FOCAL / _CANON_DIST)
    head_sy = cy - (70.0 - z_mid) * (_CANON_FOCAL / _CANON_DIST)
    ref_h = max(16.0, foot_sy - head_sy)

    pad = 4
    bx0 = max(0, min_x - pad)
    by0 = max(0, min_y - pad)
    bx1 = min(_CANON_W, max_x + pad)
    by1 = min(_CANON_H, max_y + pad)

    if bx1 <= bx0 or by1 <= by0 or not polys:
        res = (None, 0.0, 0.0, ref_h)
        _BASE_POSE_CACHE[key] = res
        return res

    surf = pygame.Surface((bx1 - bx0, by1 - by0), pygame.SRCALPHA)
    draw_poly = pygame.draw.polygon
    for _, pts, fill_c, edge_c in polys:
        shifted = [(vx - bx0, vy - by0) for vx, vy in pts]
        draw_poly(surf, fill_c, shifted)
        draw_poly(surf, edge_c, shifted, 1)

    anchor_fx = cx - bx0
    anchor_fy = foot_sy - by0
    res = (surf, anchor_fx, anchor_fy, ref_h)
    _BASE_POSE_CACHE[key] = res
    return res


def _get_scaled_pose_sprite(kind, yaw_step, anim_step, atk_step, target_bh):
    """Lấy Sprite tư thế 3D đã co giãn mượt (khử răng cưa Supersampling) khớp chính xác chiều cao bh."""
    t_bh = int(target_bh)
    if t_bh <= 240:
        q_bh = max(10, ((t_bh + 1) // 3) * 3)
    else:
        q_bh = min(680, ((t_bh + 6) // 12) * 12)
    skey = (kind, yaw_step, anim_step, atk_step, q_bh)
    scached = _SCALED_POSE_CACHE.get(skey)
    if scached is not None:
        return scached

    if len(_SCALED_POSE_CACHE) > 320:
        _SCALED_POSE_CACHE.clear()

    base_surf, afx, afy, ref_h = _render_base_pose(kind, yaw_step, anim_step, atk_step)
    if base_surf is None:
        res = (None, 0, 0)
        _SCALED_POSE_CACHE[skey] = res
        return res

    ratio = q_bh / ref_h
    bw0, bh0 = base_surf.get_size()
    nw = max(4, int(round(bw0 * ratio)))
    nh = max(6, int(round(bh0 * ratio)))
    scaled = pygame.transform.smoothscale(base_surf, (nw, nh))
    res = (scaled, int(round(afx * ratio)), int(round(afy * ratio)))
    _SCALED_POSE_CACHE[skey] = res
    return res


class Enemy:
    def __init__(self, x, y, armor=25, is_zombie=False, zombie_type="WALKER", diff_cfg=None):
        self.x = float(x)
        self.y = float(y)
        self.is_zombie = bool(is_zombie)
        self.zombie_type = zombie_type if is_zombie else None

        hp_mult = diff_cfg["hp_mult"] if diff_cfg else 1.0
        spd_mult = diff_cfg["speed_mult"] if diff_cfg else 1.0
        dmg_mult = diff_cfg["dmg_mult"] if diff_cfg else 1.0
        fire_mult = diff_cfg["bot_fire_mult"] if diff_cfg else 1.0

        if self.is_zombie:
            zcfg = ZOMBIE_TYPES.get(zombie_type, ZOMBIE_TYPES["WALKER"])
            self.scale = zcfg["scale"]
            self.radius = int(17 * min(1.25, self.scale))
            self.max_hp = max(30, int(zcfg["hp"] * hp_mult))
            self.hp = self.max_hp
            self.max_armor = max(0, int(zcfg["armor"] * hp_mult))
            self.armor = self.max_armor
            self.speed = zcfg["speed"] * spd_mult
            self.melee_damage = max(5, int(zcfg["melee_damage"] * dmg_mult))
            self.attack_cooldown = zcfg["attack_cooldown"]
            self.attack_range = zcfg["attack_range"]
            self.reward = zcfg["reward"]
            self.drop_chance = zcfg["drop_chance"]
            self.label = zcfg["label"]
            self.colors = zcfg
            self.fire_delay = 999.0
        else:
            self.scale = 1.0
            self.radius = 17
            self.max_hp = max(50, int(100 * hp_mult))
            self.hp = self.max_hp
            self.max_armor = max(50, int(armor))
            self.armor = armor
            self.speed = 98 * spd_mult
            self.melee_damage = 0
            self.attack_cooldown = 1.0
            self.attack_range = 40
            self.reward = 300
            self.drop_chance = 0.15
            self.label = "ĐẶC NHIỆM"
            self.colors = None
            self.fire_delay = random.uniform(0.45, 0.75) * fire_mult

        # Tỉ lệ cơ thể chuẩn hóa theo dáng đứng / dáng gù giải phẫu của từng loại địch
        self.world_height = 70.0 * self.scale
        if self.is_zombie and self.zombie_type in ("WALKER", "RUNNER"):
            self.head_ratio = 0.28   # Zombie gù đầu thấp hơn nên vùng Headshot mở rộng hợp lý
            self.neck_ratio = 0.02
            self.body_ratio = 0.38
            self.leg_ratio = 0.32
        else:
            self.head_ratio = 0.24
            self.neck_ratio = 0.02
            self.body_ratio = 0.40
            self.leg_ratio = 0.34

        # Hitbox 2D dự phòng
        self.head_radius = int(13 * self.scale)
        self.head_offset_y = int(-32 * self.scale)
        self.body_width = int(30 * self.scale)
        self.body_height = int(55 * self.scale)
        self.body_offset_y = int(10 * self.scale)
        self.leg_width = int(26 * self.scale)
        self.leg_height = int(25 * self.scale)
        self.leg_offset_y = int(48 * self.scale)

        self.angle = random.uniform(0.0, math.tau)
        self.anim_time = random.uniform(0.0, 3.0)
        self.walk_cycle = 0.0
        self.is_moving = False
        self.last_shot = 0.0
        self.last_melee = 0.0
        self.roar_cd = random.uniform(2.0, 7.0)
        self.strafe_dir = random.choice((-1, 1))
        self.strafe_timer = random.uniform(1.0, 2.5)
        self.alive = True
        self.muzzle_flash_timer = 0.0
        self.attack_anim = 0.0

        self.last_hit_part = None
        self.last_hit_damage = 0
        self.last_hit_time = 0

    def update(self, dt):
        self.anim_time += dt
        if self.is_moving:
            rate = 12.8 if (self.is_zombie and self.zombie_type == "RUNNER") else 8.8
            self.walk_cycle = (self.walk_cycle + dt * rate) % math.tau
        else:
            self.walk_cycle = 0.0
        self.is_moving = False

        if self.muzzle_flash_timer > 0:
            self.muzzle_flash_timer = max(0.0, self.muzzle_flash_timer - dt)
        if self.attack_anim > 0:
            self.attack_anim = max(0.0, self.attack_anim - dt * 3.5)

    def check_hit_3d(self, sx, btop, bw, bh, screen_x, screen_y):
        w_mult = 1.18 if (self.is_zombie and self.zombie_type in ("BRUTE", "MUTANT")) else 1.02
        if abs(screen_x - sx) > bw * w_mult:
            return None

        head_end_y = btop + bh * self.head_ratio
        body_end_y = btop + bh * (self.head_ratio + self.neck_ratio + self.body_ratio)
        leg_end_y = btop + bh

        if btop - (bh * 0.08) <= screen_y < head_end_y:
            return "head" if abs(screen_x - sx) <= bw * 0.54 else "body"
        if head_end_y <= screen_y < body_end_y:
            return "body"
        if body_end_y <= screen_y <= leg_end_y + (bh * 0.05):
            return "legs"
        return None

    def damage(self, amount, part="body"):
        self.last_hit_part = part
        self.last_hit_damage = amount
        self.last_hit_time = pygame.time.get_ticks()

        actual_damage = float(amount)
        if self.armor > 0:
            absorbed = min(float(self.armor), actual_damage * 0.5)
            self.armor -= absorbed
            actual_damage -= absorbed

        self.hp -= actual_damage
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return actual_damage

    def move(self, dx, dy, walls):
        r = self.radius
        d = r * 2
        test_x = pygame.Rect(int(self.x + dx - r), int(self.y - r), d, d)
        moved = False
        if test_x.collidelist(walls) == -1:
            self.x += dx
            moved = True

        test_y = pygame.Rect(int(self.x - r), int(self.y + dy - r), d, d)
        if test_y.collidelist(walls) == -1:
            self.y += dy
            moved = True
        return moved

    def move_smart(self, target_angle, speed, dt, walls):
        """Di chuyển thông minh: tự động trượt vòng qua góc tường nếu hướng thẳng bị chặn."""
        step = speed * dt
        if step <= 0.001:
            return False
        ox, oy = self.x, self.y
        self.move(math.cos(target_angle) * step, math.sin(target_angle) * step, walls)
        if math.hypot(self.x - ox, self.y - oy) >= step * 0.45:
            self.is_moving = True
            return True

        s = self.strafe_dir
        for off in (0.62 * s, -0.62 * s, 1.15 * s, -1.15 * s, 1.55 * s, -1.55 * s):
            ang = target_angle + off
            self.move(math.cos(ang) * step * 0.9, math.sin(ang) * step * 0.9, walls)
            if math.hypot(self.x - ox, self.y - oy) >= step * 0.35:
                self.is_moving = True
                return True
        self.strafe_dir = -self.strafe_dir
        return False

    def draw_roblox_3d(self, screen, sx, btop, bw, bh, font_small=None,
                       player=None, renderer=None, horizon=None):
        """Dựng nhân vật 3D giải phẫu chân thực với Cache tư thế khử răng cưa (tương thích hoàn toàn API cũ)."""
        if player is not None:
            dx = self.x - player.x
            dy = self.y - player.y
            dist = math.hypot(dx, dy)
            view_ang = math.atan2(dy, dx)
        else:
            proj_plane = renderer.projection_plane if renderer else 700.0
            dist = max(1.0, proj_plane * self.world_height / max(bh, 1))
            view_ang = self.angle - math.pi

        # 1. Bóng đổ elip hai lớp dưới bàn chân
        foot_x = int(sx)
        foot_y = int(btop + bh)
        w_shadow = int(bw * (1.75 if (self.is_zombie and self.zombie_type in ("BRUTE", "MUTANT")) else 1.48))
        shadow_surf = _get_shadow(w_shadow, max(4, int(bh * 0.12)))
        screen.blit(shadow_surf, (foot_x - shadow_surf.get_width() // 2, foot_y - shadow_surf.get_height() // 2))

        # 2. Xác định chủng loại, hướng xoay 3D tương đối (24 góc = 360 độ) & pha chuyển động
        kind = self.zombie_type if self.is_zombie else "BOT"
        rel_yaw = (self.angle - view_ang) % math.tau
        yaw_step = int(round(rel_yaw / math.tau * 24.0)) % 24

        if self.walk_cycle > 0.001:
            anim_step = int((self.walk_cycle / math.tau) * 8.0) % 8
        else:
            anim_step = -1

        if self.is_zombie:
            atk_step = 2 if self.attack_anim > 0.55 else (1 if self.attack_anim > 0.15 else 0)
        else:
            atk_step = 2 if self.muzzle_flash_timer > 0.05 else (1 if self.muzzle_flash_timer > 0.01 else 0)

        if bh <= 680:
            pose_surf, afx, afy = _get_scaled_pose_sprite(kind, yaw_step, anim_step, atk_step, bh)
            if pose_surf is not None:
                screen.blit(pose_surf, (foot_x - afx, foot_y - afy))
        else:
            # Khi ngắm ống nhòm Sniper 5.0x ở cự ly gần (bh > 680px): chỉ cắt & phóng vùng nằm trong khung hình!
            base_surf, afx, afy, ref_h = _render_base_pose(kind, yaw_step, anim_step, atk_step)
            if base_surf is not None:
                sw, sh = screen.get_size()
                ratio = bh / ref_h
                bw0, bh0 = base_surf.get_size()
                dest_x0 = foot_x - afx * ratio
                dest_y0 = foot_y - afy * ratio
                vis_x0 = max(0, int(dest_x0))
                vis_y0 = max(0, int(dest_y0))
                vis_x1 = min(sw, int(dest_x0 + bw0 * ratio))
                vis_y1 = min(sh, int(dest_y0 + bh0 * ratio))
                if vis_x1 > vis_x0 + 2 and vis_y1 > vis_y0 + 2:
                    sx0 = max(0, min(bw0 - 1, int((vis_x0 - dest_x0) / ratio)))
                    sy0 = max(0, min(bh0 - 1, int((vis_y0 - dest_y0) / ratio)))
                    sx1 = max(sx0 + 1, min(bw0, int(math.ceil((vis_x1 - dest_x0) / ratio))))
                    sy1 = max(sy0 + 1, min(bh0, int(math.ceil((vis_y1 - dest_y0) / ratio))))
                    sub = base_surf.subsurface((sx0, sy0, sx1 - sx0, sy1 - sy0))
                    scaled_sub = pygame.transform.smoothscale(sub, (vis_x1 - vis_x0, vis_y1 - vis_y0))
                    screen.blit(scaled_sub, (vis_x0, vis_y0))

        # 3. Tia lửa đầu nòng 3D rực sáng khi Đặc nhiệm khai hỏa
        if not self.is_zombie and self.muzzle_flash_timer > 0:
            theta = (yaw_step / 24.0) * math.tau
            muz_dx = int((-4.2 * math.cos(theta) + 29.2 * math.sin(theta)) * (bh / 70.0))
            fx = foot_x + muz_dx
            fy = foot_y - int(bh * 0.66)
            fr = max(5, int(bh * 0.11))
            pygame.draw.polygon(screen, (255, 215, 70), [
                (fx - fr, fy), (fx - fr // 3, fy - fr // 3), (fx, fy - fr),
                (fx + fr // 3, fy - fr // 3), (fx + fr, fy),
                (fx + fr // 3, fy + fr // 3), (fx, fy + fr), (fx - fr // 3, fy + fr // 3),
            ])
            pygame.draw.circle(screen, (255, 250, 210), (fx, fy), max(2, fr // 3))

        # 4. Thanh Máu + Giáp + Nhãn chủng loại & Sát thương nổi
        bar_w = max(28, int(bw * (1.55 if self.scale > 1.1 else 1.32)))
        bx = int(sx - bar_w / 2)
        by = int(btop - 16)
        pygame.draw.rect(screen, (14, 17, 22), (bx - 1, by - 1, bar_w + 2, 7), border_radius=2)
        hp_ratio = max(0.0, min(1.0, self.hp / max(1.0, float(self.max_hp))))
        if self.is_zombie:
            hp_color = (115, 235, 75) if hp_ratio > 0.4 else ((245, 165, 35) if hp_ratio > 0.2 else (235, 55, 55))
        else:
            hp_color = (60, 220, 100) if hp_ratio > 0.4 else ((240, 180, 40) if hp_ratio > 0.2 else (235, 60, 60))
        pygame.draw.rect(screen, hp_color, (bx, by, int(bar_w * hp_ratio), 5), border_radius=1)

        if self.armor > 0:
            ar_ratio = min(1.0, self.armor / max(1.0, float(self.max_armor)))
            pygame.draw.rect(screen, (70, 155, 245), (bx, by - 4, int(bar_w * ar_ratio), 3), border_radius=1)

        if font_small:
            now_ms = pygame.time.get_ticks()
            if self.last_hit_time and now_ms - self.last_hit_time < 850:
                p_text = (self.last_hit_part or "body").upper()
                txt_col = (255, 65, 65) if p_text == "HEAD" else ((245, 205, 70) if p_text == "BODY" else (185, 195, 215))
                hit_surf = font_small.render(f"{p_text} -{int(self.last_hit_damage)}", True, txt_col)
                screen.blit(hit_surf, (int(sx - hit_surf.get_width() // 2), by - 22))
            elif self.is_zombie and self.zombie_type != "WALKER" and dist < 850:
                tag_surf = font_small.render(self.label, True, self.colors["eye"])
                screen.blit(tag_surf, (int(sx - tag_surf.get_width() // 2), by - 21))
