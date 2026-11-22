# -*- coding: utf-8 -*-
"""
football.services.squad_service - Nghiệp vụ quản lý đội hình, chuyển đổi DB ↔ Sim,
tự động chọn đội hình 11 người, tạo SVG avatar và làm giàu thẻ cầu thủ FC Mobile.
"""
import hashlib
import json
import random

from football.classes import PlayerOld, TeamOld
from football.constants import FIRST_NAMES, FORMATION_POSITIONS, LAST_NAMES, LEAGUE_OPPONENTS, POSITIONS
from football.models import Player, db


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
    starting_ids = {p.id for p in club.players if p.is_starting}
    if starting_ids:
        team.starting_xi = [idx for idx, p in enumerate(club.players) if p.id in starting_ids]
    return team


def create_random_players(count=16):
    players = []
    for _ in range(count):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
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
    required_positions = FORMATION_POSITIONS.get(formation, FORMATION_POSITIONS['4-3-3'])

    def calculate_fit(player, position):
        try:
            pref = json.loads(player.preferred_positions) if player.preferred_positions else []
        except Exception:
            pref = []
        bonus = 20 if (position in pref or player.position == position) else 0
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
    for pos in set(required_positions):
        pos_scores = [(p.id, calculate_fit(p, pos)) for p in players]
        pos_scores.sort(key=lambda x: x[1], reverse=True)
        scores[pos] = pos_scores

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


def generate_balanced_squad(club_id, formation='4-3-3'):
    """Tạo đội hình 19 cầu thủ cân bằng đầy đủ vị trí cho CLB mới."""
    nation_pools = [
        ("Việt Nam", ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Đặng", "Bùi", "Đỗ", "Hồ"],
         ["Minh", "Quang", "Tuấn", "Hoàng", "Duy", "Đức", "Văn", "Công", "Hùng", "Hải", "Bảo", "Long", "Tiến", "Tài", "Thành"]),
        ("Anh", ["Smith", "Johnson", "Walker", "Rice", "Foden", "Palmer", "Shaw", "Kane", "Stones", "White", "Sterling"],
         ["Harry", "Declan", "Phil", "Cole", "Luke", "John", "Ben", "Jack", "Marcus", "Mason", "Jude"]),
        ("Tây Ban Nha", ["Garcia", "Rodriguez", "Torres", "Lopez", "Martinez", "Alonso", "Ramos", "Silva", "Pedri", "Gavi"],
         ["Lucas", "David", "Carlos", "Pablo", "Alvaro", "Sergio", "Ferran", "Diego", "Alejandro"]),
        ("Pháp", ["Mbappe", "Griezmann", "Tchouameni", "Camavinga", "Saliba", "Hernandez", "Kounde", "Dembele"],
         ["Kylian", "Antoine", "Aurelien", "Eduardo", "William", "Theo", "Jules", "Ousmane", "Kingsley"]),
        ("Brazil", ["Silva", "Santos", "Vinicius", "Rodrygo", "Neymar", "Casemiro", "Ederson", "Alisson", "Paqueta"],
         ["Gabriel", "Lucas", "Matheus", "Thiago", "Enzo", "Felipe", "Rodrigo", "Joao", "Bruno"]),
        ("Đức", ["Mueller", "Kimmich", "Musiala", "Wirtz", "Kroos", "Gundogan", "Sane", "Havertz", "Rudiger"],
         ["Thomas", "Joshua", "Florian", "Toni", "Ilkay", "Leroy", "Kai", "Antonio", "Leon"]),
        ("Bỉ", ["De Bruyne", "Courtois", "Lukaku", "Tielemans", "Castagne", "Onana", "Trossard"],
         ["Kevin", "Romelu", "Youri", "Timothy", "Amadou", "Leandro", "Arthur"]),
        ("Argentina", ["Messi", "Alvarez", "Martinez", "Mac Allister", "Fernandez", "Romero", "De Paul"],
         ["Julian", "Lautaro", "Alexis", "Enzo", "Cristian", "Rodrigo", "Nicolas"])
    ]

    target_positions = [
        'GK', 'LB', 'CB', 'CB', 'RB', 'CDM', 'CM', 'CAM', 'LW', 'RW', 'ST',
        'GK', 'CB', 'LWB', 'CM', 'RM', 'LM', 'ST', 'RW'
    ]

    used_names = set()
    players = []

    for i, pos in enumerate(target_positions):
        nation_info = random.choice(nation_pools)
        nation = nation_info[0]
        first_names = nation_info[2]
        last_names = nation_info[1]

        full_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        for _ in range(20):
            candidate = f"{random.choice(first_names)} {random.choice(last_names)}"
            if candidate not in used_names:
                full_name = candidate
                used_names.add(candidate)
                break

        if pos == 'GK':
            atk, deff, spd = random.randint(35, 55), random.randint(80, 93), random.randint(60, 78)
            h, w = random.randint(188, 198), random.randint(82, 95)
        elif pos in ['CB', 'LB', 'RB', 'LWB', 'RWB']:
            atk, deff, spd = random.randint(60, 80), random.randint(78, 92), random.randint(75, 92)
            h, w = random.randint(176, 193), random.randint(72, 86)
        elif pos in ['CDM', 'CM', 'CAM', 'LM', 'RM']:
            atk, deff, spd = random.randint(75, 90), random.randint(68, 88), random.randint(76, 92)
            h, w = random.randint(172, 186), random.randint(68, 80)
        else:
            atk, deff, spd = random.randint(82, 95), random.randint(45, 70), random.randint(84, 96)
            h, w = random.randint(174, 192), random.randint(68, 85)

        ovr = round((atk + deff + spd) / 3, 1)
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
            preferred_positions=json.dumps([pos]),
            club_id=club_id,
            training_level=random.randint(10, 25),
            rank_level=random.randint(1, 4),
            skill_boost=random.randint(3, 7),
            age=random.randint(19, 32),
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


