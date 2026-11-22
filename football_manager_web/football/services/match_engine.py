# -*- coding: utf-8 -*-
"""
football.services.match_engine - Engine mô phỏng trận đấu trực tiếp từng phút thực tế.
Hỗ trợ:
- Tỉ lệ sút, xG, bàn thắng, thẻ phạt, phạt góc chuẩn bóng đá thực tế (~2.5-3.0 bàn/trận)
- Bù giờ thực tế Hiệp 1 (45+1'..45+X') và Hiệp 2 (90+1'..90+X')
- Gắn mốc giây (second: 0..59) và pha lên bóng (build-up) để phát trực tiếp 10s -> 1s/phút
- Kiểm soát bóng thật, đường chuyền, cứu thua, Momentum & Ball Zone theo từng phút
- AI đội khách tự đổi chiến thuật và thay người theo diễn biến
- Mô phỏng live các trận đấu cùng vòng đấu
"""
import random
from football.constants import LEAGUE_OPPONENTS

POSITION_WEIGHTS = {
    "GK":  {"att": 0.02, "def": 0.88, "spd": 0.10, "stamina_rate": 0.25},
    "CB":  {"att": 0.08, "def": 0.72, "spd": 0.20, "stamina_rate": 0.78},
    "LB":  {"att": 0.20, "def": 0.45, "spd": 0.35, "stamina_rate": 0.95},
    "RB":  {"att": 0.20, "def": 0.45, "spd": 0.35, "stamina_rate": 0.95},
    "LWB": {"att": 0.30, "def": 0.35, "spd": 0.35, "stamina_rate": 1.15},
    "RWB": {"att": 0.30, "def": 0.35, "spd": 0.35, "stamina_rate": 1.15},
    "CDM": {"att": 0.18, "def": 0.58, "spd": 0.24, "stamina_rate": 1.00},
    "CM":  {"att": 0.35, "def": 0.35, "spd": 0.30, "stamina_rate": 1.05},
    "CAM": {"att": 0.60, "def": 0.15, "spd": 0.25, "stamina_rate": 0.95},
    "LM":  {"att": 0.40, "def": 0.25, "spd": 0.35, "stamina_rate": 1.00},
    "RM":  {"att": 0.40, "def": 0.25, "spd": 0.35, "stamina_rate": 1.00},
    "LW":  {"att": 0.52, "def": 0.10, "spd": 0.38, "stamina_rate": 0.98},
    "RW":  {"att": 0.52, "def": 0.10, "spd": 0.38, "stamina_rate": 0.98},
    "ST":  {"att": 0.72, "def": 0.05, "spd": 0.23, "stamina_rate": 0.92},
    "CF":  {"att": 0.65, "def": 0.10, "spd": 0.25, "stamina_rate": 0.94},
}
DEFAULT_WEIGHT = {"att": 0.33, "def": 0.33, "spd": 0.34, "stamina_rate": 0.95}


def format_minute_label(minute, injury_min=0):
    if injury_min and injury_min > 0:
        return f"{minute}+{injury_min}'"
    return f"{minute}'"


def _p_get(p, key, default=0):
    return p.get(key, default) if isinstance(p, dict) else getattr(p, key, default)


def _p_set(p, key, val):
    if isinstance(p, dict):
        p[key] = val
    else:
        setattr(p, key, val)


def calculate_players_strength(players, tactic="Can bang"):
    """Tính sức mạnh tấn công, phòng ngự, tốc độ, tuyến giữa của một danh sách cầu thủ đá chính."""
    if not players:
        return {"attack": 50.0, "defense": 50.0, "speed": 50.0, "overall": 50.0, "active_count": 0, "midfield": 50.0}

    active = [p for p in players if _p_get(p, 'red_cards', 0) == 0]
    if not active:
        active = players

    manpower_ratio = min(1.0, len(active) / 11.0)
    eff_att = eff_def = eff_spd = mid_power = 0.0
    has_cdm = False

    for p in active:
        pos = _p_get(p, 'position', 'CM')
        w = POSITION_WEIGHTS.get(pos, DEFAULT_WEIGHT)
        stam = max(0.35, float(_p_get(p, 'stamina', 100.0)) / 100.0)
        att = float(_p_get(p, 'attack', _p_get(p, 'overall', 65)))
        deff = float(_p_get(p, 'defense', _p_get(p, 'overall', 65)))
        spd = float(_p_get(p, 'speed', _p_get(p, 'overall', 65)))

        eff_att += (att * 0.75 + spd * 0.25) * w["att"] * 3.0 * stam
        eff_def += (deff * 0.75 + spd * 0.25) * w["def"] * 3.0 * stam
        eff_spd += spd * w["spd"] * 3.0 * stam

        if pos in ('CDM', 'CM', 'CAM', 'LM', 'RM'):
            mid_power += (att * 0.4 + deff * 0.4 + spd * 0.2) * stam
        if pos == 'CDM':
            has_cdm = True

    cnt = len(active)
    total_att = (eff_att / cnt) * manpower_ratio
    total_def = (eff_def / cnt) * manpower_ratio
    total_spd = (eff_spd / cnt) * manpower_ratio

    if has_cdm:
        total_def *= 1.05

    if tactic == "Tan cong":
        total_att *= 1.14
        total_def *= 0.90
    elif tactic in ("Phong thu", "Xe bus"):
        total_att *= 0.84
        total_def *= 1.22
    elif tactic == "Tiki-Taka":
        mid_power *= 1.24
        total_att *= 1.06
        total_def *= 1.05
    elif tactic == "Phan cong":
        total_spd *= 1.18
        total_att *= 1.10
        total_def *= 1.08

    overall = total_att * 0.4 + total_def * 0.4 + total_spd * 0.2
    return {
        "attack": total_att,
        "defense": total_def,
        "speed": total_spd,
        "overall": overall,
        "active_count": len(active),
        "midfield": max(20.0, mid_power)
    }


def calculate_team_strength(team, tactic="Can bang"):
    """Tương thích ngược với đối tượng TeamOld."""
    return calculate_players_strength(team.get_starting_xi(), tactic)


