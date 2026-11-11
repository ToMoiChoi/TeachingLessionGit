# Lớp Game Python — Teaching Lesson Git

Kho code chung của lớp Lập trình Game Python. Mỗi bạn có một thư mục game riêng; bản web của các game được gom vào trang tổng hợp `index.html`, để **phụ huynh xem kết quả học tập và chơi thử ngay trên trình duyệt**.

- Trang web: deploy tự động lên **Vercel** mỗi khi push lên nhánh `main`
- GitHub: https://github.com/ToMoiChoi/TeachingLessionGit

---

## 1. Cấu trúc thư mục

```text
Buổi 10/
├── index.html                  # Trang chủ cho phụ huynh: thống kê, thẻ sản phẩm, nút "Chơi thử"
├── favicon.png                 # Icon của trang chủ
├── vercel.json                 # Cấu hình Vercel (trailingSlash = true để game nhúng tải được)
├── games/                      # BẢN WEB đã build của các game (Vercel phục vụ thư mục này)
│   ├── games.json              # Danh sách sản phẩm hiển thị trên trang chủ
│   ├── tunglamv2/              # index.html + favicon.png + <id>.apk + <id>.tar.gz (do pygbag tạo)
│   ├── baonam/
│   └── cyberesc/
├── tools/
│   └── publish_game.py         # Chép bản build vào games/<id>/ và thêm vào games.json
├── BAM_DE_BUILD_VA_DAY_GIT.bat # Nút bấm: build 1 game -> chép vào games/ -> commit -> push
├── run_web_local.bat           # Chạy thử trang chủ trên máy: http://127.0.0.1:8000
├── run_game.bat                # Chạy bản desktop của TungLamv2
│
├── TungLamv2/                  # Code game của Tùng Lâm
├── Bảo Nam/                    # Code game của Bảo Nam
├── cyberesc/                   # Code game CyberEsc
└── football_manager_web/       # Ứng dụng web Flask (đang hoàn thiện)
```

> Thư mục code game (`TungLamv2/`, `Bảo Nam/`, `cyberesc/`) chỉ chứa **code + tài nguyên**. Bản build (`build/`, `*.apk`, `*.tar.gz`) không để trong đó. Nếu để chung, pygbag sẽ đóng gói luôn các file này vào bản build kế tiếp và làm game nặng gấp nhiều lần.

---

## 2. Bốn dự án

| Dự án | Học sinh | Thể loại | Công nghệ | Quy mô | Bản web |
|---|---|---|---|---|---|
| Lotus Tactical FPS | Tùng Lâm | Bắn súng góc nhìn thứ nhất | pygame + asyncio (pygbag) | 14 file · 4.712 dòng | `games/tunglamv2/` |
| Blade Master 2D | Bảo Nam | Đối kháng 2D | pygame + asyncio (pygbag) | 7 file · 1.417 dòng | `games/baonam/` |
| CyberEsc | cyberesc | Platformer 2D | pygame-ce + asyncio (pygbag) | 23 file · 2.151 dòng | `games/cyberesc/` |
| Football Manager | (đang cập nhật) | Web quản lý CLB | Flask + SQLAlchemy | 10 file · 2.539 dòng + 26 template | `/football/` (Vercel Python) |

### 2.1 TungLamv2 — Lotus Tactical FPS
```text
TungLamv2/
├── main.py              # Vòng lặp game (async), trạng thái hiệp, cửa hàng, bom, xử lý phím
├── settings.py          # WIDTH, HEIGHT, FPS, thời gian hiệp/mua đồ
├── sound.py             # Nạp và phát âm thanh
├── favicon.png          # Icon cho bản web (pygbag tự lấy)
├── game/                # Logic: player.py, enemy.py, map.py (tường, site A/B/C), weapon.py
├── graphics/            # Vẽ: renderer.py (raycasting), minimap.py, cs_viewmodel.py, weapon_skins.py
├── ui/                  # Giao diện: hud.py, game_view.py, game_weapon_view.py
├── assets/              # Ảnh súng/dao; assets/skin súng/ chứa 12 skin
└── sounds/              # *.wav
```
Điều khiển: `WASD` di chuyển · chuột ngắm/bắn · `R` nạp đạn · `1 2 3` đổi vũ khí · `5 6 7` lựu đạn · `B` cửa hàng · `Space` nhảy · `Ctrl` ngồi · `G` vứt súng · `F` nhặt súng · `4` đặt bom · `F12` chụp màn hình.

