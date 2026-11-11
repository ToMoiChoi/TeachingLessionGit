"""Football Manager Web - Huấn luyện viên bóng đá (Flask).

Mã nguồn được khôi phục từ bản build run.exe (bytecode Python 3.14) ngày 11/11/2026,
vì file .py gốc bị mất. Logic giữ nguyên theo bản gốc; giao diện (templates) được viết lại.
"""
import os
import json
import random
import hashlib  # noqa: F401
from datetime import datetime  # noqa: F401

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.utils import secure_filename  # noqa: F401
from sqlalchemy import text, inspect

from football.models import db, Club, Player, Coach, MatchHistory, LeagueStanding, YouthPlayer
from football.classes import PlayerOld, TeamOld, MatchOld
from football.game_engine import simulate_half, simulate_match, calculate_team_strength, run_minutes  # noqa: F401
from football.team_manager import is_valid_formation, substitute as tm_substitute  # noqa: F401
from football.league_manager import update_standings  # noqa: F401
from football.save_load import save_game, load_game
import sound

app = Flask(__name__)
app.secret_key = os.environ.get('FM_SECRET_KEY', 'doimaykhongla')
# Trên máy: sqlite trong thư mục instance/. Trên server: đặt FM_DB_URI (vd sqlite:////tmp/fm.db)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('FM_DB_URI', 'sqlite:///football_manager.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.environ.get('FM_UPLOAD_DIR', os.path.join(app.root_path, 'static/uploads'))
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'data'), exist_ok=True)
except OSError:  # hệ thống file chỉ đọc (serverless)
    pass

db.init_app(app)

def _init_db():
    db.create_all()
    # Tự nâng cấp CSDL cũ: thêm các cột mới nếu thiếu
    inspector = inspect(db.engine)
    player_cols = [col['name'] for col in inspector.get_columns('players')]
    for col_name, ddl in [
        ('preferred_positions', 'TEXT DEFAULT "[]"'),
        ('assists', 'INTEGER DEFAULT 0'),
        ('contract_wage', 'INTEGER DEFAULT 50000'),
        ('market_value', 'INTEGER DEFAULT 500000'),
        ('training_level', 'INTEGER DEFAULT 10'),
        ('rank_level', 'INTEGER DEFAULT 1'),
        ('skill_boost', 'INTEGER DEFAULT 2'),
        ('age', 'INTEGER DEFAULT 24'),
        ('height', 'INTEGER DEFAULT 178'),
        ('weight', 'INTEGER DEFAULT 72'),
        ('nationality', 'VARCHAR(50) DEFAULT "Việt Nam"'),
        ('skill_moves', 'INTEGER DEFAULT 4'),
        ('weak_foot', 'INTEGER DEFAULT 4'),
        ('playstyle', 'VARCHAR(100) DEFAULT "Rê bóng thần tốc"'),
    ]:
        if col_name not in player_cols:
            db.session.execute(text(f'ALTER TABLE players ADD COLUMN {col_name} {ddl}'))
    club_cols = [col['name'] for col in inspector.get_columns('clubs')]
    for col_name, ddl in [
        ('sponsor_name', 'VARCHAR(100) DEFAULT "VietinBank Sport"'),
        ('sponsor_weekly', 'INTEGER DEFAULT 250000'),
        ('sponsor_bonus', 'INTEGER DEFAULT 150000'),
        ('trophies', 'TEXT DEFAULT "[]"'),
    ]:
        if col_name not in club_cols:
            db.session.execute(text(f'ALTER TABLE clubs ADD COLUMN {col_name} {ddl}'))
    db.session.commit()


with app.app_context():
    try:
        _init_db()
    except Exception:
        pass

POSITIONS = ['GK', 'CB', 'LB', 'RB', 'LWB', 'RWB', 'CDM', 'CM', 'LM', 'RM', 'CAM', 'LW', 'RW', 'ST']

FIRST_NAMES = ['John', 'Ethan', 'Michael', 'David', 'James', 'Robert', 'Thomas', 'Daniel', 'Paul', 'Mark',
               'Steven', 'Andrew', 'Kenneth', 'Joshua', 'Kevin', 'Brian', 'George', 'Edward', 'Ronald', 'Timothy',
               'Jason', 'Jeffrey', 'Ryan', 'Jacob', 'Gary', 'Nicholas', 'Eric', 'Jonathan', 'Stephen', 'Larry',
               'Justin', 'Scott', 'Brandon', 'Benjamin', 'Samuel', 'Raymond', 'Gregory', 'Frank', 'Alexander',
               'Patrick', 'Jack', 'Dennis', 'Jerry', 'Tyler', 'Aaron', 'Jose', 'Nathan', 'Adam', 'Henry', 'Zachary']
LAST_NAMES = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez',
              'Martinez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson',
              'Martin', 'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis',
              'Robinson', 'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill',
              'Flores', 'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell', 'Carter',
              'Roberts', 'Turner']

# Bộ phát nhạc FIFA + tiếng click, tự chèn vào cuối mọi trang HTML (bản gốc để chuỗi ngay trong app.py)
with open(os.path.join(app.root_path, 'templates', '_audio_widget.html'), encoding='utf-8') as _f:
    GLOBAL_AUDIO_SNIPPET = _f.read()


@app.after_request
def auto_inject_audio_system(response):
    try:
        if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
            html = response.get_data(as_text=True)
            if '</body>' in html:
                # request.script_root để đường dẫn /sounds/ đúng khi app chạy dưới thư mục con (vd /football)
                snippet = GLOBAL_AUDIO_SNIPPET.replace("'/sounds/", f"'{request.script_root}/sounds/") \
                                              .replace('"/sounds/', f'"{request.script_root}/sounds/')
                html = html.replace('</body>', f'{snippet}\n</body>', 1)
                response.set_data(html)
        return response
    except Exception:
        return response


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
    p = Player(name=old_player.name, position=old_player.position, attack=old_player.attack,
               defense=old_player.defense, speed=old_player.speed, overall=old_player.overall,
               stamina=old_player.stamina, goals=old_player.goals, matches_played=old_player.matches_played,
               yellow_cards=old_player.yellow_cards, red_cards=old_player.red_cards, club_id=club_id, assists=0)
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


def create_random_players(count):
    players = []
    for _ in range(count):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f'{first} {last}'
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
            other = random.choice([x for x in POSITIONS if x != pos])
            preferred.append(other)
        p.preferred_positions = json.dumps(preferred)
        players.append(p)
    return players


