# 🚀 HƯỚNG PHÁT TRIỂN CÁC DỰ ÁN CỦA LỚP

> Cập nhật: 12/11/2026. Cả 3 game pygame và Football Manager đều đã có bản web (xem `README.md`).
> Mỗi dự án có 3 mức: **Cơ bản**, **Khá** và **Thử thách**. Học viên làm xong mức dưới rồi mới lên mức trên.

---

## 🎯 1. Tùng Lâm – Lotus Tactical FPS (`TungLamv2/`)
*Hiện có:* bắn súng 3D kiểu raycasting, hiệp đấu, cửa hàng, spike (bom), 12 skin súng, bot địch.

| Mức | Hướng phát triển | Học được gì |
|---|---|---|
| Cơ bản | • Chuyển âm thanh `.wav` sang `.ogg` cho bản web.<br>• Thêm màn hình "Click để bắt đầu".<br>• Phím F12 (chụp màn hình): trên web không ghi file ra máy được, nên ẩn tính năng này khi chạy web. | Những giới hạn khi chạy game trên trình duyệt |
| Khá | • **Leaderboard online**: cuối trận gửi số kill và số lần đặt spike lên API, rồi hiện Top 10 (bản mẫu: `deploy_4_students/1_TungLam_LotusTactical/server_leaderboard.py`).<br>• Thêm độ khó cho bot (Dễ / Thường / Khó) bằng cách chỉnh `fire_delay`, độ chính xác và máu. | HTTP, JSON, REST API, cân bằng game |
| Thử thách | • Cho bot **tìm đường** đến site A/B/C bằng BFS hoặc A* trên lưới bản đồ.<br>• Thêm map thứ 2 và màn chọn map. | Thuật toán đồ thị, tách dữ liệu map ra khỏi code |

## 🎯 2. Bảo Nam – Blade Master 2D (`Bảo Nam/`)
*Hiện có:* đối kháng 2D, 4 màn đánh boss, shop, chọn nhân vật và bản đồ.

| Mức | Hướng phát triển | Học được gì |
|---|---|---|
| Cơ bản | • **Lưu xu và đồ đã mua** bằng `localStorage` khi chạy web, để không mất khi bấm F5.<br>• Thêm màn chiến thắng sau trùm cuối, có tổng thời gian chơi. | Lưu dữ liệu, máy trạng thái (state machine) |
| Khá | • **Combo**: bấm E → E → Y trong 0,5 giây sẽ ra đòn đặc biệt.<br>• Cho boss có **nhiều pha**: dưới 50% máu thì đổi kiểu tấn công, đánh nhanh hơn (sửa `update_bot_ai` trong `fighter.py`). | Bộ đệm phím (input buffer), AI theo trạng thái |
| Thử thách | • Chế độ **2 người chơi trên cùng 1 bàn phím** (WASD và phím mũi tên).<br>• Viết hoạt ảnh nhân vật bằng sprite sheet thay cho hình vẽ tay. | Tái sử dụng lớp `Fighter`, hoạt ảnh theo khung hình |

## 🎯 3. Nhóm CyberEsc – Platformer 2D (`cyberesc/`)
*Hiện có:* 8 màn chơi, 3 súng, đồ trang trí (cosmetics), vật phẩm hỗ trợ (power-up), file lưu `save_data.json`.

| Mức | Hướng phát triển | Học được gì |
|---|---|---|
| Cơ bản | • Sửa `save_manager.py`: khi chạy web thì dùng `localStorage`, khi chạy desktop thì giữ file JSON như cũ.<br>• Hiện thời gian và số sao (1–3) sau mỗi màn. | Chạy được trên nhiều nền tảng, dùng `try/except` |
| Khá | • **Cloud Save**: đăng nhập bằng tên, lưu tiến trình lên server, chơi tiếp được trên máy khác (bản mẫu: `deploy_4_students/3_CyberEscape/server_cloud_save.py`).<br>• Thêm 1 loại địch mới và 1 boss ở màn 8. | API, đồng bộ dữ liệu, kế thừa lớp `Enemy` |
| Thử thách | • **Trình chỉnh sửa màn chơi (level editor)**: click chuột để đặt khối, xuất ra file `.json`.<br>• Nạp màn chơi từ JSON thay vì viết cứng trong `levels/lv*.py`. | Tách dữ liệu khỏi code, làm công cụ cho chính mình |

## 🎯 4. Football Manager Web (`football_manager_web/`)
*Hiện có:* khoảng 50 route, mô phỏng trận đấu theo từng phút, chuyển nhượng, lò đào tạo trẻ, bảng xếp hạng. Mã nguồn đã được khôi phục ngày 11/11.

| Mức | Hướng phát triển | Học được gì |
|---|---|---|
| Cơ bản | • Làm lại giao diện bằng một template thống nhất (Bootstrap hoặc Tailwind), vì 23/24 template gốc đã mất.<br>• Tìm người sở hữu dự án để ghi lại tên tác giả. | HTML/CSS, Jinja template |
| Khá | • Chuyển DB sang **Postgres online**: trên Vercel, file SQLite sẽ mất sau mỗi lần function khởi động lại.<br>• Thêm biểu đồ phong độ, bàn thắng và tài chính bằng Chart.js. | Database thật, trực quan hóa dữ liệu |
| Thử thách | • Thêm **đăng nhập**, mỗi người quản lý một CLB.<br>• Làm **giải đấu online giữa các bạn trong lớp**, CLB của người này đá với CLB của người kia. | Xác thực, nhiều người dùng chung một dữ liệu |

---

## 🌐 LỘ TRÌNH CHUNG CỦA LỚP

| Buổi | Chủ đề | Sản phẩm cuối buổi |
|---|---|---|
| 13 | **Lưu dữ liệu và Online** | Mọi game "nhớ" được tiến trình (localStorage); có ít nhất 1 tính năng online (leaderboard hoặc cloud save). |
| 14 | **Chất lượng** | Mỗi bạn sửa xong 3 lỗi nhận được từ buổi chơi thử chéo, có `CHANGELOG.md`, tên commit rõ ràng. |
| 15 | **Demo Day** | Thuyết trình 5 phút theo mẫu: Vấn đề → Demo → Khó khăn đã vượt qua → Hướng tiếp theo. Phụ huynh chơi thử qua trang tổng hợp. |

**Kỹ năng xuyên suốt:** chạy thử trước khi commit, mỗi tính năng làm trên một nhánh Git riêng, rồi gộp vào `main` bằng Pull Request để các bạn review code của nhau.

### ⚠️ Lưu ý kỹ thuật khi làm phần Online (Buổi 13)
1. `server_leaderboard.py` đang lưu điểm trong RAM. Render bản Free sẽ "ngủ" khi không có ai dùng, và lúc đó toàn bộ điểm bị xóa, nên cần lưu vào DB.
2. Server phải bật CORS (`flask-cors`). Nếu không, game chạy ở `*.vercel.app` gọi sang `*.onrender.com` sẽ bị trình duyệt chặn.
3. Render Free khởi động lại mất khoảng 50 giây, nên trong game phải có timeout và `try/except` để game không treo khi server chưa trả lời.
4. Một hướng gọn hơn: đặt API thành Vercel function (`api/leaderboard/index.py`), giống cách Football Manager đang chạy. Khi đó chỉ cần một nền tảng và không gặp lỗi CORS.
