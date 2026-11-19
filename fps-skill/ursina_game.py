"""
=============================================================================
  URSINA 3D SHOOTER — Súng 3D thủ công (không cần file .obj)
  - Súng ghép từ nhiều Entity hình hộp + hình trụ (cube/cylinder)
  - Tay cầm Roblox-style màu vàng da
  - Muzzle flash (tia lửa đầu nòng) + hiệu ứng giật súng
  - SMOKE: địch ẩn trong khói → KHÔNG nhìn thấy, nhưng BẮN VẪN TRÚNG
=============================================================================
"""

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController

app = Ursina(
    title='3D Shooter',
    borderless=False,
    fullscreen=False,
    development_mode=False,
)
window.exit_button.visible = False

# =============================================================================
# WORLD
# =============================================================================
ground = Entity(
    model='plane',
    scale=(60, 1, 60),
    texture='white_cube',
    color=color.rgb(80, 90, 80),
    collider='box',
)

# Vài bức tường trang trí
for pos in [(-8, 1, 15), (8, 1, 15), (0, 1, 20)]:
    Entity(
        model='cube',
        color=color.rgb(100, 100, 110),
        position=pos,
        scale=(2, 4, 1),
        collider='box',
    )

# =============================================================================
# TARGET (bia bắn / kẻ địch)
# =============================================================================
# Giữ collider='box' để raycast trúng được
# Nhưng visible sẽ được ẩn khi nằm trong smoke
target = Entity(
    model='cube',
    color=color.red,
    position=(0, 1.5, 12),
    scale=(1.2, 2.4, 0.3),
    collider='box',
)
# Lưu màu gốc để restore sau khi ra khỏi smoke
target.original_color = color.red

# =============================================================================
# SMOKE
# =============================================================================
# collider=None  → raycast bắn xuyên qua như không có
# visible_self ẩn/hiện target khi target nằm trong vùng khói
smoke_radius = 3.5          # bán kính vùng khói (đơn vị Ursina)
smoke = Entity(
    model='sphere',
    color=color.rgba(200, 200, 200, 110),   # xám mờ, bán trong suốt
    position=(0, 1.5, 8),                   # khói nằm giữa player và target
    scale=smoke_radius * 2,                 # diameter
    collider=None,                          # <-- QUAN TRỌNG: đạn đi thẳng qua
    double_sided=True,
)

def point_in_smoke(pos, smk=smoke):
    """Trả về True nếu vị trí 'pos' nằm trong vùng cầu khói."""
    return distance(pos, smk.position) < smoke_radius

def ray_crosses_smoke(origin, direction, dist, smk=smoke):
    """
    Kiểm tra xem tia bắn từ origin theo direction có đi qua vùng smoke không.
    Dùng phép chiếu điểm (closest point on ray to smoke center).
    """
    to_smoke = smk.position - origin
    proj_len = to_smoke.dot(direction)       # hình chiếu lên hướng bắn
    if proj_len < 0 or proj_len > dist:
        return False                         # khói ở sau lưng hoặc quá xa
    closest = origin + direction * proj_len
    return distance(closest, smk.position) < smoke_radius

# =============================================================================
# PLAYER
# =============================================================================
player = FirstPersonController()
player.speed           = 6
player.sensitivity     = (120, 120)
player.cursor.color    = color.white
player.cursor.scale    = 0.008
player.position        = (0, 0, 0)

# =============================================================================
# HELPER: gắn Entity con vào camera (FPS view)
# =============================================================================
def gun_part(model='cube', pos=(0,0,0), scale=(1,1,1), col=color.dark_gray, rot=(0,0,0)):
    return Entity(
        parent=camera,
        model=model,
        position=pos,
        scale=scale,
        color=col,
        rotation=rot,
        collider=None,
        always_on_top=False,
    )

# =============================================================================
# KHẨU SÚNG 3D (ghép từ nhiều Entity)
#   Tọa độ gốc (parent=camera) → góc nhìn thứ nhất
#   X: dương = phải, Y: dương = lên, Z: dương = tiến
# =============================================================================
GUN_X   =  0.38
GUN_Y   = -0.32
GUN_Z   =  0.72

GUN_COL  = color.rgb(45, 45, 50)
GRIP_COL = color.rgb(50, 35, 20)
RAIL_COL = color.rgb(60, 60, 68)