def auto_select_xi(players, formation):
    formation_map = {
        '4-3-3': ['GK', 'LB', 'CB', 'CB', 'RB', 'LW', 'CM', 'CM', 'CM', 'RW', 'ST'],
        '4-2-3-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'CDM', 'LW', 'CAM', 'RW', 'ST'],
        '5-3-2': ['GK', 'LWB', 'CB', 'CB', 'CB', 'RWB', 'CM', 'CM', 'CM', 'ST', 'ST'],
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
        elif position in ('LB', 'RB', 'LWB', 'RWB'):
            stat_score = player.defense * 0.5 + player.speed * 0.4 + player.attack * 0.1
        elif position == 'CB':
            stat_score = player.defense * 0.7 + player.speed * 0.2 + player.attack * 0.1
        elif position in ('CDM', 'CM'):
            stat_score = player.defense * 0.4 + player.attack * 0.4 + player.speed * 0.2
        elif position in ('LW', 'RW', 'CAM'):
            stat_score = player.attack * 0.5 + player.speed * 0.4 + player.defense * 0.1
        elif position == 'ST':
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
        scores[pos].sort(key=lambda x: x[1], reverse=True)

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


@app.route('/sounds/<path:filename>')
def serve_sounds(filename):
    return send_from_directory(os.path.join(app.root_path, 'sounds'), filename)


@app.route('/')
def index():
    return render_template('index.html')


def generate_balanced_squad(club_id, formation):
    # (vị trí, tên, họ, quốc tịch, tấn công, phòng thủ, tốc độ, tuổi, chiều cao, cân nặng)
    positions_template = [
        ('GK', 'Manuel', 'Neuer', 'Đức', 86, 88, 65, 38, 193, 93),
        ('LB', 'Alphonso', 'Davies', 'Canada', 78, 84, 94, 24, 183, 77),
        ('CB', 'Virgil', 'van Dijk', 'Hà Lan', 68, 92, 78, 33, 193, 92),
        ('CB', 'Ruben', 'Dias', 'Bồ Đào Nha', 66, 91, 76, 27, 187, 83),
        ('RB', 'Achraf', 'Hakimi', 'Maroc', 79, 85, 93, 26, 181, 73),
        ('CDM', 'Rodri', 'Hernandez', 'Tây Ban Nha', 82, 90, 79, 28, 191, 82),
        ('CM', 'Federico', 'Valverde', 'Uruguay', 86, 82, 88, 26, 182, 78),
        ('CAM', 'Jamal', 'Musiala', 'Đức', 90, 72, 91, 21, 184, 72),
        ('LW', 'Jérémy', 'Doku', 'Bỉ', 92, 65, 96, 22, 173, 66),
        ('RW', 'Lamine', 'Yamal', 'Tây Ban Nha', 91, 64, 93, 17, 178, 66),
        ('ST', 'Erling', 'Haaland', 'Na Uy', 95, 60, 91, 24, 194, 88),
        ('GK', 'Thibaut', 'Courtois', 'Bỉ', 84, 86, 62, 32, 200, 96),
        ('CB', 'Eder', 'Militao', 'Brazil', 65, 87, 82, 26, 186, 78),
        ('LWB', 'Marc', 'Cucurella', 'Tây Ban Nha', 75, 80, 84, 26, 175, 68),
        ('CM', 'Piotr', 'Zielinski', 'Ba Lan', 83, 76, 80, 30, 180, 76),
        ('RM', 'Steve', 'McManaman', 'Anh', 85, 70, 87, 28, 183, 74),
        ('ST', 'Angel', 'Correa', 'Argentina', 87, 58, 86, 29, 171, 70),
        ('RW', 'Ferran', 'Torres', 'Tây Ban Nha', 88, 62, 89, 24, 184, 77),
    ]
    players = []
    for i, item in enumerate(positions_template):
        pos, first_name, last_name, nation = item[0], item[1], item[2], item[3]
        atk = item[4] + random.randint(-1, 2)
        deff = item[5] + random.randint(-1, 2)
        spd = item[6] + random.randint(-1, 2)
        ovr = round((atk + deff + spd) / 3, 1)
        p = Player(**{
            'name': f'{first_name} {last_name}', 'position': pos,
            'attack': atk, 'defense': deff, 'speed': spd, 'overall': ovr,
            'stamina': 100.0, 'goals': 0, 'assists': 0, 'matches_played': 0,
            'is_starting': i < 11, 'is_substitute': i >= 11, 'club_id': club_id,
            'training_level': random.randint(18, 26), 'rank_level': random.randint(2, 4),
            'skill_boost': random.randint(4, 7),
            'age': item[7], 'height': item[8], 'weight': item[9], 'nationality': nation,
            'skill_moves': 4, 'weak_foot': 4,
            'contract_wage': random.randint(50000, 120000), 'market_value': int(ovr * 150000),
        })
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
            return render_template('create_club.html', error='Tên CLB phải có ít nhất 2 ký tự.')
        club = Club(name=name, league=league, formation=formation, tactic='Can bang', money=80000000)
        db.session.add(club)
        db.session.commit()
        generate_balanced_squad(club.id, formation)
        coach = Coach(name='Pep Guardiola', age=50, nationality='Tây Ban Nha', tactic_preference=formation)
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
    return render_template('dashboard.html', club=club, team=club, season_complete=club.round >= 18)


# ======================================================================

# ===== Học viện trẻ, tài trợ, danh hiệu, chuyển nhượng, tập luyện =====
SCOUT_HUBS = {'vietnam': {'name': 'Học Viện Trẻ Việt Nam',
             'cost': 150000,
             'pot_min': 72,
             'pot_max': 88,
             'origin': 'Học Viện JMG / PVF',
             'first_names': ['Minh',
                             'Quang',
                             'Tuấn',
                             'Hoàng',
                             'Duy',
                             'Đức',
                             'Văn',
                             'Công',
                             'Hùng',
                             'Hải',
                             'Bảo',
                             'Long'],
             'last_names': ['Nguyễn',
                            'Trần',
                            'Lê',
                            'Phạm',
                            'Hoàng',
                            'Huỳnh',
                            'Phan',
                            'Vũ',
                            'Đặng',
                            'Bùi',
                            'Đỗ',
                            'Hồ']},
 'south_america': {'name': 'Lò Đào Tạo Nam Mỹ',
                   'cost': 450000,
                   'pot_min': 82,
                   'pot_max': 95,
                   'origin': 'Santos / Boca Juniors',
                   'first_names': ['Lucas',
                                   'Mateo',
                                   'Gabriel',
                                   'Thiago',
                                   'Enzo',
                                   'Felipe',
                                   'Rodrigo',
                                   'Joao',
                                   'Diego',
                                   'Julian'],
                   'last_names': ['Silva',
                                  'Santos',
                                  'Oliveira',
                                  'Rodriguez',
                                  'Martinez',
                                  'Alvarez',
                                  'Fernandez',
                                  'Gomez',
                                  'Costa']},
 'europe': {'name': 'Lò Đào Tạo Châu Âu (Wonderkids)',
            'cost': 850000,
            'pot_min': 88,
            'pot_max': 99,
            'origin': 'La Masia / Carrington / Ajax',
            'first_names': ['Leo',
                            'Lamine',
                            'Jude',
                            'Gavi',
                            'Pedri',
                            'Kylian',
                            'Erling',
                            'Florian',
                            'Arda',
                            'Jamal'],
            'last_names': ['Yamal',
                           'Bellingham',
                           'Musiala',
                           'Wirtz',
                           'Guler',
                           'Davies',
                           'Camavinga',
                           'Mainoo',
                           'Endrick']},
 'africa': {'name': 'Học Viện Thể Lực Châu Phi',
            'cost': 300000,
            'pot_min': 76,
            'pot_max': 92,
            'origin': 'Right to Dream / ASEC',
            'first_names': ['Victor',
                            'Sadio',
                            'Mo',
                            'Achraf',
                            'Amad',
                            'Kudus',
                            'Osimhen',
                            'Bissouma',
                            'Pape'],
            'last_names': ['Diallo', 'Sarr', 'Toure', 'Kone', 'Mensah', 'Traore', 'Camara', 'Diop', 'Cisse']}}



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
            # Tên người Việt viết Họ trước, các khu vực khác viết Tên trước
            'name': f'{last} {first}' if region == 'vietnam' else f'{first} {last}',
            'position': pos, 'age': age, 'overall': cur_ovr, 'potential': pot,
            'attack': att, 'defense': deff, 'speed': spd, 'scout_origin': hub['origin'],
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
        session['youth_error'] = 'Không tìm thấy thông tin cầu thủ trẻ.'
        return redirect(url_for('youth_academy'))

    yp = YouthPlayer(name=talent['name'], position=talent['position'], age=talent.get('age', 16),
                     overall=talent['overall'], potential=talent['potential'], attack=talent['attack'],
                     defense=talent['defense'], speed=talent['speed'],
                     scout_origin=talent.get('scout_origin', 'Học viện CLB'), club_id=club.id)
    db.session.add(yp)
    db.session.commit()
    scout_results = [t for t in scout_results if t.get('name') != talent['name']]
    session['scout_results'] = scout_results
    session['youth_message'] = (f"Đã ký hợp đồng đưa tài năng trẻ {talent['name']} "
                                f"(Tiềm năng: {talent['potential']}) vào Học viện!")
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
        session['youth_error'] = 'Không tìm thấy học viên.'
        return redirect(url_for('youth_academy'))
    if club.money < cost:
        session['youth_error'] = 'Ngân sách không đủ $50,000 cho buổi huấn luyện chuyên sâu.'
        return redirect(url_for('youth_academy'))
    if yp.overall >= yp.potential:
        session['youth_error'] = f'{yp.name} đã chạm trần tiềm năng tối đa ({yp.potential} OVR)!'
        return redirect(url_for('youth_academy'))
    club.money -= cost
    yp.attack = min(yp.potential, yp.attack + random.randint(1, 3))
    yp.defense = min(yp.potential, yp.defense + random.randint(1, 3))
    yp.speed = min(yp.potential, yp.speed + random.randint(1, 3))
    yp.overall = round((yp.attack + yp.defense + yp.speed) / 3, 1)
    yp.training_points += 15
    db.session.commit()
    session['youth_message'] = f'Huấn luyện thành công! {yp.name} đã tăng lên {yp.overall} OVR!'
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
        session['youth_error'] = 'Không tìm thấy học viên.'
        return redirect(url_for('youth_academy'))
    senior_player = Player(name=yp.name, position=yp.position, attack=yp.attack, defense=yp.defense,
                           speed=yp.speed, overall=yp.overall, stamina=100.0,
                           preferred_positions=json.dumps([yp.position]), is_starting=False,
                           is_substitute=True, club_id=club.id)
    db.session.add(senior_player)
    db.session.delete(yp)
    db.session.commit()
    session['youth_message'] = (f'🚀 Chúc mừng! Cầu thủ trẻ {senior_player.name} ({senior_player.position} - '
                                f'{senior_player.overall} OVR) đã chính thức được đôn lên Đội 1!')
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
        session['youth_message'] = f'Đã thanh lý hợp đồng đào tạo với học viên {name}.'
    return redirect(url_for('youth_academy'))


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
    session['sponsor_message'] = (f'🎉 Ký kết thành công hợp đồng tài trợ mới cùng {sponsor_name}! '
                                  f'Trợ cấp: ${sponsor_weekly:,}/tuần.')
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


def build_transfer_market(club):
    # Dùng seed cố định theo CLB/mùa/vòng để thị trường không đổi khi tải lại trang
    rng = random.Random(f'market-{club.id}-{club.season}-{club.round}')
    positions = ['GK', 'CB', 'LB', 'RB', 'CM', 'CAM', 'LW', 'RW', 'ST']
    candidates = []
    base_ovr = 75 if club.league == 'Hang 1' else (84 if club.league == 'Champions League' else 64)
    for index in range(6):
        overall = rng.randint(base_ovr - 4, base_ovr + 8)
        candidates.append({
            'id': f'{club.season}-{club.round}-{index}',
            'name': f'{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}',
            'position': rng.choice(positions),
            'overall': overall,
            'attack': min(95, overall + rng.randint(-8, 8)),
            'defense': min(95, overall + rng.randint(-8, 8)),
            'speed': min(95, overall + rng.randint(-8, 8)),
            'price': overall * 75000,
        })
    return candidates


def build_incoming_offers(club, squad_players):
    rng = random.Random(f'offers-{club.id}-{club.season}-{club.round}')
    offers = []
    if len(squad_players) > 12 and rng.random() < 0.7:
        target = rng.choice(squad_players)
        opp_names = ['Hà Nội FC', 'Công An Hà Nội', 'Thể Công Viettel', 'Real Madrid', 'Manchester City',
                     'Paris Saint-Germain']
        offer_club = rng.choice(opp_names)
        premium = rng.uniform(1.1, 1.4)
        offer_price = int(target.overall * 70000 * premium)
        offers.append({'id': f'offer-{target.id}-{club.round}', 'player_id': target.id,
                       'player_name': target.name, 'club_name': offer_club, 'offer_price': offer_price})
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
                error = f"Ngân sách không đủ ${candidate['price']:,} để mua cầu thủ này."
            else:
                player = Player(name=candidate['name'], position=candidate['position'],
                                attack=candidate['attack'], defense=candidate['defense'],
                                speed=candidate['speed'], overall=candidate['overall'], stamina=100.0,
                                preferred_positions=json.dumps([candidate['position']]), club_id=club.id)
                db.session.add(player)
                club.money -= candidate['price']
                market.remove(candidate)
                session['transfer_market'] = market
                session.modified = True
                db.session.commit()
                message = f'✅ Đã ký hợp đồng thành công với {player.name}!'

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
                    success_rate = 0.6 if discount <= 0.85 else (0.85 if discount <= 0.9 else 0.98)
                    if random.random() <= success_rate:
                        player = Player(name=candidate['name'], position=candidate['position'],
                                        attack=candidate['attack'], defense=candidate['defense'],
                                        speed=candidate['speed'], overall=candidate['overall'], stamina=100.0,
                                        preferred_positions=json.dumps([candidate['position']]),
                                        club_id=club.id)
                        db.session.add(player)
                        club.money -= bid_price
                        market.remove(candidate)
                        session['transfer_market'] = market
                        session.modified = True
                        db.session.commit()
                        saved = candidate['price'] - bid_price
                        message = (f'🎉 Đàm phán thành công! CLB đối tác đồng ý bán {player.name} với giá '
                                   f'${bid_price:,} (Tiết kiệm được ${saved:,})!')
                    else:
                        error = (f'❌ CLB đối tác đã từ chối lời đề nghị trả giá rẻ hơn '
                                 f'{int((1 - discount) * 100)}% của bạn!')

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
                message = f'📤 Đã bán {p_name} và thu về +${sale_value:,} vào ngân sách!'

        elif action == 'accept_offer':
            offer_id = request.form.get('offer_id')
            offer = next((o for o in incoming_offers if o['id'] == offer_id), None)
            if offer:
                p = db.session.get(Player, offer['player_id'])
                if p and p.club_id == club.id and len(squad_players) > 11:
                    p_name = p.name
                    club.money += offer['offer_price']
                    db.session.delete(p)
                    incoming_offers.remove(offer)
                    session['incoming_offers'] = incoming_offers
                    session.modified = True
                    db.session.commit()
                    squad_players = Player.query.filter_by(club_id=club.id).all()
                    message = (f"🤝 Đã hoàn tất chuyển nhượng! {p_name} gia nhập {offer['club_name']} "
                               f"với giá ${offer['offer_price']:,}!")
                else:
                    error = 'Không thể bán cầu thủ này hoặc đội hình không đủ số lượng tối thiểu!'

        elif action == 'reject_offer':
            offer_id = request.form.get('offer_id')
            incoming_offers = [o for o in incoming_offers if o['id'] != offer_id]
            session['incoming_offers'] = incoming_offers
            session.modified = True
            message = 'Đã từ chối lời đề nghị chuyển nhượng.'

    return render_template('transfer_market.html', club=club, candidates=market, squad_players=squad_players,
                           incoming_offers=incoming_offers, message=message, error=error)


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
            player.experience = (getattr(player, 'experience', 0) or 0) + 10
            club.money -= cost
            db.session.commit()
            message = f'{player.name} đã tăng 2 điểm {focus} sau buổi tập!'
    return render_template('training.html', club=club, players=players, message=message, error=error)


# ======================================================================


# ======================================================================
# THẺ CẦU THỦ PHONG CÁCH FC MOBILE, ĐỘI HÌNH, CHỌN 11 ĐÁ CHÍNH
# ======================================================================
def enrich_player_fc(p, club):
    name_str = (p.name or 'Player').strip()
    name_parts = name_str.split()
    if len(name_parts) >= 2:
        first_name = ' '.join(name_parts[:-1]).upper()
        last_name = name_parts[-1].upper()
    else:
        first_name = 'CẦU THỦ'
        last_name = name_str.upper()

    t_lvl = getattr(p, 'training_level', 10) or 10
    r_lvl = getattr(p, 'rank_level', 1) or 1
    s_boost = getattr(p, 'skill_boost', 2) or 2

    base_ovr = int(round(p.overall or 60))
    fc_ovr = int(base_ovr + (r_lvl - 1) * 3 + t_lvl // 5)
    stat_bonus = (r_lvl - 1) * 2 + t_lvl // 4
    pac = int(p.speed + stat_bonus)
    sho = int(p.attack + stat_bonus)
    pas = int(round(p.attack * 0.6 + p.defense * 0.4) + stat_bonus)
    dri = int(round(p.speed * 0.7 + p.attack * 0.3) + stat_bonus)
    deff = int(p.defense + stat_bonus)
    phy = int(round(p.stamina * 0.7 + p.defense * 0.3) + stat_bonus)

    pos = (p.position or 'CM').upper()
    if pos in ('LW', 'RW', 'LM', 'RM'):
        playstyle_name = 'Rê bóng bứt tốc thần sầu'
        playstyle_icon = '⚡'
        playstyle_desc = 'Tăng 15% tốc độ bứt phá qua người và khả năng khống chế bóng dính chân khi tăng tốc.'
        sec_pos = 'LW, RW' if pos in ('LW', 'RW') else 'LM, RM'
    elif pos in ('ST', 'CF'):
        playstyle_name = 'Cây săn bàn sát thủ'
        playstyle_icon = '🎯'
        playstyle_desc = 'Khả năng dứt điểm 1 chạm uy lực, chọn vị trí đánh đầu và sút xa hiểm hóc trong vòng cấm.'
        sec_pos = 'ST, CF'
    elif pos in ('CAM', 'CM'):
        playstyle_name = 'Nhạc trưởng kiến tạo ma thuật'
        playstyle_icon = '🪄'
        playstyle_desc = 'Nhãn quan chiến thuật phi phàm, chọc khe bổng xé toang hàng phòng ngự đối phương.'
        sec_pos = 'CAM, CM'
    elif pos in ('CDM',):
        playstyle_name = 'Máy quét bọc lót toàn diện'
        playstyle_icon = '🛡️'
        playstyle_desc = 'Cắt bóng thông minh, tranh chấp áp sát quyết liệt làm nản lòng mọi tiền vệ tấn công.'
        sec_pos = 'CDM, CM'
    elif pos in ('CB', 'LB', 'RB', 'LWB', 'RWB'):
        playstyle_name = 'Bức tường thép không thể xuyên phá'
        playstyle_icon = '🧱'
        playstyle_desc = 'Xoạc bóng chính xác, không chiến mạnh mẽ và kèm người cực kỳ chắc chắn.'
        sec_pos = 'CB, LB, RB'
    elif pos == 'GK':
        playstyle_name = 'Bạch tuộc phản xạ xuất thần'
        playstyle_icon = '🧤'
        playstyle_desc = 'Phản xạ xuất thần trong cự ly gần, đổ người bay người cản phá phạt đền siêu đẳng.'
        sec_pos = 'GK'
    else:
        playstyle_name = 'Chiến binh công thủ toàn diện'
        playstyle_icon = '⭐'
        playstyle_desc = 'Lên công về thủ nhịp nhàng, đóng góp tích cực vào lối chơi tập thể.'
        sec_pos = pos

    attrs = {
        'pace': {
            'acceleration': int(min(250, pac + 3)),
            'sprint_speed': int(min(250, pac - 1)),
        },
        'shooting': {
            'finishing': int(min(250, sho + (8 if pos in ('ST', 'LW', 'RW') else 0))),
            'shot_power': int(min(250, sho + 4)),
            'long_shots': int(min(250, sho - 2)),
            'volleys': int(min(250, sho - 4)),
            'penalties': int(min(250, sho + 3)),
            'positioning': int(min(250, int(round((sho + dri) / 2)))),
        },
        'passing': {
            'vision': int(min(250, pas + (6 if pos in ('CAM', 'CM') else 0))),
            'short_passing': int(min(250, pas + 4)),
            'long_passing': int(min(250, pas - 2)),
            'crossing': int(min(250, pas + (8 if pos in ('LW', 'RW', 'LB', 'RB') else 0))),
            'free_kick': int(min(250, pas + 2)),
            'curve': int(min(250, int(round((pas + sho) / 2)))),
        },
        'dribbling': {
            'agility': int(min(250, dri + 5)),
            'balance': int(min(250, dri + 1)),
            'reactions': int(min(250, int(round((dri + pac) / 2)))),
            'ball_control': int(min(250, dri + 4)),
            'dribbling': int(min(250, dri + 6)),
            'composure': int(min(250, int(round(p.overall + 5)))),
        },
        'defending': {
            'interceptions': int(min(250, deff + (6 if pos in ('CB', 'CDM') else 0))),
            'heading_accuracy': int(min(250, int(round((deff + phy) / 2)))),
            'marking': int(min(250, deff + 4)),
            'standing_tackle': int(min(250, deff + 5)),
            'sliding_tackle': int(min(250, deff - 2)),
        },
        'physical': {
            'jumping': int(min(250, int(round((phy + pac) / 2)))),
            'stamina': int(round(p.stamina or 100)),
            'strength': int(min(250, phy + (6 if pos in ('CB', 'ST') else 0))),
            'aggression': int(min(250, phy - 2)),
        },
    }
    if pos == 'GK':
        attrs['goalkeeping'] = {
            'gk_diving': int(min(250, deff + 12)),
            'gk_handling': int(min(250, deff + 8)),
            'gk_kicking': int(min(250, pas + 5)),
            'gk_reflexes': int(min(250, pac + 15)),
            'gk_positioning': int(min(250, deff + 10)),
        }

    nation = getattr(p, 'nationality', 'Việt Nam') or 'Việt Nam'
    flag_code = ('VIE' if 'Việt' in nation else 'BEL' if 'Bỉ' in nation else 'BRA' if 'Brazil' in nation
                 else 'FRA' if 'Pháp' in nation else 'VIE')
    league = club.league if club else 'V-League 1'
    club_name = club.name if club else 'FC Club'

    playstyles_list = [
        {'name': 'Sút xoáy Finesse Shot', 'icon': '🌀',
         'desc': 'Cú sút má trong hiểm hóc với độ xoáy cực cao khiến thủ môn đối phương bó tay.'},
        {'name': 'Bứt tốc Speed Dribbler', 'icon': '⚡',
         'desc': 'Khả năng đẩy bóng dài và tăng tốc đoạn ngắn không thể ngăn cản.'},
        {'name': 'Chuyền điểm rơi Long Passer', 'icon': '📐',
         'desc': 'Những đường chuyền dài đảo cánh mở toang không gian tấn công.'},
        {'name': 'Đánh đầu uy lực Power Header', 'icon': '💥',
         'desc': 'Bật cao tranh chấp không chiến và đánh đầu uy lực thành bàn.'},
    ]

    tier = 'tier-ucl' if fc_ovr >= 85 else ('tier-gold' if fc_ovr >= 74 else 'tier-silver')

    return {
        'id': p.id,
        'name': p.name,
        'first_name': first_name,
        'last_name': last_name,
        'position': p.position,
        'secondary_pos': sec_pos,
        'overall': base_ovr,
        'fc_ovr': fc_ovr,
        'speed': pac,
        'attack': sho,
        'defense': deff,
        'stamina': p.stamina,
        'pac': pac,
        'sho': sho,
        'pas': pas,
        'dri': dri,
        'def': deff,
        'phy': phy,
        'tier': tier,
        'training_level': t_lvl,
        'max_training_level': 30,
        'rank_level': r_lvl,
        'max_rank_level': 5,
        'skill_boost': s_boost,
        'age': getattr(p, 'age', 24) or 24,
        'height': getattr(p, 'height', 178) or 178,
        'weight': getattr(p, 'weight', 72) or 72,
        'weak_foot': getattr(p, 'weak_foot', 4) or 4,
        'skill_moves': getattr(p, 'skill_moves', 4) or 4,
        'nationality': nation,
        'flag_code': flag_code,
        'league': league,
        'club_name': club_name,
        'is_starting': p.is_starting,
        'is_substitute': p.is_substitute,
        'goals': p.goals,
        'assists': p.assists,
        'matches_played': p.matches_played,
        'contract_wage': getattr(p, 'contract_wage', 50000) or 50000,
        'market_value': getattr(p, 'market_value', 500000) or 500000,
        'playstyle_name': playstyle_name,
        'playstyle_icon': playstyle_icon,
        'playstyle_desc': playstyle_desc,
        'attrs': attrs,
        'playstyles_list': playstyles_list,
    }


@app.route('/squad')
def squad():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))

    raw_players = Player.query.filter_by(club_id=club.id).order_by(Player.overall.desc()).all()
    starting_count = sum(1 for p in raw_players if p.is_starting)
    if starting_count != 11 and len(raw_players) >= 11:
        selected_ids = auto_select_xi(raw_players, club.formation)
        for p in raw_players:
            p.is_starting = p.id in selected_ids
            p.is_substitute = not p.is_starting
        db.session.commit()

    enriched_players = [enrich_player_fc(p, club) for p in raw_players]
    starting_players = [p for p in enriched_players if p['is_starting']]
    sub_players = [p for p in enriched_players if not p['is_starting']]
    if starting_players:
        team_ovr = int(round(sum(p['fc_ovr'] for p in starting_players) / len(starting_players)))
    else:
        team_ovr = int(round(sum(p['fc_ovr'] for p in enriched_players[:11])
                             / max(1, min(11, len(enriched_players)))))
    team_value = sum(p['market_value'] for p in enriched_players) * 10
    return render_template('squad.html', players=raw_players, enriched_players=enriched_players,
                           starting_players=starting_players, sub_players=sub_players,
                           team_ovr=team_ovr, team_value=team_value, team=club, club=club)


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
        p.is_starting = p.id in selected_ids
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
        'team_ovr': team_ovr,
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
    p1.is_starting, p2.is_starting = p2.is_starting, p1.is_starting
    p1.is_substitute = not p1.is_starting
    p2.is_substitute = not p2.is_starting
    db.session.commit()
    raw_players = Player.query.filter_by(club_id=club.id).all()
    enriched_players = [enrich_player_fc(p, club) for p in raw_players]
    starting_players = [p for p in enriched_players if p['is_starting']]
    sub_players = [p for p in enriched_players if not p['is_starting']]
    team_ovr = (int(round(sum(p['fc_ovr'] for p in starting_players) / len(starting_players)))
                if starting_players else 100)
    return jsonify({
        'success': True,
        'message': f'Đã đổi {p1.name} và {p2.name} thành công!',
        'starting_players': starting_players,
        'sub_players': sub_players,
        'team_ovr': team_ovr,
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
            p.is_starting = p.id in selected_ids
            p.is_substitute = not p.is_starting
        db.session.commit()  # (bản gốc chỉ commit trong nhánh này)
    enriched_players = [enrich_player_fc(p, club) for p in raw_players]
    starting_players = [p for p in enriched_players if p['is_starting']]
    sub_players = [p for p in enriched_players if not p['is_starting']]
    team_ovr = (int(round(sum(p['fc_ovr'] for p in starting_players) / len(starting_players)))
                if starting_players else 100)
    return jsonify({
        'success': True,
        'message': f'Đã chuyển sang sơ đồ {formation}!',
        'formation': formation,
        'starting_players': starting_players,
        'sub_players': sub_players,
        'team_ovr': team_ovr,
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
    return render_template('player_detail.html', player=current_player_enriched, club=club,
                           enriched_players=enriched_players)


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
        'club_money': club.money,
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
        'club_money': club.money,
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
    return jsonify({'success': True, 'player1': enrich_player_fc(p1, club),
                    'player2': enrich_player_fc(p2, club)})


@app.route('/select_xi', methods=['GET', 'POST'])
def select_xi():
    if 'club_id' not in session:
        return redirect(url_for('index'))
    club = db.session.get(Club, session['club_id'])
    if not club:
        return redirect(url_for('index'))
    players = Player.query.filter_by(club_id=club.id).all()
    if request.method == 'POST':
        new_formation = request.form.get('formation')
        formation_map = {
            '4-3-3': ['GK', 'LB', 'CB', 'CB', 'RB', 'LW', 'CM', 'CM', 'CM', 'RW', 'ST'],
            '4-2-3-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'CDM', 'LW', 'CAM', 'RW', 'ST'],
            '5-3-2': ['GK', 'LWB', 'CB', 'CB', 'CB', 'RWB', 'CM', 'CM', 'CM', 'ST', 'ST'],
        }
        if new_formation in formation_map:
            club.formation = new_formation
        if request.form.get('auto') == '1':
            selected_ids = auto_select_xi(players, club.formation)
        else:
            selected_ids = [int(id) for id in request.form.getlist('starting')]
            if len(selected_ids) != 11:
                return render_template('select_xi.html', team=club, players=players,
                                       error='Phải chọn đúng 11 cầu thủ đá chính!')
        for p in players:
            p.is_starting = p.id in selected_ids
            p.is_substitute = not p.is_starting
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('select_xi.html', team=club, players=players)


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
        p.is_starting = p.id in selected_ids
        p.is_substitute = not p.is_starting
    db.session.commit()
    starting_names = [p.name for p in players if p.id in selected_ids]
    return jsonify({'success': True, 'selected': selected_ids, 'names': starting_names})


# ======================================================================

# ============================ TRẬN ĐẤU ============================
LEAGUE_OPPONENTS = {'Hang 2': [{'name': 'Bình Phước FC', 'formation': '4-3-3', 'tactic': 'Tan cong'},
            {'name': 'PVF-CAND', 'formation': '4-2-3-1', 'tactic': 'Can bang'},
            {'name': 'Phù Đổng Ninh Bình', 'formation': '5-3-2', 'tactic': 'Phong thu'},
            {'name': 'Bà Rịa Vũng Tàu', 'formation': '4-3-3', 'tactic': 'Can bang'},
            {'name': 'Long An FC', 'formation': '4-2-3-1', 'tactic': 'Phong thu'},
            {'name': 'Đồng Tháp FC', 'formation': '5-3-2', 'tactic': 'Phong thu'},
            {'name': 'Huế FC', 'formation': '4-3-3', 'tactic': 'Can bang'},
            {'name': 'Hòa Bình FC', 'formation': '4-2-3-1', 'tactic': 'Can bang'},
            {'name': 'Đồng Nai FC', 'formation': '5-3-2', 'tactic': 'Phong thu'}],
 'Hang 1': [{'name': 'Công An Hà Nội', 'formation': '4-3-3', 'tactic': 'Tan cong'},
            {'name': 'Thép Xanh Nam Định', 'formation': '4-2-3-1', 'tactic': 'Tan cong'},
            {'name': 'Hà Nội FC', 'formation': '4-3-3', 'tactic': 'Can bang'},
            {'name': 'Thể Công Viettel', 'formation': '5-3-2', 'tactic': 'Phong thu'},
            {'name': 'Becamex Bình Dương', 'formation': '4-2-3-1', 'tactic': 'Can bang'},
            {'name': 'Hoàng Anh Gia Lai', 'formation': '4-3-3', 'tactic': 'Tan cong'},
            {'name': 'Hải Phòng FC', 'formation': '4-2-3-1', 'tactic': 'Can bang'},
            {'name': 'Sông Lam Nghệ An', 'formation': '5-3-2', 'tactic': 'Phong thu'},
            {'name': 'SHB Đà Nẵng', 'formation': '4-3-3', 'tactic': 'Can bang'}],
 'Champions League': [{'name': 'Real Madrid', 'formation': '4-3-3', 'tactic': 'Tan cong'},
                      {'name': 'Manchester City', 'formation': '4-2-3-1', 'tactic': 'Tan cong'},
                      {'name': 'Bayern Munich', 'formation': '4-2-3-1', 'tactic': 'Tan cong'},
                      {'name': 'Paris Saint-Germain', 'formation': '4-3-3', 'tactic': 'Tan cong'},
                      {'name': 'Arsenal FC', 'formation': '4-3-3', 'tactic': 'Can bang'},
                      {'name': 'Inter Milan', 'formation': '5-3-2', 'tactic': 'Phong thu'},
                      {'name': 'Barcelona', 'formation': '4-3-3', 'tactic': 'Tan cong'},
                      {'name': 'Liverpool FC', 'formation': '4-3-3', 'tactic': 'Tan cong'}]}


def get_opponent_for_round(league, round_num):
    opp_list = LEAGUE_OPPONENTS.get(league, LEAGUE_OPPONENTS['Hang 2'])
    idx = (round_num - 1) % len(opp_list)
    opp = opp_list[idx]
    pos_map = {
        '4-3-3': ['GK', 'LB', 'CB', 'CB', 'RB', 'CM', 'CM', 'CM', 'LW', 'RW', 'ST'],
        '4-2-3-1': ['GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'CDM', 'CAM', 'LW', 'RW', 'ST'],
        '5-3-2': ['GK', 'LWB', 'CB', 'CB', 'CB', 'RWB', 'CM', 'CM', 'CM', 'ST', 'ST'],
    }
    positions = pos_map.get(opp['formation'], pos_map['4-3-3'])
    first_names = ['Minh', 'Tuấn', 'Hoàng', 'Nam', 'Quang', 'Duy', 'Hải', 'Hùng', 'Bảo', 'Đức', 'Văn', 'Công',
                   'Phượng', 'Thắng', 'Long']
    last_names = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng', 'Bùi', 'Đỗ',
                  'Hồ', 'Ngô', 'Dương']
    players = []
    base_ovr = 75 if league == 'Hang 1' else (85 if league == 'Champions League' else 65)
    for pos in positions:
        name = f'{random.choice(last_names)} {random.choice(first_names)}'
        ovr = random.randint(base_ovr - 4, base_ovr + 6)
        players.append({'name': name, 'position': pos, 'overall': ovr, 'stamina': 100.0,
                        'attack': ovr, 'defense': ovr, 'speed': ovr, 'goals': 0})
    return {'name': opp['name'], 'formation': opp['formation'], 'tactic': opp['tactic'], 'players': players}


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
    starting_players_data = [{'id': p.id, 'name': p.name, 'position': p.position,
                              'stamina': p.stamina, 'overall': p.overall} for p in starting_players]
    if request.method == 'POST':
        for player in players:
            player.stamina = min(100.0, player.stamina + 20.0)
        db.session.commit()
        tactic = request.form.get('tactic', 'Can bang')
        club.tactic = tactic
        db.session.commit()
        session['live_match'] = {
            'home_goals': 0,
            'away_goals': 0,
            'events': [],
            'current_minute': 0,
            'home_team': club.name,
            'home_formation': club.formation,
            'away_team': opponent['name'],
            'away_formation': opponent['formation'],
            'away_tactic': opponent['tactic'],
            'subs_used': 0,
            'half': 1,
            'phase': 'first_half',
            'finalized': False,
            'finished': False,
            'tactic': tactic,
            'round': club.round + 1,
            'home_players': starting_players_data,
            'away_players': opponent['players'],
            'ball_x': 50,
            'ball_y': 50,
        }
        session['subs_used'] = 0
        return redirect(url_for('live_match'))
    return render_template('match.html', club=club, starting_players=starting_players_data,
                           round=club.round + 1, formation=club.formation, opponent=opponent)


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
        'description': f'📋 Phút {cur_min}: HLV đổi chiến thuật sang: {tactic.upper()}',
    })
    session.modified = True
    return jsonify({'success': True, 'tactic': tactic})


@app.route('/tutorial')
def tutorial():
    is_first_visit = session.pop('show_tutorial_welcome', False)
    club = db.session.get(Club, session['club_id']) if session.get('club_id') else None
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
    match.add_event(90, f'⏱️ Kết thúc trận đấu! Tỉ số {match.home_goals}-{match.away_goals}')
    club.points += match.points()
    club.matches_played += 1
    club.round += 1
    weekly_payout = club.sponsor_weekly or 250000
    win_bonus = (club.sponsor_bonus or 150000) if match.result() == 'Thắng' else 0
    club.money += weekly_payout + win_bonus
    for p_old in team_old.players:
        p_db = Player.query.filter_by(name=p_old.name, club_id=club.id).first()
        if not p_db:
            continue
        p_db.stamina = p_old.stamina
        p_db.goals = p_old.goals
        p_db.matches_played = p_old.matches_played + 1
        p_db.experience = getattr(p_db, 'experience', 0) + 5
    match_data.update({'finished': True, 'finalized': True, 'phase': 'finished', 'events': match.events})
    db.session.add(MatchHistory(
        club_id=club.id, opponent=match.away_team.name, home_goals=match.home_goals,
        away_goals=match.away_goals, result=match.result(), points=match.points(), round=match.round,
        events=json.dumps(match.events, ensure_ascii=False),
    ))
    session['last_match'] = {
        'home': match.home_team.name, 'away': match.away_team.name,
        'home_goals': match.home_goals, 'away_goals': match.away_goals,
        'result': match.result(), 'points': match.points(), 'events': match.events, 'round': match.round,
    }
    db.session.commit()


@app.route('/api/tick', methods=['POST'])
def tick():
    if 'club_id' not in session or 'live_match' not in session:
        return jsonify({'error': 'No match'}), 400
    match_data = session['live_match']
    if match_data.get('finished', False):
        return jsonify({'finished': True})
    if match_data.get('phase') == 'halftime':
        return jsonify({
            'halftime': True, 'phase': 'halftime', 'half': 1, 'current_minute': 45,
            'home_goals': match_data.get('home_goals', 0), 'away_goals': match_data.get('away_goals', 0),
            'events': match_data.get('events', []),
        })
    club = db.session.get(Club, session['club_id'])
    if not club:
        return jsonify({'error': 'Club not found'}), 404
    current_minute = match_data.get('current_minute', 0)
    if current_minute >= 90:
        return jsonify({'finished': True})

    tactic = match_data.get('tactic', 'Can bang')
    team_old = club_to_team_old(club)

    # Dựng lại đội khách từ dữ liệu lưu trong session
    opp_players_old = []
    for player_data in match_data.get('away_players', []):
        player = PlayerOld(
            player_data['name'], player_data['position'],
            player_data.get('attack', player_data.get('overall', 60)),
            player_data.get('defense', player_data.get('overall', 60)),
            player_data.get('speed', player_data.get('overall', 60)),
        )
        player.stamina = player_data.get('stamina', 100.0)
        player.goals = player_data.get('goals', 0)
        opp_players_old.append(player)
    opponent = TeamOld(match_data.get('away_team', 'Đối thủ'), opp_players_old)
    opponent.starting_xi = list(range(11))
    opponent.substitutes = list(range(11, 16))

    match = MatchOld(team_old, opponent, match_data.get('round', 1))
    match.home_goals = match_data.get('home_goals', 0)
    match.away_goals = match_data.get('away_goals', 0)
    match.events = match_data.get('events', [])
    match.finished = match_data.get('finished', False)

    prev_goals = match.home_goals + match.away_goals
    next_minute = current_minute + 1
    match = run_minutes(match, next_minute, next_minute, tactic, 'Can bang')
    if match.home_goals + match.away_goals > prev_goals:
        sound.play_goal()
    elif len(match.events) > len(match_data.get('events', [])):
        sound.play_kick()

    match_data['home_goals'] = match.home_goals
    match_data['away_goals'] = match.away_goals
    match_data['events'] = match.events
    match_data['current_minute'] = next_minute
    match_data['away_players'] = [{
        'name': player.name, 'position': player.position, 'overall': player.overall,
        'stamina': player.stamina, 'attack': player.attack, 'defense': player.defense,
        'speed': player.speed, 'goals': player.goals,
    } for player in opponent.players]

    if next_minute == 45:
        match.add_event(45, f'⏱️ Kết thúc hiệp 1! Tỉ số {match.home_goals}-{match.away_goals}')
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
            if not p_db:
                continue
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
        '5-3-2': ['GK', 'LWB', 'CB', 'CB', 'CB', 'RWB', 'CM', 'CM', 'CM', 'ST', 'ST'],
    }
    pos_list = pos_map.get(formation, pos_map['4-3-3'])
    position_map = {}
    for idx, p in enumerate(xi):
        if idx < len(pos_list):
            position_map[pos_list[idx]] = {'name': p.name, 'stamina': p.stamina}
    home_players_stamina = [{'id': p.id, 'name': p.name, 'stamina': p.stamina} for p in xi]

    return jsonify({
        'home_goals': match.home_goals,
        'away_goals': match.away_goals,
        'events': match.events,
        'finished': match_data.get('finished', False),
        'current_minute': next_minute,
        'positions': position_map,
        'home_players': home_players_stamina,
        'half': match_data.get('half', 1),
        'phase': match_data.get('phase', 'first_half'),
        'halftime': match_data.get('phase') == 'halftime',
        'low_stamina_home': [p.name for p in team_old.get_starting_xi() if p.stamina < 65],
        'low_stamina_away': [p.name for p in opponent.get_starting_xi() if p.stamina < 65],
    })


@app.route('/start_second_half', methods=['POST'])
def start_second_half():
    match_data = session.get('live_match')
    if not match_data or match_data.get('phase') != 'halftime':
        return redirect(url_for('live_match'))
    match_data['phase'] = 'second_half'
    match_data['half'] = 2
    match_data['events'].append({'minute': 46, 'description': '▶️ Hiệp 2 bắt đầu!'})
    session['live_match'] = match_data
    session.modified = True
    return redirect(url_for('live_match'))


@app.route('/get_players')
def get_players():
    if 'club_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    club = db.session.get(Club, session['club_id'])
    if not club:
        return jsonify({'error': 'Club not found'}), 404
    players = Player.query.filter_by(club_id=club.id).all()
    starting = [{'id': p.id, 'name': p.name, 'position': p.position, 'stamina': p.stamina}
                for p in players if p.is_starting]
    subs = [{'id': p.id, 'name': p.name, 'position': p.position, 'stamina': p.stamina}
            for p in players if p.is_substitute]
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
            return render_template('substitution.html', xi=xi, subs=subs, subs_used=subs_used,
                                   error='Đã thay đủ 3 người!')
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
                    'description': f'Phút {cur_min} – 🔄 {player_out.name} ra → {player_in.name} vào',
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
            'description': f'Phút {cur_min} – 🔄 {player_out.name} ra → {player_in.name} vào',
        })
        session.modified = True
        return jsonify({'success': True, 'subs_used': subs_used})
    return jsonify({'error': 'Cầu thủ không hợp lệ'}), 400