def get_opponent_for_round(league, round_num):
    """Sinh đội hình đối thủ (11 chính + 5 dự bị) theo vòng đấu và hạng giải."""
    opp_list = LEAGUE_OPPONENTS.get(league, LEAGUE_OPPONENTS["Hang 2"])
    idx = (round_num - 1) % len(opp_list)
    opp = opp_list[idx]

    positions = list(FORMATION_POSITIONS.get(opp["formation"], FORMATION_POSITIONS["4-3-3"]))
    sub_positions = ["GK", "CB", "CM", "LW", "ST"]

    first_names = ["Minh", "Tuấn", "Hoàng", "Nam", "Quang", "Duy", "Hải", "Hùng", "Bảo", "Đức", "Văn", "Công", "Phượng", "Thắng", "Long"]
    last_names = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương"]

    base_ovr = 75 if league == "Hang 1" else (85 if league == "Champions League" else 65)
    used_names = set()

    def make_player(pos, is_sub=False):
        name = f"{random.choice(last_names)} {random.choice(first_names)}"
        for _ in range(15):
            cand = f"{random.choice(last_names)} {random.choice(first_names)}"
            if cand not in used_names:
                name = cand
                used_names.add(cand)
                break
        ovr = random.randint(base_ovr - 5, base_ovr + (4 if is_sub else 6))
        if pos == 'GK':
            att, deff, spd = max(40, ovr - 18), min(98, ovr + 5), max(50, ovr - 8)
        elif pos in ['CB', 'LB', 'RB', 'LWB', 'RWB', 'CDM']:
            att, deff, spd = max(45, ovr - 6), min(98, ovr + 4), ovr
        else:
            att, deff, spd = min(98, ovr + 4), max(45, ovr - 8), min(98, ovr + 2)
        return {
            "name": name, "position": pos, "overall": ovr, "stamina": 100.0,
            "attack": att, "defense": deff, "speed": spd, "goals": 0,
            "yellow_cards": 0, "red_cards": 0
        }

    starting = [make_player(pos, is_sub=False) for pos in positions]
    subs = [make_player(pos, is_sub=True) for pos in sub_positions]
    return {
        "name": opp["name"],
        "formation": opp["formation"],
        "tactic": opp["tactic"],
        "players": starting,
        "subs": subs
    }


