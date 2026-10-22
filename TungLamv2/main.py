import math
import os
import random
import sys
import pygame
import sound

from settings import WIDTH, HEIGHT, FPS, ROUND_TIME, BUY_TIME
from game.player import Player
from game.enemy import Enemy
from game.map import walls, site_A, site_B, site_C, line_blocked
from game.weapon import get_weapon, get_weapon_damage
from graphics.renderer import Renderer
from graphics.minimap import Minimap
from graphics.weapon_skins import get_hud_icon, get_shop_icon, knife_scaled
from ui.hud import HUD
from ui.game_view import GameView

# KHỞI TẠO
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Lotus Tactical FPS")
clock = pygame.time.Clock()

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def save_screenshot(tag="manual"):
    filename = os.path.join(SCREENSHOT_DIR, f"{tag}_{pygame.time.get_ticks()}.png")
    pygame.image.save(screen, filename)
    print(f"[Screenshot] Đã lưu: {filename}")

def set_mouse_mode(gui):
    pygame.mouse.set_visible(gui)
    pygame.event.set_grab(not gui)
    pygame.mouse.get_rel()

player = Player()
renderer = Renderer()
minimap = Minimap()
hud = HUD()
game_view = GameView(screen, WIDTH, HEIGHT)

# VŨ KHÍ & TRANG BỊ
SIDEARMS = ["CLASSIC", "GHOST", "SHERIFF"]
PRIMARY_WEAPONS = ["AK-47", "M416", "GUARDIAN", "MP5", "UMP", "M014", "MAG-7", "M24", "AWM"]
GUNS = tuple(SIDEARMS + PRIMARY_WEAPONS)
AUTO_GUNS = ("AK-47", "M416", "MP5", "UMP", "MAG-7")

WEAPON_NAMES = {
    "KNIFE": "Dao", "CLASSIC": "Súng lục Classic", "GHOST": "Súng lục Ghost",
    "SHERIFF": "Súng lục Sheriff", "MP5": "SMG MP5", "UMP": "SMG UMP",
    "M014": "Shotgun M014", "MAG-7": "Shotgun MAG-7", "AK-47": "Súng trường AK-47",
    "M416": "Súng trường M416", "GUARDIAN": "Súng trường Guardian",
    "M24": "Súng tỉa M24", "AWM": "Súng tỉa AWM",
}

MAX_ARMOR = 50
current_secondary = "CLASSIC"
current_primary = None
owned = {"KNIFE", "CLASSIC"}
weapon_ammo = {}
dropped_weapons = []
bought_this_round = set()  # iid đã mua trong round này (cho phép bán lại)

# Dao cận chiến
KNIFE_RANGE, KNIFE_COOLDOWN, KNIFE_SWING_TIME = 200, 400, 0.28
last_melee, knife_swing = 0, 0.0
knife_view = knife_scaled(int(WIDTH * 0.42))
knife_idle = pygame.transform.rotate(knife_view, -45)

# Ống nhắm: scope_level 0 = tắt, 1.. = mức zoom
scope_level = 0
SCOPE_CONFIG = {
    "UMP": {"levels": [1.15], "dark": False},
    "MP5": {"levels": [1.15], "dark": False},
    "AK-47": {"levels": [1.25], "dark": False},
    "M416": {"levels": [1.25], "dark": False},
    "M24": {"levels": [2.5], "dark": True},
    "AWM": {"levels": [2.5, 5.0], "dark": True},
}
SCOPE_WEAPONS = tuple(SCOPE_CONFIG)

# Kinh tế
STARTING_MONEY, MAX_MONEY, WIN_REWARD = 800, 99000, 3250
LOSS_START, LOSS_STEP, LOSS_MAX = 1400, 500, 3400
loss_streak = 0
KILL_REWARDS = {"KNIFE": 1500, "SHOTGUN": 900, "SMG": 600, "PISTOL": 300,
                "RIFLE": 300, "GRENADE": 300, "AWM": (100, 300)}

# Lựu đạn
GRENADES = ("SMOKE", "MOLOTOV", "BOMB")
GRENADE_KEYS = {pygame.K_5: "SMOKE", pygame.K_6: "MOLOTOV", pygame.K_7: "BOMB"}
GRENADE_MAX = {"SMOKE": 2, "MOLOTOV": 2, "BOMB": 1}
GRENADE_LABEL = {"SMOKE": "Khói", "MOLOTOV": "Lửa", "BOMB": "Bom"}
GRENADE_COLORS = {"SMOKE": (180, 185, 195), "MOLOTOV": (240, 130, 40), "BOMB": (220, 60, 60)}
grenades = {"SMOKE": 0, "MOLOTOV": 0, "BOMB": 0}
held_item = None
projectiles = []
zones = []

GRAVITY, THROW_SPEED, THROW_VZ, EYE_H = 780, 560, 260, 32
SMOKE_TIME, SMOKE_RADIUS = 10.0, 130
FIRE_TIME, FIRE_RADIUS, FIRE_TICK = 3.0, 95, 0.25
BOMB_FUSE, BOMB_RADIUS = 5.0, 220
bomb_fuse = None

