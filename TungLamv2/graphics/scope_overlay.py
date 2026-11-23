"""graphics/scope_overlay.py - Hệ thống Kính ngắm Scope & Holographic ADS 4 phân khúc chuẩn Valorant / PUBG.

- SNIPER (AWM, M24): Ống ngắm bắn tỉa Mil-Dot 2.5x / 5.0x viền kim loại theo skin (Ngọc Bích Hoàng Kim / Lông Quạ Đêm).
- ACOG (GUARDIAN): Ống ngắm chiến thuật 2.0x xuyên thấu gắn trực tiếp trên thân súng, tâm Chevron + thước đo cự ly BDC.
- HOLO (VANDAL, AK-47, M416, PHANTOM, MP5, UMP): Kính ngắm phản xạ Holographic khung vòm gắn trên ray súng, mặt kính trong suốt không che tầm nhìn, màu viền & tâm laser đồng bộ từng skin.
- REFLEX (CLASSIC, GHOST, SHERIFF, M014, MAG-7): Kính ngắm điểm đỏ RMR gọn nhẹ gắn trên thước ngắm.

Tất cả khung kính được tạo sẵn 1 lần trong _SCOPE_CACHE (SRCALPHA) -> chỉ tốn 1 lệnh blit (~0.04 ms/frame), giữ vững 60-120+ FPS.
"""
import pygame

_SCOPE_CACHE = {}
_ZOOM_TEXT_CACHE = {}

# Cấu hình phong cách & bảng màu đồng bộ từng skin súng:
# (kind, frame_outer, frame_accent, reticle_color, glass_rgba)
OPTIC_THEMES = {
    # Sniper 2.5x / 5.0x
    "AWM": ("SNIPER", (226, 186, 84), (42, 198, 152), (72, 255, 168), (24, 110, 95, 26)),
    "M24": ("SNIPER", (74, 82, 104), (218, 180, 86), (255, 68, 68), (36, 58, 108, 24)),
    # DMR 2.0x ACOG
    "GUARDIAN": ("ACOG", (56, 56, 66), (222, 84, 246), (250, 95, 255), (85, 35, 105, 18)),
    # Rifles & SMGs Holographic 1.3x - 1.6x
    "VANDAL": ("HOLO", (34, 38, 46), (152, 224, 62), (175, 255, 75), (45, 85, 35, 16)),
    "AK-47": ("HOLO", (38, 42, 48), (156, 68, 38), (255, 62, 58), (40, 55, 65, 16)),
    "AK47": ("HOLO", (38, 42, 48), (156, 68, 38), (255, 62, 58), (40, 55, 65, 16)),
    "M416": ("HOLO", (44, 44, 52), (162, 138, 112), (255, 92, 34), (75, 35, 25, 16)),
    "PHANTOM": ("HOLO", (38, 46, 58), (64, 218, 255), (80, 235, 255), (25, 75, 98, 18)),
    "MP5": ("HOLO", (212, 182, 126), (88, 232, 132), (95, 255, 145), (30, 88, 55, 16)),
    "UMP": ("HOLO", (38, 34, 48), (218, 152, 72), (218, 112, 255), (65, 35, 88, 16)),
    # Pistols & Shotguns Micro-Reflex 1.15x - 1.2x
    "CLASSIC": ("REFLEX", (40, 42, 52), (236, 190, 56), (146, 220, 255), (35, 65, 95, 14)),
    "GHOST": ("REFLEX", (34, 38, 46), (182, 194, 212), (135, 235, 255), (40, 65, 85, 14)),
    "SHERIFF": ("REFLEX", (48, 46, 46), (196, 168, 96), (255, 72, 62), (65, 50, 38, 12)),
    "M014": ("REFLEX", (156, 166, 184), (238, 42, 58), (255, 64, 78), (85, 24, 34, 14)),
    "M1014": ("REFLEX", (156, 166, 184), (238, 42, 58), (255, 64, 78), (85, 24, 34, 14)),
    "MAG-7": ("REFLEX", (58, 54, 74), (255, 186, 42), (255, 205, 52), (85, 52, 20, 14)),
    "MAG7": ("REFLEX", (58, 54, 74), (255, 186, 42), (255, 205, 52), (85, 52, 20, 14)),
}


