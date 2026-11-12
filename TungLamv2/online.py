"""online.py - gọi API online chung của lớp (Buổi 13). Chép file này vào thư mục game.

Chạy được cả bản web (pygbag) lẫn bản desktop, và KHÔNG làm game bị đứng:
mỗi lệnh trả về ngay một "phiếu" (Request); mỗi khung hình bạn hỏi phiếu xem đã xong chưa.

    import online

    phieu = online.gui_diem("cyberesc", "Nam", 1200)        # gửi điểm
    phieu = online.lay_top("cyberesc")                       # lấy Top 10
    phieu = online.luu_len_mang("cyberesc", "Nam", data)     # cloud save
    phieu = online.tai_tu_mang("cyberesc", "Nam")            # cloud load

    # trong vòng lặp game, mỗi khung hình:
    if phieu and phieu.xong:
        if phieu.thanh_cong:
            print(phieu.ket_qua)        # dict server trả về
        else:
            print("Lỗi:", phieu.loi)    # mất mạng, server chưa dậy...
        phieu = None
"""
import itertools
import json
import sys
import threading
import urllib.parse

# Bản web: game nằm cùng trang Vercel nên chỉ cần đường dẫn tương đối.
# Bản desktop: cần địa chỉ đầy đủ của trang web lớp mình.
URL_DESKTOP = "https://THAY-TEN-MIEN-CUA-LOP.vercel.app"
DUONG_DAN_API = "/api/online/"
THOI_GIAN_CHO = 10  # giây; quá thời gian này coi như lỗi

LA_WEB = sys.platform == "emscripten"
_dem = itertools.count(1)
_js_san_sang = False


class Request:
    """Phiếu chờ kết quả. Đọc .xong / .thanh_cong / .ket_qua / .loi"""

    def __init__(self):
        self._id = f"r{next(_dem)}"
        self._xong = False
        self.thanh_cong = False
        self.ket_qua = None
        self.loi = None

    def _ket_thuc(self, status, text):
        try:
            data = json.loads(text) if text else {}
        except ValueError:
            data = {}
        if status == 0:
            self.loi = "Không kết nối được server (mất mạng hoặc quá thời gian chờ)"
        elif not data.get("ok"):
            self.loi = data.get("error") or f"Server trả về mã {status}"
        else:
            self.thanh_cong = True
            self.ket_qua = data
        self._xong = True

    @property
    def xong(self):
        if not self._xong and LA_WEB:
            from platform import window
            raw = window.lopNetLay(self._id)
            if raw:
                r = json.loads(str(raw))
                self._ket_thuc(r["status"], r["text"])
        return self._xong


# ---------------------------------------------------------------- gửi request
_JS = """
window.lopNet = window.lopNet || {};
window.lopNetGui = function (id, method, url, body, ms) {
  var ctl = new AbortController();
  var t = setTimeout(function () { ctl.abort(); }, ms);
  var opt = { method: method, signal: ctl.signal, cache: "no-store" };
  if (body) { opt.body = body; opt.headers = { "Content-Type": "application/json" }; }
  fetch(url, opt)
    .then(function (r) { return r.text().then(function (txt) {
      window.lopNet[id] = JSON.stringify({ status: r.status, text: txt }); }); })
    .catch(function () { window.lopNet[id] = JSON.stringify({ status: 0, text: "" }); })
    .finally(function () { clearTimeout(t); });
};
window.lopNetLay = function (id) {
  var v = window.lopNet[id]; if (v === undefined) return "";
  delete window.lopNet[id]; return v;
};
"""


def _gui(method, params, body=None):
    global _js_san_sang
    phieu = Request()
    url = DUONG_DAN_API + "?" + urllib.parse.urlencode(params)
    text = json.dumps(body, ensure_ascii=False) if body is not None else ""

    if LA_WEB:
        from platform import window
        if not _js_san_sang:
            window.eval(_JS)
            _js_san_sang = True
        window.lopNetGui(phieu._id, method, url, text, THOI_GIAN_CHO * 1000)
        return phieu

    def chay():
        import urllib.request
        import urllib.error
        req = urllib.request.Request(URL_DESKTOP.rstrip("/") + url, method=method,
                                     data=text.encode() if text else None,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=THOI_GIAN_CHO) as r:
                phieu._ket_thuc(r.status, r.read().decode())
        except urllib.error.HTTPError as e:   # server trả lỗi 4xx/5xx, vẫn đọc được lý do
            phieu._ket_thuc(e.code, e.read().decode(errors="replace"))
        except Exception:
            phieu._ket_thuc(0, "")

    threading.Thread(target=chay, daemon=True).start()
    return phieu


# ---------------------------------------------------------------- 4 chức năng
def gui_diem(game, player, score, **extra):
    """Gửi điểm. Server chỉ giữ điểm cao nhất của mỗi người.
    ket_qua: {"new_record": True/False, "best": điểm cao nhất}"""
    return _gui("POST", {"action": "score"},
                {"game": game, "player": player, "score": int(score), "extra": extra})


def lay_top(game, so_luong=10):
    """ket_qua["top"]: danh sách [{"player", "score", "extra", "time"}, ...] từ cao xuống thấp"""
    return _gui("GET", {"action": "top", "game": game, "limit": so_luong})


def luu_len_mang(game, player, data):
    """Cloud save: data là dict (tối đa ~20 KB)."""
    return _gui("POST", {"action": "save"}, {"game": game, "player": player, "data": data})


def tai_tu_mang(game, player):
    """Cloud load. ket_qua["found"] = False nếu người này chưa lưu bao giờ; ket_qua["data"] = dict"""
    return _gui("GET", {"action": "load", "game": game, "player": player})