def _get_shot_profile(shooter):
    """Hồ sơ cú sút với xG thực tế theo vùng dứt điểm."""
    pos = _p_get(shooter, 'position', 'ST')
    r = random.random()

    if r < 0.14:
        # 14%: Cơ hội rõ rệt / cận thành / đối mặt (Big Chance)
        dist = round(random.uniform(4.5, 11.0), 1)
        zone = "big_chance"
        base_xg = round(random.uniform(0.30, 0.43), 2)
        descs = [
            f"thoát xuống đối mặt thủ môn dứt điểm chìm hiểm hóc ở cự ly {dist}m",
            f"băng cắt đệm bóng cận thành một chạm cực kỳ nguy hiểm ở cự ly {dist}m",
            f"chớp thời cơ xoay người dứt điểm cận thành ở cự ly {dist}m trong vòng 5m50",
        ]
    elif r < 0.68:
        # 54%: Trong vòng cấm 16m50
        dist = round(random.uniform(10.5, 16.0), 1)
        zone = "in_box"
        base_xg = round(random.uniform(0.09, 0.17), 2)
        if pos in ('LW', 'RW'):
            descs = [
                f"bó từ cánh vào vòng cấm cứa lòng chéo góc ở cự ly {dist}m",
                f"xâm nhập nách trung lộ tung cú sút căng ở cự ly {dist}m trong vòng 16m50"
            ]
        elif pos in ('ST', 'CF'):
            descs = [
                f"xoay người vô-lê một chạm trong vòng cấm ở cự ly {dist}m",
                f"bật cao đánh đầu lái bóng về góc xa ở cự ly {dist}m"
            ]
        else:
            descs = [
                f"băng lên từ tuyến hai dứt điểm quyết đoán ở cự ly {dist}m trong vòng cấm",
                f"phối hợp bật nhả rồi tung cú sút sệt ở cự ly {dist}m"
            ]
    elif r < 0.92:
        # 24%: Rìa vòng cấm 16.5m - 21m
        dist = round(random.uniform(16.5, 21.0), 1)
        zone = "edge_box"
        base_xg = round(random.uniform(0.04, 0.08), 2)
        descs = [
            f"cứa lòng kỹ thuật từ rìa vòng cấm cự ly {dist}m",
            f"đón bóng bật ra tuyến hai vung chân sút căng ở cự ly {dist}m",
            f"nhấp một nhịp loại bỏ hậu vệ rồi sút mu chính diện ở cự ly {dist}m"
        ]
    else:
        # 8%: Sút xa > 21m
        dist = round(random.uniform(22.0, 32.0), 1)
        zone = "long_range"
        base_xg = round(random.uniform(0.02, 0.04), 2)
        descs = [
            f"táo bạo tung cú sút xa uy lực từ khoảng cách {dist}m",
            f"vung chân nã đại bác tầm xa ở cự ly {dist}m"
        ]

    return dist, random.choice(descs), zone, base_xg


def _get_assist_desc(passer):
    pos = _p_get(passer, 'position', 'CM')
    name = _p_get(passer, 'name', 'Đồng đội')
    if pos in ('CAM', 'CM'):
        return f"chọc khe tinh tế của [{pos}] {name}"
    if pos in ('LW', 'RW', 'LM', 'RM'):
        return f"pha căng ngang dọn cỗ của [{pos}] {name}"
    if pos in ('LB', 'RB', 'LWB', 'RWB'):
        return f"quả tạt chuẩn xác của [{pos}] {name}"
    return f"đường nhả bóng vừa tầm của [{pos}] {name}"


def init_other_matches(league, home_team_name, away_team_name):
    """Khởi tạo 4 cặp đấu diễn ra cùng giờ trong giải để cập nhật live từng phút."""
    opps = [o['name'] for o in LEAGUE_OPPONENTS.get(league, LEAGUE_OPPONENTS["Hang 2"])
            if o['name'] not in (home_team_name, away_team_name)]
    random.shuffle(opps)
    matches = []
    for i in range(0, min(8, len(opps) - 1), 2):
        matches.append({
            "home": opps[i],
            "away": opps[i + 1],
            "home_goals": 0,
            "away_goals": 0,
            "last_scorer": ""
        })
    return matches


def _tick_other_matches(other_matches, minute_label):
    for m in other_matches:
        # ~2.7% mỗi phút có bàn thắng ở mỗi trận đấu khác (~2.5 bàn/trận)
        if random.random() < 0.027:
            if random.random() < 0.54:
                m["home_goals"] += 1
                m["last_scorer"] = f"{m['home']} ({minute_label})"
            else:
                m["away_goals"] += 1
                m["last_scorer"] = f"{m['away']} ({minute_label})"


def _pick_weighted(players, weight_fn):
    weights = [max(1, weight_fn(_p_get(p, 'position', 'CM'))) for p in players]
    return random.choices(players, weights=weights, k=1)[0]


def _make_event(minute, injury_min, second, desc, event_type="general", is_key=False, data=None):
    ev = {
        "minute": minute,
        "injury_minute": injury_min,
        "minute_label": format_minute_label(minute, injury_min),
        "second": second,
        "clock": f"{minute:02d}:{second:02d}" if not injury_min else f"{minute}+{injury_min}:{second:02d}",
        "description": desc,
        "type": event_type,
        "event_type": event_type,
        "is_key": is_key,
    }
    if data:
        ev["data"] = data
    return ev


