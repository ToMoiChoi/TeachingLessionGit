# TÀI LIỆU KỸ THUẬT VÀ THIẾT KẾ GAME: LOTUS TACTICAL FPS (TUNGLAM FPS)

---

## 1. TỔNG QUAN DỰ ÁN (OVERVIEW)

* **Tên dự án:** Lotus Tactical FPS (TungLam v2 / v3)
* **Thể loại:** First-Person Shooter (FPS) Chiến thuật, Bắn súng góc nhìn thứ nhất kết hợp Raycasting / Pseudo-3D & Procedural 3D.
* **Cảm hứng thiết kế:**
  * Lối chơi chiến thuật đặt bom, hệ thống bombsite 3 site (Site A, B, C) lấy cảm hứng từ bản đồ **Lotus (Valorant)** và nhịp độ súng của **CS:GO**.
  * Tạo hình nhân vật kẻ địch (Enemy Bot) và bàn tay cầm vũ khí theo phong cách **Roblox Blocky 3D**.
  * Hỗ trợ cơ chế ngắm bắn (Scope ADS), đổi tay cầm vũ khí (`cl_righthand 0 / 1`), cơ chế khói che tầm nhìn (Smoke Occlusion) và cơ chế xuyên khói chân thực.
* **Công nghệ cốt lõi:**
  * **Python 3.11+ / Pygame:** Engine đồ họa, xử lý logic vật lý, âm thanh và giao diện.
  * **Pygbag (WebAssembly / Emscripten):** Đóng gói toàn bộ source game thành trang web HTML5 chạy mượt mà trên trình duyệt và xuất bản file APK/Tar.gz.
  * **Ursina Engine (`ursina_game.py`):** Bản thử nghiệm Full 3D Renderer độc lập với vũ khí ghép khối và cơ chế khói thể tích (Volumetric Smoke).

---

## 2. KIẾN TRÚC THƯ MỤC DỰ ÁN (PROJECT STRUCTURE)

```
TungLamv3/
│
├── BAM_DE_BUILD_VA_DAY_GIT.bat   # Script tự động build Web (Pygbag) & Push Git
├── DOCUMENTATION.md              # File tài liệu hướng dẫn toàn diện (file này)
├── README.md                     # File tóm tắt repository
├── index.html                    # File Web launcher chạy game trực tiếp trên trình duyệt
├── favicon.png                   # Biểu tượng website game
├── tunglamv2.apk                 # Gói cài đặt Android đóng gói sẵn
├── tunglamv2.tar.gz              # Gói nén Web package
├── ursina_game.py                # Phiên bản thử nghiệm 3D độc lập bằng Ursina Engine
│
├── screenshots/                  # Thư mục lưu ảnh chụp màn hình gameplay
│   ├── 3d_gun_ingame_awm.png
│   ├── 3d_gun_ingame_classic.png
│   ├── 3d_gun_ingame_vandal.png
│   └── full_3d_gameplay.png
│
└── TungLamv2/                    # Mã nguồn game chính (Pygame Engine)
    ├── main.py                   # Điểm khởi chạy (Game Loop, State Manager, Input)
    ├── settings.py               # Thiết lập hằng số (Độ phân giải 1600x900, FPS 120, Speed...)
    ├── sound.py                  # Quản lý phát âm thanh vũ khí, bước chân, tiếng gầm
    │
    ├── game/                     # Logic cốt lõi của gameplay
    │   ├── player.py             # Lớp Player (vị trí, máu, giáp, góc nhìn, recoil, nhảy, ngồi)
    │   ├── enemy.py              # Lớp Enemy (AI bot, di chuyển, bắn trả, Roblox Hitbox 3 tầng)
    │   ├── map.py                # Hệ thống tường cản, Bombsite A/B/C, kiểm tra vật cản Raycast
    │   └── weapon.py             # Hệ thống chỉ số 13 loại vũ khí, cơ chế đạn, reload, damage
    │
    ├── graphics/                 # Hệ thống đồ họa & dựng hình
    │   ├── renderer.py           # Bộ dựng hình Raycasting 2.5D, chiếu phối cảnh 3D
    │   ├── gun3d.py              # Dựng hình mô hình súng 3D thời gian thực (không cần file .obj)
    │   ├── cs_viewmodel.py       # Tọa độ và hiệu ứng chuyển động tay súng kiểu CS:GO
    │   ├── minimap.py            # Vẽ bản đồ radar góc trên màn hình
    │   └── weapon_skins.py       # Render icon HUD và giao diện shop
    │
    ├── ui/                       # Giao diện người dùng
    │   ├── hud.py                # Hiển thị thanh máu (HP), giáp, đạn, tiền ($), killfeed
    │   ├── game_view.py          # Quản lý màn hình Menu, Pause, GameOver, Shop
    │   └── game_weapon_view.py   # Render mô hình xem trước vũ khí trong menu
    │
    └── sounds/                   # Hiệu ứng âm thanh (Audio Assets)
        ├── footstep.wav          # Tiếng bước chân
        ├── pistol.wav            # Tiếng súng lục
        ├── shotgun.wav           # Tiếng súng shotgun
        ├── reload.wav            # Tiếng nạp đạn
        ├── ricochet.wav          # Tiếng đạn nảy kim loại
        └── zombie_roar.wav       # Tiếng gầm của quái / bot
```

