"""Chế độ Vô Tận: quái kéo tới theo từng đợt (wave), càng về sau càng đông và mạnh."""
import random

from Enemy import Boss, Enemy, FlyingEnemy, ShieldEnemy
from enemies_extra import KamikazeEnemy, MothershipBoss, SniperEnemy, TeleportEnemy

ARENA_PLATFORMS = [
    (250, 280, 160, 15), (560, 200, 150, 15), (900, 280, 170, 15), (1150, 160, 150, 15),
    (1400, 280, 170, 15), (1700, 200, 150, 15), (2000, 280, 160, 15),
]


class EndlessDirector:
    BREAK_FRAMES = 180

    def __init__(self):
        self.wave = 0
        self.score = 0
        self.break_timer = 120
        self.banner_timer = 0
        self.in_break = True

    def setup_arena(self, gp, Platform):
        for x, y, w, h in ARENA_PLATFORMS:
            gp.platforms.add(Platform(x, y, w, h))

    def _spawn_x(self, player_x):
        for _ in range(20):
            x = random.randint(80, 2300)
            if abs(x - player_x) > 380:
                return x
        return 2200 if player_x < 1200 else 150

    def spawn_wave(self, gp):
        w = self.wave
        hp_scale = 1.0 + 0.09 * (w - 1)
        px = gp.player.rect.centerx
        if w % 5 == 0:
            boss_hp = 500 + w * 70
            if (w // 5) % 2 == 1:
                boss = Boss(self._spawn_x(px), 330)
                boss.max_hp = boss.hp = boss_hp
            else:
                boss = MothershipBoss(self._spawn_x(px), 70, max_hp=boss_hp)
            gp.boss_group.add(boss)
        count = min(14, 3 + int(w * 1.4))
        pool = [("ground", 5), ("fly", 3 if w >= 2 else 0), ("shield", 2 if w >= 3 else 0),
                ("kami", 2 if w >= 3 else 0), ("sniper", 2 if w >= 4 else 0), ("tele", 2 if w >= 5 else 0)]
        kinds = [k for k, wt in pool for _ in range(wt)]
        for _ in range(count):
            kind = random.choice(kinds)
            x = self._spawn_x(px)
            if kind == "ground":
                e = Enemy(x, 330)
            elif kind == "fly":
                e = FlyingEnemy(x, random.randint(110, 200), fly_range=160)
            elif kind == "shield":
                e = ShieldEnemy(x, 335)
            elif kind == "kami":
                e = KamikazeEnemy(x, 340)
            elif kind == "sniper":
                e = SniperEnemy(x, 330)
            else:
                e = TeleportEnemy(x, random.randint(150, 260))
            e.max_hp = e.hp = int(e.max_hp * hp_scale)
            gp.enemies.add(e)
        gp.apply_difficulty()

    def update(self, gp):
        """Gọi mỗi khung hình khi đang chơi chế độ Vô Tận."""
        if self.banner_timer > 0:
            self.banner_timer -= 1
        if self.in_break:
            self.break_timer -= 1
            if self.break_timer <= 0:
                self.in_break = False
                self.wave += 1
                self.banner_timer = 100
                self.spawn_wave(gp)
                gp.on_wave_start(self.wave)
            return
        if len(gp.enemies) == 0 and not gp.boss_group.sprite:
            self.in_break = True
            self.break_timer = self.BREAK_FRAMES
            self.score += 100 * self.wave
            gp.on_wave_cleared(self.wave)