def simulate_single_minute(state):
    """
    Mô phỏng CHÍNH XÁC 1 phút thi đấu (kể cả phút bù giờ 45+X' và 90+X') trên dict `state`.
    Trả về list `new_events` phát sinh trong phút này (mỗi event có `second` để UI phát đúng nhịp 10s -> 1s).
    """
    phase = state.get('phase', 'first_half')
    if phase in ('halftime', 'finished') or state.get('finished'):
        return []

    cur_min = state.get('current_minute', 0)
    cur_inj = state.get('injury_minute', 0)
    inj_h1 = state.get('injury_time_h1', 0)
    inj_h2 = state.get('injury_time_h2', 0)

    # Xác định phút kế tiếp (bao gồm logic bù giờ thực tế)
    if phase == 'first_half':
        if cur_min < 45:
            next_min = cur_min + 1
            next_inj = 0
        else:
            # Đang trong bù giờ hiệp 1
            next_min = 45
            next_inj = cur_inj + 1
    else:  # second_half
        if cur_min < 90:
            next_min = max(46, cur_min + 1)
            next_inj = 0
        else:
            # Đang trong bù giờ hiệp 2
            next_min = 90
            next_inj = cur_inj + 1

    state['current_minute'] = next_min
    state['injury_minute'] = next_inj
    min_label = format_minute_label(next_min, next_inj)

    home_players = state.get('home_players', [])
    away_players = state.get('away_players', [])
    home_active = [p for p in home_players if p.get('red_cards', 0) == 0]
    away_active = [p for p in away_players if p.get('red_cards', 0) == 0]

    home_tactic = state.get('tactic', 'Can bang')
    away_tactic = state.get('away_tactic', 'Can bang')
    home_name = state.get('home_team', 'Đội nhà')
    away_name = state.get('away_team', 'Đối thủ')

    new_events = []

    # 1. Cập nhật các trận đấu cùng vòng
    _tick_other_matches(state.get('other_matches', []), min_label)

    # 2. AI đội khách: đổi chiến thuật & thay người hợp lý ở Hiệp 2
    if phase == 'second_half' and next_inj == 0:
        goal_diff_away = state['away_goals'] - state['home_goals']
        if next_min == 65 and goal_diff_away < 0 and away_tactic != 'Tan cong':
            state['away_tactic'] = 'Tan cong'
            away_tactic = 'Tan cong'
            new_events.append(_make_event(
                next_min, next_inj, 8,
                f"📋 {min_label}: HLV {away_name} dâng cao đội hình chuyển sang chiến thuật TẤN CÔNG tìm bàn gỡ!",
                event_type="tactic", is_key=False, data={"is_home": False, "tactic": "Tan cong"}
            ))
        elif next_min == 78 and goal_diff_away > 0 and away_tactic != 'Phong thu':
            state['away_tactic'] = 'Phong thu'
            away_tactic = 'Phong thu'
            new_events.append(_make_event(
                next_min, next_inj, 10,
                f"📋 {min_label}: {away_name} chủ động lùi sâu chuyển sang PHÒNG THỦ bảo toàn tỉ số!",
                event_type="tactic", is_key=False, data={"is_home": False, "tactic": "Phong thu"}
            ))

        # AI thay người (tối đa 3 người từ phút 60 đến 84)
        away_subs_used = state.get('away_subs_used', 0)
        away_bench = state.get('away_subs', [])
        if away_subs_used < 3 and away_bench and next_min in (62, 73, 82):
            tired = [p for p in away_active if p.get('position') != 'GK' and p.get('stamina', 100) < 76]
            if tired:
                out_p = min(tired, key=lambda x: x.get('stamina', 100))
                # Tìm cầu thủ dự bị không phải GK
                in_candidates = [s for s in away_bench if s.get('position') != 'GK'] or away_bench
                in_p = in_candidates[0]
                away_bench.remove(in_p)
                idx_out = away_players.index(out_p)
                in_p['position'] = out_p['position']  # giữ vị trí trên sơ đồ
                away_players[idx_out] = in_p
                state['away_subs_used'] = away_subs_used + 1
                away_active = [p for p in away_players if p.get('red_cards', 0) == 0]
                new_events.append(_make_event(
                    next_min, next_inj, 15,
                    f"🔄 {min_label}: {away_name} thay người — {out_p['name']} rời sân, {in_p['name']} vào thay.",
                    event_type="substitution", is_key=True,
                    data={"is_home": False, "player_out": out_p['name'], "player_in": in_p['name']}
                ))

    # 3. Tiêu hao thể lực theo chiến thuật & vị trí
    tactic_drain = {"Tan cong": 0.34, "Phan cong": 0.31, "Tiki-Taka": 0.29, "Can bang": 0.26, "Phong thu": 0.21, "Xe bus": 0.20}
    h_base_loss = tactic_drain.get(home_tactic, 0.26)
    a_base_loss = tactic_drain.get(away_tactic, 0.26)
    for p in home_active:
        w = POSITION_WEIGHTS.get(p.get('position', 'CM'), DEFAULT_WEIGHT)
        p['stamina'] = round(max(12.0, float(p.get('stamina', 100.0)) - h_base_loss * w['stamina_rate']), 1)
    for p in away_active:
        w = POSITION_WEIGHTS.get(p.get('position', 'CM'), DEFAULT_WEIGHT)
        p['stamina'] = round(max(12.0, float(p.get('stamina', 100.0)) - a_base_loss * w['stamina_rate']), 1)

    # 4. Đánh giá sức mạnh, Kiểm soát bóng thật, Đường chuyền & Ball Zone
    home_str = calculate_players_strength(home_players, home_tactic)
    away_str = calculate_players_strength(away_players, away_tactic)

    total_power = max(1.0, home_str['overall'] + away_str['overall'])
    home_prob = home_str['overall'] / total_power
    mid_diff = (home_str['midfield'] - away_str['midfield']) / max(1.0, home_str['midfield'] + away_str['midfield'])
    home_prob = min(0.78, max(0.22, home_prob + mid_diff * 0.14))

    # Kiểm soát bóng phút hiện tại (dao động tự nhiên quanh home_prob)
    minute_poss_home = min(0.85, max(0.15, home_prob + random.uniform(-0.14, 0.14)))
    state['poss_sum_home'] = state.get('poss_sum_home', 0.0) + minute_poss_home
    state['poss_ticks'] = state.get('poss_ticks', 0) + 1
    avg_poss_home = int(round((state['poss_sum_home'] / state['poss_ticks']) * 100))
    state['possession_home'] = max(22, min(78, avg_poss_home))
    state['possession_away'] = 100 - state['possession_home']

    # Đường chuyền thực tế (~8-12 đường chuyền mỗi phút tổng 2 đội)
    total_passes_min = random.randint(8, 13)
    h_passes = int(round(total_passes_min * minute_poss_home))
    a_passes = max(1, total_passes_min - h_passes)
    state['passes_home'] = state.get('passes_home', 0) + h_passes
    state['passes_away'] = state.get('passes_away', 0) + a_passes

    # Ball zone (0 = khung thành đội nhà, 50 = giữa sân, 100 = khung thành đối thủ)
    base_zone = 50 + (minute_poss_home - 0.5) * 65 + random.uniform(-12, 12)
    ball_zone = int(max(8, min(92, base_zone)))
    momentum_val = int(max(-100, min(100, (minute_poss_home - 0.5) * 180 + random.randint(-15, 15))))

    # 5. Bảng điện tử bù giờ ở đúng phút 45:00 và 90:00
    if next_min == 45 and next_inj == 0 and inj_h1 == 0:
        goals_h1 = state['home_goals'] + state['away_goals']
        cards_h1 = state['yellow_home'] + state['yellow_away'] + state['red_home'] + state['red_away']
        inj_h1 = min(4, max(1, 1 + goals_h1 // 2 + cards_h1 // 2 + random.choice([0, 1])))
        state['injury_time_h1'] = inj_h1
        new_events.append(_make_event(
            45, 0, 5,
            f"⏱️ BẢNG BÙ GIỜ: Trọng tài bàn giơ bảng điện tử — Hiệp 1 có +{inj_h1} phút bù giờ!",
            event_type="injury_time", is_key=True, data={"half": 1, "extra_minutes": inj_h1}
        ))
    elif next_min == 90 and next_inj == 0 and inj_h2 == 0:
        total_goals = state['home_goals'] + state['away_goals']
        total_subs = state.get('subs_used', 0) + state.get('away_subs_used', 0)
        inj_h2 = min(6, max(2, 2 + total_subs // 2 + total_goals // 3 + random.choice([0, 1])))
        state['injury_time_h2'] = inj_h2
        new_events.append(_make_event(
            90, 0, 5,
            f"⏱️ BẢNG BÙ GIỜ: Trọng tài bàn giơ bảng điện tử — Hiệp 2 có +{inj_h2} phút bù giờ!",
            event_type="injury_time", is_key=True, data={"half": 2, "extra_minutes": inj_h2}
        ))

    # 6. Mô phỏng biến cố chính trong phút
    roll = random.random()

    if home_active and away_active:
        # ---------- NHÁNH 1: TÌNH HUỐNG DỨT ĐIỂM (~19.5% mỗi phút -> ~19 cú sút mở/trận) ----------
        if roll < 0.195:
            is_home_att = (random.random() < home_prob)
            att_name = home_name if is_home_att else away_name
            att_players = home_active if is_home_att else away_active
            def_players = away_active if is_home_att else home_active
            ball_zone = random.randint(76, 94) if is_home_att else random.randint(6, 24)
            momentum_val = random.randint(45, 90) if is_home_att else random.randint(-90, -45)

            shooter = _pick_weighted(att_players, lambda pos: (
                42 if pos in ('ST', 'CF') else 22 if pos in ('LW', 'RW') else 16 if pos == 'CAM'
                else 10 if pos in ('CM', 'LM', 'RM') else 4 if pos == 'CDM' else 2
            ))
            passer_cands = [p for p in att_players if p['name'] != shooter['name'] and p.get('position') != 'GK']
            passer = None
            if passer_cands and random.random() < 0.72:
                passer = _pick_weighted(passer_cands, lambda pos: (
                    35 if pos in ('CAM', 'CM') else 26 if pos in ('LW', 'RW', 'LM', 'RM')
                    else 18 if pos in ('LB', 'RB', 'LWB', 'RWB') else 10
                ))

            dist, shot_desc, shot_zone, base_xg = _get_shot_profile(shooter)
            gk = next((p for p in def_players if p.get('position') == 'GK'), def_players[0])

            shooter_pwr = (shooter.get('attack', 70) * 0.75 + shooter.get('speed', 70) * 0.25) * (shooter.get('stamina', 100) / 100.0)
            gk_pwr = (gk.get('defense', 70) * 0.85 + gk.get('speed', 65) * 0.15) * (gk.get('stamina', 100) / 100.0)
            has_cdm = any(p.get('position') == 'CDM' for p in def_players)

            ratio = max(0.65, min(1.40, shooter_pwr / max(1.0, gk_pwr)))
            xg = round(min(0.65, max(0.02, base_xg * ratio * (0.94 if has_cdm else 1.0))), 2)

            if is_home_att:
                state['shots_home'] += 1
                state['xg_home'] = round(state.get('xg_home', 0.0) + xg, 2)
            else:
                state['shots_away'] += 1
                state['xg_away'] = round(state.get('xg_away', 0.0) + xg, 2)

            main_sec = random.randint(24, 52)
            # Thêm pha triển khai (build-up) trước cú sút ~14s để xem trực tiếp 10s-1s cực đã
            if passer and shot_zone in ('big_chance', 'in_box'):
                new_events.append(_make_event(
                    next_min, next_inj, max(6, main_sec - 14),
                    f"⚡ {min_label}: {att_name} tổ chức lên bóng tốc độ — {_get_assist_desc(passer)} mở ra cơ hội cho {shooter['name']}!",
                    event_type="buildup", is_key=False,
                    data={"is_home": is_home_att, "passer": passer['name'], "receiver": shooter['name']}
                ))

            shooter_tag = f"[{shooter.get('position', 'ST')}] {shooter['name']}"
            gk_tag = f"[GK] {gk['name']}"

            if random.random() < xg:
                # 7% kiểm tra VAR việt vị khi bóng vào lưới
                if random.random() < 0.07:
                    disallowed = (random.random() < 0.38)
                    new_events.append(_make_event(
                        next_min, next_inj, min(57, main_sec + 3),
                        f"🖥️ VAR {'TỪ CHỐI' if disallowed else 'XÁC NHẬN'} BÀN THẮNG! {min_label}: Trọng tài kiểm tra VAR lỗi việt vị của {shooter_tag} — {'Bàn thắng bị hủy!' if disallowed else 'Bàn thắng hoàn toàn hợp lệ!'}",
                        event_type="var_check", is_key=True,
                        data={"is_home": is_home_att, "check_type": "offside",
                              "decision": "disallowed" if disallowed else "confirmed", "player": shooter['name']}
                    ))
                    if disallowed:
                        state['offsides_home' if is_home_att else 'offsides_away'] = state.get('offsides_home' if is_home_att else 'offsides_away', 0) + 1
                        # Không cộng bàn thắng
                        state['ball_zone'] = ball_zone
                        state.setdefault('momentum', []).append({"m": min_label, "v": momentum_val})
                        state['events'].extend(new_events)
                        return new_events

                # BÀN THẮNG!
                if is_home_att:
                    state['home_goals'] += 1
                    state['target_home'] += 1
                    state.setdefault('scorers_home', []).append({"name": shooter['name'], "minute": min_label, "type": "goal"})
                else:
                    state['away_goals'] += 1
                    state['target_away'] += 1
                    state.setdefault('scorers_away', []).append({"name": shooter['name'], "minute": min_label, "type": "goal"})

                shooter['goals'] = shooter.get('goals', 0) + 1
                assist_str = f" (Kiến tạo: {_get_assist_desc(passer)})" if passer else ""
                new_events.append(_make_event(
                    next_min, next_inj, main_sec,
                    f"⚽ VÀOOO! {min_label}: {shooter_tag} ({att_name}) {shot_desc}{assist_str}! (xG: {xg}) — Tỉ số: {state['home_goals']}-{state['away_goals']}",
                    event_type="goal", is_key=True,
                    data={"is_home": is_home_att, "dist": dist, "shooter": shooter['name'],
                          "assist": passer['name'] if passer else None, "zone": shot_zone, "xg": xg,
                          "score": f"{state['home_goals']}-{state['away_goals']}"}
                ))
            else:
                # KHÔNG VÀO: Cứu thua / Xà ngang / Chệch khung thành
                is_woodwork = (random.random() < 0.09 and dist <= 26)
                is_on_target = (not is_woodwork) and (random.random() < 0.42)
                woodwork_type = random.choice(['crossbar', 'post']) if is_woodwork else None

                if is_on_target:
                    if is_home_att:
                        state['target_home'] += 1
                        state['saves_away'] = state.get('saves_away', 0) + 1
                    else:
                        state['target_away'] += 1
                        state['saves_home'] = state.get('saves_home', 0) + 1
                    res_desc = f"nhưng thủ môn {gk_tag} đã bay người cứu thua xuất sắc!"
                elif is_woodwork:
                    res_desc = "nhưng bóng dội trúng XÀ NGANG bật ra đầy tiếc nuối!" if woodwork_type == 'crossbar' else "nhưng bóng đập CỘT DỌC nảy ra ngoài!"
                else:
                    res_desc = random.choice([
                        "nhưng bóng đi chệch cột dọc trong gang tấc.",
                        "nhưng bóng đi vọt xà ngang đáng tiếc.",
                        "nhưng hậu vệ đối phương đã kịp thời lăn xả chặn bóng."
                    ])

                new_events.append(_make_event(
                    next_min, next_inj, main_sec,
                    f"🧤 Cơ hội! {min_label}: {shooter_tag} ({att_name}) {shot_desc}, {res_desc} (xG: {xg})",
                    event_type="shot_miss", is_key=(is_woodwork or shot_zone == 'big_chance' or is_on_target),
                    data={"is_home": is_home_att, "dist": dist, "shooter": shooter['name'],
                          "target": is_on_target, "woodwork": woodwork_type, "xg": xg, "zone": shot_zone}
                ))

        # ---------- NHÁNH 2: PHẠM LỖI, THẺ PHẠT & PENALTY (~16% mỗi phút) ----------
        elif roll < 0.355:
            is_home_foul = (random.random() < (1.0 - home_prob * 0.45 - 0.25))
            foul_name = home_name if is_home_foul else away_name
            victim_name = away_name if is_home_foul else home_name
            foul_players = home_active if is_home_foul else away_active
            victim_players = away_active if is_home_foul else home_active

            if is_home_foul:
                state['fouls_home'] += 1
            else:
                state['fouls_away'] += 1

            def_fouls = [p for p in foul_players if p.get('position') in ('CB', 'CDM', 'LB', 'RB', 'LWB', 'RWB', 'CM')]
            fowler = random.choice(def_fouls) if def_fouls else random.choice(foul_players)
            att_victims = [p for p in victim_players if p.get('position') in ('ST', 'LW', 'RW', 'CAM')]
            victim = random.choice(att_victims) if att_victims else random.choice(victim_players)

            fowler_tag = f"[{fowler.get('position', 'CB')}] {fowler['name']}"
            victim_tag = f"[{victim.get('position', 'ST')}] {victim['name']}"
            sev = random.random()
            sec = random.randint(14, 48)

            # 3% Penalty trong vòng cấm
            if sev < 0.03 and fowler.get('position') in ('CB', 'LB', 'RB', 'LWB', 'RWB', 'CDM', 'GK'):
                ball_zone = 12 if is_home_foul else 88
                new_events.append(_make_event(
                    next_min, next_inj, max(8, sec - 10),
                    f"⚠️ PHẠT ĐỀN 11M! {min_label}: {fowler_tag} ({foul_name}) phạm lỗi với {victim_tag} trong vòng cấm! Trọng tài chỉ tay vào chấm 11m!",
                    event_type="penalty_call", is_key=True,
                    data={"is_home_foul": is_home_foul, "fowler": fowler['name'], "victim": victim['name']}
                ))
                st_cands = [p for p in victim_players if p.get('position') in ('ST', 'CF', 'CAM')]
                taker = st_cands[0] if st_cands else victim
                gk = next((p for p in foul_players if p.get('position') == 'GK'), foul_players[0])

                is_home_pen = not is_home_foul
                if is_home_pen:
                    state['shots_home'] += 1
                    state['xg_home'] = round(state.get('xg_home', 0.0) + 0.76, 2)
                else:
                    state['shots_away'] += 1
                    state['xg_away'] = round(state.get('xg_away', 0.0) + 0.76, 2)

                pen_style = random.choice(['top_right', 'top_left', 'bottom_right', 'bottom_left', 'panenka'])
                if random.random() < 0.76:
                    if is_home_pen:
                        state['home_goals'] += 1
                        state['target_home'] += 1
                        state.setdefault('scorers_home', []).append({"name": taker['name'], "minute": f"{min_label} (P)", "type": "penalty"})
                    else:
                        state['away_goals'] += 1
                        state['target_away'] += 1
                        state.setdefault('scorers_away', []).append({"name": taker['name'], "minute": f"{min_label} (P)", "type": "penalty"})
                    taker['goals'] = taker.get('goals', 0) + 1
                    new_events.append(_make_event(
                        next_min, next_inj, sec,
                        f"🎯 PENALTY VÀOOO! {min_label}: [{taker.get('position', 'ST')}] {taker['name']} dứt điểm lạnh lùng đánh bại [GK] {gk['name']}! Tỉ số: {state['home_goals']}-{state['away_goals']}",
                        event_type="penalty_kick", is_key=True,
                        data={"is_home": is_home_pen, "taker": taker['name'], "gk": gk['name'], "is_goal": True, "style": pen_style}
                    ))
                else:
                    if is_home_pen:
                        state['target_home'] += 1
                        state['saves_away'] = state.get('saves_away', 0) + 1
                    else:
                        state['target_away'] += 1
                        state['saves_home'] = state.get('saves_home', 0) + 1
                    new_events.append(_make_event(
                        next_min, next_inj, sec,
                        f"🧤 CẢN PHÁ PENALTY! {min_label}: [GK] {gk['name']} đổ người xuất thần đẩy cú sút 11m của {taker['name']}!",
                        event_type="penalty_kick", is_key=True,
                        data={"is_home": is_home_pen, "taker": taker['name'], "gk": gk['name'], "is_goal": False, "style": pen_style}
                    ))

            # 22% Thẻ vàng (hoặc thẻ vàng thứ 2 -> thẻ đỏ)
            elif sev < 0.25:
                cur_y = fowler.get('yellow_cards', 0)
                if cur_y == 0:
                    fowler['yellow_cards'] = 1
                    if is_home_foul:
                        state['yellow_home'] += 1
                    else:
                        state['yellow_away'] += 1
                    new_events.append(_make_event(
                        next_min, next_inj, sec,
                        f"🟨 Thẻ vàng! {min_label}: {fowler_tag} ({foul_name}) nhận thẻ vàng cảnh cáo sau pha phạm lỗi chiến thuật với {victim_tag}.",
                        event_type="yellow_card", is_key=True,
                        data={"is_home": is_home_foul, "player": fowler['name'], "team": foul_name}
                    ))
                else:
                    fowler['yellow_cards'] = 2
                    fowler['red_cards'] = 1
                    if is_home_foul:
                        state['yellow_home'] += 1
                        state['red_home'] += 1
                        state.setdefault('red_cards_home', []).append({"name": fowler['name'], "minute": min_label})
                    else:
                        state['yellow_away'] += 1
                        state['red_away'] += 1
                        state.setdefault('red_cards_away', []).append({"name": fowler['name'], "minute": min_label})
                    new_events.append(_make_event(
                        next_min, next_inj, sec,
                        f"🟥 THẺ ĐỎ (2 THẺ VÀNG)! {min_label}: {fowler_tag} ({foul_name}) bị truất quyền thi đấu! {foul_name} phải chơi thiếu người!",
                        event_type="red_card", is_key=True,
                        data={"is_home": is_home_foul, "player": fowler['name'], "team": foul_name, "second_yellow": True}
                    ))

            # 1.2% Thẻ đỏ trực tiếp
            elif sev < 0.262 and fowler.get('position') in ('CB', 'CDM'):
                fowler['red_cards'] = 1
                if is_home_foul:
                    state['red_home'] += 1
                    state.setdefault('red_cards_home', []).append({"name": fowler['name'], "minute": min_label})
                else:
                    state['red_away'] += 1
                    state.setdefault('red_cards_away', []).append({"name": fowler['name'], "minute": min_label})
                new_events.append(_make_event(
                    next_min, next_inj, sec,
                    f"🟥 THẺ ĐỎ TRỰC TIẾP! {min_label}: {fowler_tag} ({foul_name}) vào bóng thô bạo với {victim_tag}! Trọng tài lập tức rút thẻ đỏ!",
                    event_type="red_card", is_key=True,
                    data={"is_home": is_home_foul, "player": fowler['name'], "team": foul_name, "direct_red": True}
                ))
            else:
                new_events.append(_make_event(
                    next_min, next_inj, sec,
                    f"⚠️ {min_label}: Trọng tài cắt còi thổi phạt {fowler_tag} ({foul_name}) sau pha tranh chấp với {victim_tag}. Đá phạt cho {victim_name}.",
                    event_type="foul", is_key=False,
                    data={"is_home": is_home_foul, "fowler": fowler['name'], "victim": victim['name']}
                ))

        # ---------- NHÁNH 3: PHẠT GÓC (~9% mỗi phút -> ~8-9 phạt góc/trận) ----------
        elif roll < 0.445:
            is_home_c = (random.random() < home_prob)
            att_name = home_name if is_home_c else away_name
            att_players = home_active if is_home_c else away_active
            ball_zone = 92 if is_home_c else 8

            if is_home_c:
                state['corners_home'] += 1
            else:
                state['corners_away'] += 1

            takers = [p for p in att_players if p.get('position') in ('LW', 'RW', 'CAM', 'LM', 'RM', 'LB', 'RB')]
            taker = random.choice(takers) if takers else att_players[0]
            headers = [p for p in att_players if p.get('position') in ('ST', 'CB', 'CF', 'CM') and p['name'] != taker['name']]
            header_p = random.choice(headers) if headers else random.choice(att_players)
            side = random.choice(['top', 'bottom'])
            sec = random.randint(18, 49)

            # ~3.5% phạt góc thành bàn đánh đầu trực tiếp
            if random.random() < 0.035:
                if is_home_c:
                    state['home_goals'] += 1
                    state['shots_home'] += 1
                    state['target_home'] += 1
                    state['xg_home'] = round(state.get('xg_home', 0.0) + 0.14, 2)
                    state.setdefault('scorers_home', []).append({"name": header_p['name'], "minute": min_label, "type": "goal"})
                else:
                    state['away_goals'] += 1
                    state['shots_away'] += 1
                    state['target_away'] += 1
                    state['xg_away'] = round(state.get('xg_away', 0.0) + 0.14, 2)
                    state.setdefault('scorers_away', []).append({"name": header_p['name'], "minute": min_label, "type": "goal"})
                header_p['goals'] = header_p.get('goals', 0) + 1
                new_events.append(_make_event(
                    next_min, next_inj, sec,
                    f"⚽ VÀOOO TỪ PHẠT GÓC! {min_label}: {taker['name']} treo bóng chuẩn xác để [{header_p.get('position', 'CB')}] {header_p['name']} ({att_name}) bật cao đánh đầu tung lưới! Tỉ số {state['home_goals']}-{state['away_goals']}",
                    event_type="goal", is_key=True,
                    data={"is_home": is_home_c, "shooter": header_p['name'], "zone": "Phạt góc", "dist": 7, "side": side}
                ))
            else:
                outcome = random.choice([
                    "nhưng thủ môn đối phương đã đấm bóng giải nguy.",
                    f"cú đánh đầu của {header_p['name']} đưa bóng đi vọt xà ngang.",
                    "hàng thủ đối phương đã kịp thời phá bóng ra xa."
                ])
                new_events.append(_make_event(
                    next_min, next_inj, sec,
                    f"🚩 Phạt góc! {min_label}: {taker['name']} ({att_name}) câu bóng vào vòng 16m50, {outcome}",
                    event_type="corner_kick", is_key=False,
                    data={"is_home": is_home_c, "taker": taker['name'], "header_player": header_p['name'], "side": side}
                ))

        # ---------- NHÁNH 4: ĐÁ PHẠT TRỰC TIẾP (~4.5% mỗi phút) ----------
        elif roll < 0.49:
            is_home_fk = (random.random() < home_prob)
            att_name = home_name if is_home_fk else away_name
            att_players = home_active if is_home_fk else away_active
            def_players = away_active if is_home_fk else home_active
            ball_zone = 78 if is_home_fk else 22

            takers = [p for p in att_players if p.get('position') in ('CAM', 'ST', 'RW', 'LW', 'CM')]
            taker = random.choice(takers) if takers else att_players[0]
            gk = next((p for p in def_players if p.get('position') == 'GK'), def_players[0])
            fk_dist = random.randint(20, 28)
            sec = random.randint(20, 50)

            if is_home_fk:
                state['shots_home'] += 1
                state['xg_home'] = round(state.get('xg_home', 0.0) + 0.06, 2)
            else:
                state['shots_away'] += 1
                state['xg_away'] = round(state.get('xg_away', 0.0) + 0.06, 2)

            if random.random() < 0.055:
                if is_home_fk:
                    state['home_goals'] += 1
                    state['target_home'] += 1
                    state.setdefault('scorers_home', []).append({"name": taker['name'], "minute": min_label, "type": "goal"})
                else:
                    state['away_goals'] += 1
                    state['target_away'] += 1
                    state.setdefault('scorers_away', []).append({"name": taker['name'], "minute": min_label, "type": "goal"})
                taker['goals'] = taker.get('goals', 0) + 1
                new_events.append(_make_event(
                    next_min, next_inj, sec,
                    f"⚽ SIÊU PHẨM ĐÁ PHẠT! {min_label}: Từ cự ly {fk_dist}m, {taker['name']} ({att_name}) vẽ đường cong qua hàng rào găm thẳng góc chữ A! Tỉ số {state['home_goals']}-{state['away_goals']}",
                    event_type="goal", is_key=True,
                    data={"is_home": is_home_fk, "shooter": taker['name'], "dist": fk_dist, "zone": "Đá phạt trực tiếp"}
                ))
            else:
                new_events.append(_make_event(
                    next_min, next_inj, sec,
                    f"🎯 Đá phạt! {min_label}: {taker['name']} ({att_name}) sút phạt cự ly {fk_dist}m, nhưng không thể đánh bại hàng rào và thủ môn {gk['name']}.",
                    event_type="free_kick", is_key=False,
                    data={"is_home": is_home_fk, "taker": taker['name'], "dist": fk_dist}
                ))

        # ---------- NHÁNH 5: RÊ BÓNG / ĐỘT PHÁ 1-ON-1 (~14% mỗi phút) ----------
        elif roll < 0.63:
            is_home_dr = (random.random() < home_prob)
            att_name = home_name if is_home_dr else away_name
            att_players = home_active if is_home_dr else away_active
            def_players = away_active if is_home_dr else home_active
            dribblers = [p for p in att_players if p.get('position') in ('LW', 'RW', 'CAM', 'ST', 'LM', 'RM')]
            dribbler = random.choice(dribblers) if dribblers else random.choice(att_players)
            defenders = [p for p in def_players if p.get('position') in ('CB', 'LB', 'RB', 'CDM')]
            defender = random.choice(defenders) if defenders else random.choice(def_players)
            sec = random.randint(12, 46)

            if random.random() < 0.55:
                ball_zone = random.randint(65, 82) if is_home_dr else random.randint(18, 35)
                new_events.append(_make_event(
                    next_min, next_inj, sec,
                    f"🪄 {min_label}: [{dribbler.get('position', 'W')}] {dribbler['name']} ({att_name}) đi bóng kỹ thuật vượt qua {defender['name']} mở ra khoảng trống thoáng đãng!",
                    event_type="dribble_success", is_key=False,
                    data={"is_home": is_home_dr, "dribbler": dribbler['name'], "defender": defender['name']}
                ))
            else:
                new_events.append(_make_event(
                    next_min, next_inj, sec,
                    f"🛡️ {min_label}: [{defender.get('position', 'CB')}] {defender['name']} đọc tình huống chuẩn xác, cắt bóng gọn gàng trước pha đột phá của {dribbler['name']}.",
                    event_type="dribble_tackle", is_key=False,
                    data={"is_home": is_home_dr, "dribbler": dribbler['name'], "defender": defender['name']}
                ))

        # ---------- NHÁNH 6: DIỄN BIẾN NHỊP TRẬN TỰ NHIÊN (1/3 số phút còn lại) ----------
        elif random.random() < 0.36:
            is_home_ctrl = (minute_poss_home >= 0.5)
            ctrl_name = home_name if is_home_ctrl else away_name
            ctrl_players = home_active if is_home_ctrl else away_active
            mids = [p for p in ctrl_players if p.get('position') in ('CM', 'CAM', 'CDM', 'LB', 'RB')]
            mid_p = random.choice(mids) if mids else random.choice(ctrl_players)
            sec = random.randint(15, 45)
            ambient_lines = [
                f"{mid_p['name']} ({ctrl_name}) luân chuyển bóng nhịp nhàng ở khu trung tuyến tìm kẽ hở.",
                f"{ctrl_name} đang dâng cao đội hình gây sức ép tầm cao (Kiểm soát bóng: {state['possession_home']}% - {state['possession_away']}%).",
                f"Trận đấu diễn ra giằng co ở khu vực giữa sân, {mid_p['name']} giữ nhịp rất chắc chắn.",
                f"{ctrl_name} triển khai bóng từ tuyến dưới kéo giãn cự ly đội hình đối phương."
            ]
            new_events.append(_make_event(
                next_min, next_inj, sec,
                f"🎙️ {min_label}: {random.choice(ambient_lines)}",
                event_type="commentary", is_key=False,
                data={"is_home": is_home_ctrl, "player": mid_p['name']}
            ))

    # 7. Kiểm tra kết thúc Hiệp 1 (sau khi chạy hết bù giờ H1) hoặc kết thúc Trận đấu (sau bù giờ H2)
    if phase == 'first_half' and next_min == 45 and next_inj >= state.get('injury_time_h1', 1):
        new_events.append(_make_event(
            45, next_inj, 59,
            f"⏱️ HẾT HIỆP 1! Trọng tài thổi còi khép lại 45 phút đầu tiên — Tỉ số tạm thời: {home_name} {state['home_goals']} - {state['away_goals']} {away_name}.",
            event_type="halftime", is_key=True
        ))
        state['phase'] = 'halftime'
        state['half'] = 1
    elif phase == 'second_half' and next_min == 90 and next_inj >= state.get('injury_time_h2', 2):
        new_events.append(_make_event(
            90, next_inj, 59,
            f"🏁 HẾT GIỜ! Trận đấu khép lại với tỉ số chung cuộc: {home_name} {state['home_goals']} - {state['away_goals']} {away_name}!",
            event_type="fulltime", is_key=True
        ))
        state['phase'] = 'finished'
        state['finished'] = True

    # Sắp xếp sự kiện trong phút theo đúng thứ tự giây (second tăng dần)
    new_events.sort(key=lambda e: e.get('second', 0))

    state['ball_zone'] = ball_zone
    state.setdefault('momentum', []).append({"m": min_label, "v": momentum_val})
    state.setdefault('events', []).extend(new_events)
    return new_events


def simulate_match(home_team, away_team, round_number=1, home_tactic="Can bang", away_tactic="Can bang"):
    """Mô phỏng nhanh trọn trận (tương thích ngược cho các module cũ & test)."""
    from football.classes import MatchOld

    def _serialize(players):
        return [{
            "name": p.name, "position": p.position, "attack": p.attack, "defense": p.defense,
            "speed": p.speed, "overall": p.overall, "stamina": p.stamina,
            "goals": 0, "yellow_cards": 0, "red_cards": 0
        } for p in players]

    state = {
        "home_team": home_team.name, "away_team": away_team.name,
        "tactic": home_tactic, "away_tactic": away_tactic,
        "home_players": _serialize(home_team.get_starting_xi()),
        "away_players": _serialize(away_team.get_starting_xi()),
        "away_subs": _serialize(away_team.get_subs()),
        "home_goals": 0, "away_goals": 0, "current_minute": 0, "injury_minute": 0,
        "injury_time_h1": 0, "injury_time_h2": 0, "phase": "first_half", "half": 1,
        "finished": False, "events": [], "other_matches": [],
        "shots_home": 0, "shots_away": 0, "target_home": 0, "target_away": 0,
        "corners_home": 0, "corners_away": 0, "fouls_home": 0, "fouls_away": 0,
        "yellow_home": 0, "yellow_away": 0, "red_home": 0, "red_away": 0,
        "xg_home": 0.0, "xg_away": 0.0, "saves_home": 0, "saves_away": 0,
        "passes_home": 0, "passes_away": 0, "possession_home": 50, "possession_away": 50,
    }

    while not state["finished"]:
        if state["phase"] == "halftime":
            state["phase"] = "second_half"
            state["half"] = 2
            state["injury_minute"] = 0
        simulate_single_minute(state)

    match = MatchOld(home_team, away_team, round_number)
    match.home_goals = state["home_goals"]
    match.away_goals = state["away_goals"]
    match.events = state["events"]
    match.finished = True
    match.shots_home = state["shots_home"]
    match.shots_away = state["shots_away"]
    match.target_home = state["target_home"]
    match.target_away = state["target_away"]
    match.corners_home = state["corners_home"]
    match.corners_away = state["corners_away"]
    match.fouls_home = state["fouls_home"]
    match.fouls_away = state["fouls_away"]
    match.yellow_home = state["yellow_home"]
    match.yellow_away = state["yellow_away"]
    match.red_home = state["red_home"]
    match.red_away = state["red_away"]
    return match
