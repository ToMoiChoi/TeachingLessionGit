import os
import pygame

# ==============================================================================
# QUẢN LÝ VÀ LIÊN KẾT SKIN SÚNG TỪ ASSETS/SKIN SÚNG
# ==============================================================================

WEAPON_SKIN_FILES = {
    "CLASSIC": "classic.png",
    "GHOST": "ghost.png",
    "SHERIFF": "sheriff.png",
    "MP5": "mp5.png",
    "UMP": "ump.png",
    "M014": "m1014.png",
    "M1014": "m1014.png",
    "MAG-7": "mag-7.png",
    "MAG7": "mag-7.png",
    "AK-47": "vandal.png",
    "AK47": "vandal.png",
    "VANDAL": "vandal.png",
    "M416": "m416.png",
    "PHANTOM": "m416.png",
    "GUARDIAN": "guardian.png",
    "M24": "m24.png",
    "AWM": "awm.png",
}

# Cấu hình kích thước (width) và góc nghiêng (độ) cho từng súng trên tay (Viewmodel)
# Góc âm xoay ngược chiều kim đồng hồ trong Pygame, giúp nòng súng hướng chéo lên tâm ngắm
VIEWMODEL_CONFIGS = {
    "CLASSIC": (380, -20),
    "GHOST": (400, -20),
    "SHERIFF": (390, -20),
    "MP5": (460, -23),
    "UMP": (470, -23),
    "M014": (500, -24),
    "M1014": (500, -24),
    "MAG-7": (480, -24),
    "MAG7": (480, -24),
    "AK-47": (530, -26),
    "AK47": (530, -26),
    "VANDAL": (530, -26),
    "M416": (530, -26),
    "PHANTOM": (530, -26),
    "GUARDIAN": (520, -25),
    "M24": (540, -26),
    "AWM": (550, -26),
}

_raw_skins = {}
_hud_icons = {}
_shop_icons = {}
_viewmodels = {}
_floor_skins = {}
_knife_raw = None
_knife_icon = None
_skin_dir = None


def get_skin_dir():
    global _skin_dir
    if _skin_dir is not None and os.path.isdir(_skin_dir):
        return _skin_dir

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    search_dirs = [
        os.path.join(base_dir, "assets"),
        "assets",
        os.path.join(".", "assets"),
    ]
    for adir in search_dirs:
        if os.path.isdir(adir):
            for sub in os.listdir(adir):
                p = os.path.join(adir, sub)
                if os.path.isdir(p) and "skin" in sub.lower():
                    _skin_dir = p
                    return _skin_dir
            for c in ["skin súng", "skin s\u00fang", "skin sung"]:
                p = os.path.join(adir, c)
                if os.path.isdir(p):
                    _skin_dir = p
                    return _skin_dir

    _skin_dir = os.path.join(base_dir, "assets", "skin súng")
    return _skin_dir


def load_raw_skin(weapon_id):
    if not weapon_id:
        return None
    w_key = str(weapon_id).upper()
    if w_key in _raw_skins and _raw_skins[w_key] is not None:
        return _raw_skins[w_key]

    fn = WEAPON_SKIN_FILES.get(w_key)
    if not fn:
        return None

    path = os.path.join(get_skin_dir(), fn)
    if not os.path.exists(path):
        return None

    try:
        raw_surf = pygame.image.load(path)
        if pygame.display.get_surface() is not None:
            surf = raw_surf.convert_alpha()
        else:
            surf = raw_surf
        _raw_skins[w_key] = surf
        return surf
    except Exception as e:
        print(f"[WeaponSkin] Không thể tải ảnh {path}: {e}")
        return None


def get_hud_icon(weapon_id, max_w=78, max_h=32):
    """Lấy icon hiển thị trong thanh HUD Slot vũ khí (Slot 1, 2, 3)."""
    if not weapon_id:
        return None
    w_key = str(weapon_id).upper()
    if w_key == "KNIFE":
        return get_knife_icon()

    cache_key = (w_key, max_w, max_h)
    if cache_key in _hud_icons:
        return _hud_icons[cache_key]

    raw = load_raw_skin(w_key)
    if raw is None:
        return None

    rw, rh = raw.get_size()
    scale = min(max_w / rw, max_h / rh)
    tw, th = max(1, int(rw * scale)), max(1, int(rh * scale))
    icon = pygame.transform.smoothscale(raw, (tw, th))
    _hud_icons[cache_key] = icon
    return icon


