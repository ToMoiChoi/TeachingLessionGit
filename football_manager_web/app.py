# -*- coding: utf-8 -*-
import os
import json
import random
import hashlib
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from sqlalchemy import text, inspect

# ----- Import từ package football & sound -----
from football.models import db, Club, Player, Coach, MatchHistory, LeagueStanding, YouthPlayer
from football.classes import PlayerOld, TeamOld, MatchOld
from football.game_engine import simulate_half, simulate_match, calculate_team_strength, run_minutes
from football.team_manager import is_valid_formation, substitute
from football.league_manager import update_standings
from football.save_load import save_game, load_game
import sound

app = Flask(__name__)
app.secret_key = 'doimaykhongla'

# Cấu hình môi trường lưu trữ (Vercel Serverless vs Môi trường máy cục bộ)
IS_VERCEL = bool(os.environ.get('VERCEL'))
if IS_VERCEL:
    db_path = '/tmp/football_manager.db'
    upload_folder = '/tmp/uploads'
    data_folder = '/tmp/data'
    # Tự động sao chép cơ sở dữ liệu mẫu có sẵn sang /tmp khi chạy trên Vercel
    if not os.path.exists(db_path):
        src_db = os.path.join(app.root_path, 'instance', 'football_manager.db')
        if os.path.exists(src_db):
            import shutil
            try:
                shutil.copy2(src_db, db_path)
            except Exception:
                pass
