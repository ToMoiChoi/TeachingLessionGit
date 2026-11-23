import asyncio
import math
import os
import random
import sys
import pygame
import sound

from settings import WIDTH, HEIGHT, FPS, ROUND_TIME, BUY_TIME, FOV
from font_vn import get_font
from game.data import (
    GAME_MODES,
    MODE_BY_ID,
    DIFFICULTIES,
    DIFF_BY_ID,
    SUPPLY_TYPES,
    pick_zombie_type,
    pick_supply_kind,
    load_profile,
    save_profile,
)
from game.player import Player
from game.enemy import Enemy
from game.map import (
    MAPS,
    MAP_ORDER,
    walls,
    line_blocked,
    set_active_map,
    get_active_map,
    get_active_map_id,
    find_clear_point,
)
from game.weapon import get_weapon, get_weapon_damage
from graphics.renderer import Renderer
from graphics.minimap import Minimap
from graphics.weapon_skins import get_hud_icon, get_shop_icon
from graphics.scope_overlay import draw_weapon_scope
from ui.hud import HUD
from ui.game_view import GameView

IS_WEB = sys.platform == "emscripten"

# KHỞI TẠO
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Lotus Tactical FPS - Zombie & Multi-Map Edition")
clock = pygame.time.Clock()

SCREENSHOT_DIR = "screenshots"
if not IS_WEB:
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def save_screenshot(tag="manual"):
    if IS_WEB:
        return
    try:
        filename = os.path.join(SCREENSHOT_DIR, f"{tag}_{pygame.time.get_ticks()}.png")
        pygame.image.save(screen, filename)
    except Exception as e:
        print(f"[Screenshot] Error: {e}")


_WEB_LOCK_JS = """
window._fpsLock = window._fpsLock || (function() {
  var st = { want: false, dx: 0, dy: 0, locked: false };
  function getCanvas() { return document.getElementById('canvas') || document.querySelector('canvas'); }
  function tryLock() {
    if (!st.want) return;
    var c = getCanvas();
    if (!c || document.pointerLockElement === c) return;
    try {
      var p = c.requestPointerLock ? c.requestPointerLock() : null;
      if (p && typeof p.catch === 'function') p.catch(function(){});
    } catch (e) {}
  }
  document.addEventListener('pointerlockchange', function() {
    var c = getCanvas();
    st.locked = !!(c && document.pointerLockElement === c);
    st.dx = 0; st.dy = 0;
  });
  document.addEventListener('mousemove', function(e) {
    if (!st.want) return;
    if (st.locked) {
      st.dx += (e.movementX || 0);
      st.dy += (e.movementY || 0);
    }
  }, true);
  document.addEventListener('mousedown', function() {
    if (st.want) tryLock();
  }, true);
  window.addEventListener('contextmenu', function(e) {
    e.preventDefault();
  }, true);
  return {
    setWant: function(w) {
      st.want = !!w;
      st.dx = 0; st.dy = 0;
      if (st.want) { tryLock(); }
      else if (document.pointerLockElement && document.exitPointerLock) {
        try { document.exitPointerLock(); } catch (e) {}
      }
    },
    consume: function() {
      var r = st.dx + ',' + st.dy + ',' + (st.locked ? '1' : '0');
      st.dx = 0; st.dy = 0;
      return r;
    }
  };
})();
"""
_web_lock_ready = False
_web_pointer_locked = False


def _ensure_web_lock():
    global _web_lock_ready
    if IS_WEB and not _web_lock_ready:
        try:
            from platform import window
            window.eval(_WEB_LOCK_JS)
            _web_lock_ready = True
        except Exception:
            pass


def set_mouse_mode(gui):
    try:
        pygame.mouse.set_visible(gui)
        if IS_WEB:
            _ensure_web_lock()
            if _web_lock_ready:
                from platform import window
                window._fpsLock.setWant(not gui)
        else:
            pygame.event.set_grab(not gui)
        pygame.mouse.get_rel()
    except Exception:
        pass


def consume_look_delta(dt):
    """Đọc chuyển động chuột 360 độ không giới hạn cho cả Desktop và Web (kèm xoay tự động sát mép màn hình)."""
    global _web_pointer_locked
    rel_dx, rel_dy = pygame.mouse.get_rel()
    if not IS_WEB:
        return rel_dx, rel_dy

    _ensure_web_lock()
    if _web_lock_ready:
        try:
            from platform import window
            raw = str(window._fpsLock.consume())
            parts = raw.split(",")
            jdx, jdy, locked = float(parts[0]), float(parts[1]), parts[2] == "1"
            _web_pointer_locked = locked
            if locked:
                return jdx, jdy
        except Exception:
            pass

    # Dự phòng khi trình duyệt chưa khóa chuột (hoặc vừa bấm ESC): đưa chuột sát mép trái/phải vẫn xoay tiếp 360° mượt!
    if pygame.mouse.get_focused():
        mx, _my = pygame.mouse.get_pos()
        edge = 48
        if mx < edge:
            rel_dx -= (1.0 - mx / float(edge)) * 680.0 * dt
        elif mx > WIDTH - edge:
            rel_dx += (1.0 - (WIDTH - mx) / float(edge)) * 680.0 * dt
    return rel_dx, rel_dy


# HỒ SƠ LƯU TRỮ & CẤU HÌNH TRẬN ĐẤU
profile = load_profile()
selected_mode_id = profile.get("last_mode", "HYBRID")
if selected_mode_id not in MODE_BY_ID:
    selected_mode_id = "HYBRID"

selected_diff_id = profile.get("last_diff", "NORMAL")
if selected_diff_id not in DIFF_BY_ID:
    selected_diff_id = "NORMAL"

initial_map = profile.get("last_map", "lotus")
if initial_map not in MAPS:
    initial_map = "lotus"
set_active_map(initial_map)

player = Player()
renderer = Renderer()
minimap = Minimap()
hud = HUD()
game_view = GameView(screen, WIDTH, HEIGHT)

# VŨ KHÍ & TRANG BỊ
SIDEARMS = ["CLASSIC", "GHOST", "SHERIFF"]
PRIMARY_WEAPONS = [
    "AK-47", "VANDAL", "M416", "PHANTOM", "GUARDIAN",
    "MP5", "UMP", "M014", "MAG-7", "M24", "AWM",
]
GUNS = tuple(SIDEARMS + PRIMARY_WEAPONS)
AUTO_GUNS = ("AK-47", "VANDAL", "M416", "PHANTOM", "MP5", "UMP", "MAG-7")

WEAPON_NAMES = {
    "KNIFE": "Dao cận chiến",
    "CLASSIC": "Classic",
    "GHOST": "Ghost",
    "SHERIFF": "Sheriff",
    "MP5": "MP5 SMG",
    "UMP": "UMP SMG",
    "M014": "M014 Shotgun",
    "MAG-7": "MAG-7 Shotgun",
    "AK-47": "AK-47",
    "VANDAL": "Vandal",
    "M416": "M416",
    "PHANTOM": "Phantom",
    "GUARDIAN": "Guardian",
    "M24": "M24 Sniper",
    "AWM": "AWM Sniper",
}

MAX_ARMOR = 50
current_secondary = "CLASSIC"
current_primary = None
owned = {"KNIFE", "CLASSIC"}
weapon_ammo = {}
dropped_weapons = []
supply_drops = []
bought_this_round = set()

# Dao cận chiến
KNIFE_RANGE, KNIFE_COOLDOWN, KNIFE_SWING_TIME = 205, 380, 0.28
last_melee, knife_swing = 0, 0.0

# Ống ngắm ADS & Sniper
scope_level = 0
SCOPE_CONFIG = {
    "CLASSIC": {"levels": [1.15], "dark": False},
    "GHOST": {"levels": [1.15], "dark": False},
    "SHERIFF": {"levels": [1.2], "dark": False},
    "UMP": {"levels": [1.3], "dark": False},
    "MP5": {"levels": [1.3], "dark": False},
    "M014": {"levels": [1.15], "dark": False},
    "MAG-7": {"levels": [1.15], "dark": False},
    "AK-47": {"levels": [1.5], "dark": False},
    "AK47": {"levels": [1.5], "dark": False},
    "VANDAL": {"levels": [1.5], "dark": False},
    "M416": {"levels": [1.6], "dark": False},
    "PHANTOM": {"levels": [1.6], "dark": False},
    "GUARDIAN": {"levels": [2.0], "dark": False},
    "M24": {"levels": [2.5, 5.0], "dark": True},
    "AWM": {"levels": [2.5, 5.0], "dark": True},
}
SCOPE_WEAPONS = tuple(SCOPE_CONFIG)
BASE_FOV = math.radians(FOV)
ADS_SPEED = 7.0
scope_zoom = 1.0