@app.route('/low_stamina')
def low_stamina():
    if 'club_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    club = db.session.get(Club, session['club_id'])
    if not club:
        return jsonify({'error': 'Club not found'}), 404
    players = Player.query.filter_by(club_id=club.id).filter(Player.is_starting == True).all()  # noqa: E712
    low = [{'name': p.name, 'stamina': p.stamina} for p in players if p.stamina < 65]
    return jsonify({'home': low})


@app.route('/result')
def result():
    if 'last_match' not in session:
        return redirect(url_for('dashboard'))
    return render_template('result.html', match=session['last_match'])


# ======================================================================


# ======================= BẢNG XẾP HẠNG / LỊCH / LỊCH SỬ =======================

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
        'name': club.name, 'points': club.points, 'played': len(history),
        'wins': wins, 'draws': draws, 'losses': losses,
        'goals_for': goals_for, 'goals_against': goals_against, 'gd': gd,
        'gf': goals_for, 'ga': goals_against, 'w': wins, 'd': draws, 'l': losses,
        'pts': club.points, 'is_player': True, 'is_user': True,
    }]

    # Kết quả các đội khác được sinh ngẫu nhiên nhưng cố định theo giải + mùa
    rng = random.Random(f'{club.league}-{club.season}')
    for opp in LEAGUE_OPPONENTS.get(club.league, LEAGUE_OPPONENTS['Hang 2']):
        p_cnt = club.matches_played
        w_cnt = rng.randint(0, p_cnt) if p_cnt else 0
        d_cnt = rng.randint(0, p_cnt - w_cnt) if p_cnt - w_cnt else 0
        l_cnt = p_cnt - w_cnt - d_cnt
        gf_cnt = rng.randint(w_cnt, max(w_cnt, p_cnt * 2)) if p_cnt else 0
        ga_cnt = rng.randint(l_cnt, max(l_cnt, p_cnt * 2)) if p_cnt else 0
        teams.append({
            'name': opp['name'], 'points': w_cnt * 3 + d_cnt, 'played': p_cnt,
            'wins': w_cnt, 'draws': d_cnt, 'losses': l_cnt,
            'goals_for': gf_cnt, 'goals_against': ga_cnt, 'gd': gf_cnt - ga_cnt,
            'gf': gf_cnt, 'ga': ga_cnt, 'w': w_cnt, 'd': d_cnt, 'l': l_cnt,
            'pts': w_cnt * 3 + d_cnt, 'is_player': False, 'is_user': False,
        })

    teams.sort(key=lambda x: (-x['points'], -x['gd'], -x['goals_for']))
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
        rounds.append({
            'round': round_number,
            'home': club.name if is_home else opponent['name'],
            'away': opponent['name'] if is_home else club.name,
            'current': round_number == club.round + 1,
        })
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


