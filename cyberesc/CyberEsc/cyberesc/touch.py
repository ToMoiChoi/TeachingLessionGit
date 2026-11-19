"""Nút bấm cảm ứng cho điện thoại (tự bật khi phát hiện chạm màn hình)."""
import pygame

from font_vn import get_font

BUTTONS = {
    # khóa: (tâm x, tâm y, bán kính, nhãn)
    "left": (55, 440, 38, "<"),
    "right": (145, 440, 38, ">"),
    "jump": (740, 440, 38, "NHẢY"),
    "shoot": (650, 440, 38, "BẮN"),
    "slash": (740, 352, 32, "CHÉM"),
    "dash": (655, 352, 32, "LƯỚT"),
    "shield": (570, 440, 28, "KHIÊN"),
    "slow": (570, 368, 28, "CHẬM"),
    "weapon": (55, 352, 28, "SÚNG"),
    "pause": (400, 470, 20, "II"),
}


class TouchControls:
    def __init__(self, screen_w=800, screen_h=500):
        self.sw, self.sh = screen_w, screen_h
        self.enabled = False
        self.fingers = {}       # finger_id -> khóa nút
        self.pressed = []       # nút vừa được chạm (xử lý 1 lần)
        self.font = get_font(13, bold=True)

    def _hit(self, x, y):
        for key, (cx, cy, r, _) in BUTTONS.items():
            if (x - cx) ** 2 + (y - cy) ** 2 <= (r + 10) ** 2:
                return key
        return None

    def handle_event(self, event, in_game):
        """Xử lý sự kiện cảm ứng. Trả về True nếu đã dùng sự kiện này."""
        if event.type == pygame.FINGERDOWN:
            self.enabled = True
            if not in_game:
                return False
            key = self._hit(event.x * self.sw, event.y * self.sh)
            if key:
                self.fingers[event.finger_id] = key
                self.pressed.append(key)
            return True
        if event.type == pygame.FINGERMOTION:
            key = self._hit(event.x * self.sw, event.y * self.sh)
            old = self.fingers.get(event.finger_id)
            if key in ("left", "right") and old in ("left", "right"):
                self.fingers[event.finger_id] = key
            return in_game
        if event.type == pygame.FINGERUP:
            self.fingers.pop(event.finger_id, None)
            return in_game
        return False

    def held(self, key):
        return key in self.fingers.values()

    def take_pressed(self):
        p, self.pressed = self.pressed, []
        return p

    def reset(self):
        self.fingers.clear()
        self.pressed.clear()

    def draw(self, screen):
        if not self.enabled:
            return
        layer = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        for key, (cx, cy, r, label) in BUTTONS.items():
            on = self.held(key)
            pygame.draw.circle(layer, (0, 243, 255, 110 if on else 45), (cx, cy), r)
            pygame.draw.circle(layer, (255, 255, 255, 150), (cx, cy), r, 2)
        screen.blit(layer, (0, 0))
        for key, (cx, cy, r, label) in BUTTONS.items():
            t = self.font.render(label, True, (255, 255, 255))
            screen.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))
