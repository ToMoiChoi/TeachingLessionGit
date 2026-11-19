# 🎮 CyberEsc - Cyberpunk 2D Platformer

**CyberEsc** là một tựa game nhập vai hành động 2D phong cách Cyberpunk được xây dựng bằng **Python** và thư viện **Pygame-CE**. Dự án được thiết kế theo kiến trúc chia tách mô-đun (Gameplay & Rendering) giúp dễ dàng bảo trì và mở rộng các màn chơi.

---

## 📂 Cấu Trúc Thư Mục Chuẩn (Project Structure)

Để game vận hành chính xác và tránh các lỗi `ImportError`, dự án cần được sắp xếp theo cấu trúc thư mục phẳng dưới đây:

```text
cyberesc/
├── README.md                 # Tài liệu hướng dẫn dự án
├── main.py                   # Điểm khởi chạy game (Game Entry Point)
├── game_engine.py            # Lớp cầu nối ủy quyền (Engine Bridge)
├── game_engine_gameplay.py   # Quản lý toàn bộ Logic & Trạng thái game
├── game_engine_layout.py     # Quản lý toàn bộ Giao diện & Đồ họa (Renderer)
├── config.py                 # Cấu hình màu sắc, hằng số hệ thống
├── player.py                 # Lớp nhân vật chính (Player)
├── Enemy.py                  # Lớp kẻ thù & Boss
├── weapon.py                 # Hệ thống vũ khí (Blaster, Shotgun, Rifle)
├── powerups.py               # Vật phẩm hỗ trợ (HP, DMG, Speed, Ammo)
├── particle.py               # Hiệu ứng hạt (Particle Effects)
├── cosmetics.py              # Trang phục & Đồ trang trí nhân vật
├── menu.py                   # Quản lý Menu & Cửa hàng (Shop)
├── levels/                   # Thư mục chứa các màn chơi
│   ├── __init__.py
│   ├── lv1.py
│   ├── lv2.py
│   └── ... (lv3.py - lv8.py)
└── Sounds/                   # Thư mục chứa âm thanh game
```

> **⚠️ Lưu ý quan trọng:** Không tạo thư mục nào có tên là `game_engine`. Tất cả các file `.py` thuộc Engine phải nằm ở thư mục gốc cùng cấp với `main.py`.

---

## 🛠️ Yêu Cầu Hệ Thống & Cài Đặt

### Yêu cầu
* **Python 3.10+** (Khuyên dùng Python 3.12 hoặc mới hơn)
* **Pygame-CE** (Pygame Community Edition)

### Cài đặt môi trường
Mở Terminal / Command Prompt và chạy lệnh cài đặt:

```bash
pip install pygame-ce
```

### Chạy Game
Chạy file `main.py` từ thư mục gốc của dự án:

```bash
python3 main.py
```

---

## 🕹️ Điều Khiển Game (Controls)

| Thao tác | Phím bấm / Chuột |
| :--- | :--- |
| **Di chuyển** | `A` / `D` hoặc Phím Mũi tên `Left` / `Right` |
| **Nhảy** | `W` / `SPACE` / Phím Mũi tên `Up` |
| **Bắn súng** | `Chuột trái` (hướng theo con trỏ chuột) hoặc Phím `K` |
| **Chém kiếm** | `Chuột phải` hoặc Phím `J` |
| **Đổi vũ khí** | Phím `1` (Blaster), `2` (Shotgun), `3` (Rifle) |
| **Tạm dừng / Menu** | Phím `ESC` |

---

## 🏗️ Kiến Trúc Mã Nguồn (Architecture Overview)

Dự án sử dụng mô hình thiết kế phân tách chức năng:

1. **`game_engine_gameplay.py` (`GameplayManager`)**:
   * Quản lý trạng thái màn chơi, camera theo dõi nhân vật.
   * Xử lý va chạm (Collisions) giữa đạn, nhân vật, quái vật và chướng ngại vật.
   * Nạp động (Dynamic Import) các màn chơi từ thư mục `levels/lvX.py`.
   * Quản lý chỉ số nâng cấp (Upgrades) và mua sắm trang phục (Cosmetics).

2. **`game_engine_layout.py` (`LayoutRenderer`)**:
   * Đảm nhận toàn bộ nhiệm vụ vẽ (Rendering) nhân vật, đạn, quái, boss, địa hình.
   * Hiển thị bảng HUD chỉ số (HP, Ammo, Coins, Weapon, Active Buffs).
   * Vẽ màn hình thông báo thắng (Victory Overlay) và Menu hệ thống.

3. **`game_engine.py` (`GameEngine`)**:
   * Đóng vai trò làm Wrapper/Bridge kết nối `GameplayManager` và `LayoutRenderer`.
   * Sử dụng cơ chế deferred import và `__getattr__` để loại bỏ hoàn toàn lỗi vòng lặp import (Circular Import).