def _build_sniper_scope_overlay():
    """Tạo sẵn mặt nạ ống nhòm bắn tỉa 1 lần duy nhất (không tạo lại mỗi frame)."""
    cx, cy = WIDTH // 2, HEIGHT // 2
    r = int(min(WIDTH, HEIGHT) * 0.42)
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 255))
    pygame.draw.circle(surf, (0, 0, 0, 0), (cx, cy), r)
    for k in range(14):
        pygame.draw.circle(surf, (0, 0, 0, 150 - k * 10), (cx, cy), r - k, 1)
    pygame.draw.circle(surf, (20, 20, 20, 255), (cx, cy), r, 5)
    col = (10, 10, 10, 255)
    pygame.draw.line(surf, col, (cx - r, cy), (cx - 6, cy), 2)
    pygame.draw.line(surf, col, (cx + 6, cy), (cx + r, cy), 2)
    pygame.draw.line(surf, col, (cx, cy - r), (cx, cy - 6), 2)
    pygame.draw.line(surf, col, (cx, cy + 6), (cx, cy + r), 2)
    pygame.draw.line(surf, col, (cx - r, cy), (cx - r // 2, cy), 5)
    pygame.draw.line(surf, col, (cx + r // 2, cy), (cx + r, cy), 5)
    pygame.draw.line(surf, col, (cx, cy + r // 2), (cx, cy + r), 5)
    for t in range(1, 5):
        d = t * r // 10
        for sx in (-1, 1):
            pygame.draw.line(surf, col, (cx + sx * d, cy - 5), (cx + sx * d, cy + 5), 1)
        pygame.draw.line(surf, col, (cx - 5, cy + d), (cx + 5, cy + d), 1)
    pygame.draw.circle(surf, (230, 40, 40, 255), (cx, cy), 2)
    return surf


_sniper_scope_surf = _build_sniper_scope_overlay()


def set_zoom(zoom):
    renderer.fov = 2 * math.atan(math.tan(BASE_FOV / 2) / zoom)
    renderer.projection_plane = (WIDTH / 2.0) / math.tan(renderer.fov / 2.0)


def cancel_scope():
    global scope_level
    scope_level = 0
    player.scoped = False


def update_scope(dt):
    global scope_zoom
    want = scope_level > 0 and player.weapon in SCOPE_WEAPONS and player.alive and not player.reloading
    target_ads = 1.0 if want else 0.0
    ads = getattr(player, "ads", 0.0)
    step = ADS_SPEED * dt
    ads = min(target_ads, ads + step) if target_ads > ads else max(target_ads, ads - step)
    player.ads = ads
    target_zoom = SCOPE_CONFIG[player.weapon]["levels"][scope_level - 1] if want else 1.0
    if want and SCOPE_CONFIG[player.weapon]["dark"] and ads < 0.85:
        target_zoom = 1.0 + (target_zoom - 1.0) * ads
    scope_zoom += (target_zoom - scope_zoom) * min(1.0, dt * 14.0)
    if abs(scope_zoom - target_zoom) < 0.002:
        scope_zoom = target_zoom
    set_zoom(scope_zoom)


# KINH TẾ & LỰU ĐẠN
STARTING_MONEY, MAX_MONEY, WIN_REWARD = 900, 99000, 3250
LOSS_START, LOSS_STEP, LOSS_MAX = 1400, 500, 3400
loss_streak = 0
KILL_REWARDS = {
    "KNIFE": 1500, "SHOTGUN": 900, "SMG": 600, "PISTOL": 350,
    "RIFLE": 350, "GRENADE": 350, "AWM": (150, 350),
}

GRENADES = ("SMOKE", "MOLOTOV", "BOMB")
GRENADE_KEYS = {pygame.K_4: "SMOKE", pygame.K_5: "MOLOTOV", pygame.K_6: "BOMB"}
GRENADE_MAX = {"SMOKE": 2, "MOLOTOV": 2, "BOMB": 2}
GRENADE_LABEL = {"SMOKE": "Khói", "MOLOTOV": "Lửa", "BOMB": "Bom nổ"}
GRENADE_COLORS = {"SMOKE": (180, 185, 195), "MOLOTOV": (240, 130, 40), "BOMB": (220, 60, 60)}
grenades = {"SMOKE": 0, "MOLOTOV": 0, "BOMB": 0}
held_item = None
projectiles = []
zones = []

GRAVITY, THROW_SPEED, THROW_VZ, EYE_H = 780, 560, 260, 32
SMOKE_TIME, SMOKE_RADIUS = 10.0, 130
FIRE_TIME, FIRE_RADIUS, FIRE_TICK = 3.5, 98, 0.25
BOMB_FUSE, BOMB_RADIUS = 5.0, 235
bomb_fuse = None

# CỬA HÀNG
ITEMS = {
    "MEDKIT": ("Hộp Cứu Thương (+50 HP)", "Hồi ngay 50 máu cho nhân vật", 350),
    "LIGHT_ARMOR": ("Giáp Nhẹ (+25)", "Hấp thụ 50% sát thương, +25 giáp", 400),
    "ARMOR": ("Giáp Nặng (+50)", "Hấp thụ 50% sát thương, tối đa 50 giáp", 1000),
    "SMOKE": ("Lựu Đạn Khói", "Tạo màn khói che tầm nhìn địch trong 10 giây", 300),
    "MOLOTOV": ("Bom Xăng Lửa", "Đốt cháy vùng đất trong 3.5 giây, khắc chế Zombie", 400),
    "BOMB": ("Bom Hẹn Giờ 5s", "Nổ diện rộng gây sát thương cực lớn", 600),
    "CLASSIC": ("Classic", "Súng lục cơ bản · 12 viên · Miễn phí", 0),
    "GHOST": ("Ghost", "Súng lục giảm thanh · 15 viên · Chính xác cao", 500),
    "SHERIFF": ("Sheriff", "Súng lục ổ quay · 6 viên · Uy lực mạnh", 800),
    "UMP": ("UMP", "SMG tốc độ cao 18v/s · Ngắm 1.3x", 1000),
    "MP5": ("MP5", "SMG 30 viên ổn định · Ngắm 1.3x", 1600),
    "M014": ("M014", "Shotgun bán tự động · 5 viên cận chiến", 900),
    "MAG-7": ("MAG-7", "Shotgun tự động 7 viên · Khắc tinh Zombie", 1500),
    "AK-47": ("AK-47", "Súng trường 25 viên · Headshot 1 viên hạ gục", 2900),
    "VANDAL": ("Vandal", "Súng trường 25 viên · Sát thương ổn định mọi cự ly", 2900),
    "M416": ("M416", "Súng trường 30 viên · Tốc độ bắn nhanh", 2900),
    "PHANTOM": ("Phantom", "Súng trường giảm thanh 30 viên · Ngắm 1.6x", 2900),
    "GUARDIAN": ("Guardian", "Súng trường bán tự động · Ngắm 2.0x", 2700),
    "M24": ("M24", "Súng tỉa cơ động · Ống ngắm 2.5x / 5x", 1100),
    "AWM": ("AWM", "Súng ngắm hạng nặng · 1 viên hạ gục", 4500),
}
SHOP_TABS = {
    "TRANG BỊ": ["MEDKIT", "LIGHT_ARMOR", "ARMOR", "SMOKE", "MOLOTOV", "BOMB"],
    "SÚNG LỤC": ["CLASSIC", "GHOST", "SHERIFF"],
    "SMG & SHOTGUN": ["UMP", "MP5", "M014", "MAG-7"],
    "SÚNG TRƯỜNG": ["AK-47", "VANDAL", "M416", "PHANTOM", "GUARDIAN"],
    "SÚNG TỈA": ["M24", "AWM"],
}
SHOP_CATEGORIES = list(SHOP_TABS)
current_shop_tab = "TRANG BỊ"
shop_open = False

dim_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
dim_surface.fill((0, 0, 0, 165))

# FONT TIẾNG VIỆT TỰ CO GIÃN THEO ĐỘ PHÂN GIẢI (1024x576 WEB / 1600x900 DESKTOP)
_UI_K = HEIGHT / 900.0
font_title = get_font(max(30, int(54 * _UI_K)), bold=True)
font_big = get_font(max(19, int(28 * _UI_K)), bold=True)
font_mid = get_font(max(15, int(21 * _UI_K)), bold=True)
font_small = get_font(max(12, int(16 * _UI_K)), bold=True)
font_tiny = get_font(max(11, int(14 * _UI_K)))

notice_text, notice_timer = "", 0.0


def notice(text, seconds=2.2):
    global notice_text, notice_timer
    notice_text = text
    notice_timer = seconds


_main_text_cache = {}


def draw_text(text, font, color, **anchor):
    key = (id(font), text, color)
    img = _main_text_cache.get(key)
    if img is None:
        if len(_main_text_cache) > 256:
            _main_text_cache.clear()
        img = font.render(text, True, color)
        _main_text_cache[key] = img
    rect = img.get_rect(**anchor)
    screen.blit(img, rect)
    return rect


def draw_notice():
    if notice_timer > 0 and notice_text:
        img = font_mid.render(notice_text, True, (255, 232, 120))
        rect = img.get_rect(center=(WIDTH // 2, 96))
        bg = rect.inflate(24, 10)
        pygame.draw.rect(screen, (16, 20, 28), bg, border_radius=6)
        pygame.draw.rect(screen, (240, 195, 70), bg, 1, border_radius=6)
        screen.blit(img, rect)


# TRẠNG THÁI TRẬN ĐẤU & ZOMBIE WAVE
enemies = []
game_state = "MENU"  # MENU / BUY / ROUND / ROUND_END / MATCH_OVER
resume_state = None
kills = 0
zombie_kills_match = 0
round_number = 1
zombie_wave = 1
zombies_to_spawn = 0
zombie_spawn_timer = 0.0
hybrid_zombie_timer = 0.0
hybrid_zombies_spawned = 0

round_timer, buy_timer = ROUND_TIME, BUY_TIME
player_score = enemy_score = 0
MATCH_WIN_SCORE = 13
match_winner = None
match_over_screenshot_taken = False

ROUND_END_TIME = 4.5
round_end_timer = 0.0
pending_winner = None
hit_flash_timer, running = 0.0, True


def current_diff():
    return DIFF_BY_ID[selected_diff_id]


def add_money(amount):
    mult = current_diff()["money_mult"]
    gained = int(round(amount * mult)) if amount > 0 else amount
    player.money = max(0, min(MAX_MONEY, getattr(player, "money", 0) + gained))
    return gained


def maybe_spawn_supply(x, y, chance=0.35):
    if len(supply_drops) >= 12:
        return
    if random.random() <= chance:
        kind = pick_supply_kind(player.hp)
        cx, cy = find_clear_point(x, y, radius=16)
        supply_drops.append({"kind": kind, "x": cx, "y": cy, "ttl": 28.0})


def on_enemy_killed(enemy, weapon_type=None, headshot=False):
    global kills, zombie_kills_match
    kills += 1
    profile["total_kills"] = profile.get("total_kills", 0) + 1

    if getattr(enemy, "is_zombie", False):
        zombie_kills_match += 1
        profile["zombie_kills"] = profile.get("zombie_kills", 0) + 1
        base_reward = enemy.reward + (60 if headshot else 0)
        gained = add_money(base_reward)
        prefix = "HEADSHOT! " if headshot else ""
        notice(f"{prefix}Hạ {enemy.label} (+${gained})")
        maybe_spawn_supply(enemy.x, enemy.y, enemy.drop_chance)
        return

    wt = weapon_type or player.weapon
    if wt == "AWM":
        reward = random.randint(*KILL_REWARDS["AWM"])
    else:
        kind = (
            "KNIFE" if wt == "KNIFE"
            else "SHOTGUN" if wt in ("M014", "MAG-7")
            else "SMG" if wt in ("MP5", "UMP")
            else "PISTOL" if wt in SIDEARMS
            else "GRENADE" if wt == "GRENADE"
            else "RIFLE"
        )
        reward = KILL_REWARDS[kind]
    gained = add_money(reward)
    prefix = "HEADSHOT! " if headshot else ""
    notice(f"{prefix}Hạ đặc nhiệm địch (+${gained})")
    maybe_spawn_supply(enemy.x, enemy.y, 0.18)


def refill_ammo():
    for w_id in GUNS:
        w = get_weapon(w_id)
        weapon_ammo[w_id] = [w.max_magazine, w.reserve]


def store_ammo():
    if player.weapon in GUNS:
        weapon_ammo[player.weapon] = [player.magazine, player.reserve]


def load_ammo():
    if player.weapon in GUNS:
        w = get_weapon(player.weapon)
        player.max_magazine = w.max_magazine
        player.fire_delay = w.fire_rate
        player.reload_time = w.reload_time
        weapon_ammo.setdefault(player.weapon, [w.max_magazine, w.reserve])
        player.magazine, player.reserve = weapon_ammo[player.weapon]
    else:
        player.max_magazine = player.magazine = player.reserve = 0


def start_reload():
    cancel_scope()
    player.reloading = True
    player.reload_start = pygame.time.get_ticks() / 1000.0
    sound.play("reload.wav")


# KHỞI TẠO ĐỊCH & ZOMBIE THEO BẢN ĐỒ
def create_tactical_bots(bot_armor=25, count=5):
    m = get_active_map()
    spawns = list(m["enemy_spawns"])
    random.shuffle(spawns)
    diff = current_diff()
    bots = []
    for sx, sy in spawns[:count]:
        cx, cy = find_clear_point(sx, sy, radius=18)
        bots.append(Enemy(cx, cy, armor=bot_armor, is_zombie=False, diff_cfg=diff))
    return bots


def spawn_single_zombie(wave_level=1, force_boss=False):
    m = get_active_map()
    portals = list(m["zombie_spawns"])
    # Chọn cổng xa người chơi ít nhất 260 đơn vị để không đẻ sát lưng bất hợp lý
    far_portals = [p for p in portals if math.hypot(p[0] - player.x, p[1] - player.y) > 260]
    sx, sy = random.choice(far_portals if far_portals else portals)
    sx += random.uniform(-28, 28)
    sy += random.uniform(-28, 28)
    cx, cy = find_clear_point(sx, sy, radius=20)
    z_type = pick_zombie_type(wave_level, force_boss=force_boss)
    z = Enemy(cx, cy, is_zombie=True, zombie_type=z_type, diff_cfg=current_diff())
    enemies.append(z)
    if force_boss or random.random() < 0.40:
        sound.play("zombie_roar.wav")
    return z


# CAMERA & HÌNH HỌC
def get_camera_horizon():
    pitch_offset = math.tan(getattr(player, "pitch", 0.0)) * renderer.projection_plane * 0.45
    cam_offset = renderer.get_camera_offset(player)
    return max(-HEIGHT, min(HEIGHT * 2, int(HEIGHT // 2 + pitch_offset + cam_offset)))


def angle_diff(a, b):
    return math.atan2(math.sin(a - b), math.cos(a - b))


def holding_knife():
    return player.weapon == "KNIFE" and held_item is None


def can_reach(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1) < 1 or not line_blocked(x1, y1, x2, y2, walls)


def seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / l2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))


def smoke_blocks(x1, y1, x2, y2):
    return any(
        z["kind"] == "SMOKE" and seg_dist(z["x"], z["y"], x1, y1, x2, y2) <= z["r"] * 0.85
        for z in zones
    )


def project(x, y, z=0.0):
    dx, dy = x - player.x, y - player.y
    dist = math.hypot(dx, dy)
    if dist < 1:
        return None
    rel = angle_diff(math.atan2(dy, dx), player.angle)
    if abs(rel) > (renderer.fov / 2 + 0.4):
        return None
    scale = renderer.projection_plane / dist
    return (
        WIDTH // 2 + math.tan(rel) * renderer.projection_plane,
        get_camera_horizon() + (EYE_H - z) * scale,
        scale,
    )


def in_range_of(obj, x, y, r):
    return obj.alive and math.hypot(obj.x - x, obj.y - y) <= r and can_reach(x, y, obj.x, obj.y)


def kill_player_if_dead():
    if player.hp <= 0:
        player.hp = 0
        player.alive = False


# QUẢN LÝ HIỆP ĐẤU & ĐỢT ZOMBIE
def reset_player(keep_guns=False, keep_armor=False, heal_full=True):
    global current_primary, current_secondary, held_item, bomb_fuse, scope_level
    m = get_active_map()
    px, py, pang = m["player_spawn"]
    player.x, player.y = find_clear_point(px, py, radius=player.radius)
    player.angle = pang
    player.pitch = 0.0
    if heal_full:
        player.hp = 100
    else:
        player.hp = min(100, max(35, int(player.hp) + 25))
    player.alive = True
    if not keep_armor:
        player.armor = 0
    player.armor = min(MAX_ARMOR, player.armor)
    if not keep_guns:
        owned.clear()
        owned.update({"KNIFE", "CLASSIC"})
        grenades.update({g: 0 for g in GRENADES})
        current_secondary = "CLASSIC"
        current_primary = None
        player.weapon = "CLASSIC"
    held_item = None
    bomb_fuse = BOMB_FUSE
    scope_level = 0
    player.scoped = False
    refill_ammo()
    if player.weapon not in owned:
        player.weapon = current_secondary if current_secondary in owned else "CLASSIC"
    load_ammo()
    player.reloading = False
    player.crouching = False
    player.is_jumping = False
    player.recoil = 0
    player.vertical_velocity = 0
    player.vertical_offset = 0


def start_combat_phase():
    """Chuyển từ BUY sang chiến đấu (gọi khi hết giờ mua hoặc người chơi bấm [N])."""
    global game_state, round_timer, zombies_to_spawn, zombie_spawn_timer
    global hybrid_zombie_timer, hybrid_zombies_spawned
    if shop_open:
        toggle_shop(False)
    game_state = "ROUND"
    if selected_mode_id == "ZOMBIE":
        round_timer = 180.0
        extra = current_diff()["zombie_extra"]
        zombies_to_spawn = 5 + zombie_wave * 3 + extra * 2
        zombie_spawn_timer = 0.3
        # Mỗi 3 đợt có Boss Đột Biến dẫn đầu!
        if zombie_wave % 3 == 0:
            spawn_single_zombie(zombie_wave, force_boss=True)
            zombies_to_spawn = max(0, zombies_to_spawn - 1)
            notice(f"ĐỢT {zombie_wave}: BOSS ZOMBIE ĐỘT BIẾN XUẤT HIỆN!", 3.2)
        else:
            sound.play("zombie_roar.wav")
            notice(f"ĐỢT ZOMBIE {zombie_wave} BẮT ĐẦU!", 2.4)
    elif selected_mode_id == "HYBRID":
        round_timer = ROUND_TIME
        hybrid_zombie_timer = 5.5
        hybrid_zombies_spawned = 0
        # Xuất hiện ngay 2 Zombie mở màn cùng đội đặc nhiệm!
        for _ in range(2):
            spawn_single_zombie(round_number)
            hybrid_zombies_spawned += 1
        notice("HIỆP BẮT ĐẦU! CẢNH GIÁC ĐẶC NHIỆM & ZOMBIE!", 2.5)
    else:
        round_timer = ROUND_TIME
        notice("HIỆP ĐẤU BẮT ĐẦU!", 2.0)


def reset_round(winner=None):
    global enemies, round_timer, buy_timer, game_state
    global shop_open, scope_level, round_end_timer, pending_winner, zombies_to_spawn

    if selected_mode_id == "ZOMBIE":
        first_wave = winner is None
        reset_player(keep_guns=not first_wave, keep_armor=not first_wave, heal_full=first_wave)
        enemies = []
        zombies_to_spawn = 0
        buy_timer = 14.0
    else:
        if winner == "PLAYER":
            reset_player(keep_guns=True, keep_armor=True, heal_full=True)
            enemies = create_tactical_bots(bot_armor=0, count=5)
        else:
            reset_player(keep_guns=False, keep_armor=False, heal_full=True)
            enemies = create_tactical_bots(bot_armor=25, count=5)
        buy_timer = 18.0

    projectiles.clear()
    zones.clear()
    dropped_weapons.clear()
    supply_drops.clear()
    bought_this_round.clear()
    round_timer = ROUND_TIME
    round_end_timer = 0.0
    pending_winner = None
    game_state = "BUY"
    shop_open = False
    scope_level = 0
    player.scoped = False


def end_round(player_won):
    global player_score, enemy_score, round_number, zombie_wave
    global game_state, match_winner, loss_streak, round_end_timer, pending_winner, shop_open

    if selected_mode_id == "ZOMBIE":
        if player_won:
            if zombie_wave > profile.get("best_wave", 0):
                profile["best_wave"] = zombie_wave
            save_profile(profile)
            bonus = add_money(950 + zombie_wave * 180)
            player_score = zombie_wave
            zombie_wave += 1
            sound.play("ricochet.wav")
            notice(f"VƯỢT QUA ĐỢT {player_score}! Thưởng +${bonus}", 3.0)
            pending_winner = "PLAYER"
            round_end_timer = 3.5
            shop_open = False
            game_state = "ROUND_END"
        else:
            if zombie_wave - 1 > profile.get("best_wave", 0):
                profile["best_wave"] = zombie_wave - 1
            save_profile(profile)
            match_winner = "ENEMY"
            game_state = "MATCH_OVER"
        return

    round_number += 1
    if player_won:
        player_score += 1
        gained = add_money(WIN_REWARD)
        loss_streak = max(0, loss_streak - 1)
        sound.play("ricochet.wav")
        notice(f"THẮNG HIỆP! +${gained}", 3.0)
    else:
        enemy_score += 1
        loss_streak += 1
        loss_bonus = min(LOSS_START + (loss_streak - 1) * LOSS_STEP, LOSS_MAX)
        gained = add_money(loss_bonus)
        notice(f"THUA HIỆP! Trợ cấp +${gained} (Chuỗi {loss_streak})", 3.0)

    save_profile(profile)
    if max(player_score, enemy_score) >= MATCH_WIN_SCORE:
        match_winner = "PLAYER" if player_won else "ENEMY"
        if match_winner == "PLAYER":
            profile["matches_won"] = profile.get("matches_won", 0) + 1
            save_profile(profile)
        game_state = "MATCH_OVER"
        return

    pending_winner = "PLAYER" if player_won else "ENEMY"
    round_end_timer = ROUND_END_TIME
    shop_open = False
    game_state = "ROUND_END"


def restart_match():
    global player_score, enemy_score, round_number, zombie_wave, match_winner
    global match_over_screenshot_taken, kills, zombie_kills_match, loss_streak
    global current_secondary, current_primary

    profile["last_map"] = get_active_map_id()
    profile["last_mode"] = selected_mode_id
    profile["last_diff"] = selected_diff_id
    save_profile(profile)

    player_score = enemy_score = 0
    round_number = 1
    zombie_wave = 1
    kills = 0
    zombie_kills_match = 0
    loss_streak = 0
    match_winner = None
    match_over_screenshot_taken = False
    owned.clear()
    owned.update({"KNIFE", "CLASSIC"})
    current_secondary = "CLASSIC"
    current_primary = None
    dropped_weapons.clear()
    supply_drops.clear()
    player.weapon = "CLASSIC"
    player.money = STARTING_MONEY if selected_mode_id != "ZOMBIE" else 1400
    reset_round()
    set_mouse_mode(False)


# GIAO DIỆN MENU CHÍNH (CHỌN CHẾ ĐỘ, ĐỘ KHÓ & 5 BẢN ĐỒ CÓ PREVIEW)
_map_thumb_cache = {}


def _get_map_thumb(map_id, w=200, h=110):
    key = (map_id, w, h)
    surf = _map_thumb_cache.get(key)
    if surf is not None:
        return surf
    m = MAPS[map_id]
    surf = pygame.Surface((w, h))
    surf.fill(m["theme"]["floor_far"])
    sx = w / 1800.0
    sy = h / 1200.0
    for s_col, s_key in (((35, 95, 60), "A"), ((35, 65, 105), "B"), ((95, 80, 35), "C")):
        sr = m["sites"].get(s_key)
        if sr:
            pygame.draw.rect(
                surf, s_col,
                (int(sr.x * sx), int(sr.y * sy), max(3, int(sr.w * sx)), max(3, int(sr.h * sy))),
            )
    w_col = m["theme"]["wall_rgb"]
    for wl in m["walls"]:
        pygame.draw.rect(
            surf, w_col,
            (int(wl.x * sx), int(wl.y * sy), max(2, int(wl.w * sx)), max(2, int(wl.h * sy))),
        )
    px, py, _ = m["player_spawn"]
    pygame.draw.circle(surf, (80, 240, 120), (int(px * sx), int(py * sy)), 4)
    for zx, zy in m["zombie_spawns"][:4]:
        pygame.draw.circle(surf, (235, 75, 85), (int(zx * sx), int(zy * sy)), 3)
    _map_thumb_cache[key] = surf
    return surf


def match_in_progress():
    return game_state == "MENU" and resume_state in ("BUY", "ROUND", "ROUND_END")


def menu_layout():
    cx = WIDTH // 2
    k = HEIGHT / 900.0
    # Hàng 1: 3 Chế độ chơi
    mode_rects = []
    mgap = max(10, int(18 * k))
    mw = min(330, (WIDTH - 64 - 2 * mgap) // 3)
    mh = max(42, int(62 * k))
    my = int(178 * k)
    m_start_x = cx - (len(GAME_MODES) * mw + (len(GAME_MODES) - 1) * mgap) // 2
    for i, m in enumerate(GAME_MODES):
        mode_rects.append((pygame.Rect(m_start_x + i * (mw + mgap), my, mw, mh), m["id"]))

    # Hàng 2: 3 Độ khó
    diff_rects = []
    dw = max(128, int(165 * k))
    dh = max(30, int(42 * k))
    dgap = max(10, int(14 * k))
    dy = int(266 * k)
    d_start_x = cx - (len(DIFFICULTIES) * dw + (len(DIFFICULTIES) - 1) * dgap) // 2
    for i, d in enumerate(DIFFICULTIES):
        diff_rects.append((pygame.Rect(d_start_x + i * (dw + dgap), dy, dw, dh), d["id"]))

    # Hàng 3: 5 Bản đồ
    map_rects = []
    cgap = max(8, int(16 * k))
    cw = min(252, (WIDTH - 56 - 4 * cgap) // 5)
    ch = max(126, int(195 * k))
    cy = int(342 * k)
    c_start_x = cx - (len(MAP_ORDER) * cw + (len(MAP_ORDER) - 1) * cgap) // 2
    for i, mid in enumerate(MAP_ORDER):
        map_rects.append((pygame.Rect(c_start_x + i * (cw + cgap), cy, cw, ch), mid))

    # Hàng 4: Các nút bấm hành động
    btn_specs = []
    if match_in_progress():
        btn_specs.append(("TIẾP TỤC TRẬN", "resume", (65, 185, 110)))
        btn_specs.append(("TRẬN MỚI", "start", (220, 65, 75)))
    else:
        btn_specs.append(("BẮT ĐẦU CHƠI", "start", (220, 65, 75)))
    if not IS_WEB:
        btn_specs.append(("THOÁT", "quit", (60, 68, 86)))

    bw = max(180, int(250 * k))
    bh = max(40, int(56 * k))
    bgap = max(12, int(20 * k))
    by = int(572 * k)
    b_start_x = cx - (len(btn_specs) * bw + (len(btn_specs) - 1) * bgap) // 2
    action_rects = [
        (pygame.Rect(b_start_x + i * (bw + bgap), by, bw, bh), label, action, col)
        for i, (label, action, col) in enumerate(btn_specs)
    ]
    return mode_rects, diff_rects, map_rects, action_rects


def go_to_menu():
    global game_state, resume_state, shop_open
    if game_state == "MENU":
        return
    resume_state = game_state
    shop_open = False
    game_state = "MENU"
    set_mouse_mode(True)


def menu_action(action):
    global game_state, running
    if action == "resume":
        game_state = resume_state
        set_mouse_mode(False)
    elif action == "start":
        restart_match()
    elif action == "quit":
        running = False


def draw_menu():
    k = HEIGHT / 900.0
    hdr_h = int(138 * k)
    active_theme = get_active_map()["theme"]
    screen.fill((14, 18, 28))
    pygame.draw.rect(screen, active_theme["sky_bot"], (0, 0, WIDTH, hdr_h))
    pygame.draw.line(screen, active_theme["accent"], (0, hdr_h), (WIDTH, hdr_h), 3)

    cx = WIDTH // 2
    draw_text("LOTUS TACTICAL FPS", font_title, (245, 247, 252), center=(cx, int(48 * k)))
    stats_str = (
        f"Kỷ lục Sinh tồn: Đợt {profile.get('best_wave', 0)}   ·   "
        f"Tổng hạ gục: {profile.get('total_kills', 0)}   ·   "
        f"Zombie đã diệt: {profile.get('zombie_kills', 0)}   ·   "
        f"Trận thắng: {profile.get('matches_won', 0)}"
    )
    draw_text(stats_str, font_small, (210, 225, 245), center=(cx, int(104 * k)))

    mouse = pygame.mouse.get_pos()
    mode_rects, diff_rects, map_rects, action_rects = menu_layout()

    # 1. Chọn chế độ chơi
    draw_text("CHẾ ĐỘ CHƠI:", font_small, (165, 178, 200), midleft=(mode_rects[0][0].left, mode_rects[0][0].top - int(16 * k)))
    for rect, mid in mode_rects:
        m = MODE_BY_ID[mid]
        sel = mid == selected_mode_id
        hov = rect.collidepoint(mouse)
        bg = m["color"] if sel else ((44, 52, 70) if hov else (28, 33, 46))
        pygame.draw.rect(screen, bg, rect, border_radius=8)
        pygame.draw.rect(screen, (255, 255, 255) if sel else m["color"], rect, 2, border_radius=8)
        draw_text(m["name"], font_mid, (255, 255, 255), center=(rect.centerx, rect.y + int(rect.h * 0.36)))
        draw_text(m["short"], font_tiny, (235, 240, 248) if sel else (170, 180, 198), center=(rect.centerx, rect.y + int(rect.h * 0.74)))

    desc_txt = MODE_BY_ID[selected_mode_id]["desc"]
    draw_text(desc_txt, font_tiny, (195, 210, 230), midleft=(mode_rects[0][0].left, mode_rects[0][0].bottom + int(12 * k)))

    # 2. Chọn độ khó
    for rect, did in diff_rects:
        d = DIFF_BY_ID[did]
        sel = did == selected_diff_id
        hov = rect.collidepoint(mouse)
        bg = d["color"] if sel else ((44, 52, 70) if hov else (28, 33, 46))
        pygame.draw.rect(screen, bg, rect, border_radius=7)
        pygame.draw.rect(screen, (255, 255, 255) if sel else d["color"], rect, 2, border_radius=7)
        txt_col = (18, 22, 28) if sel else (240, 242, 248)
        draw_text(f"ĐỘ KHÓ: {d['name']}", font_small, txt_col, center=rect.center)

    # 3. Chọn 1 trong 5 bản đồ
    cur_map = get_active_map_id()
    draw_text("CHỌN BẢN ĐỒ (5 MAPS):", font_small, (165, 178, 200), midleft=(map_rects[0][0].left, map_rects[0][0].top - int(16 * k)))
    for rect, map_id in map_rects:
        m = MAPS[map_id]
        sel = map_id == cur_map
        hov = rect.collidepoint(mouse)
        accent = m["theme"]["accent"]
        bg = (42, 50, 68) if (sel or hov) else (24, 29, 40)
        pygame.draw.rect(screen, bg, rect, border_radius=10)
        pygame.draw.rect(screen, accent if sel else (65, 75, 96), rect, 3 if sel else 1, border_radius=10)

        pad_m = max(6, int(10 * k))
        th_h = max(64, int(rect.h * 0.56))
        thumb = _get_map_thumb(map_id, rect.w - pad_m * 2, th_h)
        screen.blit(thumb, (rect.x + pad_m, rect.y + pad_m))
        pygame.draw.rect(screen, accent if sel else (55, 62, 78), (rect.x + pad_m, rect.y + pad_m, rect.w - pad_m * 2, th_h), 1)

        draw_text(m["name"], font_small, accent if sel else (240, 244, 250), center=(rect.centerx, rect.y + pad_m + th_h + int(rect.h * 0.14)))
        draw_text(m["subtitle"], font_tiny, (180, 190, 208), center=(rect.centerx, rect.y + pad_m + th_h + int(rect.h * 0.28)))

    # 4. Nút Bắt đầu / Tiếp tục
    for rect, label, _, col in action_rects:
        hov = rect.collidepoint(mouse)
        fill = (min(255, col[0] + 22), min(255, col[1] + 22), min(255, col[2] + 22)) if hov else col
        pygame.draw.rect(screen, fill, rect, border_radius=9)
        pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=9)
        draw_text(label, font_big, (255, 255, 255), center=rect.center)

    # 5. Hướng dẫn phím bấm dưới chân trang
    hint = (145, 158, 180)
    draw_text(
        "WASD: Di chuyển · Chuột/Phím ←→: Xoay · Chuột trái: Bắn · Chuột phải/[V]: Ngắm Scope · [B]: Shop · [N]: Vào trận",
        font_tiny, hint, center=(cx, HEIGHT - max(32, int(52 * k))),
    )
    draw_text(
        "1: Dao · 2: Súng lục · 3: Súng chính · 4/5/6: Khói/Lửa/Bom · [R]: Nạp đạn · [F]/[G]: Nhặt/Vứt · Space/Ctrl: Nhảy/Ngồi",
        font_tiny, hint, center=(cx, HEIGHT - max(14, int(26 * k))),
    )


# TRANG BỊ, VỨT / NHẶT SÚNG & HỘP TIẾP TẾ
def equip(weapon_id):
    global current_secondary, current_primary, held_item, scope_level
    held_item = None
    scope_level = 0
    player.scoped = False
    if weapon_id not in owned:
        notice(f"Chưa sở hữu {WEAPON_NAMES.get(weapon_id, weapon_id)} - bấm [B] mở Cửa hàng")
        return
    if weapon_id == player.weapon:
        return
    store_ammo()
    player.reloading = False
    player.weapon = weapon_id
    if weapon_id in SIDEARMS:
        current_secondary = weapon_id
    elif weapon_id in PRIMARY_WEAPONS:
        current_primary = weapon_id
    load_ammo()


def equip_grenade(kind):
    global held_item, bomb_fuse
    if grenades[kind] <= 0:
        notice(f"Chưa có {GRENADE_LABEL[kind]} - bấm [B] mua trong Cửa hàng")
        return
    if held_item == kind:
        return
    if player.weapon != "KNIFE":
        store_ammo()
        player.reloading = False
        player.weapon = "KNIFE"
        load_ammo()
    held_item = kind
    bomb_fuse = BOMB_FUSE


def cycle_slot(slot):
    if slot == 1:
        equip("KNIFE")
        return
    current, pool = (current_secondary, SIDEARMS) if slot == 2 else (current_primary, PRIMARY_WEAPONS)
    if current and current in owned:
        equip(current)
    else:
        for w in pool:
            if w in owned:
                equip(w)
                break


def remove_gun(w_id):
    global current_primary, current_secondary
    owned.discard(w_id)
    weapon_ammo.pop(w_id, None)
    if w_id == current_primary:
        current_primary = None
    if w_id == current_secondary:
        current_secondary = None


def equip_best_remaining():
    if current_primary and current_primary in owned:
        equip(current_primary)
    elif current_secondary and current_secondary in owned:
        equip(current_secondary)
    else:
        other = [g for g in GUNS if g in owned]
        equip(other[0] if other else "KNIFE")


def drop_weapon_to_ground(w_id, gx=None, gy=None):
    mag, res = weapon_ammo.get(w_id, [player.magazine, player.reserve])
    x, y = (gx, gy) if gx is not None else (player.x, player.y)
    dropped_weapons.append({"id": w_id, "x": x, "y": y, "magazine": mag, "reserve": res})
    remove_gun(w_id)


def drop_slot_group(w_id):
    group = PRIMARY_WEAPONS if w_id in PRIMARY_WEAPONS else SIDEARMS
    for old in list(group):
        if old in owned:
            drop_weapon_to_ground(old)


def drop_current_weapon():
    if held_item is not None:
        notice("Không thể vứt trang bị ném!")
        return
    if player.weapon not in GUNS or player.weapon not in owned:
        notice("Không thể vứt dao cận chiến!")
        return
    w = player.weapon
    drop_weapon_to_ground(w)
    notice(f"Đã vứt {WEAPON_NAMES.get(w, w)}")
    equip_best_remaining()


def get_nearest_dropped_weapon(max_dist=90):
    best_item, best_dist = None, max_dist
    for item in dropped_weapons:
        d = math.hypot(player.x - item["x"], player.y - item["y"])
        if d <= best_dist and not line_blocked(player.x, player.y, item["x"], item["y"], walls):
            best_dist, best_item = d, item
    return best_item, best_dist


def pickup_nearest_weapon():
    item, _ = get_nearest_dropped_weapon(90)
    if not item:
        return False
    w_id = item["id"]
    drop_slot_group(w_id)
    owned.add(w_id)
    weapon_ammo[w_id] = [item["magazine"], item["reserve"]]
    if item in dropped_weapons:
        dropped_weapons.remove(item)
    equip(w_id)
    player.magazine = item["magazine"]
    player.reserve = item["reserve"]
    sound.play("reload.wav")
    notice(f"Đã nhặt {WEAPON_NAMES.get(w_id, w_id)}")
    return True


def update_supply_drops(dt):
    if not player.alive:
        return
    for sd in supply_drops[:]:
        sd["ttl"] -= dt
        if sd["ttl"] <= 0:
            supply_drops.remove(sd)
            continue
        if math.hypot(player.x - sd["x"], player.y - sd["y"]) <= 54:
            kind = sd["kind"]
            if kind == "MEDKIT":
                if player.hp >= 100:
                    continue
                player.hp = min(100, int(player.hp) + 35)
                notice("Nhặt Hộp Cứu Thương: +35 HP")
            elif kind == "AMMO":
                target_w = player.weapon if player.weapon in GUNS else (current_primary or current_secondary)
                if target_w and target_w in GUNS:
                    w_obj = get_weapon(target_w)
                    if target_w == player.weapon:
                        player.reserve += w_obj.max_magazine * 2
                        store_ammo()
                    else:
                        weapon_ammo.setdefault(target_w, [w_obj.max_magazine, w_obj.reserve])
                        weapon_ammo[target_w][1] += w_obj.max_magazine * 2
                notice("Nhặt Hộp Tiếp Đạn: +2 băng đạn dự trữ!")
            elif kind == "ARMOR_PACK":
                if player.armor >= MAX_ARMOR:
                    continue
                player.armor = min(MAX_ARMOR, int(player.armor) + 25)
                notice("Nhặt Giáp Tiếp Tế: +25 Giáp")
            elif kind == "CASH":
                gained = add_money(350)
                notice(f"Nhặt Gói Tiền Thưởng: +${gained}")
            sound.play("reload.wav")
            supply_drops.remove(sd)


# CỬA HÀNG MUA SẮM
def toggle_shop(open_it):
    global shop_open
    if open_it and game_state != "BUY":
        notice("Đã hết thời gian mua sắm!")
        return
    shop_open = open_it
    set_mouse_mode(open_it)


def shop_layout():
    k = HEIGHT / 900.0
    pw = min(860, WIDTH - 32)
    ph = min(int(610 * max(0.84, k)), HEIGHT - 16)
    panel = pygame.Rect((WIDTH - pw) // 2, (HEIGHT - ph) // 2, pw, ph)
    tab_h = max(28, int(38 * k))
    tab_y = panel.y + max(52, int(68 * k))
    tab_w = (pw - 40) // len(SHOP_CATEGORIES)
    tabs = [
        (pygame.Rect(panel.x + 20 + i * tab_w, tab_y, tab_w - 4, tab_h), cat)
        for i, cat in enumerate(SHOP_CATEGORIES)
    ]
    items = SHOP_TABS[current_shop_tab]
    avail_h = ph - (tab_y - panel.y + tab_h + 44)
    row_step = min(64, max(44, avail_h // max(1, len(items))))
    row_h = row_step - 6
    rows = [
        (pygame.Rect(panel.x + 24, tab_y + tab_h + 10 + i * row_step, pw - 48, row_h), iid)
        for i, iid in enumerate(items)
    ]
    return panel, tabs, rows


def buy_armor(iid, amount, label):
    if player.armor >= MAX_ARMOR:
        notice(f"Giáp đã đầy ({MAX_ARMOR})!")
        return
    player.money -= ITEMS[iid][2]
    player.armor = min(MAX_ARMOR, player.armor + amount)
    bought_this_round.add(iid)
    notice(f"Đã mua {label} (+{amount} Giáp)")


def buy_item(iid):
    if game_state != "BUY":
        notice("Chỉ mua được trong giai đoạn chuẩn bị!")
        return
    name, _, price = ITEMS[iid]
    money = getattr(player, "money", 0)
    if iid in GUNS and iid in owned:
        equip(iid)
        notice(f"Đã trang bị {name}")
        return
    if money < price:
        notice(f"Không đủ tiền mua {name} (thiếu ${price - money:,})")
        return
    if iid == "MEDKIT":
        if player.hp >= 100:
            notice("Máu đã đầy 100 HP!")
            return
        player.money -= price
        player.hp = min(100, int(player.hp) + 50)
        sound.play("reload.wav")
        notice("Đã hồi +50 HP!")
    elif iid in GUNS:
        drop_slot_group(iid)
        player.money -= price
        owned.add(iid)
        w = get_weapon(iid)
        weapon_ammo[iid] = [w.max_magazine, w.reserve]
        equip(iid)
        bought_this_round.add(iid)
        notice(f"Đã mua {name}!")
    elif iid in GRENADES:
        if grenades[iid] >= GRENADE_MAX[iid]:
            notice(f"Đã mang tối đa {GRENADE_MAX[iid]} {GRENADE_LABEL[iid]}!")
            return
        player.money -= price
        grenades[iid] += 1
        bought_this_round.add(iid)
        notice(f"Đã mua {name}! Bấm phím {4 + GRENADES.index(iid)} để cầm")
    elif iid == "LIGHT_ARMOR":
        buy_armor(iid, 25, "Giáp Nhẹ")
    elif iid == "ARMOR":
        buy_armor(iid, 50, "Giáp Nặng")


def sell_item(iid):
    if game_state != "BUY" or iid not in bought_this_round:
        notice("Chỉ bán lại được đồ vừa mua trong hiệp này!")
        return
    name, _, price = ITEMS[iid]
    if iid in GUNS and iid in owned:
        remove_gun(iid)
        player.money += price
        bought_this_round.discard(iid)
        notice(f"Đã bán {name} +${price:,}")
        equip_best_remaining()
    elif iid in GRENADES and grenades[iid] > 0:
        grenades[iid] -= 1
        player.money += price
        if grenades[iid] == 0:
            bought_this_round.discard(iid)
        notice(f"Đã bán {name} +${price:,}")
    elif iid in ("LIGHT_ARMOR", "ARMOR"):
        amount = 25 if iid == "LIGHT_ARMOR" else 50
        if player.armor < amount:
            return
        player.armor -= amount
        player.money += price
        bought_this_round.discard(iid)
        notice(f"Đã bán {name} +${price:,}")


def handle_shop_click(pos, button=1):
    global current_shop_tab
    _, tabs, rows = shop_layout()
    for rect, cat in tabs:
        if rect.collidepoint(pos):
            current_shop_tab = cat
            return
    for rect, iid in rows:
        if rect.collidepoint(pos):
            (sell_item if button == 3 else buy_item)(iid)
            return


def draw_shop():
    screen.blit(dim_surface, (0, 0))
    panel, tabs, rows = shop_layout()
    pygame.draw.rect(screen, (22, 26, 36), panel, border_radius=12)
    pygame.draw.rect(screen, (220, 60, 70), panel, 2, border_radius=12)
    money = getattr(player, "money", 0)
    draw_text("CỬA HÀNG VŨ KHÍ & TIẾP TẾ", font_big, (255, 255, 255), topleft=(panel.x + 24, panel.y + 16))
    draw_text(f"Tiền: ${money:,}", font_mid, (255, 210, 60), topright=(panel.right - 24, panel.y + 20))
    draw_text(
        f"Thời gian chuẩn bị: {max(0, int(buy_timer))}s  (Bấm [N] để vào trận ngay)",
        font_tiny, (165, 178, 198), topleft=(panel.x + 24, panel.y + 48),
    )
    mouse = pygame.mouse.get_pos()
    for rect, cat in tabs:
        active = cat == current_shop_tab
        bg = (220, 60, 70) if active else ((50, 58, 76) if rect.collidepoint(mouse) else (32, 38, 52))
        pygame.draw.rect(screen, bg, rect, border_radius=6)
        draw_text(cat, font_small, (255, 255, 255) if active else (190, 195, 210), center=rect.center)

    for rect, iid in rows:
        name, desc, price = ITEMS[iid]
        sellable = iid in bought_this_round
        pygame.draw.rect(screen, (48, 56, 76) if rect.collidepoint(mouse) else (32, 37, 50), rect, border_radius=8)
        if sellable:
            pygame.draw.rect(screen, (60, 200, 100), rect, 2, border_radius=8)
        draw_text(name, font_mid, (245, 245, 250), topleft=(rect.x + 18, rect.y + 7))
        draw_text(desc, font_tiny, (155, 168, 188), topleft=(rect.x + 18, rect.y + 32))
        skin_icon = get_shop_icon(iid)
        if skin_icon:
            screen.blit(skin_icon, skin_icon.get_rect(midright=(rect.right - 220, rect.centery)))

        if iid in GUNS and iid in owned:
            equipped = player.weapon == iid
            status = "ĐANG CẦM" if equipped else "TRANG BỊ (ĐÃ MUA)"
            if sellable:
                status += " · [Chuột phải: Bán]"
            draw_text(
                status, font_small,
                (60, 225, 120) if equipped else (100, 200, 255),
                midright=(rect.right - 18, rect.centery),
            )
            continue

        is_gren = iid in GRENADES
        if is_gren:
            draw_text(
                f"Đang có: {grenades[iid]}/{GRENADE_MAX[iid]}",
                font_tiny, (155, 165, 185), midright=(rect.right - 115, rect.centery),
            )
        cost_str = "MIỄN PHÍ" if price == 0 else f"${price:,}"
        cost_col = (255, 205, 60) if money >= price else (225, 75, 75)
        if sellable:
            draw_text(
                "[Chuột phải: Bán]", font_tiny, (100, 230, 130),
                midright=(rect.right - 115 if is_gren else rect.right - 18, rect.centery - 10),
            )
            draw_text(cost_str, font_mid, cost_col, midright=(rect.right - 18, rect.centery + 10))
        else:
            draw_text(cost_str, font_mid, cost_col, midright=(rect.right - 18, rect.centery))

    draw_text(
        "Chuột trái: Mua / Trang bị   |   Chuột phải: Bán lại   |   [B] hoặc [ESC]: Đóng",
        font_tiny, (145, 155, 175), center=(panel.centerx, panel.bottom - 18),
    )


# VIEWMODEL PHỤ, ỐNG NGẮM & LỰU ĐẠN 3D
def draw_held_item():
    if not held_item:
        return
    cx, cy = WIDTH - 220, HEIGHT - 180
    pygame.draw.circle(screen, GRENADE_COLORS[held_item], (cx, cy), 36)
    pygame.draw.circle(screen, (30, 32, 40), (cx, cy), 36, 4)
    draw_text(GRENADE_LABEL[held_item], font_small, (255, 255, 255), center=(cx, cy))


def draw_scope():
    cfg = SCOPE_CONFIG[player.weapon]
    zoom = cfg["levels"][max(1, scope_level) - 1]
    draw_weapon_scope(
        screen,
        player.weapon,
        zoom,
        ads_progress=getattr(player, "ads", 1.0),
        recoil=getattr(player, "recoil", 0.0),
        font_zoom=font_small,
    )


fx_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
SMOKE_PUFFS = [
    (0, -0.3, 0.7), (-0.5, -0.1, 0.55), (0.5, -0.1, 0.55),
    (-0.3, -0.7, 0.5), (0.3, -0.7, 0.5), (0, -1.1, 0.45),
]


def throw_grenade():
    global held_item
    kind = held_item
    if kind is None or grenades[kind] <= 0:
        return
    grenades[kind] -= 1
    projectiles.append({
        "kind": kind, "x": player.x, "y": player.y, "z": float(EYE_H),
        "vx": math.cos(player.angle) * THROW_SPEED,
        "vy": math.sin(player.angle) * THROW_SPEED,
        "vz": THROW_VZ, "landed": False,
        "fuse": bomb_fuse if kind == "BOMB" else None,
    })
    if grenades[kind] <= 0:
        held_item = None


def explode(x, y):
    global hit_flash_timer
    sound.play("shotgun.wav")
    notice("BOM PHÁT NỔ!", 1.5)
    for e in enemies:
        if in_range_of(e, x, y, BOMB_RADIUS):
            e.armor = max(0, getattr(e, "armor", 0) - 55)
            e.damage(115 if getattr(e, "is_zombie", False) else 65, part="body")
            if not e.alive:
                on_enemy_killed(e, "GRENADE")
    if in_range_of(player, x, y, BOMB_RADIUS):
        player.armor = max(0, player.armor - 40)
        player.hp -= 40
        hit_flash_timer = 0.3
        kill_player_if_dead()


def burn_area(x, y, r, dmg):
    global hit_flash_timer
    for e in enemies:
        if in_range_of(e, x, y, r):
            z_mult = 2.2 if getattr(e, "is_zombie", False) else 1.0
            e.damage(dmg * z_mult, part="body")
            if not e.alive:
                on_enemy_killed(e, "GRENADE")
    if in_range_of(player, x, y, r):
        hp_before = player.hp
        player.damage(dmg)
        if player.hp < hp_before:
            hit_flash_timer = 0.15
        kill_player_if_dead()


def update_projectiles(dt):
    for p in projectiles[:]:
        if p["fuse"] is not None:
            p["fuse"] -= dt
            if p["fuse"] <= 0:
                projectiles.remove(p)
                explode(p["x"], p["y"])
                continue
        if p["landed"]:
            continue
        nx, ny = p["x"] + p["vx"] * dt, p["y"] + p["vy"] * dt
        if line_blocked(p["x"], p["y"], nx, ny, walls):
            p["vx"] = p["vy"] = 0
        else:
            p["x"], p["y"] = nx, ny
        p["vz"] -= GRAVITY * dt
        p["z"] += p["vz"] * dt
        if p["z"] > 0:
            continue
        p["z"] = 0
        p["landed"] = True
        if p["kind"] == "SMOKE":
            zones.append({"kind": "SMOKE", "x": p["x"], "y": p["y"], "r": SMOKE_RADIUS, "t": SMOKE_TIME})
            projectiles.remove(p)
        elif p["kind"] == "MOLOTOV":
            zones.append({
                "kind": "FIRE", "x": p["x"], "y": p["y"],
                "r": FIRE_RADIUS, "t": FIRE_TIME, "tick": FIRE_TICK,
            })
            burn_area(p["x"], p["y"], FIRE_RADIUS, random.randint(3, 5))
            projectiles.remove(p)


def update_zones(dt):
    for z in zones[:]:
        z["t"] -= dt
        if z["t"] <= 0:
            zones.remove(z)
            continue
        if z["kind"] == "FIRE":
            z["tick"] -= dt
            if z["tick"] <= 0:
                z["tick"] = FIRE_TICK
                burn_area(z["x"], z["y"], z["r"], random.randint(3, 5))


def draw_effects():
    """Chỉ xóa và blit fx_surface khi thực sự có khói / lửa / lựu đạn đang bay (tối ưu lớn trên Web!)."""
    if not zones and not projectiles:
        return
    fx_surface.fill((0, 0, 0, 0))
    in_smoke = False
    for z in zones:
        if z["kind"] == "SMOKE" and math.hypot(z["x"] - player.x, z["y"] - player.y) < z["r"] * 0.8:
            in_smoke = True
        pr = project(z["x"], z["y"])
        if not pr or line_blocked(player.x, player.y, z["x"], z["y"], walls):
            continue
        sx, sy, scale = pr
        if z["kind"] == "SMOKE":
            life = max(0.0, min(1.0, (SMOKE_TIME - z["t"]) / 0.6, z["t"] / 1.5))
            r = int(min(700, z["r"] * scale * (0.4 + 0.6 * life)))
            for ox, oy, k in SMOKE_PUFFS:
                pygame.draw.circle(
                    fx_surface, (175, 177, 182, int(205 * life)),
                    (int(sx + ox * r), int(sy + oy * r)), max(1, int(r * k)),
                )
        else:
            r = int(min(600, z["r"] * scale))
            pygame.draw.ellipse(fx_surface, (255, 80, 0, 75), (sx - r, sy - r * 0.2, 2 * r, r * 0.4))
            for _ in range(8):
                ox = random.uniform(-0.85, 0.85) * r
                oy = random.uniform(-0.15, 0.15) * r
                h = random.uniform(0.2, 0.55) * r
                col = random.choice(((255, 90, 20, 170), (255, 150, 30, 170), (255, 215, 60, 150)))
                pygame.draw.ellipse(fx_surface, col, (sx + ox - r * 0.12, sy + oy - h, r * 0.24, h))

    for p in projectiles:
        pr = project(p["x"], p["y"], p["z"])
        if pr and not line_blocked(player.x, player.y, p["x"], p["y"], walls):
            pygame.draw.circle(
                fx_surface, GRENADE_COLORS[p["kind"]],
                (int(pr[0]), int(pr[1])), max(3, int(7 * pr[2])),
            )
    if in_smoke:
        fx_surface.fill((170, 172, 178, 210))
    screen.blit(fx_surface, (0, 0))


# HUD KHO VŨ KHÍ & THÔNG TIN BÊN TRÁI
def draw_weapon_slots():
    draw_text(f"${getattr(player, 'money', 0):,}", font_mid, (255, 210, 60), topleft=(24, 20))
    mode_info = MODE_BY_ID[selected_mode_id]
    draw_text(
        f"{mode_info['short']} · {DIFF_BY_ID[selected_diff_id]['name']}",
        font_tiny, mode_info["color"], topleft=(24, 48),
    )
    draw_text(f"Hạ gục: {kills} (Zombie: {zombie_kills_match})", font_tiny, (205, 215, 230), topleft=(24, 68))
    cur_fps = int(round(clock.get_fps()))
    if cur_fps > 0:
        fps_col = (95, 235, 130) if cur_fps >= 55 else ((245, 200, 65) if cur_fps >= 40 else (240, 75, 75))
        draw_text(f"FPS: {cur_fps}", font_tiny, fps_col, topleft=(24, 88))

    slot_w = 185 if IS_WEB else 220
    slot_h = 28 if IS_WEB else 36
    slot_step = 32 if IS_WEB else 40
    x = WIDTH - slot_w - 14
    y = minimap.margin + minimap.height + 24
    sec = current_secondary if current_secondary in owned else None
    pri = current_primary if current_primary in owned else None
    rows = [
        (1, "Dao", player.weapon == "KNIFE" and held_item is None, True, "KNIFE"),
        (
            2,
            WEAPON_NAMES.get(sec, sec) if sec else "Súng phụ (Trống)",
            player.weapon == sec and held_item is None and sec is not None,
            sec is not None,
            sec,
        ),
        (
            3,
            WEAPON_NAMES.get(pri, pri) if pri else "Súng chính (Trống)",
            player.weapon == pri and held_item is None and pri is not None,
            pri is not None,
            pri,
        ),
    ]
    for i, g in enumerate(GRENADES):
        have = grenades[g] > 0
        label = f"{GRENADE_LABEL[g]} x{grenades[g]}" if have else f"{GRENADE_LABEL[g]} (0)"
        rows.append((4 + i, label, held_item == g, have, g))

    for i, (key, label, active, have, w_id) in enumerate(rows):
        rect = pygame.Rect(x, y + i * slot_step, slot_w, slot_h)
        bg = (220, 60, 70) if active else ((40, 46, 62) if have else (26, 28, 36))
        pygame.draw.rect(screen, bg, rect, border_radius=6)
        color = (255, 255, 255) if have else (110, 115, 130)
        draw_text(f"{key}", font_mid, color, midleft=(rect.x + 10, rect.centery))
        if label:
            draw_text(label, font_tiny, color, midleft=(rect.x + 30, rect.centery))
        if have and w_id:
            skin_icon = get_hud_icon(w_id)
            if skin_icon:
                screen.blit(skin_icon, skin_icon.get_rect(midright=(rect.right - 8, rect.centery)))


# DI CHUYỂN, BẮN SÚNG & AI BOT + ZOMBIE
def update_player_movement(dt):
    if not player.alive:
        return
    keys = pygame.key.get_pressed()
    fx, fy = math.cos(player.angle), math.sin(player.angle)
    rx, ry = -math.sin(player.angle), math.cos(player.angle)
    fwd = int(keys[pygame.K_w]) - int(keys[pygame.K_s])
    strafe = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
    mx, my = fwd * fx + strafe * rx, fwd * fy + strafe * ry
    length = math.hypot(mx, my)
    if length > 0:
        mx, my = mx / length, my / length
    player.crouching = keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]
    slow = player.crouching or keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
    step = player.speed * (0.48 if slow else 1.0) * dt
    player.move(mx * step, my * step, walls)

    # Hỗ trợ xoay góc nhìn mượt bằng phím mũi tên hoặc Q/E (rất tiện trên Web khi iframe chặn khóa chuột)
    turn = (int(keys[pygame.K_RIGHT] or keys[pygame.K_e]) - int(keys[pygame.K_LEFT] or keys[pygame.K_q]))
    if turn:
        player.angle = (player.angle + turn * (2.4 / scope_zoom) * dt) % math.tau
    pitch_turn = int(keys[pygame.K_UP]) - int(keys[pygame.K_DOWN])
    if pitch_turn:
        player.pitch = max(-player.max_pitch, min(player.max_pitch, player.pitch + pitch_turn * 1.5 * dt))


def melee_attack(is_right_click=False):
    global last_melee, knife_swing
    now = pygame.time.get_ticks()
    if now - last_melee < KNIFE_COOLDOWN:
        return
    last_melee = now
    knife_swing = KNIFE_SWING_TIME
    player.knife_swing = KNIFE_SWING_TIME
    player.knife_is_stab = is_right_click
    target, best = None, float("inf")
    for e in enemies:
        if not e.alive:
            continue
        dist = math.hypot(e.x - player.x, e.y - player.y)
        if dist > KNIFE_RANGE + e.radius or dist >= best:
            continue
        ang = angle_diff(math.atan2(e.y - player.y, e.x - player.x), player.angle)
        if abs(ang) <= 0.78 and not line_blocked(player.x, player.y, e.x, e.y, walls):
            target, best = e, dist
    if target:
        base_dmg = 95 if is_right_click else 60
        actual = target.damage(base_dmg, part="body")
        sound.play("ricochet.wav")
        if not target.alive:
            on_enemy_killed(target, "KNIFE")
        else:
            notice(f"Chém trúng {target.label}: -{int(actual)} HP")


def player_shoot():
    if not player.alive or game_state != "ROUND" or shop_open or player.reloading:
        return
    if held_item:
        throw_grenade()
        return
    if player.weapon == "KNIFE":
        melee_attack()
        return
    w_obj = get_weapon(player.weapon)
    now = pygame.time.get_ticks()
    if player.magazine <= 0:
        if player.reserve > 0:
            start_reload()
        return

    eff_fire_rate = w_obj.scoped_fire_rate if getattr(player, "scoped", False) else w_obj.fire_rate
    if now - player.last_shot < int(eff_fire_rate * 1000):
        return

    player.last_shot = now
    player.magazine -= 1
    recoil_mult = w_obj.scoped_recoil_mult if getattr(player, "scoped", False) else 1.0
    player.recoil = min(player.recoil + 0.035 * recoil_mult, 0.14)
    sound.play("pistol.wav" if w_obj.category == "PISTOL" else "shotgun.wav")

    spread = player.recoil * 0.08 * (1.0 - 0.72 * getattr(player, "ads", 0.0))
    shot_angle = player.angle + (random.random() - 0.5) * spread
    wall_dist = renderer.raycast(player, shot_angle, walls)
    cx, cy = WIDTH // 2, HEIGHT // 2
    shot_y = cy - int(player.recoil * 100)
    hit_offset = {"head": 0.11, "body": 0.43, "legs": 0.82}
    closest_enemy, closest_dist, hit_part, hit_pos = None, float("inf"), "body", None
    horizon = get_camera_horizon()

    for e in enemies:
        if not e.alive:
            continue
        dist = math.hypot(e.x - player.x, e.y - player.y)
        if dist > wall_dist + 12 or dist > 1800 or line_blocked(player.x, player.y, e.x, e.y, walls):
            continue
        h_ang = math.atan2(e.y - player.y, e.x - player.x)
        rel = angle_diff(h_ang, player.angle)
        if abs(rel) > renderer.fov / 2 + 0.08:
            continue
        sx = WIDTH // 2 + math.tan(rel) * renderer.projection_plane
        w_h = getattr(e, "world_height", 70.0)
        bh = max(10, min(2800, int(renderer.projection_plane * w_h / max(dist, 12.0))))
        bw = max(8, int(bh * 0.45))
        foot_y = horizon + int(renderer.projection_plane * 35.0 / max(dist, 12.0))
        btop = foot_y - bh
        part = e.check_hit_3d(sx, btop, bw, bh, cx, shot_y)
        if part is None and abs(angle_diff(h_ang, shot_angle)) <= math.atan2(e.radius * 1.15, dist):
            part = "head" if shot_y < btop + bh * 0.22 else ("body" if shot_y < btop + bh * 0.65 else "legs")
        if part is not None and dist < closest_dist:
            closest_enemy, closest_dist, hit_part = e, dist, part
            hit_pos = (sx, btop + bh * hit_offset[part])

    if closest_enemy:
        dmg = get_weapon_damage(player.weapon, closest_dist / 25.0, part=hit_part)
        # Shotgun cận chiến gây thêm sát thương mảnh đạn lên Zombie
        if w_obj.category == "SHOTGUN" and closest_dist < 320:
            dmg = int(dmg * 2.4)
        actual = closest_enemy.damage(dmg, part=hit_part)
        if hit_part == "head":
            sound.play("ricochet.wav")
        if not closest_enemy.alive:
            on_enemy_killed(closest_enemy, headshot=(hit_part == "head"))
        elif hit_part == "head":
            notice(f"HEADSHOT! -{int(actual)} HP")
    game_view.spawn_tracer(hit_pos)


def update_zombie_spawner(dt):
    """Điều phối xuất hiện Zombie theo đợt (Sinh tồn) hoặc tập kích giữa hiệp (Hỗn chiến)."""
    global zombies_to_spawn, zombie_spawn_timer, hybrid_zombie_timer, hybrid_zombies_spawned
    if game_state != "ROUND" or not player.alive:
        return

    alive_zombies = sum(1 for e in enemies if e.alive and getattr(e, "is_zombie", False))
    if selected_mode_id == "ZOMBIE":
        if zombies_to_spawn > 0 and alive_zombies < 14:
            zombie_spawn_timer -= dt
            if zombie_spawn_timer <= 0:
                batch = min(2 if zombie_wave >= 2 else 1, zombies_to_spawn, 14 - alive_zombies)
                for _ in range(batch):
                    spawn_single_zombie(zombie_wave)
                    zombies_to_spawn -= 1
                zombie_spawn_timer = max(0.75, 2.2 - zombie_wave * 0.12)
    elif selected_mode_id == "HYBRID":
        max_hybrid = 4 + current_diff()["zombie_extra"] * 2
        if hybrid_zombies_spawned < max_hybrid and alive_zombies < 5:
            hybrid_zombie_timer -= dt
            if hybrid_zombie_timer <= 0:
                spawn_single_zombie(max(1, round_number // 2 + 1))
                hybrid_zombies_spawned += 1
                hybrid_zombie_timer = random.uniform(9.0, 13.5)
                notice("CẢNH BÁO: ZOMBIE XUẤT HIỆN TẬP KÍCH!", 1.8)


def update_enemies(dt):
    global hit_flash_timer
    if game_state != "ROUND" or not player.alive:
        return
    now = pygame.time.get_ticks() / 1000.0
    diff = current_diff()

    for e in enemies:
        if not e.alive:
            continue
        dx, dy = player.x - e.x, player.y - e.y
        dist = math.hypot(dx, dy)
        e.angle = math.atan2(dy, dx)

        if getattr(e, "is_zombie", False):
            # Zombie luôn săn đuổi người chơi trên toàn bản đồ (trượt vòng qua tường mượt mà)
            e.roar_cd -= dt
            if e.roar_cd <= 0 and dist < 520:
                e.roar_cd = random.uniform(6.0, 12.0)
                sound.play("zombie_roar.wav")

            if dist > e.attack_range:
                e.move_smart(e.angle, e.speed, dt, walls)
            if dist <= e.attack_range + player.radius and now - e.last_melee >= e.attack_cooldown:
                if not line_blocked(e.x, e.y, player.x, player.y, walls):
                    e.last_melee = now
                    e.attack_anim = 1.0
                    hp_before = player.hp
                    player.damage(e.melee_damage)
                    if player.hp < hp_before:
                        hit_flash_timer = 0.20
                    kill_player_if_dead()
            e.update(dt)
            continue

        # AI Đặc nhiệm bắn súng
        if dist >= 1050:
            e.update(dt)
            continue

        blocked = line_blocked(e.x, e.y, player.x, player.y, walls) or smoke_blocks(e.x, e.y, player.x, player.y)
        if blocked:
            # Tiến dần áp sát nếu khuất tầm nhìn
            if dist < 680:
                e.move_smart(e.angle, e.speed * 0.75, dt, walls)
            e.update(dt)
            continue

        e.strafe_timer -= dt
        if e.strafe_timer <= 0:
            e.strafe_dir = -e.strafe_dir
            e.strafe_timer = random.uniform(1.0, 2.4)

        if dist > 430:
            e.move_smart(e.angle, e.speed, dt, walls)
        elif dist < 210:
            e.move_smart(e.angle + math.pi, e.speed * 0.85, dt, walls)
        else:
            e.move_smart(e.angle + e.strafe_dir * (math.pi * 0.5), e.speed * 0.65, dt, walls)

        if now - e.last_shot >= e.fire_delay:
            e.last_shot = now
            e.muzzle_flash_timer = 0.1
            hit_prob = max(0.16, min(0.82, 0.72 - dist / 1350.0 + diff["bot_acc_bonus"]))
            if random.random() <= hit_prob:
                hp_before = player.hp
                rnd = random.random()
                raw_dmg = 48 if rnd < 0.12 else (16 if rnd > 0.82 else 22)
                player.damage(int(raw_dmg * diff["dmg_mult"]))
                if player.hp < hp_before:
                    hit_flash_timer = 0.15
                kill_player_if_dead()
        e.update(dt)


def draw_pickup_prompt():
    item, _ = get_nearest_dropped_weapon(90)
    if not item:
        return
    w_name = WEAPON_NAMES.get(item["id"], item["id"])
    text = f"Bấm [F] nhặt {w_name} ({item['magazine']}/{item['reserve']})"
    tw, th = font_small.size(text)
    rect = pygame.Rect(WIDTH // 2 - tw // 2 - 14, HEIGHT - 180, tw + 28, th + 10)
    pygame.draw.rect(screen, (20, 24, 32), rect, border_radius=6)
    pygame.draw.rect(screen, (255, 215, 0), rect, 2, border_radius=6)
    draw_text(text, font_small, (255, 255, 255), center=rect.center)


def draw_round_end_banner():
    secs = max(0.0, round_end_timer)
    won = pending_winner == "PLAYER"
    if selected_mode_id == "ZOMBIE":
        title = f"HOÀN THÀNH ĐỢT {zombie_wave - 1}!"
        sub = f"Đợt {zombie_wave} chuẩn bị sau {secs:.1f}s"
    else:
        title = "THẮNG HIỆP!" if won else "THUA HIỆP!"
        sub = f"Hiệp tiếp theo sau {secs:.1f}s"
    color = (90, 230, 130) if won else (255, 100, 100)
    draw_text(title, font_big, color, center=(WIDTH // 2, 140))
    draw_text(sub, font_mid, (255, 230, 120), center=(WIDTH // 2, 176))
    if player.alive:
        draw_text("Nhặt súng rơi: [F]   ·   Vứt súng: [G]", font_small, (200, 208, 224), center=(WIDTH // 2, HEIGHT - 135))
    bw, bh = 320, 8
    bx, by = WIDTH // 2 - bw // 2, 202
    pygame.draw.rect(screen, (40, 46, 62), (bx, by, bw, bh), border_radius=4)
    total_t = 3.5 if selected_mode_id == "ZOMBIE" else ROUND_END_TIME
    pygame.draw.rect(screen, color, (bx, by, int(bw * min(1.0, secs / total_t)), bh), border_radius=4)


def toggle_scope_ads():
    global scope_level
    if holding_knife():
        melee_attack(is_right_click=True)
    elif player.weapon in SCOPE_WEAPONS and held_item is None and player.alive and not player.reloading:
        n = len(SCOPE_CONFIG[player.weapon]["levels"])
        scope_level = (scope_level + 1) % (n + 1)
        player.scoped = scope_level > 0


# XỬ LÝ SỰ KIỆN PHÍM & CHUỘT
def handle_keydown(key):
    global running
    in_play = game_state in ("BUY", "ROUND", "ROUND_END")
    free = in_play and not shop_open
    if key in (pygame.K_ESCAPE, pygame.K_p):
        if shop_open:
            toggle_shop(False)
        elif game_state == "MENU":
            if match_in_progress():
                menu_action("resume")
            elif not IS_WEB and key == pygame.K_ESCAPE:
                running = False
        else:
            go_to_menu()
    elif key == pygame.K_F12 and not IS_WEB:
        save_screenshot("manual")
    elif game_state == "MENU":
        if key == pygame.K_RETURN:
            menu_action("resume" if match_in_progress() else "start")
    elif key == pygame.K_n and game_state == "BUY":
        start_combat_phase()
    elif key == pygame.K_b and in_play:
        toggle_shop(not shop_open)
    elif key in (pygame.K_1, pygame.K_2, pygame.K_3) and in_play:
        cycle_slot(key - pygame.K_0)
    elif key in GRENADE_KEYS and free:
        equip_grenade(GRENADE_KEYS[key])
    elif key in (pygame.K_v, pygame.K_z) and free:
        toggle_scope_ads()
    elif key in (pygame.K_x, pygame.K_h) and in_play:
        player.righthand = not getattr(player, "righthand", True)
        notice("TAY CẦM: PHẢI" if player.righthand else "TAY CẦM: TRÁI", 1.5)
    elif key == pygame.K_SPACE and free:
        player.jump()
    elif key == pygame.K_g and free and player.alive:
        drop_current_weapon()
    elif key == pygame.K_f and free and player.alive:
        pickup_nearest_weapon()
    elif key == pygame.K_r and free and player.weapon in GUNS and not player.reloading:
        if player.magazine < player.max_magazine and player.reserve > 0:
            start_reload()
    elif key == pygame.K_RETURN and game_state == "MATCH_OVER":
        restart_match()


def handle_mouse_down(event):
    global scope_level, selected_mode_id, selected_diff_id, resume_state
    if event.button == 1:
        if game_state == "MENU":
            mode_rects, diff_rects, map_rects, action_rects = menu_layout()
            for rect, mid in mode_rects:
                if rect.collidepoint(event.pos):
                    if selected_mode_id != mid:
                        selected_mode_id = mid
                        resume_state = None
                    return
            for rect, did in diff_rects:
                if rect.collidepoint(event.pos):
                    selected_diff_id = did
                    return
            for rect, map_id in map_rects:
                if rect.collidepoint(event.pos):
                    if get_active_map_id() != map_id:
                        set_active_map(map_id)
                        resume_state = None
                    return
            for rect, _label, action, _col in action_rects:
                if rect.collidepoint(event.pos):
                    menu_action(action)
                    return
        elif shop_open:
            handle_shop_click(event.pos, button=1)
        elif game_state == "ROUND":
            player_shoot()
    elif event.button == 3:
        if shop_open:
            handle_shop_click(event.pos, button=3)
        elif game_state in ("BUY", "ROUND", "ROUND_END"):
            toggle_scope_ads()


# VÒNG LẶP GAME BẤT ĐỒNG BỘ (TƯƠNG THÍCH PYGBAG WEB & DESKTOP)
async def main():
    global running, game_state, buy_timer, round_timer, round_end_timer
    global notice_timer, bomb_fuse, held_item, hit_flash_timer, knife_swing
    global match_over_screenshot_taken, shop_open

    reset_round()
    game_state = "MENU"
    set_mouse_mode(True)

    while running:
        # Trên Web pygbag: await asyncio.sleep(0) đã đồng bộ đúng 60Hz của trình duyệt, không gọi SDL_Delay lần 2
        dt = min(0.05, clock.tick(0 if IS_WEB else FPS) / 1000.0)
        in_play = game_state in ("BUY", "ROUND", "ROUND_END")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                handle_keydown(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                handle_mouse_down(event)

        if game_state == "ROUND" and not shop_open and player.alive and not player.reloading:
            if player.weapon in AUTO_GUNS and pygame.mouse.get_pressed()[0]:
                player_shoot()

        notice_timer = max(0.0, notice_timer - dt)

        if game_state == "BUY":
            buy_timer -= dt
            if buy_timer <= 0:
                start_combat_phase()

        if shop_open and game_state != "BUY":
            toggle_shop(False)

        if game_state not in ("MATCH_OVER", "MENU"):
            if not shop_open:
                update_player_movement(dt)
                mdx, mdy = consume_look_delta(dt)
                player.look(mdx, mdy, sensitivity=0.0025 / scope_zoom)
            else:
                pygame.mouse.get_rel()
            player.update_vertical(dt)
            update_scope(dt)

            if player.reloading and pygame.time.get_ticks() / 1000.0 - player.reload_start >= player.reload_time:
                amt = min(player.max_magazine - player.magazine, player.reserve)
                player.magazine += amt
                player.reserve -= amt
                player.reloading = False
                store_ammo()

            player.recoil = max(0.0, player.recoil - dt * 0.25)
            hit_flash_timer = max(0.0, hit_flash_timer - dt)
            knife_swing = max(0.0, knife_swing - dt)
            player.knife_swing = knife_swing
            game_view.update_vfx(dt)

            if game_state != "BUY":
                update_zombie_spawner(dt)
                update_enemies(dt)

            update_projectiles(dt)
            update_zones(dt)
            update_supply_drops(dt)

            if game_state == "ROUND" and held_item == "BOMB" and player.alive:
                bomb_fuse -= dt
                if bomb_fuse <= 0:
                    grenades["BOMB"] = max(0, grenades["BOMB"] - 1)
                    held_item = None
                    explode(player.x, player.y)

            if game_state == "ROUND":
                round_timer -= dt
                if not player.alive:
                    end_round(False)
                elif selected_mode_id == "ZOMBIE":
                    alive_cnt = sum(1 for e in enemies if e.alive)
                    if zombies_to_spawn <= 0 and alive_cnt == 0:
                        end_round(True)
                    elif round_timer <= 0:
                        end_round(True)
                else:
                    if round_timer <= 0:
                        end_round(False)
                    elif not any(e.alive for e in enemies):
                        end_round(True)
            elif game_state == "ROUND_END":
                round_end_timer -= dt
                if round_end_timer <= 0:
                    reset_round(pending_winner)

        if game_state == "MENU":
            draw_menu()
        else:
            smokes = [z for z in zones if z.get("kind") == "SMOKE"]
            fires = [z for z in zones if z.get("kind") == "FIRE"]
            view_state = "ROUND" if game_state == "ROUND_END" else game_state

            header_title = None
            header_sub = None
            buy_sub = None
            match_sum = None
            if selected_mode_id == "ZOMBIE":
                alive_cnt = sum(1 for e in enemies if e.alive) + zombies_to_spawn
                header_title = f"ĐỢT {zombie_wave}"
                header_sub = f"Còn {alive_cnt} Zombie" if game_state == "ROUND" else f"Chuẩn bị ({int(max(0, buy_timer))}s)"
                buy_sub = f"CHUẨN BỊ ĐỢT ZOMBIE {zombie_wave}"
                match_sum = f"Dừng bước ở Đợt {zombie_wave}  ·  Đã diệt {zombie_kills_match} Zombie  ·  Kỷ lục: Đợt {profile.get('best_wave', 0)}"
            elif selected_mode_id == "HYBRID":
                alive_z = sum(1 for e in enemies if e.alive and getattr(e, "is_zombie", False))
                alive_b = sum(1 for e in enemies if e.alive and not getattr(e, "is_zombie", False))
                if game_state == "ROUND":
                    header_sub = f"{int(max(0, round_timer))}s · {alive_b} Bot · {alive_z} Zombie"
                buy_sub = f"HIỆP {round_number} · {get_active_map()['name']}"
                match_sum = f"Tỉ số {player_score} - {enemy_score}  ·  Hạ gục {kills} ({zombie_kills_match} Zombie)"

            game_view.render_frame(
                player,
                [] if game_state == "BUY" else enemies,
                walls,
                renderer,
                minimap,
                hud,
                get_camera_horizon(),
                view_state,
                round_timer,
                buy_timer,
                player_score,
                enemy_score,
                dt=dt,
                hit_flash_timer=hit_flash_timer,
                match_winner=match_winner,
                smokes=smokes,
                fires=fires,
                bomb_fuse=(bomb_fuse if held_item == "BOMB" else None),
                dropped_weapons=dropped_weapons,
                supply_drops=supply_drops,
                header_title=header_title,
                header_sub=header_sub,
                buy_subtitle=buy_sub,
                match_summary=match_sum,
            )
            if in_play:
                draw_effects()
                if player.alive:
                    if held_item:
                        draw_held_item()
                    elif player.weapon in SCOPE_WEAPONS:
                        cur_ads = getattr(player, "ads", 0.0)
                        is_sniper_dark = SCOPE_CONFIG[player.weapon]["dark"]
                        if cur_ads > (0.78 if is_sniper_dark else 0.48):
                            draw_scope()
                            if is_sniper_dark:
                                hud.draw(
                                    screen, player, player_score, enemy_score, round_timer,
                                    header_title=header_title, header_sub=header_sub,
                                )
                draw_weapon_slots()
                if player.alive and not shop_open:
                    draw_pickup_prompt()
                    if IS_WEB and not _web_pointer_locked:
                        draw_text(
                            "Click chuột vào màn hình để khóa tâm xoay 360°  ·  [P]/[ESC]: Tạm dừng",
                            font_tiny, (255, 225, 120), center=(WIDTH // 2, HEIGHT - 16),
                        )
                if game_state == "ROUND_END":
                    draw_round_end_banner()

        if shop_open:
            draw_shop()
        draw_notice()

        if game_state == "MATCH_OVER" and not match_over_screenshot_taken:
            save_screenshot("match_over")
            match_over_screenshot_taken = True

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