else:
    instance_dir = os.path.join(app.root_path, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    db_path = os.path.join(instance_dir, 'football_manager.db')
    upload_folder = os.path.join(app.root_path, 'static', 'uploads')
    data_folder = os.path.join(app.root_path, 'data')

os.makedirs(upload_folder, exist_ok=True)
os.makedirs(data_folder, exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = upload_folder
app.config['DATA_FOLDER'] = data_folder

db.init_app(app)

# ===== TỰ ĐỘNG THÊM CỘT NẾU CHƯA CÓ =====
with app.app_context():
    db.create_all()
    try:
        inspector = inspect(db.engine)
        player_cols = [col['name'] for col in inspector.get_columns('players')]
        if 'preferred_positions' not in player_cols:
            db.session.execute(text('ALTER TABLE players ADD COLUMN preferred_positions TEXT DEFAULT "[]"'))
        if 'assists' not in player_cols:
            db.session.execute(text('ALTER TABLE players ADD COLUMN assists INTEGER DEFAULT 0'))
        if 'contract_wage' not in player_cols:
            db.session.execute(text('ALTER TABLE players ADD COLUMN contract_wage INTEGER DEFAULT 50000'))
        if 'market_value' not in player_cols:
            db.session.execute(text('ALTER TABLE players ADD COLUMN market_value INTEGER DEFAULT 500000'))
        if 'training_level' not in player_cols:
            db.session.execute(text('ALTER TABLE players ADD COLUMN training_level INTEGER DEFAULT 10'))
        if 'rank_level' not in player_cols:
            db.session.execute(text('ALTER TABLE players ADD COLUMN rank_level INTEGER DEFAULT 1'))
        if 'skill_boost' not in player_cols:
            db.session.execute(text('ALTER TABLE players ADD COLUMN skill_boost INTEGER DEFAULT 2'))
        if 'age' not in player_cols:
            db.session.execute(text('ALTER TABLE players ADD COLUMN age INTEGER DEFAULT 24'))
        if 'height' not in player_cols:
            db.session.execute(text('ALTER TABLE players ADD COLUMN height INTEGER DEFAULT 178'))
        if 'weight' not in player_cols:
            db.session.execute(text('ALTER TABLE players ADD COLUMN weight INTEGER DEFAULT 72'))
        if 'nationality' not in player_cols:
            db.session.execute(text('ALTER TABLE players ADD COLUMN nationality VARCHAR(50) DEFAULT "Việt Nam"'))
        if 'skill_moves' not in player_cols:
            db.session.execute(text('ALTER TABLE players ADD COLUMN skill_moves INTEGER DEFAULT 4'))
        if 'weak_foot' not in player_cols:
            db.session.execute(text('ALTER TABLE players ADD COLUMN weak_foot INTEGER DEFAULT 4'))
        if 'playstyle' not in player_cols:
            db.session.execute(text('ALTER TABLE players ADD COLUMN playstyle VARCHAR(100) DEFAULT "Rê bóng thần tốc"'))
        if 'yellow_cards' not in player_cols:
            db.session.execute(text('ALTER TABLE players ADD COLUMN yellow_cards INTEGER DEFAULT 0'))
        if 'red_cards' not in player_cols:
            db.session.execute(text('ALTER TABLE players ADD COLUMN red_cards INTEGER DEFAULT 0'))

        club_cols = [col['name'] for col in inspector.get_columns('clubs')]
        if 'sponsor_name' not in club_cols:
            db.session.execute(text('ALTER TABLE clubs ADD COLUMN sponsor_name VARCHAR(100) DEFAULT "VietinBank Sport"'))
        if 'sponsor_weekly' not in club_cols:
            db.session.execute(text('ALTER TABLE clubs ADD COLUMN sponsor_weekly INTEGER DEFAULT 250000'))
        if 'sponsor_bonus' not in club_cols:
            db.session.execute(text('ALTER TABLE clubs ADD COLUMN sponsor_bonus INTEGER DEFAULT 150000'))
        if 'trophies' not in club_cols:
            db.session.execute(text('ALTER TABLE clubs ADD COLUMN trophies TEXT DEFAULT "[]"'))

        db.session.commit()
    except Exception:
        pass

POSITIONS = ["GK", "CB", "LB", "RB", "LWB", "RWB", "CDM", "CM", "LM", "RM", "CAM", "LW", "RW", "ST"]
FIRST_NAMES = ["John", "Ethan", "Michael", "David", "James", "Robert", "Thomas", "Daniel", "Paul", "Mark",
               "Steven", "Andrew", "Kenneth", "Joshua", "Kevin", "Brian", "George", "Edward", "Ronald", "Timothy",
               "Jason", "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas", "Eric", "Jonathan", "Stephen", "Larry",
               "Justin", "Scott", "Brandon", "Benjamin", "Samuel", "Raymond", "Gregory", "Frank", "Alexander",
               "Patrick", "Jack", "Dennis", "Jerry", "Tyler", "Aaron", "Jose", "Nathan", "Adam", "Henry", "Zachary"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee",
              "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
              "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
              "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts", "Turner"]


# ===== ĐOẠN MÃ ÂM THANH TỰ ĐỘNG BƠM VÀO TẤT CẢ CÁC TRANG =====
GLOBAL_AUDIO_SNIPPET = """
<!-- TỰ ĐỘNG CHÈN BỘ PHÁT NHẠC FIFA & TIẾNG CLICK (NHỎ GỌN & KÉO THẢ ĐƯỢC) -->
<div id="fifa-player-widget">
    <div class="f-drag-handle" id="fDragHandle" title="Giữ chuột để kéo di chuyển">⋮⋮</div>
    <div class="f-info">
        <span class="f-disc" id="fDisc">💿</span>
        <div class="f-text">
            <span class="f-title" id="fTitle">Love Me Again</span>
            <span class="f-sub">FIFA Soundtrack</span>
        </div>
    </div>
    <div class="f-controls">
        <select id="fSongSelect" title="Chọn bài hát">
            <option value="0">John Newman - Love Me Again</option>
            <option value="1">Glass Animals - Heat Waves</option>
            <option value="2">Joy Crookes - Feet Don't Fail Me Now</option>
        </select>
        <button id="fPrevBtn" title="Bài trước">⏮️</button>
        <button id="fPlayBtn" title="Phát/Dừng">⏸️</button>
        <button id="fNextBtn" title="Bài tiếp">⏭️</button>
        <button id="fShuffleBtn" title="Phát ngẫu nhiên">🔀</button>
        <div class="f-vol">
            <span>🔈</span>
            <input type="range" id="fVolume" min="0" max="1" step="0.05" value="0.35">
            <span>🔊</span>
        </div>
    </div>
</div>

<style>
#fifa-player-widget {
    position: fixed;
    bottom: 14px;
    right: 14px;
    background: rgba(15, 23, 42, 0.92);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(99, 102, 241, 0.4);
    box-shadow: 0 6px 22px rgba(0, 0, 0, 0.6), 0 0 12px rgba(99, 102, 241, 0.25);
    border-radius: 30px;
    padding: 4px 12px;
    display: flex;
    align-items: center;
    gap: 8px;
    z-index: 99999;
    color: #fff;
    font-family: 'Segoe UI', Tahoma, sans-serif;
    font-size: 0.76rem;
    cursor: default;
    user-select: none;
    transition: box-shadow 0.2s, border-color 0.2s;
}
#fifa-player-widget.dragging {
    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.8), 0 0 20px rgba(99, 102, 241, 0.5);
    border-color: #6366f1;
    opacity: 0.95;
    transition: none;
}
.f-drag-handle {
    cursor: grab;
    color: #94a3b8;
    font-size: 0.9rem;
    padding: 2px 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
}
.f-drag-handle:active { cursor: grabbing; color: #fff; }
.f-info { display: flex; align-items: center; gap: 6px; }
.f-disc { font-size: 1.1rem; animation: fSpin 6s linear infinite paused; }
.f-disc.playing { animation-play-state: running; }
@keyframes fSpin { 100% { transform: rotate(360deg); } }
.f-text { display: flex; flex-direction: column; max-width: 95px; }
.f-title { font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #e0e7ff; font-size: 0.75rem; }
.f-sub { font-size: 0.62rem; color: #a5b4fc; }
.f-controls { display: flex; align-items: center; gap: 5px; }
.f-controls button {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #fff;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 0.68rem;
    transition: all 0.15s;
    padding: 0;
}
.f-controls button:hover { background: #4f46e5; transform: scale(1.08); }
.f-controls button.active { background: #10b981; border-color: #10b981; }
#fSongSelect {
    background: #1e293b;
    border: 1px solid rgba(99, 102, 241, 0.4);
    color: #fff;
    padding: 3px 6px;
    border-radius: 12px;
    outline: none;
    font-size: 0.7rem;
    cursor: pointer;
    max-width: 130px;
}
.f-vol { display: flex; align-items: center; gap: 3px; font-size: 0.68rem; }
.f-vol input[type="range"] { width: 50px; height: 3px; cursor: pointer; accent-color: #6366f1; }
@media (max-width: 768px) {
    #fifa-player-widget { border-radius: 14px; padding: 4px 8px; }
    #fSongSelect, .f-vol { display: none; }
}
</style>

<script>
(function() {
    // 1. ĐỒNG NHẤT TIẾNG CLICK.WAV CHO TẤT CẢ CÁC NÚT
    const clickAudio = new Audio('/sounds/sfx/Click.wav');
    clickAudio.volume = 0.5;
    document.addEventListener('click', (e) => {
        if (e.target.closest('a, button, select, input, .btn, [onclick], .tactic-btn')) {
            clickAudio.currentTime = 0;
            clickAudio.play().catch(()=>{});
        }
    });

    // 2. NẾU LÀ TRANG TRẬN ĐẤU THÌ TẮT NHẠC FIFA VÀ ẨN WIDGET
    if (window.location.pathname.includes('/live_match')) {
        const w = document.getElementById('fifa-player-widget');
        if (w) w.style.display = 'none';
        return;
    }

    const widget = document.getElementById('fifa-player-widget');
    const dragHandle = document.getElementById('fDragHandle');

    // ==================== TÍNH NĂNG KÉO THẢ WIDGET (DRAGGABLE) ====================
    let isDragging = false;
    let startX = 0, startY = 0;
    let initialLeft = 0, initialTop = 0;

    // Khôi phục vị trí đã kéo trước đó
    const savedPos = JSON.parse(localStorage.getItem('fifa_widget_pos') || 'null');
    if (savedPos && widget) {
        widget.style.left = `${Math.min(window.innerWidth - 80, Math.max(10, savedPos.left))}px`;
        widget.style.top = `${Math.min(window.innerHeight - 50, Math.max(10, savedPos.top))}px`;
        widget.style.right = 'auto';
        widget.style.bottom = 'auto';
    }

    function onDragStart(e) {
        if (e.target.closest('button, select, input')) return; // Không kéo khi bấm nút
        isDragging = true;
        widget.classList.add('dragging');
        const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
        const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;
        startX = clientX;
        startY = clientY;

        const rect = widget.getBoundingClientRect();
        initialLeft = rect.left;
        initialTop = rect.top;

        widget.style.left = `${initialLeft}px`;
        widget.style.top = `${initialTop}px`;
        widget.style.right = 'auto';
        widget.style.bottom = 'auto';

        document.addEventListener('mousemove', onDragMove);
        document.addEventListener('mouseup', onDragEnd);
        document.addEventListener('touchmove', onDragMove, { passive: false });
        document.addEventListener('touchend', onDragEnd);
    }

    function onDragMove(e) {
        if (!isDragging) return;
        if (e.cancelable) e.preventDefault();
        const clientX = e.type.includes('touch') ? e.touches[0].clientX : e.clientX;
        const clientY = e.type.includes('touch') ? e.touches[0].clientY : e.clientY;

        const dx = clientX - startX;
        const dy = clientY - startY;

        let newLeft = initialLeft + dx;
        let newTop = initialTop + dy;

        // Giới hạn trong màn hình
        const maxLeft = window.innerWidth - widget.offsetWidth - 8;
        const maxTop = window.innerHeight - widget.offsetHeight - 8;
        newLeft = Math.max(8, Math.min(maxLeft, newLeft));
        newTop = Math.max(8, Math.min(maxTop, newTop));

        widget.style.left = `${newLeft}px`;
        widget.style.top = `${newTop}px`;
    }

    function onDragEnd() {
        if (!isDragging) return;
        isDragging = false;
        widget.classList.remove('dragging');
        const rect = widget.getBoundingClientRect();
        localStorage.setItem('fifa_widget_pos', JSON.stringify({ left: rect.left, top: rect.top }));

        document.removeEventListener('mousemove', onDragMove);
        document.removeEventListener('mouseup', onDragEnd);
        document.removeEventListener('touchmove', onDragMove);
        document.removeEventListener('touchend', onDragEnd);
    }

    if (dragHandle) dragHandle.addEventListener('mousedown', onDragStart);
    if (widget) {
        widget.addEventListener('mousedown', (e) => {
            if (e.target === widget || e.target.classList.contains('f-info') || e.target.classList.contains('f-text')) {
                onDragStart(e);
            }
        });
        widget.addEventListener('touchstart', onDragStart, { passive: true });
    }

    // ==================== PHÁT NHẠC FIFA LIÊN TỤC ====================
    const fifaTracks = [
        { title: "Love Me Again", file: "/sounds/bgm/John Newman - Love Me Again.mp3" },
        { title: "Heat Waves", file: "/sounds/bgm/Glass Animals - Heat Waves (Official Video).mp3" },
        { title: "Feet Don't Fail Me Now", file: "/sounds/bgm/Joy Crookes - Feet Don t Fail Me Now (Official Video).mp3" }
    ];

    const audio = new Audio();
    audio.preload = "auto";

    let currentIdx = parseInt(localStorage.getItem('fifa_track_idx') || '0');
    let isShuffle = localStorage.getItem('fifa_shuffle') === 'true';
    let savedVol = parseFloat(localStorage.getItem('fifa_volume') || '0.35');
    let shouldPlay = localStorage.getItem('fifa_is_playing') !== 'false';

    const disc = document.getElementById('fDisc');
    const titleEl = document.getElementById('fTitle');
    const selectEl = document.getElementById('fSongSelect');
    const playBtn = document.getElementById('fPlayBtn');
    const prevBtn = document.getElementById('fPrevBtn');
    const nextBtn = document.getElementById('fNextBtn');
    const shuffleBtn = document.getElementById('fShuffleBtn');
    const volInput = document.getElementById('fVolume');

    audio.volume = savedVol;
    volInput.value = savedVol;
    if (isShuffle) shuffleBtn.classList.add('active');

    function loadAndPlay(idx, startAtTime = 0, triggerPlay = true) {
        currentIdx = (idx + fifaTracks.length) % fifaTracks.length;
        const track = fifaTracks[currentIdx];
        audio.src = track.file;
        titleEl.textContent = track.title;
        selectEl.value = currentIdx;
        localStorage.setItem('fifa_track_idx', currentIdx);
        audio.currentTime = startAtTime;

        if (triggerPlay && shouldPlay) {
            audio.play().then(() => {
                playBtn.textContent = '⏸️';
                disc.classList.add('playing');
                localStorage.setItem('fifa_is_playing', 'true');
            }).catch(() => {
                playBtn.textContent = '▶️';
                disc.classList.remove('playing');
            });
        } else {
            playBtn.textContent = '▶️';
            disc.classList.remove('playing');
        }
    }

    function playNext() {
        let nextIdx;
        if (isShuffle) {
            do {
                nextIdx = Math.floor(Math.random() * fifaTracks.length);
            } while (nextIdx === currentIdx && fifaTracks.length > 1);
        } else {
            nextIdx = currentIdx + 1;
        }
        loadAndPlay(nextIdx, 0, true);
    }

    audio.addEventListener('timeupdate', () => {
        localStorage.setItem('fifa_track_time', audio.currentTime);
    });

    audio.addEventListener('ended', playNext);

    playBtn.addEventListener('click', () => {
        if (audio.paused) {
            shouldPlay = true;
            localStorage.setItem('fifa_is_playing', 'true');
            audio.play().then(() => {
                playBtn.textContent = '⏸️';
                disc.classList.add('playing');
            }).catch(()=>{});
        } else {
            shouldPlay = false;
            localStorage.setItem('fifa_is_playing', 'false');
            audio.pause();
            playBtn.textContent = '▶️';
            disc.classList.remove('playing');
        }
    });

    nextBtn.addEventListener('click', playNext);
    prevBtn.addEventListener('click', () => loadAndPlay(currentIdx - 1, 0, true));

    shuffleBtn.addEventListener('click', () => {
        isShuffle = !isShuffle;
        shuffleBtn.classList.toggle('active', isShuffle);
        localStorage.setItem('fifa_shuffle', isShuffle);
    });

    selectEl.addEventListener('change', (e) => loadAndPlay(parseInt(e.target.value), 0, true));

    volInput.addEventListener('input', (e) => {
        audio.volume = parseFloat(e.target.value);
        localStorage.setItem('fifa_volume', audio.volume);
    });

    const savedTime = parseFloat(localStorage.getItem('fifa_track_time') || '0');
    loadAndPlay(currentIdx, savedTime, shouldPlay);

    document.addEventListener('click', () => {
        if (audio.paused && shouldPlay) {
            audio.play().then(() => {
                playBtn.textContent = '⏸️';
                disc.classList.add('playing');
            }).catch(()=>{});
        }
    }, { once: true });
})();
</script>
"""

# ===== HOOK TỰ ĐỘNG CHÈN VÀO TẤT CẢ TRANG MÀ KHÔNG CẦN SỬA FILE TEMPLATE =====
@app.after_request
def auto_inject_audio_system(response):
    """Tự động chèn hệ thống âm thanh vào TẤT CẢ các trang HTML."""
    if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
        try:
            html = response.get_data(as_text=True)
            if '</body>' in html:
                html = html.replace('</body>', f'{GLOBAL_AUDIO_SNIPPET}\n</body>', 1)
                response.set_data(html)
        except Exception:
            pass
    return response


# ===== HÀM CHUYỂN ĐỔI DB ↔ CLASS CŨ =====
def player_to_old(db_player):
    p = PlayerOld(db_player.name, db_player.position, db_player.attack, db_player.defense, db_player.speed)
    p.stamina = db_player.stamina
    p.goals = db_player.goals
    p.matches_played = db_player.matches_played
    p.overall = db_player.overall
    p.yellow_cards = db_player.yellow_cards
    p.red_cards = db_player.red_cards
    p.preferred_positions = getattr(db_player, 'preferred_positions', '[]')
    return p


def old_to_player(old_player, club_id):
    p = Player(
        name=old_player.name,
        position=old_player.position,
        attack=old_player.attack,
        defense=old_player.defense,
        speed=old_player.speed,
        overall=old_player.overall,
        stamina=old_player.stamina,
        goals=old_player.goals,
        matches_played=old_player.matches_played,
        yellow_cards=old_player.yellow_cards,
        red_cards=old_player.red_cards,
        club_id=club_id,
        assists=0
    )
    p.preferred_positions = getattr(old_player, 'preferred_positions', '[]')
    return p


def club_to_team_old(club):
    players_old = [player_to_old(p) for p in club.players]
    team = TeamOld(club.name, players_old)
    team.formation = club.formation
    team.tactic = club.tactic
    starting_ids = [p.id for p in club.players if p.is_starting]
    if starting_ids:
        indices = [club.players.index(p) for p in club.players if p.id in starting_ids]
        team.starting_xi = indices
    return team


def create_random_players(count=16):
    players = []
    for _ in range(count):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        pos = random.choice(POSITIONS)
        r = random.random()
        if r < 0.6:
            att, deff, spd = random.randint(50, 70), random.randint(50, 70), random.randint(50, 70)
        elif r < 0.9:
            att, deff, spd = random.randint(70, 85), random.randint(70, 85), random.randint(70, 85)
        else:
            att, deff, spd = random.randint(85, 95), random.randint(85, 95), random.randint(85, 95)
        p = PlayerOld(name, pos, att, deff, spd)
        preferred = [pos]
        if random.random() < 0.4:
            other = random.choice([p for p in POSITIONS if p != pos])
            preferred.append(other)
        p.preferred_positions = json.dumps(preferred)
        players.append(p)
    return players


def auto_select_xi(players, formation):
    formation_map = {
        '4-3-3': ['GK', 'LB', 'CB', 'CB', 'RB', 'LW', 'CM', 'CM', 'CM', 'RW', 'ST'],
        '4-2-3-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'CDM', 'LW', 'CAM', 'RW', 'ST'],
        '4-4-2': ['GK', 'LB', 'CB', 'CB', 'RB', 'LM', 'CM', 'CM', 'RM', 'ST', 'ST'],
        '4-3-2-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'CM', 'CM', 'CAM', 'CAM', 'ST'],
        '3-4-3': ['GK', 'CB', 'CB', 'CB', 'LM', 'CM', 'CM', 'RM', 'LW', 'RW', 'ST'],
        '3-5-2': ['GK', 'CB', 'CB', 'CB', 'LWB', 'CDM', 'CM', 'CM', 'RWB', 'ST', 'ST'],
        '5-3-2': ['GK', 'LWB', 'CB', 'CB', 'CB', 'RWB', 'CM', 'CM', 'CM', 'ST', 'ST'],
        '5-4-1': ['GK', 'LWB', 'CB', 'CB', 'CB', 'RWB', 'LM', 'CM', 'CM', 'RM', 'ST']
    }
    required_positions = formation_map.get(formation, formation_map['4-3-3'])

    def calculate_fit(player, position):
        try:
            pref = json.loads(player.preferred_positions) if player.preferred_positions else []
        except Exception:
            pref = []
        bonus = 20 if position in pref else 0
        if position == 'GK':
            stat_score = player.defense * 0.7 + player.speed * 0.3
        elif position in ['LB', 'RB', 'LWB', 'RWB']:
            stat_score = player.defense * 0.5 + player.speed * 0.4 + player.attack * 0.1
        elif position == 'CB':
            stat_score = player.defense * 0.7 + player.speed * 0.2 + player.attack * 0.1
        elif position in ['CDM', 'CM']:
            stat_score = player.defense * 0.4 + player.attack * 0.4 + player.speed * 0.2
        elif position in ['LW', 'RW', 'CAM', 'LM', 'RM']:
            stat_score = player.attack * 0.5 + player.speed * 0.4 + player.defense * 0.1
        elif position in ['ST', 'CF']:
            stat_score = player.attack * 0.6 + player.speed * 0.3 + player.defense * 0.1
        else:
            stat_score = player.overall
        return player.overall * 0.5 + stat_score * 0.3 + bonus * 0.2

    scores = {}
    for pos in required_positions:
        scores[pos] = []
        for p in players:
            fit_score = calculate_fit(p, pos)
            scores[pos].append((p.id, fit_score))
        scores[pos].sort(key=lambda x: x, reverse=True)

    selected = []
    used_ids = set()
    for pos in required_positions:
        for pid, _ in scores[pos]:
            if pid not in used_ids:
                selected.append(pid)
                used_ids.add(pid)
                break
    if len(selected) < 11:
        remaining = [p.id for p in players if p.id not in used_ids]
        while len(selected) < 11 and remaining:
            selected.append(remaining.pop(0))
    return selected


# ===== PHỤC VỤ FILE ÂM THANH =====
@app.route('/sounds/<path:filename>')
def serve_sounds(filename):
    return send_from_directory(os.path.join(app.root_path, 'sounds'), filename)


# ===== CÁC ROUTES GIAO DIỆN CHÍNH =====
@app.route('/')
def index():
    return render_template('index.html')


def generate_balanced_squad(club_id, formation='4-3-3'):
    """Tạo đội hình 18-20 cầu thủ ngẫu nhiên, cân bằng vị trí đầy đủ, không hardcode bất kỳ siêu sao nào."""
    nation_pools = [
        ("Việt Nam", ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Đặng", "Bùi", "Đỗ", "Hồ"], ["Minh", "Quang", "Tuấn", "Hoàng", "Duy", "Đức", "Văn", "Công", "Hùng", "Hải", "Bảo", "Long", "Tiến", "Tài", "Thành"]),
        ("Anh", ["Smith", "Johnson", "Walker", "Rice", "Foden", "Palmer", "Shaw", "Kane", "Stones", "White", "Sterling"], ["Harry", "Declan", "Phil", "Cole", "Luke", "John", "Ben", "Jack", "Marcus", "Mason", "Jude"]),
        ("Tây Ban Nha", ["Garcia", "Rodriguez", "Torres", "Lopez", "Martinez", "Alonso", "Ramos", "Silva", "Pedri", "Gavi"], ["Lucas", "David", "Carlos", "Pablo", "Alvaro", "Sergio", "Ferran", "Diego", "Alejandro"]),
        ("Pháp", ["Mbappe", "Griezmann", "Tchouameni", "Camavinga", "Saliba", "Hernandez", "Kounde", "Dembele"], ["Kylian", "Antoine", "Aurelien", "Eduardo", "William", "Theo", "Jules", "Ousmane", "Kingsley"]),
        ("Brazil", ["Silva", "Santos", "Vinicius", "Rodrygo", "Neymar", "Casemiro", "Ederson", "Alisson", "Paqueta"], ["Gabriel", "Lucas", "Matheus", "Thiago", "Enzo", "Felipe", "Rodrigo", "Joao", "Bruno"]),
        ("Đức", ["Mueller", "Kimmich", "Musiala", "Wirtz", "Kroos", "Gundogan", "Sane", "Havertz", "Rudiger"], ["Thomas", "Joshua", "Florian", "Toni", "Ilkay", "Leroy", "Kai", "Antonio", "Leon"]),
        ("Bỉ", ["De Bruyne", "Courtois", "Lukaku", "Tielemans", "Castagne", "Onana", "Trossard"], ["Kevin", "Romelu", "Youri", "Timothy", "Amadou", "Leandro", "Arthur"]),
        ("Argentina", ["Messi", "Alvarez", "Martinez", "Mac Allister", "Fernandez", "Romero", "De Paul"], ["Julian", "Lautaro", "Alexis", "Enzo", "Cristian", "Rodrigo", "Nicolas"])
    ]

    target_positions = [
        # 11 Đá chính (Phù hợp mọi sơ đồ)
        'GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'CM', 'CAM', 'LW', 'RW', 'ST',
        # 7-8 Dự bị
        'GK', 'CB', 'LWB', 'CM', 'RM', 'LM', 'ST', 'RW'
    ]

    used_names = set()
    players = []

    for i, pos in enumerate(target_positions):
        # Chọn ngẫu nhiên quốc tịch & tên
        nation_info = random.choice(nation_pools)
        nation = nation_info[0]
        first_names = nation_info[2]
        last_names = nation_info[1]

        for _ in range(20):
            fn = random.choice(first_names)
            ln = random.choice(last_names)
            full_name = f"{fn} {ln}"
            if full_name not in used_names:
                used_names.add(full_name)
                break

        # Chỉ số ngẫu nhiên theo vị trí
        if pos == 'GK':
            atk = random.randint(35, 55)
            deff = random.randint(80, 93)
            spd = random.randint(60, 78)
            h = random.randint(188, 198)
            w = random.randint(82, 95)
        elif pos in ['CB', 'LB', 'RB', 'LWB', 'RWB']:
            atk = random.randint(60, 80)
            deff = random.randint(78, 92)
            spd = random.randint(75, 92)
            h = random.randint(176, 193)
            w = random.randint(72, 86)
        elif pos in ['CDM', 'CM', 'CAM', 'LM', 'RM']:
            atk = random.randint(75, 90)
            deff = random.randint(68, 88)
            spd = random.randint(76, 92)
            h = random.randint(172, 186)
            w = random.randint(68, 80)
        else: # ST, LW, RW, CF
            atk = random.randint(82, 95)
            deff = random.randint(45, 70)
            spd = random.randint(84, 96)
            h = random.randint(174, 192)
            w = random.randint(68, 85)

        ovr = round((atk + deff + spd) / 3, 1)
        age = random.randint(19, 32)
        rank = random.randint(1, 4)
        training = random.randint(10, 25)
        skill_boost = random.randint(3, 7)

        p = Player(
            name=full_name,
            position=pos,
            attack=atk,
            defense=deff,
            speed=spd,
            overall=ovr,
            stamina=100.0,
            goals=0,
            assists=0,
            matches_played=0,
            is_starting=(i < 11),
            is_substitute=(i >= 11),
            club_id=club_id,
            training_level=training,
            rank_level=rank,
            skill_boost=skill_boost,
            age=age,
            height=h,
            weight=w,
            nationality=nation,
            skill_moves=random.randint(3, 5),
            weak_foot=random.randint(3, 5),
            contract_wage=random.randint(45000, 110000),
            market_value=int(ovr * random.randint(120000, 180000))
        )
        players.append(p)
        db.session.add(p)

    db.session.commit()
    return players


@app.route('/create_club', methods=['GET', 'POST'])
def create_club():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        league = request.form.get('league', 'Hang 2')
        formation = request.form.get('formation', '4-3-3')
        if len(name) < 2:
            return render_template('create_club.html', error="Tên CLB phải có ít nhất 2 ký tự.")
        club = Club(name=name, league=league, formation=formation, tactic='Can bang', money=80000000)
        db.session.add(club)
        db.session.commit()
        
        # Tạo đội hình 18 cầu thủ cân bằng đầy đủ vị trí
        generate_balanced_squad(club.id, formation)
        
        coach = Coach(name="Pep Guardiola", age=50, nationality="Tây Ban Nha", tactic_preference=formation)
        db.session.add(coach)
        db.session.commit()
        club.coach_id = coach.id
        db.session.commit()
        session['club_id'] = club.id
        session['show_tutorial_welcome'] = True
        return redirect(url_for('squad'))
    return render_template('create_club.html')


@app.route('/dashboard')
def dashboard():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    return render_template('dashboard.html', club=club, team=club, season_complete=(club.round >= 18))


# ===== 1. TÍNH NĂNG HỌC VIỆN TRẺ & SĂN WONDERKIDS =====
SCOUT_HUBS = {
    "vietnam": {
        "name": "Học Viện Trẻ Việt Nam", "cost": 150000,
        "pot_min": 72, "pot_max": 88, "origin": "Học Viện JMG / PVF",
        "first_names": ["Minh", "Quang", "Tuấn", "Hoàng", "Duy", "Đức", "Văn", "Công", "Hùng", "Hải", "Bảo", "Long"],
        "last_names": ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Đặng", "Bùi", "Đỗ", "Hồ"]
    },
    "south_america": {
        "name": "Lò Đào Tạo Nam Mỹ", "cost": 450000,
        "pot_min": 82, "pot_max": 95, "origin": "Santos / Boca Juniors",
        "first_names": ["Lucas", "Mateo", "Gabriel", "Thiago", "Enzo", "Felipe", "Rodrigo", "Joao", "Diego", "Julian"],
        "last_names": ["Silva", "Santos", "Oliveira", "Rodriguez", "Martinez", "Alvarez", "Fernandez", "Gomez", "Costa"]
    },
    "europe": {
        "name": "Lò Đào Tạo Châu Âu (Wonderkids)", "cost": 850000,
        "pot_min": 88, "pot_max": 99, "origin": "La Masia / Carrington / Ajax",
        "first_names": ["Leo", "Lamine", "Jude", "Gavi", "Pedri", "Kylian", "Erling", "Florian", "Arda", "Jamal"],
        "last_names": ["Yamal", "Bellingham", "Musiala", "Wirtz", "Guler", "Davies", "Camavinga", "Mainoo", "Endrick"]
    },
    "africa": {
        "name": "Học Viện Thể Lực Châu Phi", "cost": 300000,
        "pot_min": 76, "pot_max": 92, "origin": "Right to Dream / ASEC",
        "first_names": ["Victor", "Sadio", "Mo", "Achraf", "Amad", "Kudus", "Osimhen", "Bissouma", "Pape"],
        "last_names": ["Diallo", "Sarr", "Toure", "Kone", "Mensah", "Traore", "Camara", "Diop", "Cisse"]
    }
}

@app.route('/youth_academy')
def youth_academy():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    youth_players = YouthPlayer.query.filter_by(club_id=club.id).all()
    scout_results = session.get('scout_results', [])
    message = session.pop('youth_message', None)
    error = session.pop('youth_error', None)
    return render_template('youth_academy.html', club=club, youth_players=youth_players,
                           scout_results=scout_results, message=message, error=error)

@app.route('/scout_wonderkids', methods=['POST'])
def scout_wonderkids():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    region = request.form.get('region', 'vietnam')
    hub = SCOUT_HUBS.get(region, SCOUT_HUBS['vietnam'])
    cost = hub['cost']

    if club.money < cost:
        session['youth_error'] = f"Ngân sách không đủ ${cost:,} để cử Scout đến {hub['name']}!"
        return redirect(url_for('youth_academy'))

    club.money -= cost
    db.session.commit()

    positions = ['GK', 'CB', 'LB', 'RB', 'CDM', 'CM', 'CAM', 'LW', 'RW', 'ST']
    talents = []
    for _ in range(3):
        first = random.choice(hub['first_names'])
        last = random.choice(hub['last_names'])
        pos = random.choice(positions)
        age = random.randint(15, 18)
        pot = random.randint(hub['pot_min'], hub['pot_max'])
        cur_ovr = random.randint(max(52, pot - 24), pot - 10)
        att = min(99, cur_ovr + random.randint(-6, 6))
        deff = min(99, cur_ovr + random.randint(-6, 6))
        spd = min(99, cur_ovr + random.randint(-6, 6))
        if region == 'africa':
            spd = min(99, spd + 10)
        elif region == 'south_america':
            att = min(99, att + 6)
        talents.append({
            "name": f"{last} {first}" if region == 'vietnam' else f"{first} {last}",
            "position": pos, "age": age, "overall": cur_ovr, "potential": pot,
            "attack": att, "defense": deff, "speed": spd, "scout_origin": hub['origin']
        })

    session['scout_results'] = talents
    session['youth_message'] = f"Tuyển trạch viên đã phát hiện {len(talents)} tài năng trẻ tại {hub['name']}!"
    return redirect(url_for('youth_academy'))

@app.route('/sign_youth_player', methods=['POST'])
def sign_youth_player():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))

    scout_results = session.get('scout_results', [])
    talent_idx = request.form.get('talent_index', type=int)

    talent = None
    if talent_idx is not None and 0 <= talent_idx < len(scout_results):
        talent = scout_results[talent_idx]
    else:
        raw_data = request.form.get('talent_data')
        if raw_data:
            try:
                talent = json.loads(raw_data)
            except Exception:
                try:
                    import ast
                    talent = ast.literal_eval(raw_data)
                except Exception:
                    talent = None

    if not talent:
        session['youth_error'] = "Không tìm thấy thông tin cầu thủ trẻ."
        return redirect(url_for('youth_academy'))

    yp = YouthPlayer(
        name=talent['name'], position=talent['position'], age=talent.get('age', 16),
        overall=talent['overall'], potential=talent['potential'],
        attack=talent['attack'], defense=talent['defense'], speed=talent['speed'],
        scout_origin=talent.get('scout_origin', 'Học viện CLB'), club_id=club.id
    )
    db.session.add(yp)
    db.session.commit()

    scout_results = [t for t in scout_results if t.get('name') != talent['name']]
    session['scout_results'] = scout_results
    session['youth_message'] = f"Đã ký hợp đồng đưa tài năng trẻ {talent['name']} (Tiềm năng: {talent['potential']}) vào Học viện!"
    return redirect(url_for('youth_academy'))

@app.route('/train_youth_player', methods=['POST'])
def train_youth_player():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    youth_id = request.form.get('youth_id', type=int)
    yp = db.session.get(YouthPlayer, youth_id)
    cost = 50000
    if not yp or yp.club_id != club.id:
        session['youth_error'] = "Không tìm thấy học viên."
        return redirect(url_for('youth_academy'))
    if club.money < cost:
        session['youth_error'] = "Ngân sách không đủ $50,000 cho buổi huấn luyện chuyên sâu."
        return redirect(url_for('youth_academy'))
    if yp.overall >= yp.potential:
        session['youth_error'] = f"{yp.name} đã chạm trần tiềm năng tối đa ({yp.potential} OVR)!"
        return redirect(url_for('youth_academy'))

    club.money -= cost
    yp.attack = min(yp.potential, yp.attack + random.randint(1, 3))
    yp.defense = min(yp.potential, yp.defense + random.randint(1, 3))
    yp.speed = min(yp.potential, yp.speed + random.randint(1, 3))
    yp.overall = round((yp.attack + yp.defense + yp.speed) / 3, 1)
    yp.training_points += 15
    db.session.commit()

    session['youth_message'] = f"Huấn luyện thành công! {yp.name} đã tăng lên {yp.overall} OVR!"
    return redirect(url_for('youth_academy'))

@app.route('/promote_youth/<int:youth_id>', methods=['POST'])
def promote_youth(youth_id):
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    yp = db.session.get(YouthPlayer, youth_id)
    if not yp or yp.club_id != club.id:
        session['youth_error'] = "Không tìm thấy học viên."
        return redirect(url_for('youth_academy'))

    senior_player = Player(
        name=yp.name, position=yp.position, attack=yp.attack, defense=yp.defense,
        speed=yp.speed, overall=yp.overall, stamina=100.0,
        preferred_positions=json.dumps([yp.position]),
        is_starting=False, is_substitute=True, club_id=club.id
    )
    db.session.add(senior_player)
    db.session.delete(yp)
    db.session.commit()

    session['youth_message'] = f"🚀 Chúc mừng! Cầu thủ trẻ {senior_player.name} ({senior_player.position} - {senior_player.overall} OVR) đã chính thức được đôn lên Đội 1!"
    return redirect(url_for('youth_academy'))

@app.route('/release_youth/<int:youth_id>', methods=['POST'])
def release_youth(youth_id):
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    yp = db.session.get(YouthPlayer, youth_id)
    if yp and yp.club_id == club.id:
        name = yp.name
        db.session.delete(yp)
        db.session.commit()
        session['youth_message'] = f"Đã thanh lý hợp đồng đào tạo với học viên {name}."
    return redirect(url_for('youth_academy'))


# ===== 2. TÍNH NĂNG TÀI TRỢ & PHÒNG TRUYỀN THỐNG =====
@app.route('/sponsorship')
def sponsorship():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    message = session.pop('sponsor_message', None)
    return render_template('sponsorship.html', club=club, message=message)

@app.route('/sign_sponsor', methods=['POST'])
def sign_sponsor():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    sponsor_name = request.form.get('sponsor_name', 'VietinBank Sport')
    sponsor_weekly = request.form.get('sponsor_weekly', type=int) or 250000
    sponsor_bonus = request.form.get('sponsor_bonus', type=int) or 150000

    club.sponsor_name = sponsor_name
    club.sponsor_weekly = sponsor_weekly
    club.sponsor_bonus = sponsor_bonus
    db.session.commit()

    session['sponsor_message'] = f"🎉 Ký kết thành công hợp đồng tài trợ mới cùng {sponsor_name}! Trợ cấp: ${sponsor_weekly:,}/tuần."
    return redirect(url_for('sponsorship'))

@app.route('/trophy_room')
def trophy_room():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    try:
        trophies_list = json.loads(club.trophies or '[]')
    except Exception:
        trophies_list = []
    return render_template('trophy_room.html', club=club, trophies_list=trophies_list)


# ===== 3. THỊ TRƯỜNG CHUYỂN NHƯỢNG & ĐÀM PHÁN GIÁ =====
def build_transfer_market(club):
    rng = random.Random(f"market-{club.id}-{club.season}-{club.round}")
    positions = ['GK', 'CB', 'LB', 'RB', 'CM', 'CAM', 'LW', 'RW', 'ST']
    candidates = []
    base_ovr = 75 if club.league == "Hang 1" else (84 if club.league == "Champions League" else 64)
    for index in range(6):
        overall = rng.randint(base_ovr - 4, base_ovr + 8)
        candidates.append({
            'id': f'{club.season}-{club.round}-{index}',
            'name': f'{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}',
            'position': rng.choice(positions), 'overall': overall,
            'attack': min(95, overall + rng.randint(-8, 8)),
            'defense': min(95, overall + rng.randint(-8, 8)),
            'speed': min(95, overall + rng.randint(-8, 8)),
            'price': overall * 75000
        })
    return candidates

def build_incoming_offers(club, squad_players):
    rng = random.Random(f"offers-{club.id}-{club.season}-{club.round}")
    offers = []
    if len(squad_players) > 12 and rng.random() < 0.7:
        target = rng.choice(squad_players)
        opp_names = ["Hà Nội FC", "Công An Hà Nội", "Thể Công Viettel", "Real Madrid", "Manchester City", "Paris Saint-Germain"]
        offer_club = rng.choice(opp_names)
        premium = rng.uniform(1.1, 1.4)
        offer_price = int(target.overall * 70000 * premium)
        offers.append({
            "id": f"offer-{target.id}-{club.round}",
            "player_id": target.id,
            "player_name": target.name,
            "club_name": offer_club,
            "offer_price": offer_price
        })
    return offers

@app.route('/transfer_market', methods=['GET', 'POST'])
def transfer_market():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))

    squad_players = Player.query.filter_by(club_id=club.id).all()
    market = session.get('transfer_market')
    if market is None:
        market = build_transfer_market(club)
        session['transfer_market'] = market

    incoming_offers = session.get('incoming_offers')
    if incoming_offers is None:
        incoming_offers = build_incoming_offers(club, squad_players)
        session['incoming_offers'] = incoming_offers

    message = None
    error = None

    if request.method == 'POST':
        action = request.form.get('action', 'buy_now')

        if action == 'buy_now':
            candidate_id = request.form.get('candidate_id')
            candidate = next((item for item in market if item['id'] == candidate_id), None)
            if not candidate:
                error = 'Cầu thủ này không còn trên thị trường.'
            elif club.money < candidate['price']:
                error = f'Ngân sách không đủ ${candidate["price"]:,} để mua cầu thủ này.'
            else:
                player = Player(name=candidate['name'], position=candidate['position'], attack=candidate['attack'],
                                defense=candidate['defense'], speed=candidate['speed'], overall=candidate['overall'],
                                stamina=100.0, preferred_positions=json.dumps([candidate['position']]), club_id=club.id)
                db.session.add(player)
                club.money -= candidate['price']
                market.remove(candidate)
                session['transfer_market'] = market
                session.modified = True
                db.session.commit()
                message = f"✅ Đã ký hợp đồng thành công với {player.name}!"

        elif action == 'negotiate_bid':
            candidate_id = request.form.get('candidate_id')
            discount = float(request.form.get('bid_discount', 1.0))
            candidate = next((item for item in market if item['id'] == candidate_id), None)
            if not candidate:
                error = 'Cầu thủ này không còn trên thị trường.'
            else:
                bid_price = int(candidate['price'] * discount)
                if club.money < bid_price:
                    error = f'Ngân sách không đủ ${bid_price:,} cho mức giá đề xuất này.'
                else:
                    success_rate = 0.6 if discount <= 0.85 else (0.85 if discount <= 0.90 else 0.98)
                    if random.random() <= success_rate:
                        player = Player(name=candidate['name'], position=candidate['position'], attack=candidate['attack'],
                                        defense=candidate['defense'], speed=candidate['speed'], overall=candidate['overall'],
                                        stamina=100.0, preferred_positions=json.dumps([candidate['position']]), club_id=club.id)
                        db.session.add(player)
                        club.money -= bid_price
                        market.remove(candidate)
                        session['transfer_market'] = market
                        session.modified = True
                        db.session.commit()
                        saved = candidate['price'] - bid_price
                        message = f"🎉 Đàm phán thành công! CLB đối tác đồng ý bán {player.name} với giá ${bid_price:,} (Tiết kiệm được ${saved:,})!"
                    else:
                        error = f"❌ CLB đối tác đã từ chối lời đề nghị trả giá rẻ hơn {int((1-discount)*100)}% của bạn!"

        elif action == 'sell_player':
            player_id = request.form.get('player_id', type=int)
            p = db.session.get(Player, player_id)
            if len(squad_players) <= 11:
                error = 'Không thể bán vì đội hình tối thiểu cần 11 cầu thủ!'
            elif p and p.club_id == club.id:
                sale_value = int(p.overall * 65000)
                club.money += sale_value
                p_name = p.name
                db.session.delete(p)
                db.session.commit()
                squad_players = Player.query.filter_by(club_id=club.id).all()
                message = f"📤 Đã bán {p_name} và thu về +${sale_value:,} vào ngân sách!"

        elif action == 'accept_offer':
            offer_id = request.form.get('offer_id')
            offer = next((o for o in incoming_offers if o['id'] == offer_id), None)
            if offer:
                p = db.session.get(Player, offer['player_id'])
                if p and p.club_id == club.id and len(squad_players) > 11:
                    club.money += offer['offer_price']
                    db.session.delete(p)
                    incoming_offers.remove(offer)
                    session['incoming_offers'] = incoming_offers
                    session.modified = True
                    db.session.commit()
                    squad_players = Player.query.filter_by(club_id=club.id).all()
                    message = f"🤝 Đã hoàn tất chuyển nhượng! {p.name} gia nhập {offer['club_name']} với giá ${offer['offer_price']:,}!"
                else:
                    error = 'Không thể bán cầu thủ này hoặc đội hình không đủ số lượng tối thiểu!'

        elif action == 'reject_offer':
            offer_id = request.form.get('offer_id')
            incoming_offers = [o for o in incoming_offers if o['id'] != offer_id]
            session['incoming_offers'] = incoming_offers
            session.modified = True
            message = "Đã từ chối lời đề nghị chuyển nhượng."

    return render_template('transfer_market.html', club=club, candidates=market,
                           squad_players=squad_players, incoming_offers=incoming_offers,
                           message=message, error=error)