### 2.2 Bảo Nam — Blade Master 2D
```text
Bảo Nam/
├── main.py      # Lớp Game: menu, chọn bản đồ/nhân vật, shop, chiến đấu, vòng lặp async
├── config.py    # Hằng số, màu, font, danh sách LEVELS (boss), hàm vẽ chữ/thanh máu
├── entities.py  # Particle, Fighter
├── fighter.py   # Lớp nhân vật đối kháng
├── levels.py    # Dữ liệu màn chơi
├── ui.py        # Vẽ menu, chọn bản đồ, chọn nhân vật, shop, HUD, game over
├── sound.py     # Phát âm thanh từ thư mục sounds/
└── sounds/      # *.wav
```
Điều khiển: `A/D` di chuyển · `W/Space` nhảy · `E` đòn nhẹ · `Y` đòn nặng · `C` kỹ năng · `Z` đỡ đòn · `X` hồi máu · `F` dựng tường · `Shift` chạy. Menu: `C` chọn NV, `M` đổi bản đồ, `L` đổi màn, `S` shop.

### 2.3 cyberesc — CyberEsc
Xem chi tiết trong `cyberesc/readme_cyberesc_game_project.md`. Tóm tắt:
```text
cyberesc/
├── main.py                  # Điểm khởi chạy
├── game_engine.py           # Cầu nối giữa gameplay và layout
├── game_engine_gameplay.py  # Logic, va chạm, nạp màn chơi động
├── game_engine_layout.py    # Vẽ toàn bộ hình và HUD
├── config.py, player.py, Enemy.py, weapon.py, powerups.py, particle.py, cosmetics.py, menu.py
├── save_manager.py + save_data.json   # Lưu tiến trình (xu, màn đã mở, nâng cấp)
├── levels/lv1.py … lv8.py   # 8 màn chơi
└── Sounds/Sounds.py + Sounds/sounds/*.wav
```
Điều khiển: `A/D` di chuyển · `W/Space` nhảy · chuột trái/`K` bắn · chuột phải/`J` chém · `1 2 3` đổi súng · `Esc` tạm dừng.

### 2.4 football_manager_web — Football Manager
Mã nguồn Python gốc bị mất; ngày 11/11/2026 đã **khôi phục từ bản build `run.exe`** (giải nén PyInstaller → dịch ngược bytecode Python 3.14 → viết lại thành `.py`, giữ nguyên logic, số liệu và câu chữ). 23/24 template HTML gốc không còn nên giao diện được viết lại.
```text
football_manager_web/
├── app.py               # Flask: ~50 route (CLB, đội hình, trận đấu trực tiếp, chuyển nhượng, lò trẻ, tài trợ, BXH, lưu/tải)
├── launcher.py          # Chạy trên máy: mở http://127.0.0.1:5000
├── sound.py             # Âm thanh phía máy (pygame, tự bỏ qua nếu không có)
├── football/
│   ├── models.py        # SQLAlchemy: Club, Player, YouthPlayer, Coach, MatchHistory, LeagueStanding
│   ├── game_engine.py   # Mô phỏng trận đấu theo từng phút
│   ├── classes.py       # PlayerOld / TeamOld / MatchOld dùng khi mô phỏng
│   └── team_manager.py, league_manager.py, save_load.py
├── templates/           # base.html + 25 trang (Jinja2); _audio_widget.html = trình phát nhạc tự chèn
├── static/css/style.css, static/images/
└── sounds/sfx/
```
Chạy trên máy: `cd football_manager_web` → `pip install -r requirements.txt` → `python launcher.py`.

