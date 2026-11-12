# Buổi 13: Lưu dữ liệu và Online

Mỗi game đã có sẵn 2 file mới, **không cần cài thêm gì**:

| File | Dùng để | Chạy ở |
|---|---|---|
| `luu_tru.py` | Lưu tiến trình trên máy người chơi (bấm F5 không mất) | Web: `localStorage` · Desktop: file `.json` |
| `online.py` | Gửi điểm, lấy Top 10, lưu tiến trình lên mạng | Gọi API chung của lớp `/api/online/` |

> Cả lớp dùng **chung 1 API** do thầy/cô đã đưa lên Vercel. Các bạn **không phải tự tạo server**.
> Mỗi game dùng một tên riêng: `tunglamv2`, `baonam`, `cyberesc`.

---

## Phần 1: Lưu trên máy (`luu_tru.py`)

```python
import luu_tru

MAC_DINH = {"gold": 10000, "items": []}
data = luu_tru.doc("baonam_save", MAC_DINH)   # lúc mở game
...
luu_tru.ghi("baonam_save", data)              # lúc mua đồ, thắng màn, thoát game
```

**CyberEsc:** chỉ cần sửa 2 hàm trong `save_manager.py`, các file khác giữ nguyên:
```python
import luu_tru

def load_game_data():
    return luu_tru.doc("cyberesc_save", DEFAULT_DATA)

def save_game_data(data):
    luu_tru.ghi("cyberesc_save", data)
```

**Blade Master:** hiện vàng luôn bắt đầu bằng `START_GOLD` và chưa được lưu. Đọc bằng `luu_tru.doc(...)` khi tạo game, ghi bằng `luu_tru.ghi(...)` mỗi khi vàng hoặc đồ thay đổi.

Kiểm tra: chơi, có thêm vàng → bấm F5 → vàng vẫn còn là đạt.

---

## Phần 2: Online (`online.py`)

Gọi mạng mất thời gian (có khi vài giây), nên **không được bắt game đứng chờ**. Mỗi lệnh trả về ngay một **phiếu**; mỗi khung hình, game hỏi xem phiếu xong chưa.

```python
import online

phieu = None      # đặt ngoài vòng lặp
top10 = []

# Hết trận: gửi điểm
phieu = online.gui_diem("tunglamv2", ten_nguoi_choi, so_kill, spike=so_spike)

# Trong vòng lặp game, mỗi khung hình:
if phieu and phieu.xong:
    if phieu.thanh_cong:
        print("Điểm cao nhất của bạn:", phieu.ket_qua["best"])
    else:
        print("Lỗi mạng:", phieu.loi)    # game vẫn chạy bình thường
    phieu = None
```

Lấy Top 10 để vẽ bảng xếp hạng:
```python
phieu_top = online.lay_top("tunglamv2")
# ... khi phieu_top.xong và phieu_top.thanh_cong:
top10 = phieu_top.ket_qua["top"]      # [{"player": "Nam", "score": 15, "extra": {...}}, ...]
for i, dong in enumerate(top10):
    chu = font.render(f"{i+1}. {dong['player']}  {dong['score']}", True, (255, 255, 255))
    screen.blit(chu, (100, 100 + i * 30))
```

Cloud save (CyberEsc, hoặc Blade Master nếu làm xong phần 1):
```python
online.luu_len_mang("cyberesc", ten, data)     # data là dict
p = online.tai_tu_mang("cyberesc", ten)        # khi xong: p.ket_qua["found"], p.ket_qua["data"]
```

| Game | Việc online gợi ý | Điểm gửi lên |
|---|---|---|
| Lotus FPS | Bảng xếp hạng cuối trận | số kill, `spike=` số lần đặt spike |
| Blade Master | Bảng xếp hạng thời gian hạ boss (hoặc cloud save) | ví dụ: `100000 - số_giây` |
| CyberEsc | Cloud save theo tên + Top tổng sao | tổng số sao |

---

## Kiểm tra / lỗi thường gặp

- **Bản web (sau khi đẩy lên):** mở https://teachinglesson.vercel.app/api/online/. Thấy `"ok": true` là API đang chạy.
- **Chạy trên máy (`python main.py`):** `online.py` đã trỏ sẵn tới https://teachinglesson.vercel.app, không cần sửa.
- **Chạy `run_web_local.bat` (127.0.0.1:8000):** trên máy không có API, nên lệnh online sẽ báo lỗi. Đây là bình thường; đẩy lên Vercel rồi thử.
- Tên người chơi tối đa 20 ký tự; tên game chỉ gồm chữ thường, số, `-`, `_`.
- Server chỉ giữ **điểm cao nhất** của mỗi người.