@app.route('/training', methods=['GET', 'POST'])
def training():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    players = Player.query.filter_by(club_id=club.id).order_by(Player.overall.desc()).all()
    message = None
    error = None
    if request.method == 'POST':
        player = db.session.get(Player, request.form.get('player_id', type=int))
        focus = request.form.get('focus')
        cost = 100000
        if not player or player.club_id != club.id:
            error = 'Không tìm thấy cầu thủ.'
        elif focus not in {'attack', 'defense', 'speed'}:
            error = 'Kiểu tập luyện không hợp lệ.'
        elif club.money < cost:
            error = 'Ngân sách không đủ cho buổi tập này.'
        elif getattr(player, focus) >= 99:
            error = f'{player.name} đã đạt chỉ số tối đa ở kỹ năng này.'
        else:
            setattr(player, focus, min(99, getattr(player, focus) + 2))
            player.overall = round((player.attack + player.defense + player.speed) / 3, 1)
            player.experience = getattr(player, 'experience', 0) + 10
            club.money -= cost
            db.session.commit()
            message = f"{player.name} đã tăng 2 điểm {focus} sau buổi tập!"
    return render_template('training.html', club=club, players=players, message=message, error=error)


def generate_player_svg_avatar(name, position="CM", seed_num=0):
    """Tạo vector SVG chân dung cầu thủ bóng đá độc nhất, sắc nét, ngẫu nhiên theo tên & ID."""
    h = int(hashlib.md5(f"{name}_{seed_num}".encode('utf-8')).hexdigest(), 16)
    
    skin_tones = [
        ("#fcd5b5", "#e6ab84", "#cb8c66"),
        ("#f1c29b", "#d6986e", "#b5774d"),
        ("#e0ab76", "#bd824d", "#9a6231"),
        ("#c68642", "#9e5b22", "#773d10"),
        ("#8d5524", "#61350f", "#402005"),
        ("#583515", "#391f09", "#241002"),
        ("#fbe3d2", "#e8baa0", "#ce9376"),
        ("#a86835", "#7c4419", "#562b0c")
    ]
    skin = skin_tones[h % len(skin_tones)]
    
    hair_colors = [
        ("#18181b", "#09090b"),
        ("#271810", "#180e0a"),
        ("#422314", "#261208"),
        ("#78350f", "#451a03"),
        ("#d97706", "#92400e"),
        ("#f59e0b", "#b45309"),
        ("#94a3b8", "#475569"),
        ("#b91c1c", "#7f1d1d")
    ]
    hair = hair_colors[(h >> 3) % len(hair_colors)]
    
    kit_palettes = [
        ("#0284c7", "#0369a1", "#38bdf8", "#ffffff"),
        ("#dc2626", "#991b1b", "#f87171", "#ffffff"),
        ("#16a34a", "#15803d", "#4ade80", "#ffffff"),
        ("#7c3aed", "#5b21b6", "#a78bfa", "#fef08a"),
        ("#d97706", "#b45309", "#fbbf24", "#1e293b"),
        ("#0f172a", "#020617", "#38bdf8", "#38bdf8"),
        ("#e11d48", "#9f1239", "#fda4af", "#ffffff"),
        ("#2563eb", "#1d4ed8", "#60a5fa", "#ffffff"),
    ]
    kit = kit_palettes[(h >> 6) % len(kit_palettes)]
    
    style_idx = (h >> 9) % 7
    has_beard = ((h >> 12) % 3) == 0
    has_mustache = ((h >> 14) % 4) == 0
    has_headband = ((h >> 16) % 5) == 0
    avatar_id = f"av_{h & 0xffffff}"
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 185" width="100%" height="100%" class="fc-player-avatar-svg">
  <defs>
    <radialGradient id="{avatar_id}_glow" cx="50%" cy="30%" r="65%">
      <stop offset="0%" stop-color="{kit[2]}" stop-opacity="0.55"/>
      <stop offset="60%" stop-color="{kit[1]}" stop-opacity="0.2"/>
      <stop offset="100%" stop-color="#030712" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="{avatar_id}_skin" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{skin[0]}"/>
      <stop offset="70%" stop-color="{skin[1]}"/>
      <stop offset="100%" stop-color="{skin[2]}"/>
    </linearGradient>
    <linearGradient id="{avatar_id}_hair" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{hair[0]}"/>
      <stop offset="100%" stop-color="{hair[1]}"/>
    </linearGradient>
    <linearGradient id="{avatar_id}_kit" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{kit[0]}"/>
      <stop offset="100%" stop-color="{kit[1]}"/>
    </linearGradient>
    <linearGradient id="{avatar_id}_trim" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{kit[2]}"/>
      <stop offset="100%" stop-color="{kit[3]}"/>
    </linearGradient>
  </defs>

  <circle cx="80" cy="80" r="75" fill="url(#{avatar_id}_glow)"/>
  <path d="M40 0 L80 90 L120 0 Z" fill="{kit[2]}" opacity="0.08"/>

  <!-- Athletic Jersey & Shoulders -->
  <g id="body">
    <path d="M22 185 C24 150 42 135 58 130 L68 128 L80 142 L92 128 L102 130 C118 135 136 150 138 185 Z" fill="url(#{avatar_id}_kit)"/>
    <path d="M54 135 L80 162 L106 135 L100 132 L80 152 L60 132 Z" fill="url(#{avatar_id}_trim)" opacity="0.85"/>
    <path d="M42 165 L80 185 L118 165 L112 160 L80 178 L48 160 Z" fill="url(#{avatar_id}_trim)" opacity="0.5"/>
    <path d="M66 128 L80 144 L94 128 L88 124 L80 133 L72 124 Z" fill="{kit[3]}"/>
    <circle cx="104" cy="155" r="7" fill="{kit[3]}" opacity="0.9"/>
    <path d="M101 155 L104 151 L107 155 L104 158 Z" fill="{kit[0]}"/>
  </g>

  <!-- Neck -->
  <g id="neck">
    <path d="M68 106 L68 130 L92 130 L92 106 Z" fill="url(#{avatar_id}_skin)"/>
    <path d="M68 106 C74 120 86 120 92 106 L92 118 C86 126 74 126 68 118 Z" fill="{skin[2]}" opacity="0.4"/>
  </g>

  <!-- Head & Face Base -->
  <g id="head">
    <ellipse cx="50" cy="88" rx="5" ry="9" fill="url(#{avatar_id}_skin)"/>
    <ellipse cx="110" cy="88" rx="5" ry="9" fill="url(#{avatar_id}_skin)"/>
    <ellipse cx="51" cy="88" rx="2.5" ry="5" fill="{skin[2]}" opacity="0.4"/>
    <ellipse cx="109" cy="88" rx="2.5" ry="5" fill="{skin[2]}" opacity="0.4"/>

    <path d="M52 75 C50 100 58 118 80 118 C102 118 110 100 108 75 C108 50 102 42 80 42 C58 42 52 50 52 75 Z" fill="url(#{avatar_id}_skin)"/>

    <path d="M59 70 Q67 66 74 69" stroke="{hair[1]}" stroke-width="2.6" stroke-linecap="round" fill="none"/>
    <path d="M86 69 Q93 66 101 70" stroke="{hair[1]}" stroke-width="2.6" stroke-linecap="round" fill="none"/>

    <g fill="#ffffff">
      <ellipse cx="67" cy="76" rx="5" ry="3.2"/>
      <ellipse cx="93" cy="76" rx="5" ry="3.2"/>
    </g>
    <circle cx="67.5" cy="76" r="2.2" fill="#1e1e24"/>
    <circle cx="93.5" cy="76" r="2.2" fill="#1e1e24"/>
    <circle cx="68.5" cy="75" r="0.8" fill="#ffffff"/>
    <circle cx="94.5" cy="75" r="0.8" fill="#ffffff"/>

    <path d="M80 73 L80 88 L84 89 L76 89" stroke="{skin[2]}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    <path d="M72 99 Q80 103 88 99" stroke="{skin[2]}" stroke-width="2.2" stroke-linecap="round" fill="none"/>