---

## 3. HỆ THỐNG ĐIỀU KHIỂN (CONTROLS & KEYBINDINGS)

| Phím / Nút chuột | Hành động trong Game | Chức năng chi tiết |
| :--- | :--- | :--- |
| **W, A, S, D** | Di chuyển (Movement) | Tiến, lùi, di chuyển ngang trái / phải |
| **Di chuột (Mouse)** | Xoay góc nhìn (Look) | Xoay ngang (Yaw) và ngước lên / nhìn xuống (Pitch) |
| **Space** | Nhảy (Jump) | Bật nhảy né đạn và vượt vật cản |
| **Left Ctrl** | Ngồi (Crouch) | Hạ thấp trọng tâm nhân vật, tăng độ chính xác |
| **Left Shift** | Đi bộ chậm (Walk) | Đi chậm giữ im lặng, không phát tiếng bước chân |
| **Chuột trái (LMB)** | Bắn / Tấn công | Bắn súng / Chém nhanh với Dao (50 sát thương) |
| **Chuột phải (RMB)** | Ngắm / Đâm mạnh | Bật Scope ống ngắm súng / Đâm mạnh với Dao (80 sát thương) |
| **R** | Nạp đạn (Reload) | Nạp lại băng đạn súng hiện tại |
| **1** | Vũ khí chính (Primary) | Trang bị Rifle / Sniper / Shotgun / SMG |
| **2** | Súng phụ (Secondary) | Trang bị súng lục (Classic, Ghost, Sheriff) |
| **3** | Cận chiến (Melee) | Rút Dao găm (Tactical Knife) |
| **4** | Lựu đạn khói (Smoke) | Trang bị quả ném khói che tầm nhìn |
| **5** | Bom lửa (Molotov) | Trang bị bom lửa gây sát thương diện rộng |
| **6** | Bom Spike / C4 | Đặt bom tại các khu vực Site A, B, C |
| **B** | Mua đồ (Buy Menu) | Mở giao diện cửa hàng vũ khí & trang bị |
| **G** | Vứt súng (Drop) | Thả khẩu súng đang cầm trên tay xuống đất |
| **F** | Nhặt súng (Pickup) | Nhặt vũ khí rơi gần vị trí đứng |
| **X hoặc H** | Đổi tay cầm súng | Chuyển đổi giữa tay phải và tay trái (`cl_righthand`) |
| **F12** | Chụp màn hình | Lưu ảnh gameplay vào thư mục `screenshots/` |
| **ESC** | Thoát / Menu | Đóng Menu mua đồ hoặc tạm dừng về Menu chính |

---

## 4. CƠ CHẾ GAMEPLAY (GAMEPLAY MECHANICS)

### 4.1. Chu kỳ vòng đấu (Round Cycle)
Game vận hành theo thể thức thi đấu Tactical Round-based:
1. **Giai đoạn Mua sắm (Buy Phase - 30 giây):**
   * Người chơi đứng trong khu vực spawn, bấm phím `B` để mua súng, giáp và lựu đạn.
   * Cho phép bán lại (Refund) các món đồ vừa mua trong round bằng chuột phải (`RMB`).
2. **Giai đoạn Tác chiến (Combat Phase - 100 giây):**
   * Cổng mở, người chơi tiến ra bản đồ tiến hành kiểm soát các khu vực trọng yếu (Site A, Site B, Site C, Mid, Lower).
   * Tiêu diệt toàn bộ lực lượng địch hoặc hoàn thành nhiệm vụ khu vực bombsite.