# CỬA HÀNG
ITEMS = {
    "LIGHT_ARMOR": ("Giáp nhẹ (+25 Giáp)", "Tăng giáp hấp thụ 50% sát thương, +25 giáp", 400),
    "ARMOR": ("Giáp nặng (+50 Giáp)", "Tăng giáp hấp thụ 50% sát thương, tối đa 50", 1000),
    "SMOKE": ("Smoke (Lựu đạn khói)", "Chạm đất tạo vùng khói trong 10 giây", 300),
    "MOLOTOV": ("Bom xăng", "Chạm đất tạo vùng lửa 3 giây · Thiêu đốt 1-2 HP", 400),
    "BOMB": ("Quả bom", "Cầm lên đếm ngược 5 giây rồi nổ (-50 HP, -50 Giáp)", 600),
    "CLASSIC": ("Classic", "Bán tự động · 12 viên/băng · Miễn phí", 0),
    "GHOST": ("Ghost", "Bán tự động · 15 viên/băng", 500),
    "SHERIFF": ("Sheriff", "Bán tự động · 6 viên/băng", 800),
    "UMP": ("UMP", "Tự động hoàn toàn · Băng 20 viên", 1000),
    "MP5": ("MP5", "Tự động · Băng 30 viên", 1600),
    "M014": ("M014", "Shotgun bán tự động · 5 viên/băng", 900),
    "MAG-7": ("MAG-7", "Shotgun · Băng 7 viên", 1500),
    "AK-47": ("AK-47", "Tự động · Băng 25 viên", 2900),
    "M416": ("M416", "Tự động · Băng 30 viên", 2900),
    "GUARDIAN": ("Guardian", "Súng trường bán tự động", 2700),
    "M24": ("M24", "Súng tỉa hạng nhẹ · 5 viên", 1100),
    "AWM": ("AWM", "Súng tỉa hạng nặng · 5 viên", 4500),
}
SHOP_TABS = {
    "TRANG BỊ": ["LIGHT_ARMOR", "ARMOR", "SMOKE", "MOLOTOV", "BOMB"],
    "SÚNG PHỤ": ["CLASSIC", "GHOST", "SHERIFF"],
    "SMG & SHOTGUN": ["UMP", "MP5", "M014", "MAG-7"],
    "SÚNG TRƯỜNG": ["AK-47", "M416", "GUARDIAN"],
    "SÚNG TỈA": ["M24", "AWM"],
}
SHOP_CATEGORIES = list(SHOP_TABS)
current_shop_tab = "TRANG BỊ"
shop_open = False

dim_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
dim_surface.fill((0, 0, 0, 160))

# FONT & THÔNG BÁO

def make_font(size, bold=False):
    return pygame.font.SysFont("segoeui,arial,dejavusans,freesans", size, bold=bold)

font_title, font_big, font_mid, font_small = make_font(64, True), make_font(30, True), make_font(22, True), make_font(17)
notice_text, notice_timer = "", 0.0

def notice(text, seconds=2.0):
    global notice_text, notice_timer
    notice_text = text
    notice_timer = seconds

def draw_text(text, font, color, **anchor):
    img = font.render(text, True, color)
    rect = img.get_rect(**anchor)
    screen.blit(img, rect)
    return rect