# ======================= KẾT THÚC MÙA GIẢI =======================

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
        return render_template('season_end.html', message='💀 Không đủ tiền trả lương toàn đội! Game Over.')

    try:
        trophies_list = json.loads(club.trophies if club.trophies else '[]')
    except Exception:
        trophies_list = []

    msg = ''
    if club.league == 'Hang 2' and club.position <= 2:
        msg = (f'🎉 Chúc mừng! Bạn xuất sắc cán đích ở vị trí #{club.position}, giành Cúp Thăng Hạng lên Hạng 1 '
               f'và nhận thưởng $1,500,000!')
        club.league = 'Hang 1'
        club.money += 1500000
        if 'h2_promotion' not in trophies_list:
            trophies_list.append('h2_promotion')
    elif club.league == 'Hang 1' and club.position == 1:
        msg = ('🏆 Chúc mừng! Bạn đã ĐOẠT CHỨC VÔ ĐỊCH QUỐC GIA (V-League 1), nhận thưởng $8,000,000 và chính thức '
               'tiến vào đấu trường đỉnh cao thế giới: UEFA CHAMPIONS LEAGUE (Cúp C1)!')
        club.league = 'Champions League'
        club.money += 8000000
        if 'h1_champion' not in trophies_list:
            trophies_list.append('h1_champion')
    elif club.league == 'Champions League' and club.position == 1:
        msg = ('⭐🏆⭐ THẦN KỲ! BẠN ĐÃ ĐÁNH BẠI REAL MADRID, MAN CITY VÀ ĐĂNG QUANG NGÔI VÔ ĐỊCH UEFA CHAMPIONS '
               'LEAGUE (CÚP C1 CHÂU ÂU)! NHẬN THƯỞNG $15,000,000 VÀ LƯU DANH VĨ ĐẠI VÀO PHÒNG TRUYỀN THỐNG!')
        club.money += 15000000
        if 'ucl_champion' not in trophies_list:
            trophies_list.append('ucl_champion')
    else:
        msg = (f'Mùa giải khép lại ở vị trí #{club.position}. Hãy nâng cấp đội hình và quyết tâm chinh phục '
               f'danh hiệu ở mùa sau!')

    club.trophies = json.dumps(trophies_list)
    club.round = 0
    club.matches_played = 0
    club.points = 0
    club.season += 1
    db.session.commit()
    return render_template('season_end.html', club=club, message=msg)