'''

    if has_beard:
        svg += f'''
    <path d="M56 86 C58 112 66 118 80 118 C94 118 102 112 104 86 C100 102 92 110 80 110 C68 110 60 102 56 86 Z" fill="{hair[1]}" opacity="0.65"/>
'''
    if has_mustache:
        svg += f'''
    <path d="M72 95 Q80 93 88 95 Q80 97 72 95 Z" fill="{hair[1]}" opacity="0.75"/>
'''

    svg += '''
  </g>
  <g id="hair">
'''

    if style_idx == 0:
        svg += f'''
    <path d="M50 72 C48 50 56 36 80 34 C104 36 112 50 110 72 C108 55 102 46 80 46 C58 46 52 55 50 72 Z" fill="url(#{avatar_id}_hair)"/>
    <path d="M54 48 L60 30 L66 42 L74 26 L80 40 L88 28 L94 42 L102 32 L106 50 C96 42 64 42 54 48 Z" fill="url(#{avatar_id}_hair)"/>
'''
    elif style_idx == 1:
        svg += f'''
    <path d="M50 70 C48 58 52 50 56 46 C60 30 72 24 82 24 C94 24 104 32 106 46 C110 52 112 60 110 70 C106 54 100 48 80 48 C60 48 54 54 50 70 Z" fill="url(#{avatar_id}_hair)"/>
    <path d="M56 44 C62 26 76 22 92 25 C104 27 108 38 106 46 C94 38 68 38 56 44 Z" fill="{hair[0]}"/>
'''
    elif style_idx == 2:
        svg += f'''
    <path d="M46 72 C44 48 48 30 80 28 C112 30 116 48 114 72 C110 52 104 44 80 44 C56 44 50 52 46 72 Z" fill="url(#{avatar_id}_hair)"/>
    <circle cx="60" cy="38" r="10" fill="url(#{avatar_id}_hair)"/>
    <circle cx="76" cy="32" r="11" fill="url(#{avatar_id}_hair)"/>
    <circle cx="92" cy="34" r="10" fill="url(#{avatar_id}_hair)"/>
    <circle cx="104" cy="42" r="9" fill="url(#{avatar_id}_hair)"/>
    <circle cx="52" cy="48" r="8" fill="url(#{avatar_id}_hair)"/>
'''
    elif style_idx == 3:
        svg += f'''
    <path d="M50 70 C48 52 54 40 76 34 C98 28 112 38 112 58 C112 66 110 72 108 72 C104 56 96 46 78 46 C60 46 54 56 50 70 Z" fill="url(#{avatar_id}_hair)"/>
    <path d="M52 48 C64 32 88 28 110 36 C102 44 84 42 62 48 Z" fill="{hair[0]}"/>
'''
    elif style_idx == 4:
        svg += f'''
    <path d="M51 72 C49 52 55 40 80 38 C105 40 111 52 109 72 C107 58 102 48 80 48 C58 48 53 58 51 72 Z" fill="url(#{avatar_id}_hair)"/>
'''
    elif style_idx == 5:
        svg += f'''
    <path d="M48 82 C44 52 52 32 80 30 C108 32 116 52 112 82 C108 60 102 48 80 48 C58 48 52 60 48 82 Z" fill="url(#{avatar_id}_hair)"/>
    <path d="M46 76 C42 96 46 110 50 120 C50 105 52 90 54 80 Z" fill="url(#{avatar_id}_hair)"/>
    <path d="M114 76 C118 96 114 110 110 120 C110 105 108 90 106 80 Z" fill="url(#{avatar_id}_hair)"/>