def get_shop_icon(weapon_id, max_w=130, max_h=42):
    """Lấy icon kích thước rõ ràng để hiển thị trong Cửa hàng vũ khí."""
    if not weapon_id:
        return None
    w_key = str(weapon_id).upper()
    if w_key == "KNIFE":
        return get_knife_icon()

    cache_key = (w_key, max_w, max_h)
    if cache_key in _shop_icons:
        return _shop_icons[cache_key]

    raw = load_raw_skin(w_key)
    if raw is None:
        return None

    rw, rh = raw.get_size()
    scale = min(max_w / rw, max_h / rh)
    tw, th = max(1, int(rw * scale)), max(1, int(rh * scale))
    icon = pygame.transform.smoothscale(raw, (tw, th))
    _shop_icons[cache_key] = icon
    return icon


def get_viewmodel_skin(weapon_id):
    """Lấy ảnh skin súng trên tay (Viewmodel) hiển thị góc nhìn thứ nhất với độ lớn và góc nghiêng chuẩn."""
    if not weapon_id:
        return None
    w_key = str(weapon_id).upper()
    if w_key in _viewmodels:
        return _viewmodels[w_key]

    raw = load_raw_skin(w_key)
    if raw is None:
        return None

    cfg = VIEWMODEL_CONFIGS.get(w_key, (560, 7))
    target_w, rot_deg = cfg

    rw, rh = raw.get_size()
    target_h = max(1, int(rh * target_w / rw))
    scaled = pygame.transform.smoothscale(raw, (target_w, target_h))
    if rot_deg != 0:
        scaled = pygame.transform.rotate(scaled, rot_deg)

    _viewmodels[w_key] = scaled
    return scaled


_vm_parts = {}

VM_SCALE = 1.35  # súng to hơn, chiếm nửa dưới-phải màn hình như Valorant
VM_PISTOLS = {"CLASSIC", "GHOST", "SHERIFF"}  # súng lục: nhỏ hơn, ít nghiêng hơn, lệch xuống-phải
VM_ANGLE = -28    # nòng chéo lên-trái về tâm ngắm (âm = cùng chiều kim đồng hồ)


def _taper(img, pivot, near, far, strip=4):
    """Co/giãn chiều cao theo chiều dài súng quanh đường ngắm (y của đầu nòng) để giả phối cảnh."""
    w, h = img.get_size()
    px, py = pivot
    pad = int(h * (max(near, far) - 1) + 4)
    out = pygame.Surface((w, h + 2 * pad), pygame.SRCALPHA)
    for x in range(0, w, strip):
        sw = min(strip, w - x)
        f = near + (far - near) * (x / max(1, w - 1))
        col = img.subsurface((x, 0, sw, h))
        nh = max(1, int(h * f))
        col = pygame.transform.scale(col, (sw, nh))
        out.blit(col, (x, pad + py - py * f))
    return out, (px, py + pad)


def get_viewmodel_parts(weapon_id):
    """Trả về (ảnh chưa xoay đã tối màu, tọa độ đầu nòng trong ảnh, góc hếch nòng độ) để xoay quanh đầu nòng."""
    if not weapon_id:
        return None
    w_key = str(weapon_id).upper()
    if w_key in _vm_parts:
        return _vm_parts[w_key]

    raw = load_raw_skin(w_key)
    if raw is None:
        return None

    target_w, rot_deg = VIEWMODEL_CONFIGS.get(w_key, (520, -14))
    is_pistol = w_key in VM_PISTOLS
    target_w = int(target_w * (0.95 if is_pistol else VM_SCALE))
    rw, rh = raw.get_size()
    scale = target_w / rw
    img = pygame.transform.smoothscale(raw, (target_w, max(1, int(rh * scale))))

    # Đầu nòng = cột pixel đục nằm ngoài cùng bên trái, lấy trung bình chiều cao của vài cột đầu
    mask = pygame.mask.from_surface(img, 40)
    mw, mh = mask.get_size()
    pts = []
    for x in range(mw):
        ys = [y for y in range(mh) if mask.get_at((x, y))]
        if ys:
            pts.extend((x, y) for y in ys)
            if x - pts[0][0] >= 3:
                break
    if pts:
        pivot = (min(p[0] for p in pts), sum(p[1] for p in pts) / len(pts))
    else:
        pivot = (0, mh / 2)

    # Bóp phối cảnh góc nhìn từ sau: đầu nòng (xa) nhỏ, báng (gần camera) to
    img, pivot = _taper(img, pivot, 0.85, 1.15 if is_pistol else 1.3)

    # Tối bớt cho khớp ánh sáng map
    img.fill((185, 185, 195, 255), special_flags=pygame.BLEND_RGBA_MULT)

    # Góc cấu hình cũ là độ xoay pygame (âm = cùng chiều kim đồng hồ); nòng chỉ hếch nhẹ ~5°
    angle = 0  # nòng song song hướng nhìn, không chụm vào tâm
    anchor = (0.58, 0.68) if is_pistol else (0.46, 0.64)
    _vm_parts[w_key] = (img, pivot, angle, anchor)
    return _vm_parts[w_key]