# ======================= THỐNG KÊ / LƯƠNG =======================

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


# ======================= LƯU / TẢI GAME =======================

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
            return render_template('save.html', error='Vui lòng nhập passcode.')
        players = Player.query.filter_by(club_id=club.id).all()
        history = MatchHistory.query.filter_by(club_id=club.id).order_by(MatchHistory.round).all()
        data = {
            'club_name': club.name, 'league': club.league, 'season': club.season,
            'money': club.money, 'points': club.points, 'matches_played': club.matches_played,
            'position': club.position, 'round': club.round, 'formation': club.formation,
            'tactic': club.tactic,
            'players': [p.to_dict() for p in players],
            'match_history': [{'opponent': m.opponent, 'home_goals': m.home_goals, 'away_goals': m.away_goals,
                               'result': m.result, 'points': m.points, 'round': m.round, 'events': m.events}
                              for m in history],
        }
        save_game(data, passcode)
        return render_template('save.html', success=True)
    return render_template('save.html')


@app.route('/load', methods=['GET', 'POST'])
def load():
    if request.method == 'POST':
        passcode = request.form.get('passcode', '').strip()
        if not passcode:
            return render_template('load.html', error='Vui lòng nhập passcode.')
        data = load_game(passcode)
        if data:
            club = Club(name=data['club_name'], league=data['league'], season=data['season'],
                        money=data['money'], points=data['points'], matches_played=data['matches_played'],
                        position=data['position'], round=data['round'], formation=data['formation'],
                        tactic=data['tactic'])
            db.session.add(club)
            db.session.commit()
            for p_data in data['players']:
                p = Player(name=p_data['name'], position=p_data['position'], attack=p_data['attack'],
                           defense=p_data['defense'], speed=p_data['speed'], overall=p_data['overall'],
                           stamina=p_data['stamina'], goals=p_data['goals'], matches_played=p_data['matches_played'],
                           is_starting=p_data.get('is_starting', False),
                           is_substitute=p_data.get('is_substitute', False),
                           preferred_positions=p_data.get('preferred_positions', '[]'),
                           club_id=club.id)
                db.session.add(p)
            db.session.commit()
            session['club_id'] = club.id
            return redirect(url_for('dashboard'))
        return render_template('load.html', error='Sai passcode hoặc không tìm thấy file.')
    return render_template('load.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def auto_open_browser():
    try:
        import time
        import webbrowser
        time.sleep(1.0)
        webbrowser.open('http://127.0.0.1:5000', new=2)
    except Exception:
        pass


if __name__ == '__main__':
    import threading
    threading.Thread(target=auto_open_browser, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False)