'''
        if has_headband:
            svg += f'''
    <path d="M48 64 C64 56 96 56 112 64 L110 70 C96 62 64 62 50 70 Z" fill="{kit[3]}"/>
'''
    else:
        svg += f'''
    <path d="M48 70 C46 48 54 36 80 34 C106 36 114 48 112 70 C108 52 100 44 80 44 C60 44 52 52 48 70 Z" fill="url(#{avatar_id}_hair)"/>
    <path d="M50 56 C44 72 44 95 48 114 L52 112 C48 95 48 74 54 58 Z" fill="url(#{avatar_id}_hair)"/>
    <path d="M58 46 C54 66 54 90 58 110 L62 108 C58 90 58 68 62 48 Z" fill="url(#{avatar_id}_hair)"/>
    <path d="M102 46 C106 66 106 90 102 110 L98 108 C102 90 102 68 98 48 Z" fill="url(#{avatar_id}_hair)"/>
    <path d="M110 56 C116 72 116 95 112 114 L108 112 C112 95 112 74 106 58 Z" fill="url(#{avatar_id}_hair)"/>
'''

    svg += f'''
  </g>
  <path d="M52 74 C50 98 58 116 80 116 C102 116 110 98 108 74" stroke="{kit[2]}" stroke-width="1.2" stroke-opacity="0.5" fill="none"/>