def get_dropped_skin(weapon_id, width, height):
    """Lấy ảnh skin rơi trên sàn ở chế độ 3D."""
    if not weapon_id or width <= 0 or height <= 0:
        return None
    w_key = str(weapon_id).upper()
    cache_key = (w_key, width, height)
    if cache_key in _floor_skins:
        return _floor_skins[cache_key]

    raw = load_raw_skin(w_key)
    if raw is None:
        return None

    scaled = pygame.transform.smoothscale(raw, (width, height))
    _floor_skins[cache_key] = scaled
    return scaled


# ==============================================================================
# TẠO SPRITE DAO CẬN CHIẾN (KNIFE)
# ==============================================================================

def build_knife_sprite():
    global _knife_raw
    if _knife_raw is not None:
        return _knife_raw

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "assets", "knife.png")
    if os.path.exists(path):
        try:
            img = pygame.image.load(path)
            if pygame.display.get_surface() is not None:
                img = img.convert_alpha()
            _knife_raw = img.subsurface(img.get_bounding_rect()).copy()
            return _knife_raw
        except pygame.error:
            pass

    S = pygame.Surface((800, 340), pygame.SRCALPHA)
    silver = (200, 204, 212)
    silver_hi = (240, 243, 248)
    black = (24, 24, 28)
    grip = (40, 40, 46)
    guard_col = (150, 153, 162)

    pygame.draw.polygon(S, silver, [
        (50, 140), (130, 116), (250, 104), (450, 98),
        (462, 186), (330, 192), (200, 180), (110, 160)
    ])
    pygame.draw.polygon(S, black, [
        (125, 130), (250, 108), (450, 102), (455, 158),
        (330, 164), (190, 150)
    ])
    for i in range(6):
        x = 255 + i * 22
        pygame.draw.polygon(S, silver, [(x, 104), (x + 9, 92), (x + 20, 104)])

    pygame.draw.lines(S, silver_hi, False, [
        (50, 140), (110, 160), (200, 180), (330, 192), (462, 186)
    ], 3)
    pygame.draw.lines(S, silver_hi, False, [(50, 140), (130, 116), (250, 104)], 2)
    pygame.draw.polygon(S, guard_col, [(445, 96), (500, 88), (500, 180), (462, 188)])

    handle = [
        (490, 86), (742, 110), (752, 122), (722, 208), (690, 188),
        (662, 172), (632, 188), (606, 166), (578, 180), (548, 160), (500, 156)
    ]
    pygame.draw.polygon(S, grip, handle)

    mask = pygame.Surface((800, 340), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255), handle)
    tex = pygame.Surface((800, 340), pygame.SRCALPHA)
    for k in range(-400, 800, 14):
        pygame.draw.line(tex, (76, 76, 86), (k, 60), (k + 120, 240), 1)
        pygame.draw.line(tex, (76, 76, 86), (k + 120, 60), (k, 240), 1)
    tex.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    S.blit(tex, (0, 0))

    pygame.draw.polygon(S, silver, handle, 3)
    for cx, cy in ((487, 125), (695, 135)):
        pygame.draw.circle(S, silver, (cx, cy), 9)
        pygame.draw.circle(S, black, (cx, cy), 4)
    pygame.draw.rect(S, silver, (736, 102, 20, 22), 3, border_radius=4)

    _knife_raw = S.subsurface(S.get_bounding_rect()).copy()
    return _knife_raw


def knife_scaled(width):
    raw = build_knife_sprite()
    height = max(1, int(raw.get_height() * width / raw.get_width()))
    return pygame.transform.smoothscale(raw, (width, height))


def get_knife_icon():
    global _knife_icon
    if _knife_icon is None:
        _knife_icon = knife_scaled(68)
    return _knife_icon