def generate_player_svg_avatar(name, position="CM", seed_num=0):
    """Tạo vector SVG chân dung cầu thủ bóng đá độc nhất theo tên & ID."""
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
        ("#18181b", "#09090b"), ("#271810", "#180e0a"), ("#422314", "#261208"),
        ("#78350f", "#451a03"), ("#d97706", "#92400e"), ("#f59e0b", "#b45309"),
        ("#94a3b8", "#475569"), ("#b91c1c", "#7f1d1d")
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
  <g id="body">
    <path d="M22 185 C24 150 42 135 58 130 L68 128 L80 142 L92 128 L102 130 C118 135 136 150 138 185 Z" fill="url(#{avatar_id}_kit)"/>
    <path d="M54 135 L80 162 L106 135 L100 132 L80 152 L60 132 Z" fill="url(#{avatar_id}_trim)" opacity="0.85"/>
    <path d="M42 165 L80 185 L118 165 L112 160 L80 178 L48 160 Z" fill="url(#{avatar_id}_trim)" opacity="0.5"/>
    <path d="M66 128 L80 144 L94 128 L88 124 L80 133 L72 124 Z" fill="{kit[3]}"/>
    <circle cx="104" cy="155" r="7" fill="{kit[3]}" opacity="0.9"/>
    <path d="M101 155 L104 151 L107 155 L104 158 Z" fill="{kit[0]}"/>
  </g>
  <g id="neck">
    <path d="M68 106 L68 130 L92 130 L92 106 Z" fill="url(#{avatar_id}_skin)"/>
    <path d="M68 106 C74 120 86 120 92 106 L92 118 C86 126 74 126 68 118 Z" fill="{skin[2]}" opacity="0.4"/>
  </g>
  <g id="head">
    <ellipse cx="50" cy="88" rx="5" ry="9" fill="url(#{avatar_id}_skin)"/>
    <ellipse cx="110" cy="88" rx="5" ry="9" fill="url(#{avatar_id}_skin)"/>
    <path d="M52 75 C50 100 58 118 80 118 C102 118 110 100 108 75 C108 50 102 42 80 42 C58 42 52 50 52 75 Z" fill="url(#{avatar_id}_skin)"/>
    <path d="M59 70 Q67 66 74 69" stroke="{hair[1]}" stroke-width="2.6" stroke-linecap="round" fill="none"/>
    <path d="M86 69 Q93 66 101 70" stroke="{hair[1]}" stroke-width="2.6" stroke-linecap="round" fill="none"/>
    <g fill="#ffffff"><ellipse cx="67" cy="76" rx="5" ry="3.2"/><ellipse cx="93" cy="76" rx="5" ry="3.2"/></g>
    <circle cx="67.5" cy="76" r="2.2" fill="#1e1e24"/><circle cx="93.5" cy="76" r="2.2" fill="#1e1e24"/>
    <circle cx="68.5" cy="75" r="0.8" fill="#ffffff"/><circle cx="94.5" cy="75" r="0.8" fill="#ffffff"/>
    <path d="M80 73 L80 88 L84 89 L76 89" stroke="{skin[2]}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
    <path d="M72 99 Q80 103 88 99" stroke="{skin[2]}" stroke-width="2.2" stroke-linecap="round" fill="none"/>'''

    if has_beard:
        svg += f'<path d="M56 86 C58 112 66 118 80 118 C94 118 102 112 104 86 C100 102 92 110 80 110 C68 110 60 102 56 86 Z" fill="{hair[1]}" opacity="0.65"/>'
    if has_mustache:
        svg += f'<path d="M72 95 Q80 93 88 95 Q80 97 72 95 Z" fill="{hair[1]}" opacity="0.75"/>'

    svg += '</g><g id="hair">'
    if style_idx == 0:
        svg += f'<path d="M50 72 C48 50 56 36 80 34 C104 36 112 50 110 72 C108 55 102 46 80 46 C58 46 52 55 50 72 Z" fill="url(#{avatar_id}_hair)"/><path d="M54 48 L60 30 L66 42 L74 26 L80 40 L88 28 L94 42 L102 32 L106 50 C96 42 64 42 54 48 Z" fill="url(#{avatar_id}_hair)"/>'
    elif style_idx == 1:
        svg += f'<path d="M50 70 C48 58 52 50 56 46 C60 30 72 24 82 24 C94 24 104 32 106 46 C110 52 112 60 110 70 C106 54 100 48 80 48 C60 48 54 54 50 70 Z" fill="url(#{avatar_id}_hair)"/>'
    elif style_idx == 2:
        svg += f'<path d="M46 72 C44 48 48 30 80 28 C112 30 116 48 114 72 C110 52 104 44 80 44 C56 44 50 52 46 72 Z" fill="url(#{avatar_id}_hair)"/><circle cx="60" cy="38" r="10" fill="url(#{avatar_id}_hair)"/><circle cx="76" cy="32" r="11" fill="url(#{avatar_id}_hair)"/><circle cx="92" cy="34" r="10" fill="url(#{avatar_id}_hair)"/>'
    elif style_idx == 3:
        svg += f'<path d="M50 70 C48 52 54 40 76 34 C98 28 112 38 112 58 C112 66 110 72 108 72 C104 56 96 46 78 46 C60 46 54 56 50 70 Z" fill="url(#{avatar_id}_hair)"/>'
    elif style_idx == 4:
        svg += f'<path d="M51 72 C49 52 55 40 80 38 C105 40 111 52 109 72 C107 58 102 48 80 48 C58 48 53 58 51 72 Z" fill="url(#{avatar_id}_hair)"/>'
    elif style_idx == 5:
        svg += f'<path d="M48 82 C44 52 52 32 80 30 C108 32 116 52 112 82 C108 60 102 48 80 48 C58 48 52 60 48 82 Z" fill="url(#{avatar_id}_hair)"/>'
        if has_headband:
            svg += f'<path d="M48 64 C64 56 96 56 112 64 L110 70 C96 62 64 62 50 70 Z" fill="{kit[3]}"/>'
    else:
        svg += f'<path d="M48 70 C46 48 54 36 80 34 C106 36 114 48 112 70 C108 52 100 44 80 44 C60 44 52 52 48 70 Z" fill="url(#{avatar_id}_hair)"/>'

    svg += f'</g><path d="M52 74 C50 98 58 116 80 116 C102 116 110 98 108 74" stroke="{kit[2]}" stroke-width="1.2" stroke-opacity="0.5" fill="none"/></svg>'
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
        playstyle_name, playstyle_icon = "Rê bóng bứt tốc thần sầu", "⚡"
        playstyle_desc = "Tăng 15% tốc độ bứt phá qua người và khả năng khống chế bóng dính chân khi tăng tốc."
        sec_pos = "LW, RW" if pos in ['LW', 'RW'] else "LM, RM"
    elif pos in ['ST', 'CF']:
        playstyle_name, playstyle_icon = "Cây săn bàn sát thủ", "🎯"
        playstyle_desc = "Khả năng dứt điểm 1 chạm uy lực, chọn vị trí đánh đầu và sút xa hiểm hóc trong vòng cấm."
        sec_pos = "ST, CF"
    elif pos in ['CAM', 'CM']:
        playstyle_name, playstyle_icon = "Nhạc trưởng kiến tạo ma thuật", "🪄"
        playstyle_desc = "Nhãn quan chiến thuật phi phàm, chọc khe bổng xé toang hàng phòng ngự đối phương."
        sec_pos = "CAM, CM"
    elif pos == 'CDM':
        playstyle_name, playstyle_icon = "Máy quét bọc lót toàn diện", "🛡️"
        playstyle_desc = "Cắt bóng thông minh, tranh chấp áp sát quyết liệt làm nản lòng mọi tiền vệ tấn công."
        sec_pos = "CDM, CM"
    elif pos in ['CB', 'LB', 'RB', 'LWB', 'RWB']:
        playstyle_name, playstyle_icon = "Bức tường thép không thể xuyên phá", "🧱"
        playstyle_desc = "Xoạc bóng chính xác, không chiến mạnh mẽ và kèm người cực kỳ chắc chắn."
        sec_pos = "CB, LB, RB"
    elif pos == 'GK':
        playstyle_name, playstyle_icon = "Bạch tuộc phản xạ xuất thần", "🧤"
        playstyle_desc = "Phản xạ xuất thần trong cự ly gần, đổ người bay người cản phá phạt đền siêu đẳng."
        sec_pos = "GK"
    else:
        playstyle_name, playstyle_icon = "Chiến binh công thủ toàn diện", "⭐"
        playstyle_desc = "Lên công về thủ nhịp nhàng, đóng góp tích cực vào lối chơi tập thể."
        sec_pos = pos

    attrs = {
        "pace": {"acceleration": int(min(250, pac + 3)), "sprint_speed": int(min(250, pac - 1))},
        "shooting": {
            "finishing": int(min(250, sho + (8 if pos in ['ST', 'LW', 'RW'] else 0))),
            "shot_power": int(min(250, sho + 4)), "long_shots": int(min(250, sho - 2)),
            "volleys": int(min(250, sho - 4)), "penalties": int(min(250, sho + 3)),
            "positioning": int(min(250, int(round((sho + dri) / 2))))
        },
        "passing": {
            "vision": int(min(250, pas + (6 if pos in ['CAM', 'CM'] else 0))),
            "short_passing": int(min(250, pas + 4)), "long_passing": int(min(250, pas - 2)),
            "crossing": int(min(250, pas + (8 if pos in ['LW', 'RW', 'LB', 'RB'] else 0))),
            "free_kick": int(min(250, pas + 2)), "curve": int(min(250, int(round((pas + sho) / 2))))
        },
        "dribbling": {
            "agility": int(min(250, dri + 5)), "balance": int(min(250, dri + 1)),
            "reactions": int(min(250, int(round((dri + pac) / 2)))), "ball_control": int(min(250, dri + 4)),
            "dribbling": int(min(250, dri + 6)), "composure": int(min(250, int(round((p.overall or 60) + 5))))
        },
        "defending": {
            "interceptions": int(min(250, deff + (6 if pos in ['CB', 'CDM'] else 0))),
            "heading_accuracy": int(min(250, int(round((deff + phy) / 2)))),
            "marking": int(min(250, deff + 4)), "standing_tackle": int(min(250, deff + 5)),
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
            "gk_diving": int(min(250, deff + 12)), "gk_handling": int(min(250, deff + 8)),
            "gk_kicking": int(min(250, pas + 5)), "gk_reflexes": int(min(250, pac + 15)),
            "gk_positioning": int(min(250, deff + 10))
        }

    nation = getattr(p, 'nationality', 'Việt Nam') or 'Việt Nam'
    flag_map = [("Việt", "VIE"), ("Anh", "ENG"), ("Tây Ban Nha", "ESP"), ("Pháp", "FRA"),
                ("Brazil", "BRA"), ("Đức", "GER"), ("Bỉ", "BEL")]
    flag_code = next((code for key, code in flag_map if key in nation), "ARG")

    playstyles_list = [
        {"name": "Sút xoáy Finesse Shot", "icon": "🌀", "desc": "Cú sút má trong hiểm hóc với độ xoáy cực cao."},
        {"name": "Bứt tốc Speed Dribbler", "icon": "⚡", "desc": "Khả năng đẩy bóng dài và tăng tốc đoạn ngắn."},
        {"name": "Chuyền điểm rơi Long Passer", "icon": "📐", "desc": "Những đường chuyền dài đảo cánh mở không gian."},
        {"name": "Đánh đầu uy lực Power Header", "icon": "💥", "desc": "Bật cao tranh chấp không chiến và đánh đầu uy lực."}
    ]

    tier = 'tier-ucl' if fc_ovr >= 85 else ('tier-gold' if fc_ovr >= 74 else 'tier-silver')
    return {
        "id": p.id, "name": p.name, "first_name": first_name, "last_name": last_name,
        "position": p.position, "secondary_pos": sec_pos, "overall": base_ovr, "fc_ovr": fc_ovr,
        "speed": pac, "attack": sho, "defense": deff, "stamina": p.stamina,
        "pac": pac, "sho": sho, "pas": pas, "dri": dri, "def": deff, "phy": phy,
        "tier": tier, "avatar_svg": generate_player_svg_avatar(p.name, p.position, p.id),
        "training_level": t_lvl, "max_training_level": 30, "rank_level": r_lvl, "max_rank_level": 5,
        "skill_boost": s_boost, "age": getattr(p, 'age', 24) or 24,
        "height": getattr(p, 'height', 178) or 178, "weight": getattr(p, 'weight', 72) or 72,
        "weak_foot": getattr(p, 'weak_foot', 4) or 4, "skill_moves": getattr(p, 'skill_moves', 4) or 4,
        "nationality": nation, "flag_code": flag_code,
        "league": club.league if club else "V-League 1",
        "club_name": club.name if club else "FC Club",
        "is_starting": p.is_starting, "is_substitute": p.is_substitute,
        "goals": p.goals, "assists": p.assists, "matches_played": p.matches_played,
        "contract_wage": getattr(p, 'contract_wage', 50000) or 50000,
        "market_value": getattr(p, 'market_value', 500000) or 500000,
        "playstyle_name": playstyle_name, "playstyle_icon": playstyle_icon,
        "playstyle_desc": playstyle_desc, "attrs": attrs, "playstyles_list": playstyles_list
    }