</svg>'''
    return svg


def enrich_player_fc(p, club=None):
    """Làm giàu dữ liệu cầu thủ chuẩn giao diện FC Mobile (FUT / FC 24/25)."""
    name_str = (p.name or "Player").strip()
    name_parts = name_str.split()
    if len(name_parts) >= 2:
        first_name = " ".join(name_parts[:-1]).upper()
        last_name = name_parts[-1].upper()
    else:
        first_name = "CẦU THỦ"
        last_name = name_str.upper()

    t_lvl = getattr(p, 'training_level', 10) or 10
    r_lvl = getattr(p, 'rank_level', 1) or 1
    s_boost = getattr(p, 'skill_boost', 2) or 2
    
    # Tính OVR và chỉ số theo chuẩn FC Mobile
    base_ovr = int(round(p.overall or 60))
    fc_ovr = int(base_ovr + (r_lvl - 1) * 3 + (t_lvl // 5))
    
    stat_bonus = (r_lvl - 1) * 2 + (t_lvl // 4)
    pac = int(p.speed + stat_bonus)
    sho = int(p.attack + stat_bonus)
    pas = int(round(p.attack * 0.6 + p.defense * 0.4) + stat_bonus)
    dri = int(round(p.speed * 0.7 + p.attack * 0.3) + stat_bonus)
    deff = int(p.defense + stat_bonus)
    phy = int(round(p.stamina * 0.7 + p.defense * 0.3) + stat_bonus)
    
    pos = (p.position or "CM").upper()
    if pos in ['LW', 'RW', 'LM', 'RM']:
        playstyle_name = "Rê bóng bứt tốc thần sầu"
        playstyle_icon = "⚡"
        playstyle_desc = "Tăng 15% tốc độ bứt phá qua người và khả năng khống chế bóng dính chân khi tăng tốc."
        sec_pos = "LW, RW" if pos in ['LW', 'RW'] else "LM, RM"
    elif pos in ['ST', 'CF']:
        playstyle_name = "Cây săn bàn sát thủ"
        playstyle_icon = "🎯"
        playstyle_desc = "Khả năng dứt điểm 1 chạm uy lực, chọn vị trí đánh đầu và sút xa hiểm hóc trong vòng cấm."
        sec_pos = "ST, CF"
    elif pos in ['CAM', 'CM']:
        playstyle_name = "Nhạc trưởng kiến tạo ma thuật"
        playstyle_icon = "🪄"
        playstyle_desc = "Nhãn quan chiến thuật phi phàm, chọc khe bổng xé toang hàng phòng ngự đối phương."
        sec_pos = "CAM, CM"
    elif pos in ['CDM']:
        playstyle_name = "Máy quét bọc lót toàn diện"
        playstyle_icon = "🛡️"
        playstyle_desc = "Cắt bóng thông minh, tranh chấp áp sát quyết liệt làm nản lòng mọi tiền vệ tấn công."
        sec_pos = "CDM, CM"
    elif pos in ['CB', 'LB', 'RB', 'LWB', 'RWB']:
        playstyle_name = "Bức tường thép không thể xuyên phá"
        playstyle_icon = "🧱"
        playstyle_desc = "Xoạc bóng chính xác, không chiến mạnh mẽ và kèm người cực kỳ chắc chắn."
        sec_pos = "CB, LB, RB"
    elif pos == 'GK':
        playstyle_name = "Bạch tuộc phản xạ xuất thần"
        playstyle_icon = "🧤"
        playstyle_desc = "Phản xạ xuất thần trong cự ly gần, đổ người bay người cản phá phạt đền siêu đẳng."
        sec_pos = "GK"
    else:
        playstyle_name = "Chiến binh công thủ toàn diện"
        playstyle_icon = "⭐"
        playstyle_desc = "Lên công về thủ nhịp nhàng, đóng góp tích cực vào lối chơi tập thể."
        sec_pos = pos

    # Chi tiết 24+ thuộc tính chuyên sâu
    attrs = {
        "pace": {
            "acceleration": int(min(250, pac + 3)),
            "sprint_speed": int(min(250, pac - 1))
        },
        "shooting": {
            "finishing": int(min(250, sho + (8 if pos in ['ST', 'LW', 'RW'] else 0))),
            "shot_power": int(min(250, sho + 4)),
            "long_shots": int(min(250, sho - 2)),
            "volleys": int(min(250, sho - 4)),
            "penalties": int(min(250, sho + 3)),
            "positioning": int(min(250, int(round((sho + dri) / 2))))
        },
        "passing": {
            "vision": int(min(250, pas + (6 if pos in ['CAM', 'CM'] else 0))),
            "short_passing": int(min(250, pas + 4)),
            "long_passing": int(min(250, pas - 2)),
            "crossing": int(min(250, pas + (8 if pos in ['LW', 'RW', 'LB', 'RB'] else 0))),
            "free_kick": int(min(250, pas + 2)),
            "curve": int(min(250, int(round((pas + sho) / 2))))
        },
        "dribbling": {
            "agility": int(min(250, dri + 5)),
            "balance": int(min(250, dri + 1)),
            "reactions": int(min(250, int(round((dri + pac) / 2)))),
            "ball_control": int(min(250, dri + 4)),
            "dribbling": int(min(250, dri + 6)),
            "composure": int(min(250, int(round(p.overall + 5))))
        },
        "defending": {
            "interceptions": int(min(250, deff + (6 if pos in ['CB', 'CDM'] else 0))),
            "heading_accuracy": int(min(250, int(round((deff + phy) / 2)))),
            "marking": int(min(250, deff + 4)),
            "standing_tackle": int(min(250, deff + 5)),
            "sliding_tackle": int(min(250, deff - 2))
        },
        "physical": {
            "jumping": int(min(250, int(round((phy + pac) / 2)))),
            "stamina": int(round(p.stamina or 100)),
            "strength": int(min(250, phy + (6 if pos in ['CB', 'ST'] else 0))),
            "aggression": int(min(250, phy - 2))
        }
    }

    if pos == 'GK':
        attrs["goalkeeping"] = {
            "gk_diving": int(min(250, deff + 12)),
            "gk_handling": int(min(250, deff + 8)),
            "gk_kicking": int(min(250, pas + 5)),
            "gk_reflexes": int(min(250, pac + 15)),
            "gk_positioning": int(min(250, deff + 10))
        }

    nation = getattr(p, 'nationality', 'Việt Nam') or 'Việt Nam'
    flag_code = "VIE" if "Việt" in nation else ("ENG" if "Anh" in nation else ("ESP" if "Tây Ban Nha" in nation else ("FRA" if "Pháp" in nation else ("BRA" if "Brazil" in nation else ("GER" if "Đức" in nation else ("BEL" if "Bỉ" in nation else "ARG"))))))
    league = club.league if club else "V-League 1"
    club_name = club.name if club else "FC Club"

    playstyles_list = [
        {"name": "Sút xoáy Finesse Shot", "icon": "🌀", "desc": "Cú sút má trong hiểm hóc với độ xoáy cực cao khiến thủ môn đối phương bó tay."},
        {"name": "Bứt tốc Speed Dribbler", "icon": "⚡", "desc": "Khả năng đẩy bóng dài và tăng tốc đoạn ngắn không thể ngăn cản."},
        {"name": "Chuyền điểm rơi Long Passer", "icon": "📐", "desc": "Những đường chuyền dài đảo cánh mở toang không gian tấn công."},
        {"name": "Đánh đầu uy lực Power Header", "icon": "💥", "desc": "Bật cao tranh chấp không chiến và đánh đầu uy lực thành bàn."}
    ]

    tier = 'tier-ucl' if fc_ovr >= 85 else ('tier-gold' if fc_ovr >= 74 else 'tier-silver')
    avatar_svg = generate_player_svg_avatar(p.name, p.position, p.id)

    return {
        "id": p.id,
        "name": p.name,
        "first_name": first_name,
        "last_name": last_name,
        "position": p.position,
        "secondary_pos": sec_pos,
        "overall": base_ovr,
        "fc_ovr": fc_ovr,
        "speed": pac,
        "attack": sho,
        "defense": deff,
        "stamina": p.stamina,
        "pac": pac,
        "sho": sho,
        "pas": pas,
        "dri": dri,
        "def": deff,
        "phy": phy,
        "tier": tier,
        "avatar_svg": avatar_svg,
        "training_level": t_lvl,
        "max_training_level": 30,
        "rank_level": r_lvl,
        "max_rank_level": 5,
        "skill_boost": s_boost,
        "age": getattr(p, 'age', 24) or 24,
        "height": getattr(p, 'height', 178) or 178,
        "weight": getattr(p, 'weight', 72) or 72,
        "weak_foot": getattr(p, 'weak_foot', 4) or 4,
        "skill_moves": getattr(p, 'skill_moves', 4) or 4,
        "nationality": nation,
        "flag_code": flag_code,
        "league": league,
        "club_name": club_name,
        "is_starting": p.is_starting,
        "is_substitute": p.is_substitute,
        "goals": p.goals,
        "assists": p.assists,
        "matches_played": p.matches_played,
        "contract_wage": getattr(p, 'contract_wage', 50000) or 50000,
        "market_value": getattr(p, 'market_value', 500000) or 500000,
        "playstyle_name": playstyle_name,
        "playstyle_icon": playstyle_icon,
        "playstyle_desc": playstyle_desc,
        "attrs": attrs,
        "playstyles_list": playstyles_list
    }


@app.route('/squad')
def squad():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    raw_players = Player.query.filter_by(club_id=club.id).order_by(Player.overall.desc()).all()
    
    # Ensure at least 11 players are marked as starting
    starting_count = sum(1 for p in raw_players if p.is_starting)
    if starting_count != 11 and len(raw_players) >= 11:
        selected_ids = auto_select_xi(raw_players, club.formation)
        for p in raw_players:
            p.is_starting = (p.id in selected_ids)
            p.is_substitute = not p.is_starting
        db.session.commit()

    enriched_players = [enrich_player_fc(p, club) for p in raw_players]
    starting_players = [p for p in enriched_players if p['is_starting']]
    sub_players = [p for p in enriched_players if not p['is_starting']]

    # Calculate team average FC OVR
    if starting_players:
        team_ovr = int(round(sum(p['fc_ovr'] for p in starting_players) / len(starting_players)))
    else:
        team_ovr = int(round(sum(p['fc_ovr'] for p in enriched_players[:11]) / max(1, min(11, len(enriched_players)))))

    # Calculate team market value
    team_value = sum(p['market_value'] for p in enriched_players) * 10

    return render_template('squad.html', 
                           players=raw_players, 
                           enriched_players=enriched_players, 
                           starting_players=starting_players,
                           sub_players=sub_players,
                           team_ovr=team_ovr,
                           team_value=team_value,
                           team=club, 
                           club=club)


@app.route('/api/auto_build_squad', methods=['POST'])
def api_auto_build_squad():
    if 'club_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    club = db.session.get(Club, session['club_id'])
    if not club:
        return jsonify({'error': 'Club not found'}), 404
    raw_players = Player.query.filter_by(club_id=club.id).all()
    if len(raw_players) < 11:
        return jsonify({'error': 'Cần tối thiểu 11 cầu thủ để xây dựng đội hình'}), 400
    
    selected_ids = auto_select_xi(raw_players, club.formation)
    for p in raw_players:
        p.is_starting = (p.id in selected_ids)
        p.is_substitute = not p.is_starting
    db.session.commit()

    enriched_players = [enrich_player_fc(p, club) for p in raw_players]
    starting_players = [p for p in enriched_players if p['is_starting']]
    sub_players = [p for p in enriched_players if not p['is_starting']]
    team_ovr = int(round(sum(p['fc_ovr'] for p in starting_players) / len(starting_players)))

    return jsonify({
        'success': True,
        'message': f'Đã tự động tối ưu 11 cầu thủ xuất sắc nhất cho sơ đồ {club.formation}!',
        'starting_players': starting_players,
        'sub_players': sub_players,
        'team_ovr': team_ovr
    })


@app.route('/api/swap_squad_players', methods=['POST'])
def api_swap_squad_players():
    if 'club_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    club = db.session.get(Club, session['club_id'])
    if not club:
        return jsonify({'error': 'Club not found'}), 404

    data = request.get_json() or {}
    p1_id = data.get('p1_id')
    p2_id = data.get('p2_id')

    p1 = db.session.get(Player, p1_id)
    p2 = db.session.get(Player, p2_id)
    if not p1 or not p2 or p1.club_id != club.id or p2.club_id != club.id:
        return jsonify({'error': 'Không tìm thấy cầu thủ đổi'}), 404

    # Swap starting state
    p1.is_starting, p2.is_starting = p2.is_starting, p1.is_starting
    p1.is_substitute = not p1.is_starting
    p2.is_substitute = not p2.is_starting
    db.session.commit()

    raw_players = Player.query.filter_by(club_id=club.id).all()
    enriched_players = [enrich_player_fc(p, club) for p in raw_players]
    starting_players = [p for p in enriched_players if p['is_starting']]
    sub_players = [p for p in enriched_players if not p['is_starting']]
    team_ovr = int(round(sum(p['fc_ovr'] for p in starting_players) / len(starting_players))) if starting_players else 100

    return jsonify({
        'success': True,
        'message': f'Đã đổi {p1.name} và {p2.name} thành công!',
        'starting_players': starting_players,
        'sub_players': sub_players,
        'team_ovr': team_ovr
    })


@app.route('/api/change_formation', methods=['POST'])
def api_change_formation():
    if 'club_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    club = db.session.get(Club, session['club_id'])
    if not club:
        return jsonify({'error': 'Club not found'}), 404

    data = request.get_json() or {}
    formation = data.get('formation', '4-3-3')
    club.formation = formation
    
    raw_players = Player.query.filter_by(club_id=club.id).all()
    if len(raw_players) >= 11:
        selected_ids = auto_select_xi(raw_players, formation)
        for p in raw_players:
            p.is_starting = (p.id in selected_ids)
            p.is_substitute = not p.is_starting
    db.session.commit()

    enriched_players = [enrich_player_fc(p, club) for p in raw_players]
    starting_players = [p for p in enriched_players if p['is_starting']]
    sub_players = [p for p in enriched_players if not p['is_starting']]
    team_ovr = int(round(sum(p['fc_ovr'] for p in starting_players) / len(starting_players))) if starting_players else 100

    return jsonify({
        'success': True,
        'message': f'Đã chuyển sang sơ đồ {formation}!',
        'formation': formation,
        'starting_players': starting_players,
        'sub_players': sub_players,
        'team_ovr': team_ovr
    })


@app.route('/player/<int:player_id>')
def player_detail(player_id):
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    p = db.session.get(Player, player_id)
    if not p:
        return redirect(url_for('squad'))
    raw_players = Player.query.filter_by(club_id=club.id).order_by(Player.overall.desc()).all()
    enriched_players = [enrich_player_fc(pl, club) for pl in raw_players]
    current_player_enriched = enrich_player_fc(p, club)
    return render_template('player_detail.html', player=current_player_enriched, club=club, enriched_players=enriched_players)


@app.route('/api/player/<int:player_id>')
def api_get_player(player_id):
    if 'club_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    club = db.session.get(Club, session['club_id'])
    p = db.session.get(Player, player_id)
    if not p:
        return jsonify({'error': 'Player not found'}), 404
    return jsonify({'success': True, 'player': enrich_player_fc(p, club)})


@app.route('/api/train_player', methods=['POST'])
def api_train_player():
    if 'club_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    club = db.session.get(Club, session['club_id'])
    if not club:
        return jsonify({'error': 'Club not found'}), 404

    data = request.get_json() or {}
    player_id = data.get('player_id')
    p = db.session.get(Player, player_id)
    if not p or p.club_id != club.id:
        return jsonify({'error': 'Cầu thủ không tồn tại hoặc không thuộc CLB'}), 404

    cost = 120000
    if club.money < cost:
        return jsonify({'error': 'Ngân sách CLB không đủ (Cần 120,000 $)'}), 400

    current_lvl = getattr(p, 'training_level', 10) or 10
    if current_lvl >= 30:
        return jsonify({'error': 'Cầu thủ đã đạt cấp huấn luyện tối đa (30/30)'}), 400

    p.training_level = current_lvl + 1
    p.speed = min(99, p.speed + 1)
    p.attack = min(99, p.attack + 1)
    p.defense = min(99, p.defense + 1)
    p.overall = round((p.attack + p.defense + p.speed) / 3, 1)
    club.money -= cost
    db.session.commit()

    enriched = enrich_player_fc(p, club)
    return jsonify({
        'success': True,
        'message': f'Huấn luyện thành công! {p.name} đã lên cấp {p.training_level}/30',
        'player': enriched,
        'club_money': club.money
    })


@app.route('/api/rankup_player', methods=['POST'])
def api_rankup_player():
    if 'club_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    club = db.session.get(Club, session['club_id'])
    if not club:
        return jsonify({'error': 'Club not found'}), 404

    data = request.get_json() or {}
    player_id = data.get('player_id')
    p = db.session.get(Player, player_id)
    if not p or p.club_id != club.id:
        return jsonify({'error': 'Cầu thủ không tồn tại'}), 404

    current_rank = getattr(p, 'rank_level', 1) or 1
    if current_rank >= 5:
        return jsonify({'error': 'Cầu thủ đã đạt cấp thăng hạng tối đa (5 Kim cương)'}), 400

    cost = 400000 * current_rank
    if club.money < cost:
        return jsonify({'error': f'Ngân sách CLB không đủ (Cần {cost:,} $)'}), 400

    p.rank_level = current_rank + 1
    p.speed = min(99, p.speed + 2)
    p.attack = min(99, p.attack + 2)
    p.defense = min(99, p.defense + 2)
    p.overall = round((p.attack + p.defense + p.speed) / 3, 1)
    club.money -= cost
    db.session.commit()

    enriched = enrich_player_fc(p, club)
    return jsonify({
        'success': True,
        'message': f'Thăng hạng thành công! {p.name} đã đạt Hạng {p.rank_level} 🔶',
        'player': enriched,
        'club_money': club.money
    })


@app.route('/api/compare_players', methods=['POST'])
def api_compare_players():
    if 'club_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    club = db.session.get(Club, session['club_id'])
    data = request.get_json() or {}
    p1_id = data.get('p1_id')
    p2_id = data.get('p2_id')
    
    p1 = db.session.get(Player, p1_id)
    p2 = db.session.get(Player, p2_id)
    if not p1 or not p2:
        return jsonify({'error': 'Không tìm thấy cầu thủ so sánh'}), 404
        
    return jsonify({
        'success': True,
        'player1': enrich_player_fc(p1, club),
        'player2': enrich_player_fc(p2, club)
    })



@app.route('/api/skill_boost_player', methods=['POST'])
def api_skill_boost_player():
    if 'club_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    club = db.session.get(Club, session['club_id'])
    if not club:
        return jsonify({'error': 'Club not found'}), 404

    data = request.get_json() or {}
    player_id = data.get('player_id')
    p = db.session.get(Player, player_id)
    if not p or p.club_id != club.id:
        return jsonify({'error': 'Cầu thủ không tồn tại'}), 404

    current_sb = getattr(p, 'skill_boost', 2) or 2
    if current_sb >= 15:
        return jsonify({'error': 'Cầu thủ đã đạt cấp Điểm kỹ năng tối đa (+15)'}), 400

    cost = 250000 * current_sb
    if club.money < cost:
        return jsonify({'error': f'Ngân sách CLB không đủ (Cần {cost:,} $)'}), 400

    p.skill_boost = current_sb + 1
    p.speed = min(99, p.speed + 1)
    p.attack = min(99, p.attack + 1)
    p.defense = min(99, p.defense + 1)
    p.overall = round((p.attack + p.defense + p.speed) / 3, 1)
    club.money -= cost
    db.session.commit()

    enriched = enrich_player_fc(p, club)
    return jsonify({
        'success': True,
        'message': f'Nâng cấp Điểm kỹ năng thành công! {p.name} đạt Kỹ năng +{p.skill_boost} 🔥',
        'player': enriched,
        'club_money': club.money
    })


@app.route('/api/transfer_training', methods=['POST'])
def api_transfer_training():
    if 'club_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    club = db.session.get(Club, session['club_id'])
    if not club:
        return jsonify({'error': 'Club not found'}), 404

    data = request.get_json() or {}
    src_id = data.get('source_player_id')
    tgt_id = data.get('target_player_id')

    p_src = db.session.get(Player, src_id)
    p_tgt = db.session.get(Player, tgt_id)
    if not p_src or not p_tgt or p_src.club_id != club.id or p_tgt.club_id != club.id:
        return jsonify({'error': 'Không tìm thấy cầu thủ'}), 404

    cost = 150000
    if club.money < cost:
        return jsonify({'error': f'Ngân sách CLB không đủ (Cần {cost:,} $)'}), 400

    src_lvl = getattr(p_src, 'training_level', 1) or 1
    tgt_lvl = getattr(p_tgt, 'training_level', 1) or 1

    if src_lvl <= 1:
        return jsonify({'error': f'{p_src.name} chưa có cấp huấn luyện nào để chuyển!'}), 400

    # Transfer level
    transferred = src_lvl - 1
    p_tgt.training_level = min(30, tgt_lvl + transferred)
    p_src.training_level = 1

    p_tgt.speed = min(99, p_tgt.speed + transferred)
    p_tgt.attack = min(99, p_tgt.attack + transferred)
    p_tgt.defense = min(99, p_tgt.defense + transferred)
    p_tgt.overall = round((p_tgt.attack + p_tgt.defense + p_tgt.speed) / 3, 1)

    p_src.speed = max(40, p_src.speed - transferred)
    p_src.attack = max(40, p_src.attack - transferred)
    p_src.defense = max(40, p_src.defense - transferred)
    p_src.overall = round((p_src.attack + p_src.defense + p_src.speed) / 3, 1)

    club.money -= cost
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Đã chuyển {transferred} cấp huấn luyện từ {p_src.name} sang {p_tgt.name}!',
        'source_player': enrich_player_fc(p_src, club),
        'target_player': enrich_player_fc(p_tgt, club),
        'club_money': club.money
    })


@app.route('/select_xi', methods=['GET', 'POST'])
def select_xi():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    raw_players = Player.query.filter_by(club_id=club.id).all()
    if request.method == 'POST':
        new_formation = request.form.get('formation')
        formation_map = {
            '4-3-3': ['GK', 'LB', 'CB', 'CB', 'RB', 'LW', 'CM', 'CM', 'CM', 'RW', 'ST'],
            '4-2-3-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'CDM', 'LW', 'CAM', 'RW', 'ST'],
            '5-3-2': ['GK', 'LWB', 'CB', 'CB', 'CB', 'RWB', 'CM', 'CM', 'CM', 'ST', 'ST'],
            '4-4-2': ['GK', 'LB', 'CB', 'CB', 'RB', 'LM', 'CM', 'CM', 'RM', 'ST', 'ST'],
            '3-5-2': ['GK', 'CB', 'CB', 'CB', 'LM', 'CDM', 'CAM', 'CDM', 'RM', 'ST', 'ST']
        }
        if new_formation in formation_map:
            club.formation = new_formation
        if request.form.get('auto') == '1':
            selected_ids = auto_select_xi(raw_players, club.formation)
        else:
            selected_ids = [int(id) for id in request.form.getlist('starting')]
            if len(selected_ids) != 11:
                enriched_players = [enrich_player_fc(p, club) for p in raw_players]
                starting_players = [p for p in enriched_players if p['is_starting']]
                sub_players = [p for p in enriched_players if not p['is_starting']]
                team_ovr = int(round(sum(p['fc_ovr'] for p in starting_players) / len(starting_players))) if starting_players else 100
                team_value = sum(p['market_value'] for p in enriched_players) * 10
                return render_template('select_xi.html', team=club, club=club, players=raw_players,
                                       enriched_players=enriched_players, starting_players=starting_players,
                                       sub_players=sub_players, team_ovr=team_ovr, team_value=team_value,
                                       error="Phải chọn đúng 11 cầu thủ đá chính!")
        for p in raw_players:
            p.is_starting = (p.id in selected_ids)
            p.is_substitute = not p.is_starting
        db.session.commit()
        return redirect(url_for('select_xi'))

    # Ensure at least 11 players are marked starting
    starting_count = sum(1 for p in raw_players if p.is_starting)
    if starting_count != 11 and len(raw_players) >= 11:
        selected_ids = auto_select_xi(raw_players, club.formation)
        for p in raw_players:
            p.is_starting = (p.id in selected_ids)
            p.is_substitute = not p.is_starting
        db.session.commit()

    enriched_players = [enrich_player_fc(p, club) for p in raw_players]
    starting_players = [p for p in enriched_players if p['is_starting']]
    sub_players = [p for p in enriched_players if not p['is_starting']]
    team_ovr = int(round(sum(p['fc_ovr'] for p in starting_players) / len(starting_players))) if starting_players else 100
    team_value = sum(p['market_value'] for p in enriched_players) * 10

    return render_template('select_xi.html', team=club, club=club, players=raw_players,
                           enriched_players=enriched_players, starting_players=starting_players,
                           sub_players=sub_players, team_ovr=team_ovr, team_value=team_value)


@app.route('/auto_select_xi_api', methods=['POST'])
def auto_select_xi_api():
    if 'club_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    club = db.session.get(Club, session['club_id'])
    if not club:
        return jsonify({'error': 'Club not found'}), 404
    players = Player.query.filter_by(club_id=club.id).all()
    if not players:
        return jsonify({'error': 'No players'}), 400
    selected_ids = auto_select_xi(players, club.formation)
    for p in players:
        p.is_starting = (p.id in selected_ids)
        p.is_substitute = not p.is_starting
    db.session.commit()
    enriched = [enrich_player_fc(p, club) for p in players]
    starting_players = [p for p in enriched if p['is_starting']]
    sub_players = [p for p in enriched if not p['is_starting']]
    team_ovr = int(round(sum(p['fc_ovr'] for p in starting_players) / len(starting_players))) if starting_players else 100
    return jsonify({
        'success': True,
        'selected': selected_ids,
        'starting_players': starting_players,
        'sub_players': sub_players,
        'team_ovr': team_ovr
    })


LEAGUE_OPPONENTS = {
    "Hang 2": [
        {"name": "Bình Phước FC", "formation": "4-3-3", "tactic": "Tan cong"},
        {"name": "PVF-CAND", "formation": "4-2-3-1", "tactic": "Can bang"},
        {"name": "Phù Đổng Ninh Bình", "formation": "5-3-2", "tactic": "Phong thu"},
        {"name": "Bà Rịa Vũng Tàu", "formation": "4-3-3", "tactic": "Can bang"},
        {"name": "Long An FC", "formation": "4-2-3-1", "tactic": "Phong thu"},
        {"name": "Đồng Tháp FC", "formation": "5-3-2", "tactic": "Phong thu"},
        {"name": "Huế FC", "formation": "4-3-3", "tactic": "Can bang"},
        {"name": "Hòa Bình FC", "formation": "4-2-3-1", "tactic": "Can bang"},
        {"name": "Đồng Nai FC", "formation": "5-3-2", "tactic": "Phong thu"}
    ],
    "Hang 1": [
        {"name": "Công An Hà Nội", "formation": "4-3-3", "tactic": "Tan cong"},
        {"name": "Thép Xanh Nam Định", "formation": "4-2-3-1", "tactic": "Tan cong"},
        {"name": "Hà Nội FC", "formation": "4-3-3", "tactic": "Can bang"},
        {"name": "Thể Công Viettel", "formation": "5-3-2", "tactic": "Phong thu"},
        {"name": "Becamex Bình Dương", "formation": "4-2-3-1", "tactic": "Can bang"},
        {"name": "Hoàng Anh Gia Lai", "formation": "4-3-3", "tactic": "Tan cong"},
        {"name": "Hải Phòng FC", "formation": "4-2-3-1", "tactic": "Can bang"},
        {"name": "Sông Lam Nghệ An", "formation": "5-3-2", "tactic": "Phong thu"},
        {"name": "SHB Đà Nẵng", "formation": "4-3-3", "tactic": "Can bang"}
    ],
    "Champions League": [
        {"name": "Real Madrid", "formation": "4-3-3", "tactic": "Tan cong"},
        {"name": "Manchester City", "formation": "4-2-3-1", "tactic": "Tan cong"},
        {"name": "Bayern Munich", "formation": "4-2-3-1", "tactic": "Tan cong"},
        {"name": "Paris Saint-Germain", "formation": "4-3-3", "tactic": "Tan cong"},
        {"name": "Arsenal FC", "formation": "4-3-3", "tactic": "Can bang"},
        {"name": "Inter Milan", "formation": "5-3-2", "tactic": "Phong thu"},
        {"name": "Barcelona", "formation": "4-3-3", "tactic": "Tan cong"},
        {"name": "Liverpool FC", "formation": "4-3-3", "tactic": "Tan cong"}
    ]
}

def get_opponent_for_round(league, round_num):
    opp_list = LEAGUE_OPPONENTS.get(league, LEAGUE_OPPONENTS["Hang 2"])
    idx = (round_num - 1) % len(opp_list)
    opp = opp_list[idx]
    pos_map = {
        "4-3-3": ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CM", "LW", "RW", "ST"],
        "4-2-3-1": ["GK", "LB", "CB", "CB", "RB", "CDM", "CDM", "CAM", "LW", "RW", "ST"],
        "5-3-2": ["GK", "LWB", "CB", "CB", "CB", "RWB", "CM", "CM", "CM", "ST", "ST"]
    }
    positions = pos_map.get(opp["formation"], pos_map["4-3-3"])
    first_names = ["Minh", "Tuấn", "Hoàng", "Nam", "Quang", "Duy", "Hải", "Hùng", "Bảo", "Đức", "Văn", "Công", "Phượng", "Thắng", "Long"]
    last_names = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương"]

    players = []
    base_ovr = 75 if league == "Hang 1" else (85 if league == "Champions League" else 65)
    for pos in positions:
        name = f"{random.choice(last_names)} {random.choice(first_names)}"
        ovr = random.randint(base_ovr - 4, base_ovr + 6)
        players.append({"name": name, "position": pos, "overall": ovr, "stamina": 100.0,
                        "attack": ovr, "defense": ovr, "speed": ovr, "goals": 0})
    return {"name": opp["name"], "formation": opp["formation"], "tactic": opp["tactic"], "players": players}


# ===== MÔ PHỎNG TRẬN ĐẤU & LIVE MATCH ROUTES =====
@app.route('/match', methods=['GET', 'POST'], endpoint='play_match')
@app.route('/match_alias', methods=['GET', 'POST'], endpoint='match')
def play_match():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    players = Player.query.filter_by(club_id=club.id).all()
    opponent = get_opponent_for_round(club.league, club.round + 1)

    starting_players = [p for p in players if p.is_starting]
    starting_players_data = [
        {'id': p.id, 'name': p.name, 'position': p.position, 'stamina': p.stamina, 'overall': p.overall}
        for p in starting_players
    ]

    if request.method == 'POST':
        for player in players:
            player.stamina = min(100.0, player.stamina + 20.0)
        db.session.commit()
        tactic = request.form.get('tactic', 'Can bang')
        club.tactic = tactic
        db.session.commit()
        session['live_match'] = {
            'home_goals': 0, 'away_goals': 0, 'events': [], 'current_minute': 0,
            'home_team': club.name, 'home_formation': club.formation,
            'away_team': opponent['name'], 'away_formation': opponent['formation'],
            'away_tactic': opponent['tactic'], 'subs_used': 0, 'half': 1,
            'phase': 'first_half', 'finalized': False, 'finished': False,
            'tactic': tactic, 'round': club.round + 1,
            'home_players': starting_players_data, 'away_players': opponent['players'],
            'ball_x': 50, 'ball_y': 50,
            'shots_home': 0, 'shots_away': 0,
            'target_home': 0, 'target_away': 0,
            'corners_home': 0, 'corners_away': 0,
            'fouls_home': 0, 'fouls_away': 0,
            'yellow_home': 0, 'yellow_away': 0,
            'red_home': 0, 'red_away': 0,
            'home_cards': {}
        }
        session['subs_used'] = 0
        return redirect(url_for('live_match'))

    return render_template('match.html', club=club, starting_players=starting_players_data, round=club.round + 1,
                           formation=club.formation, opponent=opponent)


@app.route('/live_match')
def live_match():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club or 'live_match' not in session:
        return redirect(url_for('play_match'))
    match_data = session['live_match']
    return render_template('live_match.html', club=club, match=match_data, match_json=json.dumps(match_data))


@app.route('/api/change_tactic', methods=['POST'])
def change_tactic():
    if 'live_match' not in session:
        return jsonify({'error': 'No match'}), 400
    tactic = request.json.get('tactic', 'Can bang')
    session['live_match']['tactic'] = tactic
    cur_min = session['live_match'].get('current_minute', 0)
    session['live_match']['events'].append({
        'minute': cur_min,
        'description': f"📋 Phút {cur_min}: HLV đổi chiến thuật sang: {tactic.upper()}"
    })
    session.modified = True
    return jsonify({'success': True, 'tactic': tactic})


@app.route('/tutorial')
def tutorial():
    is_first_visit = session.pop('show_tutorial_welcome', False)
    club = db.session.get(Club, session.get('club_id')) if session.get('club_id') else None
    return render_template('tutorial.html', is_first_visit=is_first_visit, club=club)


@app.route('/match_status')
def match_status():
    if 'live_match' not in session:
        return jsonify({'error': 'No match'})
    return jsonify(session['live_match'])


def finalize_live_match(club, team_old, match, match_data):
    if match_data.get('finalized'):
        return
    match.finished = True
    match.add_event(90, f"⏱️ Kết thúc trận đấu! Tỉ số {match.home_goals}-{match.away_goals}")
    club.points += match.points()
    club.matches_played += 1
    club.round += 1

    # Tài trợ & Thưởng trận đấu
    weekly_payout = club.sponsor_weekly or 250000
    win_bonus = (club.sponsor_bonus or 150000) if match.result() == 'Thắng' else 0
    club.money += (weekly_payout + win_bonus)

    home_cards = match_data.get('home_cards', {})
    for p_old in team_old.players:
        p_db = Player.query.filter_by(name=p_old.name, club_id=club.id).first()
        if p_db:
            p_db.stamina = p_old.stamina
            p_db.goals = p_old.goals
            card_info = home_cards.get(p_old.name, {'yellow': 0, 'red': 0})
            p_db.yellow_cards = getattr(p_db, 'yellow_cards', 0) + card_info.get('yellow', 0)
            p_db.red_cards = getattr(p_db, 'red_cards', 0) + card_info.get('red', 0)
            p_db.matches_played = p_old.matches_played + 1
            p_db.experience = getattr(p_db, 'experience', 0) + 5
    match_data.update({'finished': True, 'finalized': True, 'phase': 'finished', 'events': match.events})
    db.session.add(MatchHistory(
        club_id=club.id, opponent=match.away_team.name,
        home_goals=match.home_goals, away_goals=match.away_goals,
        result=match.result(), points=match.points(), round=match.round,
        events=json.dumps(match.events, ensure_ascii=False)
    ))
    session['last_match'] = {'home': match.home_team.name, 'away': match.away_team.name,
        'home_goals': match.home_goals, 'away_goals': match.away_goals,
        'result': match.result(), 'points': match.points(), 'events': match.events, 'round': match.round}
    db.session.commit()


@app.route('/api/tick', methods=['POST'])
def tick():
    if 'club_id' not in session or 'live_match' not in session:
        return jsonify({'error': 'No match'}), 400
    match_data = session['live_match']
    if match_data.get('finished', False):
        return jsonify({'finished': True, 'home_goals': match_data.get('home_goals', 0), 'away_goals': match_data.get('away_goals', 0)})
    if match_data.get('phase') == 'halftime':
        return jsonify({
            'halftime': True, 'phase': 'halftime', 'half': 1,
            'current_minute': 45, 'home_goals': match_data.get('home_goals', 0),
            'away_goals': match_data.get('away_goals', 0), 'events': match_data.get('events', []),
            'stats': {
                'shots_home': match_data.get('shots_home', 0),
                'shots_away': match_data.get('shots_away', 0),
                'target_home': match_data.get('target_home', 0),
                'target_away': match_data.get('target_away', 0),
                'fouls_home': match_data.get('fouls_home', 0),
                'fouls_away': match_data.get('fouls_away', 0),
                'yellow_home': match_data.get('yellow_home', 0),
                'yellow_away': match_data.get('yellow_away', 0),
                'red_home': match_data.get('red_home', 0),
                'red_away': match_data.get('red_away', 0)
            }
        })
    club = db.session.get(Club, session['club_id'])
    if not club:
        return jsonify({'error': 'Club not found'}), 404
    current_minute = match_data.get('current_minute', 0)
    if current_minute >= 90:
        return jsonify({'finished': True, 'home_goals': match_data.get('home_goals', 0), 'away_goals': match_data.get('away_goals', 0)})

    tactic = match_data.get('tactic', 'Can bang')
    team_old = club_to_team_old(club)
    home_cards = match_data.get('home_cards', {})
    for p in team_old.players:
        c = home_cards.get(p.name, {'yellow': 0, 'red': 0})
        p.yellow_cards = c['yellow']
        p.red_cards = c['red']

    opp_players_old = []
    for player_data in match_data.get('away_players', []):
        player = PlayerOld(player_data['name'], player_data['position'],
                           player_data.get('attack', player_data.get('overall', 60)),
                           player_data.get('defense', player_data.get('overall', 60)),
                           player_data.get('speed', player_data.get('overall', 60)))
        player.stamina = player_data.get('stamina', 100.0)
        player.goals = player_data.get('goals', 0)
        player.yellow_cards = player_data.get('yellow_cards', 0)
        player.red_cards = player_data.get('red_cards', 0)
        opp_players_old.append(player)
    opponent = TeamOld(match_data.get('away_team', 'Đối thủ'), opp_players_old)
    opponent.starting_xi = list(range(11))
    opponent.substitutes = list(range(11, 16))
    match = MatchOld(team_old, opponent, match_data.get('round', 1))
    match.home_goals = match_data.get('home_goals', 0)
    match.away_goals = match_data.get('away_goals', 0)
    match.events = list(match_data.get('events', []))
    match.finished = match_data.get('finished', False)
    match.shots_home = match_data.get('shots_home', 0)
    match.shots_away = match_data.get('shots_away', 0)
    match.target_home = match_data.get('target_home', 0)
    match.target_away = match_data.get('target_away', 0)
    match.fouls_home = match_data.get('fouls_home', 0)
    match.fouls_away = match_data.get('fouls_away', 0)
    match.yellow_home = match_data.get('yellow_home', 0)
    match.yellow_away = match_data.get('yellow_away', 0)
    match.red_home = match_data.get('red_home', 0)
    match.red_away = match_data.get('red_away', 0)
    match.corners_home = match_data.get('corners_home', 0)
    match.corners_away = match_data.get('corners_away', 0)

    events_count_before = len(match.events)
    prev_goals = match.home_goals + match.away_goals
    next_minute = current_minute + 1
    match = run_minutes(match, next_minute, next_minute, tactic, "Can bang")

    new_events = match.events[events_count_before:]

    # Nếu phát backend local
    if (match.home_goals + match.away_goals) > prev_goals:
        sound.play_goal()
    else:
        if len(match.events) > events_count_before:
            sound.play_kick()

    # Cập nhật lại thẻ phạt cho cầu thủ hai đội
    for p in team_old.players:
        home_cards[p.name] = {
            'yellow': getattr(p, 'yellow_cards', 0),
            'red': getattr(p, 'red_cards', 0)
        }
    match_data['home_cards'] = home_cards

    match_data['home_goals'] = match.home_goals
    match_data['away_goals'] = match.away_goals
    match_data['events'] = match.events
    match_data['current_minute'] = next_minute
    match_data['shots_home'] = match.shots_home
    match_data['shots_away'] = match.shots_away
    match_data['target_home'] = match.target_home
    match_data['target_away'] = match.target_away
    match_data['fouls_home'] = match.fouls_home
    match_data['fouls_away'] = match.fouls_away
    match_data['yellow_home'] = match.yellow_home
    match_data['yellow_away'] = match.yellow_away
    match_data['red_home'] = match.red_home
    match_data['red_away'] = match.red_away
    match_data['corners_home'] = getattr(match, 'corners_home', 0)
    match_data['corners_away'] = getattr(match, 'corners_away', 0)

    match_data['away_players'] = [
        {'name': player.name, 'position': player.position, 'overall': player.overall,
         'stamina': player.stamina, 'attack': player.attack, 'defense': player.defense,
         'speed': player.speed, 'goals': player.goals,
         'yellow_cards': getattr(player, 'yellow_cards', 0),
         'red_cards': getattr(player, 'red_cards', 0)}
        for player in opponent.players
    ]

    if next_minute == 45:
        match.add_event(45, f"⏱️ Kết thúc hiệp 1! Tỉ số {match.home_goals}-{match.away_goals}")
        match_data['phase'] = 'halftime'
        match_data['half'] = 1
    elif next_minute == 90:
        finalize_live_match(club, team_old, match, match_data)
    else:
        match_data['phase'] = 'first_half' if next_minute < 45 else 'second_half'
        match_data['half'] = 1 if next_minute < 45 else 2
    match_data['finished'] = match_data.get('finished', False)

    if not match_data.get('finished', False):
        for p_old in team_old.players:
            p_db = Player.query.filter_by(name=p_old.name, club_id=club.id).first()
            if p_db:
                p_db.stamina = p_old.stamina
                p_db.goals = p_old.goals
        db.session.commit()

    session['live_match'] = match_data
    session.modified = True

    players = Player.query.filter_by(club_id=club.id).all()
    xi = [p for p in players if p.is_starting]
    formation = club.formation
    pos_map = {
        '4-3-3': ['GK', 'LB', 'CB', 'CB', 'RB', 'LW', 'CM', 'CM', 'CM', 'RW', 'ST'],
        '4-2-3-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'CDM', 'LW', 'CAM', 'RW', 'ST'],
        '5-3-2': ['GK', 'LWB', 'CB', 'CB', 'CB', 'RWB', 'CM', 'CM', 'CM', 'ST', 'ST']
    }
    pos_list = pos_map.get(formation, pos_map['4-3-3'])
    position_map = {}
    for idx, p in enumerate(xi):
        if idx < len(pos_list):
            position_map[pos_list[idx]] = {'name': p.name, 'stamina': p.stamina}

    home_players_stamina = [
        {
            'id': p.id,
            'name': p.name,
            'stamina': p.stamina,
            'yellow_cards': home_cards.get(p.name, {}).get('yellow', 0),
            'red_cards': home_cards.get(p.name, {}).get('red', 0)
        }
        for p in xi
    ]

    return jsonify({
        'home_goals': match.home_goals,
        'away_goals': match.away_goals,
        'events': match.events,
        'new_events': new_events,
        'stats': {
            'shots_home': match.shots_home,
            'shots_away': match.shots_away,
            'target_home': match.target_home,
            'target_away': match.target_away,
            'corners_home': getattr(match, 'corners_home', 0),
            'corners_away': getattr(match, 'corners_away', 0),
            'fouls_home': match.fouls_home,
            'fouls_away': match.fouls_away,
            'yellow_home': match.yellow_home,
            'yellow_away': match.yellow_away,
            'red_home': match.red_home,
            'red_away': match.red_away
        },
        'finished': match_data.get('finished', False),
        'current_minute': next_minute,
        'positions': position_map,
        'home_players': home_players_stamina,
        'away_players': [
            {
                'id': idx + 11,
                'name': p.name,
                'stamina': p.stamina,
                'yellow_cards': getattr(p, 'yellow_cards', 0),
                'red_cards': getattr(p, 'red_cards', 0)
            }
            for idx, p in enumerate(opponent.players[:11])
        ],
        'half': match_data.get('half', 1),
        'phase': match_data.get('phase', 'first_half'),
        'halftime': match_data.get('phase') == 'halftime',
        'low_stamina_home': [p.name for p in team_old.get_starting_xi() if p.stamina < 65],
        'low_stamina_away': [p.name for p in opponent.get_starting_xi() if p.stamina < 65]
    })


@app.route('/start_second_half', methods=['POST'])
def start_second_half():
    match_data = session.get('live_match')
    if not match_data or match_data.get('phase') != 'halftime':
        return jsonify({'success': False, 'error': 'Not halftime'}), 400
    match_data['phase'] = 'second_half'
    match_data['half'] = 2
    match_data['events'].append({'minute': 46, 'description': '▶️ Hiệp 2 bắt đầu!'})
    session['live_match'] = match_data
    session.modified = True
    return jsonify({'success': True, 'half': 2})


@app.route('/get_players')
def get_players():
    if 'club_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    club = db.session.get(Club, session['club_id'])
    if not club:
        return jsonify({'error': 'Club not found'}), 404
    players = Player.query.filter_by(club_id=club.id).all()
    starting = [{'id': p.id, 'name': p.name, 'position': p.position, 'stamina': p.stamina} for p in players if p.is_starting]
    subs = [{'id': p.id, 'name': p.name, 'position': p.position, 'stamina': p.stamina} for p in players if p.is_substitute]
    return jsonify({'starting': starting, 'subs': subs})


@app.route('/substitute', methods=['GET', 'POST'])
def substitute():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    if club.round >= 18:
        return redirect(url_for('season_end'))
    players = Player.query.filter_by(club_id=club.id).all()
    xi = [p for p in players if p.is_starting]
    subs = [p for p in players if p.is_substitute]
    subs_used = session.get('subs_used', 0)
    if request.method == 'POST':
        out_id = int(request.form.get('player_out', 0))
        in_id = int(request.form.get('player_in', 0))
        if subs_used >= 3:
            return render_template('substitution.html', xi=xi, subs=subs, subs_used=subs_used, error="Đã thay đủ 3 người!")
        player_out = db.session.get(Player, out_id)
        player_in = db.session.get(Player, in_id)
        if player_out and player_in:
            player_out.is_starting = False
            player_out.is_substitute = True
            player_in.is_starting = True
            player_in.is_substitute = False
            db.session.commit()
            subs_used += 1
            session['subs_used'] = subs_used
            if 'live_match' in session:
                cur_min = session['live_match'].get('current_minute', 45)
                session['live_match']['events'].append({
                    'minute': cur_min,
                    'description': f'Phút {cur_min} – 🔄 {player_out.name} ra → {player_in.name} vào'
                })
                session.modified = True
            return redirect(url_for('live_match'))
    return render_template('substitution.html', xi=xi, subs=subs, subs_used=subs_used)


@app.route('/substitute_api', methods=['POST'])
def substitute_api():
    if 'club_id' not in session or 'live_match' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    club = db.session.get(Club, session['club_id'])
    if not club:
        return jsonify({'error': 'Club not found'}), 404
    data = request.json or {}
    out_id = data.get('player_out')
    in_id = data.get('player_in')
    player_out = db.session.get(Player, out_id)
    player_in = db.session.get(Player, in_id)
    subs_used = session.get('subs_used', 0)
    if subs_used >= 3:
        return jsonify({'error': 'Đã thay đủ 3 người'}), 400
    if player_out and player_in:
        player_out.is_starting = False
        player_out.is_substitute = True
        player_in.is_starting = True
        player_in.is_substitute = False
        db.session.commit()
        subs_used += 1
        session['subs_used'] = subs_used
        cur_min = session['live_match'].get('current_minute', 45)
        session['live_match']['events'].append({
            'minute': cur_min,
            'description': f'Phút {cur_min} – 🔄 {player_out.name} ra → {player_in.name} vào'
        })
        session.modified = True
        return jsonify({
            'success': True,
            'subs_used': subs_used,
            'player_out': {'id': player_out.id, 'name': player_out.name},
            'player_in': {'id': player_in.id, 'name': player_in.name, 'stamina': getattr(player_in, 'stamina', 100), 'position': getattr(player_in, 'position', '')}
        })
    return jsonify({'error': 'Cầu thủ không hợp lệ'}), 400


@app.route('/low_stamina')
def low_stamina():
    if 'club_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    club = db.session.get(Club, session['club_id'])
    if not club:
        return jsonify({'error': 'Club not found'}), 404
    players = Player.query.filter_by(club_id=club.id).filter(Player.is_starting == True).all()
    low = [{'name': p.name, 'stamina': p.stamina} for p in players if p.stamina < 65]
    return jsonify({'home': low})


@app.route('/result')
def result():
    if 'last_match' not in session:
        return redirect(url_for('dashboard'))
    return render_template('result.html', match=session['last_match'])


@app.route('/standings')
def standings():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    history = MatchHistory.query.filter_by(club_id=club.id).all()
    wins = sum(1 for m in history if m.result == 'Thắng')
    draws = sum(1 for m in history if m.result == 'Hòa')
    losses = sum(1 for m in history if m.result == 'Thua')
    goals_for = sum(m.home_goals for m in history)
    goals_against = sum(m.away_goals for m in history)
    gd = goals_for - goals_against

    teams = [{
        "name": club.name, "points": club.points, "played": len(history),
        "wins": wins, "draws": draws, "losses": losses,
        "goals_for": goals_for, "goals_against": goals_against, "gd": gd,
        "gf": goals_for, "ga": goals_against, "w": wins, "d": draws, "l": losses,
        "pts": club.points, "is_player": True, "is_user": True
    }]

    rng = random.Random(f"{club.league}-{club.season}")
    for opp in LEAGUE_OPPONENTS.get(club.league, LEAGUE_OPPONENTS['Hang 2']):
        p_cnt = club.matches_played
        w_cnt = rng.randint(0, p_cnt) if p_cnt else 0
        d_cnt = rng.randint(0, p_cnt - w_cnt) if (p_cnt - w_cnt) else 0
        l_cnt = p_cnt - w_cnt - d_cnt
        gf_cnt = rng.randint(w_cnt, max(w_cnt, p_cnt * 2)) if p_cnt else 0
        ga_cnt = rng.randint(l_cnt, max(l_cnt, p_cnt * 2)) if p_cnt else 0
        teams.append({
            "name": opp['name'], "points": w_cnt * 3 + d_cnt, "played": p_cnt,
            "wins": w_cnt, "draws": d_cnt, "losses": l_cnt,
            "goals_for": gf_cnt, "goals_against": ga_cnt, "gd": gf_cnt - ga_cnt,
            "gf": gf_cnt, "ga": ga_cnt, "w": w_cnt, "d": d_cnt, "l": l_cnt,
            "pts": w_cnt * 3 + d_cnt, "is_player": False, "is_user": False
        })

    teams.sort(key=lambda x: (-x["points"], -x["gd"], -x["goals_for"]))
    club.position = next(i for i, t in enumerate(teams, 1) if t['is_player'])
    db.session.commit()
    return render_template('standings.html', teams=teams, club=club)


@app.route('/schedule')
def schedule():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    rounds = []
    for round_number in range(1, 19):
        opponent = get_opponent_for_round(club.league, round_number)
        is_home = round_number % 2 == 1
        rounds.append({"round": round_number,
                       "home": club.name if is_home else opponent['name'],
                       "away": opponent['name'] if is_home else club.name,
                       "current": round_number == club.round + 1})
    return render_template('schedule.html', rounds=rounds)


@app.route('/match_history')
def match_history():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    matches = MatchHistory.query.filter_by(club_id=club.id).order_by(MatchHistory.round.desc()).all()
    return render_template('match_history.html', matches=matches)


@app.route('/season_end')
def season_end():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    players = Player.query.filter_by(club_id=club.id).all()
    total_wage = sum(int(p.overall * 10000) for p in players)
    club.money -= total_wage

    if club.money < 0:
        db.session.delete(club)
        db.session.commit()
        session.clear()
        return render_template('season_end.html', message="💀 Không đủ tiền trả lương toàn đội! Game Over.")

    try:
        trophies_list = json.loads(club.trophies or '[]')
    except Exception:
        trophies_list = []

    msg = ""
    if club.league == "Hang 2" and club.position <= 2:
        msg = f"🎉 Chúc mừng! Bạn xuất sắc cán đích ở vị trí #{club.position}, giành Cúp Thăng Hạng lên Hạng 1 và nhận thưởng $1,500,000!"
        club.league = "Hang 1"
        club.money += 1500000
        if "h2_promotion" not in trophies_list:
            trophies_list.append("h2_promotion")
    elif club.league == "Hang 1" and club.position == 1:
        msg = "🏆 Chúc mừng! Bạn đã ĐOẠT CHỨC VÔ ĐỊCH QUỐC GIA (V-League 1), nhận thưởng $8,000,000 và chính thức tiến vào đấu trường đỉnh cao thế giới: UEFA CHAMPIONS LEAGUE (Cúp C1)!"
        club.league = "Champions League"
        club.money += 8000000
        if "h1_champion" not in trophies_list:
            trophies_list.append("h1_champion")
    elif club.league == "Champions League" and club.position == 1:
        msg = "⭐🏆⭐ THẦN KỲ! BẠN ĐÃ ĐÁNH BẠI REAL MADRID, MAN CITY VÀ ĐĂNG QUANG NGÔI VÔ ĐỊCH UEFA CHAMPIONS LEAGUE (CÚP C1 CHÂU ÂU)! NHẬN THƯỞNG $15,000,000 VÀ LƯU DANH VĨ ĐẠI VÀO PHÒNG TRUYỀN THỐNG!"
        club.money += 15000000
        if "ucl_champion" not in trophies_list:
            trophies_list.append("ucl_champion")
    else:
        msg = f"Mùa giải khép lại ở vị trí #{club.position}. Hãy nâng cấp đội hình và quyết tâm chinh phục danh hiệu ở mùa sau!"

    club.trophies = json.dumps(trophies_list)
    club.round = 0
    club.matches_played = 0
    club.points = 0
    club.season += 1
    db.session.commit()
    return render_template('season_end.html', club=club, message=msg)


@app.route('/player_stats')
def player_stats():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    players = Player.query.filter_by(club_id=club.id).order_by(Player.goals.desc()).all()
    enriched_players = [enrich_player_fc(p, club) for p in players]
    return render_template('player_stats.html', club=club, players=players, enriched_players=enriched_players)


@app.route('/salary', endpoint='salary')
@app.route('/salary_view', endpoint='salary_view')
def salary_view():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    players = Player.query.filter_by(club_id=club.id).all()
    items = [{'player': p, 'salary': int(p.overall * 10000)} for p in players]
    total_wage = sum(it['salary'] for it in items)
    avg_salary = int(total_wage / len(players)) if players else 0
    return render_template('salary.html', club=club, total_wage=total_wage, avg_salary=avg_salary, items=items)


@app.route('/save', methods=['GET', 'POST'])
def save():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    if request.method == 'POST':
        passcode = request.form.get('passcode', '').strip()
        if not passcode:
            return render_template('save.html', error="Vui lòng nhập passcode.")
        players = Player.query.filter_by(club_id=club.id).all()
        history = MatchHistory.query.filter_by(club_id=club.id).order_by(MatchHistory.round).all()
        data = {
            "club_name": club.name, "league": club.league, "season": club.season,
            "money": club.money, "points": club.points, "matches_played": club.matches_played,
            "position": club.position, "round": club.round, "formation": club.formation,
            "tactic": club.tactic, "players": [p.to_dict() for p in players],
            "match_history": [{"opponent": m.opponent, "home_goals": m.home_goals,
                               "away_goals": m.away_goals, "result": m.result,
                               "points": m.points, "round": m.round, "events": m.events} for m in history],
        }
        save_game(data, passcode)
        return render_template('save.html', success=True)
    return render_template('save.html')


@app.route('/load', methods=['GET', 'POST'])
def load():
    if request.method == 'POST':
        passcode = request.form.get('passcode', '').strip()
        if not passcode:
            return render_template('load.html', error="Vui lòng nhập passcode.")
        data = load_game(passcode)
        if data:
            club = Club(name=data["club_name"], league=data["league"], season=data["season"],
                        money=data["money"], points=data["points"], matches_played=data["matches_played"],
                        position=data["position"], round=data["round"], formation=data["formation"],
                        tactic=data["tactic"])
            db.session.add(club)
            db.session.commit()
            for p_data in data["players"]:
                p = Player(name=p_data["name"], position=p_data["position"],
                           attack=p_data["attack"], defense=p_data["defense"], speed=p_data["speed"],
                           overall=p_data["overall"], stamina=p_data["stamina"], goals=p_data["goals"],
                           matches_played=p_data["matches_played"],
                           is_starting=p_data.get("is_starting", False),
                           is_substitute=p_data.get("is_substitute", False),
                           preferred_positions=p_data.get("preferred_positions", '[]'),
                           club_id=club.id)
                db.session.add(p)
            db.session.commit()
            session['club_id'] = club.id
            return redirect(url_for('dashboard'))
        else:
            return render_template('load.html', error="Sai passcode hoặc không tìm thấy file.")
    return render_template('load.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def auto_open_browser():
    import time
    import webbrowser
    time.sleep(1.0)
    try:
        webbrowser.open('http://127.0.0.1:5000', new=2)
    except Exception:
        pass


if __name__ == '__main__':
    import threading
    threading.Thread(target=auto_open_browser, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)