Trên web: `vercel.json` chuyển `/football/...` vào `api/football/index.py` (Vercel Python function). Server chỉ ghi được vào `/tmp` nên **dữ liệu là tạm**: CLB có thể mất khi server khởi động lại. Muốn lưu lâu dài thì đặt biến môi trường `FM_DB_URI` trên Vercel trỏ tới một database Postgres (vd Neon).

---

## 3. Chạy trên máy

```bat
:: Chạy 1 game bản desktop
cd TungLamv2
python main.py

:: Chạy trang chủ + các bản web
run_web_local.bat      :: mở http://127.0.0.1:8000
```
Yêu cầu: Python 3.11+, `pip install pygame-ce pygbag`.

> Dùng `127.0.0.1`, **không** dùng `localhost`. Nếu thấy `localhost`, pygbag tưởng là server dev và tải pygame từ `/cdn/`, gây lỗi 404.

---

## 4. Nộp bài / cập nhật game lên web

1. Bấm đúp `BAM_DE_BUILD_VA_DAY_GIT.bat`.
2. Chọn số thứ tự thư mục game của mình.
3. Script sẽ tự làm:
   - build bằng `pygbag --build` (kết quả ở `<game>/build/web/`, file này không lên Git)
   - chạy `tools/publish_game.py`: chép bản build vào `games/<id>/`. Nếu là game mới, script hỏi tên, tác giả, mô tả rồi thêm vào `games.json`
   - commit, `git pull --rebase`, rồi `git push`. Vercel tự cập nhật trang web.

Yêu cầu để game chạy được trên web (pygbag):
- `main.py` có `async def main()` và trong vòng lặp có `await asyncio.sleep(0)`.
- Âm thanh dùng `.wav` hoặc `.ogg`.
- Đường dẫn file dùng tương đối so với thư mục game.

---

## 5. Trang chủ cho phụ huynh (`index.html` + `games/games.json`)

Trang chủ đọc `games/games.json` và tự hiển thị: tổng số sản phẩm, số game chơi được, tổng số file/dòng code; mỗi bạn một thẻ có mô tả, tính năng, phím điều khiển, nút **Chơi thử** (game mở toàn màn hình ngay trong trang).

Các trường của một mục trong `games.json`:

| Trường | Bắt buộc | Ý nghĩa |
|---|---|---|
| `id` | ✔ | Tên thư mục trong `games/` (`games/<id>/`) |
| `title`, `author`, `description`, `tag` | ✔ | Tên game, tên học sinh, mô tả, thể loại |
| `emoji`, `color` | | Hình và màu ảnh bìa |
| `playable` | | `false` thì thẻ hiện "Đang hoàn thiện" và tắt nút chơi (mặc định `true`) |
| `status` | | Chữ trên nhãn khi `playable: false` |
| `stats` | | `{ "files": số file .py, "lines": số dòng code }` |
| `features` | | Danh sách điểm nổi bật |
| `controls` | | Danh sách `["Phím", "Tác dụng"]` |

Đếm số file/dòng code của một game (Git Bash):
```bash
find "TungLamv2" -name '*.py' -not -path '*/build/*' | wc -l
find "TungLamv2" -name '*.py' -not -path '*/build/*' -exec cat {} + | wc -l
```

---

## 6. Quy tắc giữ repo sạch

`.gitignore` đã chặn các file sau, **không commit**:
- `__pycache__/`, `*.pyc`: file cache Python tự sinh
- `*/build/`, `*/dist/`, `*.exe`: bản build tạm
- `/<thư mục game>/*.apk`, `*.tar.gz`: bản build chỉ nằm trong `games/<id>/`
- `.venv/`, `.idea/`, `.vscode/`, `screenshots/`, `instance/`

Đợt dọn dẹp 11/11/2026 đã xóa: toàn bộ `__pycache__`, thư mục trùng `Bảo Nam/sounds/sounds/`, bản build cũ trong `TungLamv2/` (`build/`, `tunglamv2.apk`, `tunglamv2.tar.gz`, `index.html`), script cũ `deploy_web.bat` (script này ghi đè trang chủ), và các thư mục rỗng/IDE/build trong `football_manager_web/` (kể cả 2 template bị lưu nhầm dạng Word, nay đã thành `.html`).