3. **Giai đoạn Kết thúc (Round End & Match Result):**
   * Tính toán kết quả thắng/thua, phân phát tiền thưởng kinh tế và chuẩn bị cho round kế tiếp.

### 4.2. Hệ thống kinh tế (Economy System)
* **Tiền khởi đầu:** \$800
* **Tiền tối đa tích lũy:** \$99,000
* **Thưởng thắng round:** +\$3,250
* **Thưởng thua (Loss Streak):** Khởi điểm \$1,400, mỗi trận thua liên tiếp cộng thêm \$500, tối đa chạm mốc \$3,400.
* **Thưởng hạ gục theo vũ khí (Kill Bounty):**
  * Dao (Knife): **+\$1,500** (thưởng cao nhất cho pha áp sát liều lĩnh)
  * Shotgun (M014, MAG-7): **+\$900**
  * Súng tiểu liên (MP5, UMP): **+\$600**
  * Súng trường (AK-47, M416, Guardian): **+\$300**
  * Súng lục (Classic, Ghost, Sheriff): **+\$300**
  * Lựu đạn: **+\$300**
  * Súng tỉa AWM: **+\$100 - \$300**

---

## 5. KHO VŨ KHÍ & BẢNG SÁT THƯƠNG CHI TIẾT (WEAPON ARSENAL)

Hệ thống vũ khí được cân bằng theo cự ly mét thực tế và vị trí trúng đạn (Đầu, Thân, Chân).

### 5.1. Dao cận chiến (Melee)
* **Tên:** Knife
* **Giá:** Miễn phí (\$0)
* **Cơ chế:** Chuột trái vung chém nhanh (50 sát thương), Chuột phải đâm chí mạng (80 sát thương). Tầm đánh hiệu quả: 8m (khoảng cách 200 đơn vị).

### 5.2. Súng phụ (Pistols / Sidearms)

| Vũ khí | Giá (\$) | Băng đạn / Dự trữ | Tốc độ bắn | Sát thương Đầu (Head) | Sát thương Thân (Body) | Sát thương Chân (Legs) | Đặc điểm nổi bật |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **CLASSIC** | 0 | 12 / 60 | 6.75 v/s | 78 *(<=30m)* / 66 | 26 *(<=30m)* / 22 | 22 *(<=30m)* / 18 | Súng lục khởi đầu, miễn phí, cơ động |
| **GHOST** | 500 | 15 / 60 | 6.75 v/s | 105 *(<=30m)* / 88 | 30 *(<=30m)* / 25 | 26 *(<=30m)* / 21 | Giảm thanh, độ chụm đạn cao, bắn êm |
| **SHERIFF** | 800 | 6 / 36 | 4.00 v/s | **160** *(<=30m)* / **145** | 55 *(<=30m)* / 50 | 47 *(<=30m)* / 43 | Sát thương cực lớn, One-shot Headshot dưới 30m |

### 5.3. Súng tiểu liên (Submachine Guns - SMG)

| Vũ khí | Giá (\$) | Băng đạn / Dự trữ | Tốc độ bắn | Sát thương Đầu | Sát thương Thân | Sát thương Chân | Đặc điểm nổi bật |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **UMP** | 1,000 | 20 / 80 | **18.0 v/s** | 67 *(<=20m)* / 62 | 27 *(<=20m)* / 25 | 23 *(<=20m)* / 21 | Bắn chính 18 v/s · Ngắm 1.15x bắn chùm 4 viên (4 v/s), giảm nhẹ giãn hồng tâm |
| **MP5** | 1,600 | 30 / 90 | 13.33 v/s | 78 *(<=20m)* / 66 | 26 *(<=20m)* / 22 | 22 *(<=20m)* / 18 | Bắn chính 13.33 v/s · Ngắm 1.15x (12 v/s), giảm giãn hồng tâm, đầm tay |

### 5.4. Súng bắn đạn hoa cải (Shotguns)

| Vũ khí | Giá (\$) | Băng đạn / Dự trữ | Cơ chế | Sát thương Đầu | Sát thương Thân | Sát thương Chân | Đặc điểm nổi bật |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **M014** | 900 | 5 / 25 | Bán tự động (1.1 v/s) | 44 *(<=8m)* / 34 / 18 | 22 *(<=8m)* / 17 / 9 | 19 *(<=8m)* / 14 / 8 | Cận chiến bán tự động, cự ly 0-8m, 8-12m, 12-50m |
| **MAG-7** | 1,500 | 7 / 28 | Tự động hoàn toàn (7 v/s) | 34 *(<=10m)* / 26 / 20 | 17 *(<=10m)* / 13 / 10 | 14 *(<=10m)* / 11 / 9 | Xả đạn liên thanh 7 v/s, cự ly 0-10m, 10-15m, 15-50m |