def draw_notice():
    if notice_timer > 0:
        draw_text(notice_text, font_mid, (255, 230, 120), center=(WIDTH // 2, 90))

# TIỀN & ĐẠN

def add_money(amount):
    player.money = min(MAX_MONEY, getattr(player, "money", 0) + amount)

def kill_reward(text, weapon_type=None):
    global kills
    kills += 1
    wt = weapon_type or player.weapon
    if wt == "AWM":
        reward = random.randint(*KILL_REWARDS["AWM"])
    else:
        kind = ("KNIFE" if wt == "KNIFE" else "SHOTGUN" if wt in ("M014", "MAG-7")
                else "SMG" if wt in ("MP5", "UMP") else "PISTOL" if wt in SIDEARMS
                else "GRENADE" if wt == "GRENADE" else "RIFLE")
        reward = KILL_REWARDS[kind]
    add_money(reward)
    notice(f"{text} (+${reward})")


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
    player.reloading = True
    player.reload_start = pygame.time.get_ticks() / 1000.0
    sound.play("reload.wav")

# TRẠNG THÁI TRẬN ĐẤU

def create_enemies(enemy_armor=25):
    return [Enemy(x, y, armor=enemy_armor)
            for x, y in [(400, 280), (540, 330), (1300, 280), (1400, 330), (1220, 820)]]

enemies = create_enemies()
game_state = "BUY"   # MENU / BUY / ROUND / ROUND_END / MATCH_OVER
resume_state = None
kills = 0
round_number = 1
round_timer, buy_timer = ROUND_TIME, BUY_TIME
player_score = enemy_score = 0
MATCH_WIN_SCORE = 13
match_winner = None
match_over_screenshot_taken = False

# Thời gian nghỉ sau khi kết thúc round (nhặt đồ) trước khi sang round mới
ROUND_END_TIME = 5.0
round_end_timer = 0.0
pending_winner = None  # "PLAYER" / "ENEMY": kết quả round vừa xong, dùng khi reset_round

spike_carried, spike_planted, spike_timer, SPIKE_TIME = True, False, 0, 35

hit_flash_timer, running = 0.0, True

# CAMERA & HÌNH HỌC

def get_camera_horizon():
    pitch_offset = math.tan(getattr(player, "pitch", 0.0)) * renderer.projection_plane * 0.45
    cam_offset = renderer.get_camera_offset(player) if hasattr(renderer, "get_camera_offset") else 0
    return max(-HEIGHT, min(HEIGHT * 2, int(HEIGHT // 2 + pitch_offset + cam_offset)))

def angle_diff(a, b):
    return math.atan2(math.sin(a - b), math.cos(a - b))

def holding_knife():
    return player.weapon == "KNIFE" and held_item is None

def can_reach(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1) < 1 or not line_blocked(x1, y1, x2, y2)

def seg_dist(px, py, x1, y1, x2, y2):
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    t = 0 if l2 == 0 else max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / l2))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))

def smoke_blocks(x1, y1, x2, y2):
    return any(z["kind"] == "SMOKE" and seg_dist(z["x"], z["y"], x1, y1, x2, y2) <= z["r"] * 0.8
               for z in zones)

def project(x, y, z=0.0):
    dx, dy = x - player.x, y - player.y
    dist = math.hypot(dx, dy)
    if dist < 1:
        return None
    rel = angle_diff(math.atan2(dy, dx), player.angle)
    if abs(rel) > (renderer.fov / 2 + 0.4):
        return None
    scale = renderer.projection_plane / dist
    return (WIDTH // 2 + math.tan(rel) * renderer.projection_plane,
            get_camera_horizon() + (EYE_H - z) * scale, scale)

def in_range_of(obj, x, y, r):
    """Đối tượng (còn sống) trong bán kính r và không bị tường chắn."""
    return obj.alive and math.hypot(obj.x - x, obj.y - y) <= r and can_reach(x, y, obj.x, obj.y)

def kill_player_if_dead():
    if player.hp <= 0:
        player.hp = 0
        player.alive = False

# RESET VÒNG / TRẬN

def reset_player(keep_guns=False, keep_armor=False):
    global current_primary, current_secondary, held_item, bomb_fuse, scope_level
    player.x, player.y = 880, 1050
    player.angle = -math.pi / 2
    player.pitch = 0.0
    player.hp = 100
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

def reset_round(winner=None):
    global enemies, round_timer, buy_timer, game_state, spike_carried, spike_planted
    global spike_timer, shop_open, scope_level, round_end_timer, pending_winner
    if winner == "PLAYER":
        reset_player(keep_guns=True, keep_armor=True)
        enemies = create_enemies(enemy_armor=0)
    else:
        reset_player()
        if winner is None:
            player.armor = 0
        enemies = create_enemies(enemy_armor=25)
    projectiles.clear()
    zones.clear()
    dropped_weapons.clear()
    bought_this_round.clear()
    round_timer = ROUND_TIME
    buy_timer = BUY_TIME
    round_end_timer = 0.0
    pending_winner = None
    game_state = "BUY"
    shop_open = False
    spike_carried = True
    spike_planted = False
    spike_timer = 0
    scope_level = 0
    player.scoped = False

def end_round(player_won):
    global player_score, enemy_score, round_number, game_state, match_winner, loss_streak
    global round_end_timer, pending_winner, shop_open
    round_number += 1
    if player_won:
        player_score += 1
        add_money(WIN_REWARD)
        loss_streak = max(0, loss_streak - 1)
        sound.play("ricochet.wav")
        notice(f"CHIẾN THẮNG VÒNG! +${WIN_REWARD}", 3.0)
    else:
        enemy_score += 1
        loss_streak += 1
        loss_bonus = min(LOSS_START + (loss_streak - 1) * LOSS_STEP, LOSS_MAX)
        planted_bonus = 300 if spike_planted else 0
        add_money(loss_bonus + planted_bonus)
        extra = f" +${planted_bonus} đặt Spike" if planted_bonus else ""
        notice(f"THẤT BẠI! +${loss_bonus}{extra} | Chuỗi thua: {loss_streak}", 3.0)
    if max(player_score, enemy_score) >= MATCH_WIN_SCORE:
        match_winner = "PLAYER" if player_won else "ENEMY"
        game_state = "MATCH_OVER"
        return
    # Không reset ngay: cho 5 giây nhặt đồ rồi mới sang round mới
    pending_winner = "PLAYER" if player_won else "ENEMY"
    round_end_timer = ROUND_END_TIME
    shop_open = False
    game_state = "ROUND_END"

def restart_match():
    global player_score, enemy_score, round_number, match_winner, match_over_screenshot_taken
    global kills, loss_streak, current_secondary, current_primary
    player_score = enemy_score = 0
    round_number = 1
    kills = 0
    loss_streak = 0
    match_winner = None
    match_over_screenshot_taken = False
    owned.clear()
    owned.update({"KNIFE", "CLASSIC"})
    current_secondary = "CLASSIC"
    current_primary = None
    dropped_weapons.clear()
    player.weapon = "CLASSIC"
    player.money = STARTING_MONEY
    reset_round()
    set_mouse_mode(False)

# MENU
menu_bg = pygame.Surface((WIDTH, HEIGHT))
menu_bg.fill((18, 22, 34))
pygame.draw.rect(menu_bg, (220, 60, 70), (WIDTH // 2 - 150, HEIGHT // 4 + 50, 300, 4))

def match_in_progress():
    return game_state == "MENU" and resume_state in ("BUY", "ROUND", "ROUND_END")

def menu_buttons():
    labels = [("TIẾP TỤC", "resume")] if match_in_progress() else []
    labels += [("TRẬN MỚI" if match_in_progress() else "VÀO TRẬN", "start"), ("THOÁT", "quit")]
    return [(pygame.Rect(WIDTH // 2 - 160, HEIGHT // 2 - 20 + i * 80, 320, 60), label, action)
            for i, (label, action) in enumerate(labels)]

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
    screen.blit(menu_bg, (0, 0))
    draw_text("LOTUS TACTICAL FPS", font_title, (240, 240, 245), center=(WIDTH // 2, HEIGHT // 4))
    draw_text("Chiến thuật · Bắn súng góc nhìn thứ nhất", font_small, (150, 160, 180),
              center=(WIDTH // 2, HEIGHT // 4 + 90))
    mouse = pygame.mouse.get_pos()
    for rect, label, _ in menu_buttons():
        hover = rect.collidepoint(mouse)
        pygame.draw.rect(screen, (220, 60, 70) if hover else (40, 46, 62), rect, border_radius=8)
        pygame.draw.rect(screen, (220, 60, 70), rect, 2, border_radius=8)
        draw_text(label, font_big, (255, 255, 255), center=rect.center)
    hint = (130, 140, 160)
    draw_text("WASD: di chuyển   Chuột: ngắm/bắn/đâm dao   [X]/[H]: Đổi tay cầm (Trái/Phải)   B: cửa hàng",
              font_small, hint, center=(WIDTH // 2, HEIGHT - 60))
    draw_text("1: dao   2: súng phụ   3: súng chính   R: nạp đạn   G: vứt súng   F: nhặt súng   "
              "Space: nhảy   Ctrl: ngồi   ESC: về menu",
              font_small, hint, center=(WIDTH // 2, HEIGHT - 32))

# TRANG BỊ, ĐỔI SLOT, VỨT / NHẶT SÚNG

def equip(weapon_id):
    global current_secondary, current_primary, held_item, scope_level
    held_item = None
    scope_level = 0
    player.scoped = False
    if weapon_id not in owned:
        notice(f"Chưa mua {WEAPON_NAMES.get(weapon_id, weapon_id).lower()} - ấn B để mở cửa hàng")
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
        notice(f"Chưa mua {GRENADE_LABEL[kind].lower()} - ấn B để mở cửa hàng")
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
    """Xóa súng khỏi kho và khỏi slot hiện tại."""
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
    """Vứt các súng cùng nhóm (súng chính / súng phụ) với w_id."""
    group = PRIMARY_WEAPONS if w_id in PRIMARY_WEAPONS else SIDEARMS
    for old in list(group):
        if old in owned:
            drop_weapon_to_ground(old)

def drop_current_weapon():
    if held_item is not None:
        notice("Không thể vứt vật phẩm này!")
        return
    if player.weapon not in GUNS or player.weapon not in owned:
        notice("Không thể vứt dao!")
        return
    w = player.weapon
    drop_weapon_to_ground(w)
    notice(f"Đã vứt {WEAPON_NAMES.get(w, w)}")
    equip_best_remaining()

def get_nearest_dropped_weapon(max_dist=90):
    best_item, best_dist = None, max_dist
    for item in dropped_weapons:
        d = math.hypot(player.x - item["x"], player.y - item["y"])
        if d <= best_dist and not line_blocked(player.x, player.y, item["x"], item["y"]):
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

# CỬA HÀNG

def toggle_shop(open_it):
    global shop_open
    if open_it and game_state != "BUY":
        notice("Đã hết thời gian mua đồ")
        return
    shop_open = open_it
    set_mouse_mode(open_it)

def shop_layout():
    pw = 820
    ph = min(590, HEIGHT - 20)
    panel = pygame.Rect((WIDTH - pw) // 2, (HEIGHT - ph) // 2, pw, ph)
    tab_w = (pw - 40) // len(SHOP_CATEGORIES)
    tabs = [(pygame.Rect(panel.x + 20 + i * tab_w, panel.y + 70, tab_w - 4, 38), cat)
            for i, cat in enumerate(SHOP_CATEGORIES)]
    rows = [(pygame.Rect(panel.x + 24, panel.y + 122 + i * 66, pw - 48, 58), iid)
            for i, iid in enumerate(SHOP_TABS[current_shop_tab])]
    return panel, tabs, rows

def buy_armor(iid, amount, label):
    if player.armor >= MAX_ARMOR:
        notice(f"Giáp đã đầy tối đa ({MAX_ARMOR})!")
        return
    player.money -= ITEMS[iid][2]
    player.armor = min(MAX_ARMOR, player.armor + amount)
    bought_this_round.add(iid)
    notice(f"Đã mua {label} +{amount} Giáp!")

def buy_item(iid):
    if game_state != "BUY":
        notice("Đã hết thời gian mua!")
        return
    name, _, price = ITEMS[iid]
    money = getattr(player, "money", 0)
    if iid in GUNS and iid in owned:
        equip(iid)
        notice(f"Đã trang bị {name}")
        return
    if money < price:
        notice(f"Không đủ tiền mua {name} (Thiếu ${price - money})")
        return
    if iid in GUNS:
        drop_slot_group(iid)
        player.money -= price
        owned.add(iid)
        w = get_weapon(iid)
        weapon_ammo[iid] = [w.max_magazine, w.reserve]
        equip(iid)
        bought_this_round.add(iid)
        notice(f"Đã mua thành công {name}!")
    elif iid in GRENADES:
        if grenades[iid] >= GRENADE_MAX[iid]:
            notice(f"Chỉ mang được tối đa {GRENADE_MAX[iid]} {GRENADE_LABEL[iid].lower()}!")
            return
        player.money -= price
        grenades[iid] += 1
        bought_this_round.add(iid)
        notice(f"Đã mua {name}! Ấn {5 + GRENADES.index(iid)} để cầm")
    elif iid == "LIGHT_ARMOR":
        buy_armor(iid, 25, "Giáp nhẹ")
    elif iid == "ARMOR":
        buy_armor(iid, 50, "Giáp nặng")

def sell_item(iid):
    """Bán lại vật phẩm đã mua trong round này (hoàn tiền 100%)."""
    if game_state != "BUY":
        notice("Chỉ có thể bán trong thời gian chuẩn bị!")
        return
    if iid not in bought_this_round:
        notice("Chỉ bán được vật phẩm mua trong round này!")
        return
    name, _, price = ITEMS[iid]
    if iid in GUNS:
        if iid not in owned:
            notice("Không còn vật phẩm để bán!")
            return
        remove_gun(iid)  # xóa khỏi kho, KHÔNG để rơi xuống đất (đã xử lý global bên trong)
        player.money += price
        bought_this_round.discard(iid)
        notice(f"Đã bán {name} +${price:,}")
        equip_best_remaining()
        if player.weapon not in owned:
            equip("KNIFE")
    elif iid in GRENADES:
        if grenades[iid] <= 0:
            notice("Không còn vật phẩm để bán!")
            return
        grenades[iid] -= 1
        player.money += price
        notice(f"Đã bán {name} +${price:,}")
    elif iid in ("LIGHT_ARMOR", "ARMOR"):
        amount = 25 if iid == "LIGHT_ARMOR" else 50
        if player.armor < amount:
            notice("Không thể bán giáp vì đã dùng rồi!")
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
    draw_text("CỬA HÀNG VŨ KHÍ & TRANG BỊ", font_big, (255, 255, 255), topleft=(panel.x + 24, panel.y + 18))
    draw_text(f"Tiền: ${money:,}", font_mid, (255, 210, 60), topright=(panel.right - 24, panel.y + 22))
    draw_text(f"Thời gian chuẩn bị: {max(0, int(buy_timer))} giây", font_small, (160, 170, 190),
              topleft=(panel.x + 24, panel.y + 50))
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
        draw_text(name, font_mid, (245, 245, 250), topleft=(rect.x + 18, rect.y + 8))
        draw_text(desc, font_small, (150, 160, 180), topleft=(rect.x + 18, rect.y + 32))
        skin_icon = get_shop_icon(iid)
        if skin_icon:
            screen.blit(skin_icon, skin_icon.get_rect(midright=(rect.right - 220, rect.centery)))
        if iid in GUNS and iid in owned:
            equipped = player.weapon == iid
            status = "ĐANG TRANG BỊ" if equipped else "TRANG BỊ (ĐÃ CÓ)"
            if sellable:
                status += "  [P2: BÁN]"
            draw_text(status, font_mid, (60, 220, 120) if equipped else (100, 200, 255),
                      midright=(rect.right - 18, rect.centery))
            continue
        is_gren = iid in GRENADES
        if is_gren:
            draw_text(f"Đang có: {grenades[iid]}/{GRENADE_MAX[iid]}", font_small, (150, 160, 180),
                      midright=(rect.right - 110, rect.centery))
        cost_str = "MIỄN PHÍ" if price == 0 else f"${price:,}"
        cost_col = (255, 205, 60) if money >= price else (225, 75, 75)
        if sellable:
            draw_text("[P2: BÁN]", font_small, (100, 230, 130),
                      midright=(rect.right - 110 if is_gren else rect.right - 18, rect.centery - 10))
            draw_text(cost_str, font_mid, cost_col, midright=(rect.right - 18, rect.centery + 10))
        else:
            draw_text(cost_str, font_mid, cost_col, midright=(rect.right - 18, rect.centery))
    draw_text("Chuột trái: Mua / Trang bị   |   Chuột phải: Bán (round này)   |   [B]/[ESC]: đóng",
              font_small, (140, 150, 170), center=(panel.centerx, panel.bottom - 20))

# VIEWMODEL & VẬT PHẨM NÉM

def draw_knife_view():
    if knife_swing > 0:
        s = math.sin((1 - knife_swing / KNIFE_SWING_TIME) * math.pi)
        rot = pygame.transform.rotate(knife_view, -45 - s * 55)
        screen.blit(rot, (WIDTH - int(WIDTH * 0.46) + int(s * 80), HEIGHT - int(HEIGHT * 0.52) - int(s * 60)))
    else:
        screen.blit(knife_idle, (WIDTH - int(WIDTH * 0.42) + 20, HEIGHT - int(HEIGHT * 0.48) + 30))

def draw_held_item():
    if not held_item:
        return
    cx, cy = WIDTH - 220, HEIGHT - 180
    pygame.draw.circle(screen, GRENADE_COLORS[held_item], (cx, cy), 36)
    pygame.draw.circle(screen, (30, 32, 40), (cx, cy), 36, 4)
    draw_text(GRENADE_LABEL[held_item], font_mid, (255, 255, 255), center=(cx, cy))

def draw_scope():
    cfg = SCOPE_CONFIG[player.weapon]
    zoom = cfg["levels"][scope_level - 1]
    cx, cy = WIDTH // 2, HEIGHT // 2
    surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    if not cfg["dark"]:  # SMG / Rifle: dây ngắm ADS
        gap, arm, col = 12, 20, (255, 255, 255, 200)
        for p1, p2 in (((cx - gap - arm, cy), (cx - gap, cy)), ((cx + gap, cy), (cx + gap + arm, cy)),
                       ((cx, cy - gap - arm), (cx, cy - gap)), ((cx, cy + gap), (cx, cy + gap + arm))):
            pygame.draw.line(surf, col, p1, p2, 2)
        pygame.draw.circle(surf, col, (cx, cy), 2)
    else:  # Sniper: viền tối + kính tròn + dây ngắm
        r = int(min(WIDTH, HEIGHT) * 0.28)
        col = (180, 220, 180, 255)
        surf.fill((0, 0, 0, 220))
        pygame.draw.circle(surf, (0, 0, 0, 0), (cx, cy), r)
        pygame.draw.circle(surf, (30, 30, 30, 255), (cx, cy), r, 6)
        pygame.draw.line(surf, col, (cx - r, cy), (cx + r, cy), 1)
        pygame.draw.line(surf, col, (cx, cy - r), (cx, cy + r), 1)
        pygame.draw.circle(surf, col, (cx, cy), 3)
    screen.blit(surf, (0, 0))
    draw_text(f"{zoom:.2g}x", font_mid, (220, 255, 180), topright=(WIDTH - 24, 24))


fx_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
SMOKE_PUFFS = [(0, -0.3, 0.7), (-0.5, -0.1, 0.55), (0.5, -0.1, 0.55),
               (-0.3, -0.7, 0.5), (0.3, -0.7, 0.5), (0, -1.1, 0.45)]

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
    notice("BOM NỔ!", 1.5)
    for e in enemies:
        if in_range_of(e, x, y, BOMB_RADIUS):
            e.armor = max(0, getattr(e, "armor", 0) - 50)
            e.damage(50, part="body")
            if not e.alive:
                kill_reward("Hạ gục bằng bom", "GRENADE")
    if in_range_of(player, x, y, BOMB_RADIUS):
        player.armor = max(0, player.armor - 50)
        player.hp -= 50
        hit_flash_timer = 0.3
        kill_player_if_dead()

def burn_area(x, y, r, dmg):
    """Gây sát thương lửa lên mọi mục tiêu trong vùng."""
    global hit_flash_timer
    for e in enemies:
        if in_range_of(e, x, y, r):
            e.damage(dmg, part="body")
            if not e.alive:
                kill_reward("Thiêu chết kẻ địch", "GRENADE")
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
        if line_blocked(p["x"], p["y"], nx, ny):
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
            zones.append({"kind": "FIRE", "x": p["x"], "y": p["y"], "r": FIRE_RADIUS,
                          "t": FIRE_TIME, "tick": FIRE_TICK})
            burn_area(p["x"], p["y"], FIRE_RADIUS, random.randint(1, 2))
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
                burn_area(z["x"], z["y"], z["r"], random.randint(1, 2))

def draw_effects():
    fx_surface.fill((0, 0, 0, 0))
    in_smoke = False
    for z in zones:
        if z["kind"] == "SMOKE" and math.hypot(z["x"] - player.x, z["y"] - player.y) < z["r"] * 0.8:
            in_smoke = True
        pr = project(z["x"], z["y"])
        if not pr or line_blocked(player.x, player.y, z["x"], z["y"]):
            continue
        sx, sy, scale = pr
        if z["kind"] == "SMOKE":
            life = max(0.0, min(1.0, (SMOKE_TIME - z["t"]) / 0.6, z["t"] / 1.5))
            r = int(min(900, z["r"] * scale * (0.4 + 0.6 * life)))
            for ox, oy, k in SMOKE_PUFFS:
                pygame.draw.circle(fx_surface, (175, 177, 182, int(215 * life)),
                                   (int(sx + ox * r), int(sy + oy * r)), max(1, int(r * k)))
        else:
            r = int(min(700, z["r"] * scale))
            pygame.draw.ellipse(fx_surface, (255, 80, 0, 70), (sx - r, sy - r * 0.2, 2 * r, r * 0.4))
            for _ in range(12):
                ox = random.uniform(-0.9, 0.9) * r
                oy = random.uniform(-0.15, 0.15) * r
                h = random.uniform(0.2, 0.6) * r
                col = random.choice([(255, 90, 20, 170), (255, 150, 30, 170), (255, 215, 60, 150)])
                pygame.draw.ellipse(fx_surface, col, (sx + ox - r * 0.12, sy + oy - h, r * 0.24, h))
    for p in projectiles:
        pr = project(p["x"], p["y"], p["z"])
        if pr and not line_blocked(player.x, player.y, p["x"], p["y"]):
            pygame.draw.circle(fx_surface, GRENADE_COLORS[p["kind"]],
                               (int(pr[0]), int(pr[1])), max(3, int(7 * pr[2])))
    if in_smoke:
        fx_surface.fill((170, 172, 178, 215))
    screen.blit(fx_surface, (0, 0))

# HUD VŨ KHÍ & TIỀN

def draw_weapon_slots():
    draw_text(f"${getattr(player, 'money', 0):,}", font_mid, (255, 210, 60), topleft=(24, 24))
    bonus = min(LOSS_START + max(0, loss_streak - 1) * LOSS_STEP, LOSS_MAX) if loss_streak else 0
    draw_text(f"Thưởng thua: ${bonus:,}", font_small, (220, 220, 220), topleft=(24, 54))
    # Đặt dưới minimap, kết thúc trước ô đạn để không đè viewmodel súng
    x, y = WIDTH - 235, 200
    sec = current_secondary if current_secondary in owned else None
    pri = current_primary if current_primary in owned else None
    rows = []
    # 1: Dao
    rows.append((1, "Dao", player.weapon == "KNIFE" and held_item is None, True, "KNIFE"))
    # 2: Súng lục
    sec_label = WEAPON_NAMES.get(sec, sec) if sec else "Súng phụ (Trống)"
    rows.append((2, sec_label, player.weapon == sec and held_item is None and sec is not None, sec is not None, sec))
    # 3: Súng chính
    pri_label = WEAPON_NAMES.get(pri, pri) if pri else "Súng chính (Trống)"
    rows.append((3, pri_label, player.weapon == pri and held_item is None and pri is not None, pri is not None, pri))
    # 4: Spike
    spike_label = "Spike (Đang mang)" if spike_carried else "Spike (Chưa nhặt)"
    rows.append((4, spike_label, False, spike_carried, "SPIKE"))
    # 5, 6, 7: Trang bị ném
    for i, g in enumerate(GRENADES):
        have = grenades[g] > 0
        label = f"{GRENADE_LABEL[g]} x{grenades[g]}" if have else f"{GRENADE_LABEL[g]} (chưa có)"
        rows.append((5 + i, label, held_item == g, have, g))
    for i, (key, label, active, have, w_id) in enumerate(rows):
        rect = pygame.Rect(x, y + i * 40, 220, 36)
        bg = (220, 60, 70) if active else ((40, 46, 62) if have else (28, 30, 38))
        pygame.draw.rect(screen, bg, rect, border_radius=6)
        color = (255, 255, 255) if have else (110, 115, 130)
        draw_text(f"{key}", font_mid, color, midleft=(rect.x + 10, rect.centery))
        if label:
            draw_text(label, font_small, color, midleft=(rect.x + 32, rect.centery))
        if have and w_id:
            skin_icon = get_hud_icon(w_id)
            if skin_icon:
                screen.blit(skin_icon, skin_icon.get_rect(midright=(rect.right - 8, rect.centery)))

# DI CHUYỂN, CẬN CHIẾN, BẮN SÚNG, AI KẺ ĐỊCH

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
    step = player.speed * (0.45 if slow else 1.0) * dt
    player.move(mx * step, my * step, walls)

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
        if abs(ang) <= 0.75 and not line_blocked(player.x, player.y, e.x, e.y):
            target, best = e, dist
    if target:
        actual = target.damage(80 if is_right_click else 50, part="body")
        sound.play("ricochet.wav")
        notice(f"Đâm dao: -{int(actual)} HP")
        if not target.alive:
            kill_reward("Hạ gục bằng Dao", "KNIFE")

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
    if now - player.last_shot < int(w_obj.fire_rate * 1000):
        return
    player.last_shot = now
    player.magazine -= 1
    player.recoil = min(player.recoil + 0.035, 0.14)
    sound.play("pistol.wav" if w_obj.category == "PISTOL" else "shotgun.wav")
    shot_angle = player.angle + (random.random() - 0.5) * player.recoil * 0.08
    wall_dist = renderer.raycast(player, shot_angle, walls)
    cx, cy = WIDTH // 2, HEIGHT // 2
    shot_y = cy - int(player.recoil * 100)
    hit_offset = {"head": 0.11, "body": 0.43, "legs": 0.82}
    closest_enemy, closest_dist, hit_part, hit_pos = None, float("inf"), "body", None
    for e in enemies:
        if not e.alive:
            continue
        dist = math.hypot(e.x - player.x, e.y - player.y)
        if (dist > wall_dist or dist > 1800 or line_blocked(player.x, player.y, e.x, e.y)
                or smoke_blocks(player.x, player.y, e.x, e.y)):
            continue
        h_ang = math.atan2(e.y - player.y, e.x - player.x)
        rel = angle_diff(h_ang, player.angle)
        if abs(rel) > renderer.fov / 2:
            continue
        sx = WIDTH // 2 + math.tan(rel) * renderer.projection_plane
        bh = max(10, min(400, int(renderer.projection_plane * 70 / dist)))
        bw = max(8, int(bh * 0.45))
        btop = get_camera_horizon() + int(bh * 0.5) - bh
        part = e.check_hit_3d(sx, btop, bw, bh, cx, shot_y)
        if part is None and abs(angle_diff(h_ang, shot_angle)) <= math.atan2(e.radius, dist):
            part = "head" if shot_y < btop + bh * 0.22 else ("body" if shot_y < btop + bh * 0.65 else "legs")
        if part is not None and dist < closest_dist:
            closest_enemy, closest_dist, hit_part = e, dist, part
            hit_pos = (sx, btop + bh * hit_offset[part])
    if closest_enemy:
        dmg = get_weapon_damage(player.weapon, closest_dist / 25.0, part=hit_part)
        actual = closest_enemy.damage(dmg, part=hit_part)
        part_vi = {"head": "ĐẦU", "body": "THÂN", "legs": "CHÂN"}[hit_part]
        if hit_part == "head":
            sound.play("ricochet.wav")
            notice(f"HEADSHOT! Trúng {part_vi}: -{int(actual)} HP")
        else:
            notice(f"Bắn trúng {part_vi}: -{int(actual)} HP")
        if not closest_enemy.alive:
            kill_reward(("HEADSHOT! " if hit_part == "head" else "") + "Hạ gục kẻ địch")
    game_view.spawn_tracer(hit_pos)

def update_enemies(dt):
    global hit_flash_timer
    if game_state != "ROUND" or not player.alive:
        return
    now = pygame.time.get_ticks() / 1000.0
    for e in enemies:
        if not e.alive:
            continue
        dx, dy = player.x - e.x, player.y - e.y
        dist = math.hypot(dx, dy)
        if dist >= 900:
            continue
        e.angle = math.atan2(dy, dx)
        if line_blocked(e.x, e.y, player.x, player.y) or smoke_blocks(e.x, e.y, player.x, player.y):
            continue
        if dist > 450:
            e.move(math.cos(e.angle) * e.speed * dt, math.sin(e.angle) * e.speed * dt, walls)
        elif dist < 220:
            e.move(-math.cos(e.angle) * e.speed * dt, -math.sin(e.angle) * e.speed * dt, walls)
        if now - e.last_shot >= e.fire_delay:
            e.last_shot = now
            if (pygame.time.get_ticks() % 1000) / 1000.0 <= max(0.20, 0.75 - dist / 1300):
                hp_before = player.hp
                rnd = random.random()
                player.damage(55 if rnd < 0.15 else (18 if rnd > 0.85 else 24))
                if player.hp < hp_before:
                    hit_flash_timer = 0.15

def draw_pickup_prompt():
    item, _ = get_nearest_dropped_weapon(90)
    if not item:
        return
    w_name = WEAPON_NAMES.get(item["id"], item["id"])
    text = f"Ấn [F] để nhặt {w_name} ({item['magazine']}/{item['reserve']})"
    tw, th = font_small.size(text)
    rect = pygame.Rect(WIDTH // 2 - tw // 2 - 14, HEIGHT - 180, tw + 28, th + 10)
    bg = pygame.Surface(rect.size, pygame.SRCALPHA)
    bg.fill((20, 24, 32, 220))
    screen.blit(bg, rect.topleft)
    pygame.draw.rect(screen, (255, 215, 0), rect, 2, border_radius=6)
    draw_text(text, font_small, (255, 255, 255), center=rect.center)

def draw_round_end_banner():
    """Đếm ngược 5 giây nhặt đồ sau khi kết thúc round."""
    secs = max(0.0, round_end_timer)
    won = pending_winner == "PLAYER"
    title = "BẠN THẮNG VÒNG!" if won else "BẠN THUA VÒNG!"
    color = (90, 230, 130) if won else (255, 100, 100)
    draw_text(title, font_big, color, center=(WIDTH // 2, 140))
    draw_text(f"Vòng mới bắt đầu sau {secs:.1f}s", font_mid, (255, 230, 120),
              center=(WIDTH // 2, 178))
    if player.alive:
        draw_text("Nhặt đồ: [F] nhặt súng   [G] vứt súng", font_small, (200, 205, 220),
                  center=(WIDTH // 2, HEIGHT - 140))
    # Thanh tiến trình
    bw, bh = 320, 8
    bx, by = WIDTH // 2 - bw // 2, 202
    pygame.draw.rect(screen, (40, 46, 62), (bx, by, bw, bh), border_radius=4)
    pygame.draw.rect(screen, color, (bx, by, int(bw * secs / ROUND_END_TIME), bh), border_radius=4)

# XỬ LÝ SỰ KIỆN

def handle_keydown(key):
    global running, spike_carried, spike_planted, spike_timer
    in_play = game_state in ("BUY", "ROUND", "ROUND_END")
    free = in_play and not shop_open  # đang chơi, shop đóng
    if key == pygame.K_ESCAPE:
        if shop_open:
            toggle_shop(False)
        elif game_state == "MENU":
            running = False
        else:
            go_to_menu()
    elif key == pygame.K_F12:
        save_screenshot("manual")
    elif game_state == "MENU":
        if key == pygame.K_RETURN:
            menu_action("resume" if match_in_progress() else "start")
    elif key == pygame.K_b and in_play:
        toggle_shop(not shop_open)
    elif key in (pygame.K_1, pygame.K_2, pygame.K_3) and in_play:
        cycle_slot(key - pygame.K_0)
    elif key in GRENADE_KEYS and free:
        equip_grenade(GRENADE_KEYS[key])
    elif key in (pygame.K_x, pygame.K_h) and in_play:
        player.righthand = not getattr(player, "righthand", True)
        hand_name = "TAY PHẢI (cl_righthand 1)" if player.righthand else "TAY TRÁI (cl_righthand 0)"
        notice(f"HƯỚNG CẦM SÚNG / DAO: {hand_name}", 2.0)
    elif key == pygame.K_SPACE and free:
        player.jump()
    elif key == pygame.K_g and free and player.alive:
        drop_current_weapon()
    elif key == pygame.K_f and free and player.alive:
        pickup_nearest_weapon()
    elif key == pygame.K_r and free and player.weapon in GUNS and not player.reloading:
        if player.magazine < player.max_magazine and player.reserve > 0:
            start_reload()
    elif key == pygame.K_4 and game_state == "ROUND" and not shop_open and spike_carried:
        if any(s.collidepoint(player.x, player.y) for s in (site_A, site_B, site_C)):
            spike_carried = False
            spike_planted = True
            spike_timer = 0
            notice("ĐÃ ĐẶT SPIKE! Bảo vệ Spike trong 35 giây!", 3.0)
    elif key == pygame.K_RETURN and game_state == "MATCH_OVER":
        restart_match()

def handle_mouse_down(event):
    global scope_level
    if event.button == 1:
        if game_state == "MENU":
            for rect, _label, action in menu_buttons():
                if rect.collidepoint(event.pos):
                    menu_action(action)
                    break
        elif shop_open:
            handle_shop_click(event.pos, button=1)
        elif game_state == "ROUND":
            player_shoot()
    elif event.button == 3:
        if shop_open:
            handle_shop_click(event.pos, button=3)  # chuột phải trong shop = bán
        elif game_state == "ROUND":
            if holding_knife():
                melee_attack(is_right_click=True)
            elif player.weapon in SCOPE_WEAPONS and held_item is None and player.alive:
                n = len(SCOPE_CONFIG[player.weapon]["levels"])
                scope_level = (scope_level + 1) % (n + 1)  # 0 → 1 → ... → 0
                player.scoped = (scope_level > 0)

# KHỞI ĐỘNG & VÒNG LẶP CHÍNH
reset_round()
game_state = "MENU"
set_mouse_mode(True)

while running:
    dt = clock.tick(FPS) / 1000.0
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
            game_state = "ROUND"
            round_timer = ROUND_TIME
            notice("VÒNG ĐẤU BẮT ĐẦU!", 2.0)
    if shop_open and game_state != "BUY":
        toggle_shop(False)
    if game_state not in ("MATCH_OVER", "MENU"):
        if not shop_open:
            update_player_movement(dt)
            player.look(*pygame.mouse.get_rel(), sensitivity=0.0025)
        player.update_vertical(dt)
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
        if game_state != "BUY":  # địch bị chặn bởi barrier trong buy phase
            update_enemies(dt)
        update_projectiles(dt)
        update_zones(dt)
        if game_state == "ROUND" and held_item == "BOMB" and player.alive:
            bomb_fuse -= dt
            if bomb_fuse <= 0:
                grenades["BOMB"] -= 1
                held_item = None
                explode(player.x, player.y)
        if game_state == "ROUND":
            if not spike_planted:
                round_timer -= dt
                if round_timer <= 0:
                    end_round(False)
            else:
                spike_timer += dt
                if spike_timer >= SPIKE_TIME:
                    end_round(True)
            if game_state == "ROUND":
                if not player.alive:
                    end_round(False)
                elif not any(e.alive for e in enemies):
                    end_round(True)
        elif game_state == "ROUND_END":
            # Giai đoạn nghỉ: được di chuyển, nhặt/vứt súng; hết 5 giây mới sang round mới
            round_end_timer -= dt
            if round_end_timer <= 0:
                reset_round(pending_winner)
    if game_state == "MENU":
        draw_menu()
    else:
        smokes = [z for z in zones if z.get("kind") == "SMOKE"]
        fires = [z for z in zones if z.get("kind") == "FIRE"]
        # GameView chỉ biết BUY/ROUND/MATCH_OVER -> ROUND_END vẽ như ROUND
        view_state = "ROUND" if game_state == "ROUND_END" else game_state
        game_view.render_frame(
            player, [] if game_state == "BUY" else enemies, walls, renderer, minimap, hud,
            get_camera_horizon(), view_state, round_timer, buy_timer,
            player_score, enemy_score, spike_carried, spike_planted,
            spike_timer, SPIKE_TIME, hit_flash_timer, match_winner,
            smokes=smokes, fires=fires,
            bomb_fuse=(bomb_fuse if held_item == "BOMB" else None),
            dropped_weapons=dropped_weapons,
        )
        if in_play:
            draw_effects()
            if player.alive:
                if held_item:
                    draw_held_item()
                elif scope_level > 0 and player.weapon in SCOPE_WEAPONS:
                    draw_scope()
            draw_weapon_slots()
            if player.alive and not shop_open:
                draw_pickup_prompt()
            if game_state == "ROUND_END":
                draw_round_end_banner()
        if game_state == "MATCH_OVER":
            draw_text("Enter: Chơi lại   |   ESC: Về menu", font_small, (220, 220, 230),
                      center=(WIDTH // 2, HEIGHT - 40))
        if shop_open:
            draw_shop()
        draw_notice()
    if game_state == "MATCH_OVER" and not match_over_screenshot_taken:
        save_screenshot("match_over")
        match_over_screenshot_taken = True
    pygame.display.flip()

pygame.quit()
sys.exit()