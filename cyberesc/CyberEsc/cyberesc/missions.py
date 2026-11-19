"""Nhiệm vụ hằng ngày: mỗi ngày 3 nhiệm vụ (chọn theo ngày), hoàn thành để nhận coins."""
import datetime
import random

# (mã, mô tả, sự kiện, [mục tiêu có thể], thưởng, cách đếm)
POOL = [
    ("kill", "Hạ {n} quái", "kill", [25, 35, 50], 150, "add"),
    ("parry", "Chém phản đạn {n} lần", "parry", [5, 10], 160, "add"),
    ("clear", "Hoàn thành {n} màn chơi", "clear", [2, 3], 200, "add"),
    ("coins", "Nhặt {n} coins", "coins", [300, 500], 150, "add"),
    ("wave", "Đạt wave {n} ở chế độ Vô Tận", "wave", [4, 6], 250, "max"),
    ("dash", "Lướt (Q) {n} lần", "dash", [20, 40], 100, "add"),
    ("boss", "Hạ {n} boss", "boss", [1], 300, "add"),
    ("star3", "Đạt 3 sao ở {n} màn", "star3", [1, 2], 220, "add"),
    ("special", "Hạ {n} quái bằng Laser hoặc Lựu đạn", "special_kill", [10], 200, "add"),
]


def today_str():
    return datetime.date.today().isoformat()


class MissionManager:
    def __init__(self, state=None):
        self.date = ""
        self.missions = []
        if isinstance(state, dict):
            self.date = state.get("date", "")
            self.missions = list(state.get("list", []))
        self.ensure_today()

    def ensure_today(self):
        day = today_str()
        if self.date == day and len(self.missions) == 3:
            return
        rng = random.Random(day)
        picks = rng.sample(POOL, 3)
        self.missions = []
        for mid, text, event, targets, reward, mode in picks:
            n = rng.choice(targets)
            self.missions.append({"id": mid, "text": text.format(n=n), "event": event, "target": n,
                                  "progress": 0, "reward": reward, "mode": mode, "claimed": False})
        self.date = day

    def record(self, event, amount=1):
        """Ghi nhận tiến độ. Trả về danh sách nhiệm vụ vừa hoàn thành (để báo trên màn hình)."""
        self.ensure_today()
        done = []
        for m in self.missions:
            if m["event"] != event or m["progress"] >= m["target"]:
                continue
            if m["mode"] == "max":
                m["progress"] = max(m["progress"], amount)
            else:
                m["progress"] += amount
            m["progress"] = min(m["progress"], m["target"])
            if m["progress"] >= m["target"]:
                done.append(m)
        return done

    def claimable_count(self):
        return sum(1 for m in self.missions if m["progress"] >= m["target"] and not m["claimed"])

    def claim(self, idx):
        if 0 <= idx < len(self.missions):
            m = self.missions[idx]
            if m["progress"] >= m["target"] and not m["claimed"]:
                m["claimed"] = True
                return m["reward"]
        return 0

    def export_state(self):
        return {"date": self.date, "list": self.missions}