### 5.5. Súng trường tấn công (Assault Rifles)

| Vũ khí | Giá (\$) | Băng đạn / Dự trữ | Tốc độ bắn | Sát thương Đầu | Sát thương Thân | Sát thương Chân | Đặc điểm nổi bật |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **AK-47 / VANDAL** | 2,900 | 25 / 75 | 9.25 v/s | **160 (Mọi cự ly)** | 40 | 34 | Bắn chính 9.25 v/s · Ngắm 1.25x (8.32 v/s), giảm nhẹ giãn hồng tâm, 1 hit headshot |
| **M416 / PHANTOM**| 2,900 | 30 / 90 | 11.0 v/s | 156 *(<=15m)* / 140 / 124 | 39 / 35 / 31 | 33 / 29 / 26 | Bắn chính 11 v/s · Ngắm 1.25x (9.9 v/s), giảm nhẹ giãn hồng tâm, 30 viên ổn định |
| **GUARDIAN** | 2,700 | 12 / 36 | 6.50 v/s | **195 (Mọi cự ly)** | 65 | 49 | Bán tự động 6.5 v/s · Ngắm 1.5x (6.5 v/s), giảm nhẹ giãn hồng tâm, 1 hit headshot |

### 5.6. Súng bắn tỉa (Sniper Rifles)

| Vũ khí | Giá (\$) | Băng đạn / Dự trữ | Tốc độ bắn | Sát thương Đầu | Sát thương Thân | Sát thương Chân | Đặc điểm nổi bật |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **M24** | 1,100 | 5 / 15 | 1.50 v/s | **202** | 101 | 85 | Bắn chính 1.5 v/s · Ngắm 2.5x (1.2 v/s), giảm nhẹ giãn hồng tâm, giá rẻ cơ động |
| **AWM** | 4,500 | 5 / 15 | 0.75 v/s | **255** | **150** | 120 | Bán tự động 0.75 v/s · Ngắm 2 cấp 2.5x và 5x (0.75 v/s), One-shot Body mọi tầm |

---

## 6. TRANG BỊ CHIẾN THUẬT (TACTICAL UTILITIES)

1. **Khói (Smoke Grenade - Phím 4):**
   * Số lượng tối đa mang theo: 2 quả.
   * Tạo ra một khối cầu khói màu xám mờ che khuất hoàn toàn tầm nhìn.
   * **Cơ chế đặc biệt:** Kẻ địch đứng trong khói hoặc phía sau khói sẽ bị ẩn hình dạng đối với mắt người chơi và Bot AI (không kích hoạt bắn). Tuy nhiên, **đạn và đường đạn (Raycast) vẫn bay xuyên qua bình thường**, cho phép game thủ bắn dò góc (spam through smoke).
2. **Bom lửa (Molotov - Phím 5):**
   * Số lượng tối đa mang theo: 2 quả.
   * Khi chạm đất bùng lên vùng lửa thiêu đốt diện rộng, gây sát thương liên tục theo thời gian cho bất kỳ ai dẫm vào khu vực. Thích hợp để dọn góc hoặc cản bước đối phương.
3. **Bom C4 / Spike (Phím 6):**
   * Số lượng: 1 quả.
   * Được mang vào khu vực đánh dấu bombsite (Site A, B, C) để tiến hành kích hoạt mục tiêu.

---

## 7. CÔNG NGHỆ ĐỒ HỌA & KỸ THUẬT RENDER ĐẶC TRƯNG

### 7.1. Viewmodel súng 3D thời gian thực (`gun3d.py`)
Khác với các game 2.5D truyền thống dùng sprite hình ảnh 2D cố định, tựa game này tích hợp hệ thống **dựng hình 3D vector thuần túy**:
* Mô hình súng được tạo nên từ tập hợp các khối hình học cơ bản: `Box` (thân súng, nẹp ray), `Cylinder` (nòng súng, giảm thanh, ống ngắm), `Extrude` (báng súng, tay cầm, băng đạn cong) và `Beam` (cánh tay người chơi).
* Sử dụng hệ toạ độ không gian thực với thuật toán chiếu phối cảnh 3D (Perspective Projection), loại bỏ mặt khuất (Backface Culling) và tính toán ánh sáng bóng mờ (Directional + Ambient Lighting).
* Hỗ trợ đổi tay súng trái / phải theo chuẩn Counter-Strike (`cl_righthand 1 / 0`) bằng cách lật ma trận trục toạ độ Z.