def _build_sniper_frame(w, h, outer_c, accent_c, ret_c, glass_rgba):
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2
    r = int(min(w, h) * 0.43)

    # Màn tối bao quanh ống nhòm bắn tỉa
    surf.fill((6, 8, 12, 238))
    pygame.draw.circle(surf, (0, 0, 0, 0), (cx, cy), r)

    # Ánh phản quang nhẹ sát rìa thấu kính (tâm kính trong suốt 100%)
    for k in range(16):
        alpha = max(0, glass_rgba[3] + (16 - k) * 3)
        pygame.draw.circle(surf, (glass_rgba[0], glass_rgba[1], glass_rgba[2], alpha), (cx, cy), r - k, 1)

    # Núm vặn chỉnh tiêu cự trên đỉnh & bên phải ống ngắm
    tur_w, tur_h = max(28, r // 5), max(14, r // 14)
    pygame.draw.rect(surf, (24, 28, 34, 255), (cx - tur_w // 2, cy - r - tur_h - 4, tur_w, tur_h + 6), border_radius=4)
    pygame.draw.rect(surf, outer_c + (255,), (cx - tur_w // 2, cy - r - tur_h - 4, tur_w, 4), border_radius=2)
    pygame.draw.rect(surf, (24, 28, 34, 255), (cx + r - 2, cy - tur_w // 2, tur_h + 6, tur_w), border_radius=4)
    pygame.draw.rect(surf, outer_c + (255,), (cx + r + tur_h, cy - tur_w // 2, 4, tur_w), border_radius=2)

    # Vành kim loại kép theo skin (Vàng Ngọc Bích cho AWM / Xám Đêm Lông Quạ cho M24)
    pygame.draw.circle(surf, (18, 20, 26, 255), (cx, cy), r + 8, 10)
    pygame.draw.circle(surf, outer_c + (255,), (cx, cy), r + 3, 4)
    pygame.draw.circle(surf, accent_c + (235,), (cx, cy), r - 2, 2)

    # Lưới tâm Mil-Dot sắc mảnh chuẩn bắn tỉa
    line_dark = (14, 18, 22, 230)
    gap = max(14, r // 16)
    post = int(r * 0.52)
    # 4 thanh dày ngoài rìa
    pygame.draw.line(surf, line_dark, (cx - r, cy), (cx - post, cy), 5)
    pygame.draw.line(surf, line_dark, (cx + post, cy), (cx + r, cy), 5)
    pygame.draw.line(surf, line_dark, (cx, cy + post), (cx, cy + r), 5)
    pygame.draw.line(surf, line_dark, (cx, cy - r), (cx, cy - post), 3)
    # Dây tóc mảnh vào sát tâm
    pygame.draw.line(surf, line_dark, (cx - post, cy), (cx - gap, cy), 1)
    pygame.draw.line(surf, line_dark, (cx + gap, cy), (cx + post, cy), 1)
    pygame.draw.line(surf, line_dark, (cx, cy - post), (cx, cy - gap), 1)
    pygame.draw.line(surf, line_dark, (cx, cy + gap), (cx, cy + post), 1)

    # Vạch chia Mil-Dot dọc & ngang
    step = max(16, (post - gap) // 5)
    for idx in range(1, 6):
        d = gap + idx * step
        th = 6 if idx % 2 == 0 else 3
        for sgn in (-1, 1):
            pygame.draw.line(surf, line_dark, (cx + sgn * d, cy - th), (cx + sgn * d, cy + th), 1)
        pygame.draw.line(surf, line_dark, (cx - th, cy + d), (cx + th, cy + d), 1)
        if idx <= 3:
            w_drop = th + idx * 3
            pygame.draw.line(surf, (*ret_c, 155), (cx - w_drop, cy + d), (cx + w_drop, cy + d), 1)

    # Thước đo khoảng cách mục tiêu góc trái dưới thấu kính
    rx0, ry0 = cx - int(r * 0.56), cy + int(r * 0.44)
    pygame.draw.line(surf, (*ret_c, 165), (rx0, ry0), (rx0 + int(r * 0.28), ry0), 1)
    for k in range(1, 5):
        kx = rx0 + k * int(r * 0.065)
        kh = int(r * (0.16 / (k * 0.75)))
        pygame.draw.line(surf, (*ret_c, 155), (kx, ry0), (kx, ry0 - kh), 1)
    return surf


def _build_acog_frame(w, h, outer_c, accent_c, ret_c, glass_rgba):
    """Ống ngắm ACOG 2.0x xuyên thấu (nhìn thấy cả thế giới xung quanh & khẩu Guardian bên dưới)."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2
    r = int(h * 0.175)

    # Làm dịu nhẹ vùng rìa màn hình để nổi bật thấu kính trung tâm
    surf.fill((8, 10, 16, 48))
    pygame.draw.circle(surf, glass_rgba, (cx, cy), r)

    # Chân ngàm kẹp trực tiếp xuống ray trên của khẩu súng 3D ở (cx, cy + r)
    clamp_w = int(r * 0.72)
    clamp_h = int(h * 0.048)
    pygame.draw.polygon(surf, (26, 28, 34, 248), [
        (cx - clamp_w // 2, cy + r + 4),
        (cx + clamp_w // 2, cy + r + 4),
        (cx + int(clamp_w * 0.65), cy + r + clamp_h),
        (cx - int(clamp_w * 0.65), cy + r + clamp_h),
    ])
    pygame.draw.line(surf, (*accent_c, 220), (cx - clamp_w // 2, cy + r + 8), (cx + clamp_w // 2, cy + r + 8), 2)

    # Thanh sợi quang thu sáng trên đỉnh ống ACOG + núm chỉnh bên phải
    fib_w = int(r * 0.46)
    pygame.draw.rect(surf, outer_c + (248,), (cx - fib_w // 2, cy - r - 15, fib_w, 12), border_radius=3)
    pygame.draw.rect(surf, (*accent_c, 245), (cx - fib_w // 2 + 5, cy - r - 12, fib_w - 10, 5), border_radius=2)
    pygame.draw.rect(surf, outer_c + (248,), (cx + r + 2, cy - 14, 11, 28), border_radius=3)

    # Vành ống ACOG dày sắc khối 3D
    pygame.draw.circle(surf, (20, 22, 28, 250), (cx, cy), r + 9, 12)
    pygame.draw.circle(surf, outer_c + (252,), (cx, cy), r + 4, 5)
    pygame.draw.circle(surf, (*accent_c, 215), (cx, cy), r - 1, 2)

    # Dây tóc ngang & thước đo đạn rơi BDC bên trong kính ACOG
    pygame.draw.line(surf, (18, 20, 26, 195), (cx - r + 8, cy), (cx - 22, cy), 2)
    pygame.draw.line(surf, (18, 20, 26, 195), (cx + 22, cy), (cx + r - 8, cy), 2)
    pygame.draw.line(surf, (18, 20, 26, 195), (cx, cy + 20), (cx, cy + r - 8), 2)
    for k in range(1, 4):
        dy = 22 + k * int(r * 0.18)
        tw = max(4, 12 - k * 2)
        pygame.draw.line(surf, (*ret_c, 190), (cx - tw, cy + dy), (cx + tw, cy + dy), 2)
    return surf


def _build_holo_frame(w, h, outer_c, accent_c, ret_c, glass_rgba):
    """Kính ngắm phản xạ Holographic / Red-Dot (Valorant / EOTech) gắn khít trên lưng súng trường & SMG."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2
    hw = int(h * 0.155)
    hh = int(h * 0.105)

    # Làm dịu nhẹ vùng rìa ngoài để khung kính Holographic nổi bật rõ ràng ngay khi bật ngắm
    surf.fill((6, 8, 14, 54))
    win_rect = pygame.Rect(cx - hw, cy - hh, hw * 2, hh * 2)
    pygame.draw.rect(surf, (0, 0, 0, 0), win_rect, border_radius=14)
    pygame.draw.rect(surf, glass_rgba, win_rect, border_radius=14)

    # Đế ngàm Picatinny nối liền khung kính xuống lưng súng 3D phía dưới
    base_w = int(hw * 1.55)
    base_h = int(h * 0.040)
    base_rect = pygame.Rect(cx - base_w // 2, cy + hh + 2, base_w, base_h)
    pygame.draw.rect(surf, (20, 23, 30, 250), base_rect, border_radius=4)
    pygame.draw.rect(surf, outer_c + (250,), base_rect, 2, border_radius=4)
    pygame.draw.line(surf, (*accent_c, 240), (cx - hw // 2, base_rect.centery), (cx + hw // 2, base_rect.centery), 3)

    # Vòm bảo vệ Holographic 3D dày dặn có tai vát hai bên & viền phát sáng rõ nét
    hood_outer = win_rect.inflate(22, 18)
    pygame.draw.rect(surf, (18, 21, 28, 250), hood_outer, 12, border_radius=18)
    pygame.draw.rect(surf, outer_c + (252,), win_rect.inflate(12, 10), 5, border_radius=16)
    pygame.draw.rect(surf, (*accent_c, 240), win_rect.inflate(2, 2), 2, border_radius=14)

    # 2 tai bảo vệ bên hông + nút nguồn laser trên đỉnh kính
    ear_h = int(hh * 0.78)
    pygame.draw.rect(surf, (*accent_c, 245), (hood_outer.left - 4, cy - ear_h // 2, 5, ear_h), border_radius=2)
    pygame.draw.rect(surf, (*accent_c, 245), (hood_outer.right - 1, cy - ear_h // 2, 5, ear_h), border_radius=2)
    top_w = int(hw * 0.55)
    pygame.draw.rect(surf, (22, 26, 34, 250), (cx - top_w // 2, hood_outer.top - 7, top_w, 8), border_radius=3)
    pygame.draw.line(surf, (*accent_c, 240), (cx - top_w // 3, hood_outer.top - 3), (cx + top_w // 3, hood_outer.top - 3), 2)
    return surf


def _build_reflex_mini_frame(w, h, outer_c, accent_c, ret_c, glass_rgba):
    """Kính ngắm điểm đỏ RMR Micro-Reflex chữ U thoáng rộng cho Súng lục & Shotgun."""
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx, cy = w // 2, h // 2
    hw = int(h * 0.100)
    hh = int(h * 0.068)

    surf.fill((6, 8, 14, 38))
    win_rect = pygame.Rect(cx - hw, cy - hh, hw * 2, hh * 2)
    pygame.draw.rect(surf, (0, 0, 0, 0), win_rect, border_radius=10)
    pygame.draw.rect(surf, glass_rgba, win_rect, border_radius=10)

    # Khung chữ U RMR rõ nét (mở thoáng cạnh trên, 2 trụ hai bên + viền vòm mảnh + đế gắn lên slide)
    pygame.draw.rect(surf, (*accent_c, 165), win_rect.inflate(4, 4), 2, border_radius=11)
    pillar_w = 9
    pygame.draw.rect(surf, (20, 23, 30, 248), (cx - hw - pillar_w, cy - hh, pillar_w, hh * 2 + 8), border_radius=3)
    pygame.draw.rect(surf, (20, 23, 30, 248), (cx + hw, cy - hh, pillar_w, hh * 2 + 8), border_radius=3)
    pygame.draw.rect(surf, (*accent_c, 235), (cx - hw - pillar_w + 2, cy - hh + 4, 3, hh * 2 - 4), border_radius=2)
    pygame.draw.rect(surf, (*accent_c, 235), (cx + hw + 4, cy - hh + 4, 3, hh * 2 - 4), border_radius=2)

    # Đế gắn RMR dưới chân kính
    base_rect = pygame.Rect(cx - hw - 6, cy + hh + 2, (hw + 6) * 2, int(h * 0.028))
    pygame.draw.rect(surf, (18, 20, 26, 248), base_rect, border_radius=3)
    pygame.draw.line(surf, (*accent_c, 240), (cx - hw // 2, base_rect.centery), (cx + hw // 2, base_rect.centery), 2)
    return surf


def get_scope_frame(weapon_id, w, h):
    w_key = str(weapon_id).upper()
    ckey = (w_key, w, h)
    cached = _SCOPE_CACHE.get(ckey)
    if cached is not None:
        return cached

    if len(_SCOPE_CACHE) > 32:
        _SCOPE_CACHE.clear()

    kind, outer_c, accent_c, ret_c, glass_rgba = OPTIC_THEMES.get(
        w_key, ("HOLO", (40, 44, 54), (90, 210, 255), (255, 70, 70), (35, 65, 85, 16))
    )
    if kind == "SNIPER":
        surf = _build_sniper_frame(w, h, outer_c, accent_c, ret_c, glass_rgba)
    elif kind == "ACOG":
        surf = _build_acog_frame(w, h, outer_c, accent_c, ret_c, glass_rgba)
    elif kind == "REFLEX":
        surf = _build_reflex_mini_frame(w, h, outer_c, accent_c, ret_c, glass_rgba)
    else:
        surf = _build_holo_frame(w, h, outer_c, accent_c, ret_c, glass_rgba)

    res = (surf, kind, accent_c, ret_c)
    _SCOPE_CACHE[ckey] = res
    return res


def draw_weapon_scope(screen, weapon_id, zoom, ads_progress=1.0, recoil=0.0, font_zoom=None):
    """Vẽ khung kính ngắm + tâm laser động phản hồi độ giật cho mọi loại súng."""
    w, h = screen.get_size()
    surf, kind, accent_c, ret_c = get_scope_frame(weapon_id, w, h)

    # Hiệu ứng nâng kính mượt khi vừa bấm ngắm (ads 0.50 -> 1.0)
    t = max(0.0, min(1.0, (ads_progress - 0.45) / 0.50))
    rise_y = int((1.0 - t) * h * 0.06) if kind != "SNIPER" else 0
    screen.blit(surf, (0, rise_y))

    cx = w // 2
    # Tâm laser dịch nhẹ theo độ giật thực tế giống Valorant ADS
    cy = h // 2 + rise_y - int(recoil * 38.0)

    if kind == "SNIPER":
        # Mũi tên Chevron mảnh + chấm laser sáng ở chính tâm ống ngắm tỉa
        pygame.draw.circle(screen, (20, 20, 24), (cx, cy), 4, 1)
        pygame.draw.circle(screen, ret_c, (cx, cy), 2)
    elif kind == "ACOG":
        # Tâm Chevron (^) chiến thuật 2.0x phát sáng rõ nét
        pygame.draw.lines(screen, (20, 12, 24), False, [(cx - 8, cy + 7), (cx, cy - 1), (cx + 8, cy + 7)], 4)
        pygame.draw.lines(screen, ret_c, False, [(cx - 7, cy + 6), (cx, cy - 1), (cx + 7, cy + 6)], 2)
        pygame.draw.circle(screen, (255, 255, 255), (cx, cy - 1), 1)
    elif kind == "HOLO":
        # Tâm Holographic EOTech / Valorant: vòng tròn đứt nét 4 góc + chấm laser 2px chính giữa
        r_ring = max(14, int(h * 0.024) + int(recoil * 45.0))
        pygame.draw.circle(screen, ret_c, (cx, cy), r_ring, 1)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            pygame.draw.line(
                screen, ret_c,
                (cx + dx * (r_ring - 3), cy + dy * (r_ring - 3)),
                (cx + dx * (r_ring + 4), cy + dy * (r_ring + 4)),
                2,
            )
        pygame.draw.circle(screen, (25, 10, 10), (cx, cy), 3)
        pygame.draw.circle(screen, (255, 72, 68) if ret_c[0] < 180 else ret_c, (cx, cy), 2)
    else:
        # Tâm Micro-Reflex gọn thoáng cho Pistol & Shotgun
        gap = max(8, int(h * 0.014) + int(recoil * 35.0))
        pygame.draw.line(screen, ret_c, (cx - gap - 6, cy), (cx - gap, cy), 2)
        pygame.draw.line(screen, ret_c, (cx + gap, cy), (cx + gap + 6, cy), 2)
        pygame.draw.circle(screen, (20, 20, 24), (cx, cy), 3)
        pygame.draw.circle(screen, ret_c, (cx, cy), 2)

    # Hiển thị độ phóng đại (1.3x / 1.5x / 2.0x / 2.5x / 5.0x) ngay cạnh khung kính ngắm
    if font_zoom is not None:
        z_txt = f"SCOPE {zoom:.2g}x"
        tkey = (id(font_zoom), z_txt, accent_c)
        z_img = _ZOOM_TEXT_CACHE.get(tkey)
        if z_img is None:
            if len(_ZOOM_TEXT_CACHE) > 64:
                _ZOOM_TEXT_CACHE.clear()
            z_img = font_zoom.render(z_txt, True, accent_c)
            _ZOOM_TEXT_CACHE[tkey] = z_img
        if kind == "SNIPER":
            zx, zy = cx + int(min(w, h) * 0.24), h // 2 + int(min(w, h) * 0.26)
        elif kind == "ACOG":
            zx, zy = cx + int(h * 0.19), cy + int(h * 0.13)
        else:
            zx, zy = cx + int(h * 0.165), cy + int(h * 0.075)
        bg_r = z_img.get_rect(topleft=(zx, zy)).inflate(10, 4)
        pygame.draw.rect(screen, (14, 18, 24), bg_r, border_radius=4)
        pygame.draw.rect(screen, accent_c, bg_r, 1, border_radius=4)
        screen.blit(z_img, (zx, zy))