# Thân chính (receiver)
gun_body = gun_part(
    pos=(GUN_X, GUN_Y, GUN_Z),
    scale=(0.045, 0.055, 0.32),
    col=GUN_COL,
)
# Nòng súng (barrel)
gun_barrel = gun_part(
    model='cylinder',
    pos=(GUN_X, GUN_Y + 0.016, GUN_Z - 0.26),
    scale=(0.015, 0.21, 0.015),
    col=color.rgb(35, 35, 40),
    rot=(90, 0, 0),
)
# Thanh ray trên
gun_rail = gun_part(
    pos=(GUN_X, GUN_Y + 0.036, GUN_Z),
    scale=(0.018, 0.012, 0.28),
    col=RAIL_COL,
)
# Tay cầm (grip)
gun_grip = gun_part(
    pos=(GUN_X, GUN_Y - 0.055, GUN_Z + 0.08),
    scale=(0.038, 0.09, 0.04),
    col=GRIP_COL,
    rot=(12, 0, 0),
)
# Băng đạn (magazine)
gun_mag = gun_part(
    pos=(GUN_X, GUN_Y - 0.055, GUN_Z + 0.03),
    scale=(0.030, 0.085, 0.030),
    col=color.rgb(30, 30, 35),
    rot=(5, 0, 0),
)
# Cò súng
gun_trigger = gun_part(
    model='cylinder',
    pos=(GUN_X, GUN_Y - 0.028, GUN_Z + 0.045),
    scale=(0.005, 0.038, 0.005),
    col=color.rgb(55, 55, 60),
    rot=(90, 0, 0),
)
# Báng súng
gun_stock = gun_part(
    pos=(GUN_X - 0.003, GUN_Y - 0.006, GUN_Z + 0.19),
    scale=(0.040, 0.044, 0.08),
    col=GRIP_COL,
)
# Họng nòng
gun_muzzle = gun_part(
    model='cylinder',
    pos=(GUN_X, GUN_Y + 0.016, GUN_Z - 0.37),
    scale=(0.020, 0.025, 0.020),
    col=color.rgb(25, 25, 30),
    rot=(90, 0, 0),
)
# Tay trái đỡ nòng
hand_l = gun_part(
    pos=(GUN_X - 0.00, GUN_Y - 0.045, GUN_Z - 0.11),
    scale=(0.055, 0.045, 0.055),
    col=color.rgb(240, 200, 100),
)
# Tay phải cầm cò
hand_r = gun_part(
    pos=(GUN_X + 0.00, GUN_Y - 0.055, GUN_Z + 0.09),
    scale=(0.048, 0.055, 0.048),
    col=color.rgb(240, 200, 100),
)

GUN_PARTS = [gun_body, gun_barrel, gun_rail, gun_grip, gun_mag,
             gun_trigger, gun_stock, gun_muzzle, hand_l, hand_r]

# =============================================================================
# MUZZLE FLASH
# =============================================================================
muzzle_flash = Entity(
    parent=camera,
    model='sphere',
    color=color.yellow,
    position=(GUN_X, GUN_Y + 0.016, GUN_Z - 0.40),
    scale=0.06,
    enabled=False,
    collider=None,
)

# =============================================================================
# TRẠNG THÁI
# =============================================================================
GUN_IDLE_Z      = GUN_Z
GUN_KICK_Z      = GUN_Z + 0.06
can_shoot       = True
FIRE_RATE       = 0.12

# =============================================================================
# BẮN — cơ chế smoke xuyên đạn nhưng ẩn địch
# =============================================================================
def shoot():
    global can_shoot
    if not can_shoot:
        return
    can_shoot = False

    # --- Giật súng ---
    for part in GUN_PARTS:
        orig_z = part.z
        part.z = orig_z + (GUN_KICK_Z - GUN_IDLE_Z)
        part.animate('z', orig_z, duration=0.10, curve=curve.out_expo)

    # --- Muzzle flash ---
    muzzle_flash.enabled = True
    invoke(setattr, muzzle_flash, 'enabled', False, delay=0.05)

    # --- Raycast bình thường (smoke không có collider → xuyên qua) ---
    hit_info = raycast(
        origin=camera.world_position,
        direction=camera.forward,
        distance=200,
        ignore=[player],
    )

    if hit_info.hit and hit_info.entity == target:
        # Tính khoảng cách tới target
        hit_dist = distance(camera.world_position, target.world_position)
        # Kiểm tra tia bắn có đi qua smoke không
        in_smoke_shot = ray_crosses_smoke(
            camera.world_position,
            camera.forward,
            hit_dist,
        )

        if in_smoke_shot:
            # Bắn xuyên khói → vẫn trúng nhưng KHÔNG có visual feedback rõ ràng
            # (không blink vì không nhìn thấy địch)
            print('Bắn xuyên khói — trúng địch! (không nhìn thấy)')
        else:
            # Bắn rõ ràng → nhấp nháy đỏ
            target.blink(color.white, duration=0.12)
            print('Bắn trúng mục tiêu!')

    invoke(reset_shoot, delay=FIRE_RATE)

def reset_shoot():
    global can_shoot
    can_shoot = True

# =============================================================================
# UPDATE — mỗi frame: ẩn/hiện target dựa trên vị trí trong smoke
# =============================================================================
def update():
    # Địch trong smoke → ẩn hoàn toàn (người chơi không nhìn thấy)
    if point_in_smoke(target.position):
        target.visible = False
    else:
        target.visible = True

    # (Nếu player đứng trong smoke → tất cả mờ đi — tuỳ chọn)
    if point_in_smoke(camera.world_position):
        smoke.color = color.rgba(200, 200, 200, 200)   # dày hơn khi đứng trong
    else:
        smoke.color = color.rgba(200, 200, 200, 110)

# =============================================================================
# INPUT
# =============================================================================
def input(key):
    if key == 'left mouse down':
        shoot()
    if key == 'escape':
        application.quit()

app.run()