### 7.2. Nhân vật kẻ địch phong cách Roblox 3D Hitbox (`enemy.py`)
Mô hình Bot được thiết kế chia theo 3 tỉ lệ khối hộp độc lập:
* **Đầu (Head - 22% chiều cao):** Vùng trúng đạn chí mạng, nhận hệ số sát thương nhân từ x3 đến x4 tùy súng.
* **Thân (Body / Torso - 40% chiều cao):** Vùng nhận sát thương cơ chuẩn. Sát thương sẽ ưu tiên trừ vào Giáp (Armor) trước khi trừ vào Máu (HP).
* **Chân (Legs - 36% chiều cao):** Vùng nhận ít sát thương hơn (~80-85% sát thương chuẩn).
* Bot có đầy đủ animation cử động chân tay theo chu kỳ bước đi (Walk cycle) và hiệu ứng giật người khi trúng đòn.

### 7.3. Trí tuệ nhân tạo (Bot AI) & Tầm nhìn
* **Line of Sight (LOS):** Bot tính toán tia kiểm tra chướng ngại vật xem có tường cản giữa Bot và người chơi không.
* **Smoke Check:** Nếu đường ngắm của Bot bị cắt ngang bởi quả cầu khói, Bot sẽ mất dấu người chơi và ngừng bắn cho đến khi người chơi bước ra khỏi màn khói.

---

## 8. HƯỚNG DẪN CÀI ĐẶT VÀ TRẢI NGHIỆM

### 8.1. Yêu cầu hệ thống
* Hệ điều hành: Windows 10/11, macOS, hoặc Linux.
* Python phiên bản 3.10 trở lên (khuyên dùng Python 3.11 hoặc 3.12).
* Các thư viện bắt buộc:
  ```bash
  pip install pygame pygbag
  ```
  *(Nếu muốn trải nghiệm bản thử nghiệm 3D Ursina, cài thêm: `pip install ursina`)*

### 8.2. Chạy game trực tiếp trên máy tính (Desktop Mode)
Chạy mã nguồn Pygame chính thức:
```powershell
python TungLamv2/main.py
```

Chạy bản thử nghiệm đồ họa 3D Ursina:
```powershell
python ursina_game.py
```

### 8.3. Chạy trên trình duyệt Web hoặc Build thành file WebAssembly / APK
Dự án đã tích hợp sẵn công cụ build tự động 1-click qua file batch `BAM_DE_BUILD_VA_DAY_GIT.bat`:
1. Nhấp đúp vào file `BAM_DE_BUILD_VA_DAY_GIT.bat` trên Windows.
2. Script sẽ tự động kiểm tra Python, cài đặt `pygbag` nếu chưa có.
3. Đóng gói mã nguồn thành tệp HTML5, WebAssembly, file `.apk` cho Android và `.tar.gz`.
4. Hoặc bạn có thể tự khởi chạy web server local bằng lệnh:
   ```bash
   pygbag TungLamv2/main.py
   ```
   Sau đó mở trình duyệt truy cập: `http://localhost:8000` để chơi game ngay trên web!

---

## 9. ĐỀ XUẤT LỘ TRÌNH NÂNG CẤP TIẾP THEO (ROADMAP)

1. **Multiplayer qua WebSocket / WebRTC:** Tích hợp phòng chơi online nhiều người thi đấu đối kháng chia phe T / CT.
2. **Nâng cấp Hệ thống âm thanh:** Bổ sung âm thanh nạp đạn đặc trưng cho từng loại súng, hiệu ứng tiếng súng vang dội trong hành lang kín (reverb).
3. **Thêm hiệu ứng hoạt ảnh Viewmodel (Inspect Weapon):** Bổ sung phím kiểm tra súng (Inspect - phím Y) xoay ngắm skin súng 3D.
4. **Hệ thống Bom Hẹn giờ:** Đếm ngược thời gian nổ của Spike/C4 kèm hiệu ứng âm thanh tít tít dồn dập và cơ chế gỡ bom (Defuse) giữ phím E.
