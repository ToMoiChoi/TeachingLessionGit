import random


def calculate_team_strength(team, tactic):
    starting_players = team.get_starting_xi()
    if not starting_players:
        return {'attack': 50, 'defense': 50, 'speed': 50, 'overall': 50}
    n = len(starting_players)
    total_att = sum(p.attack * (p.stamina / 100.0) for p in starting_players) / n
    total_def = sum(p.defense * (p.stamina / 100.0) for p in starting_players) / n
    total_spd = sum(p.speed * (p.stamina / 100.0) for p in starting_players) / n
    if tactic == 'Tan cong':
        total_att *= 1.15
        total_def *= 0.9
    elif tactic == 'Phong thu':
        total_att *= 0.85
        total_def *= 1.2
    overall = (total_att + total_def + total_spd) / 3
    return {'attack': total_att, 'defense': total_def, 'speed': total_spd, 'overall': overall}


def run_minutes(match, start_min, end_min, home_tactic, away_tactic):
    home_team = match.home_team
    away_team = match.away_team
    home_xi = home_team.get_starting_xi()
    away_xi = away_team.get_starting_xi()

    for minute in range(start_min, end_min + 1):
        stamina_loss = 0.35 if home_tactic == 'Tan cong' else (0.25 if home_tactic == 'Phong thu' else 0.3)
        for p in home_xi:
            p.stamina = max(10.0, p.stamina - stamina_loss)
        for p in away_xi:
            p.stamina = max(10.0, p.stamina - 0.3)

        home_str = calculate_team_strength(home_team, home_tactic)
        away_str = calculate_team_strength(away_team, away_tactic)

        if random.random() >= 0.12:
            continue

        total_power = home_str['overall'] + away_str['overall']
        home_chance = home_str['overall'] / total_power if total_power > 0 else 0.5
        is_home_attack = random.random() < home_chance
        att_team = home_team if is_home_attack else away_team
        att_players = home_xi if is_home_attack else away_xi
        def_players = away_xi if is_home_attack else home_xi

        attackers = [p for p in att_players if p.position in ('ST', 'LW', 'RW', 'CAM', 'CM')]
        shooter = random.choice(attackers) if attackers else random.choice(att_players)
        passers = [p for p in att_players if p != shooter]
        passer = random.choice(passers) if passers else None

        dist_roll = random.random()
        if dist_roll < 0.65:
            dist = round(random.uniform(6.0, 16.0), 1)
            shot_desc = random.choice([
                f'đối mặt thủ môn dứt điểm chìm ở cự ly {dist}m',
                f'băng vào đệm bóng cận thành ở cự ly {dist}m',
                f'bật cao đánh đầu dũng mãnh ở cự ly {dist}m',
                f'phối hợp bật nhả một chạm rồi dứt điểm ở cự ly {dist}m',
            ])
            base_prob = 0.36
        elif dist_roll < 0.95:
            dist = round(random.uniform(16.5, 20.0), 1)
            shot_desc = random.choice([
                f'tung cú sút xa quyết đoán ở cự ly {dist}m rìa vòng cấm',
                f'băng lên dứt điểm tuyến hai sấm sét ở cự ly {dist}m',
                f'cứa lòng kỹ thuật đưa bóng lượn vòng cung từ cự ly {dist}m',
                f'vung chân nã đại bác ở cự ly {dist}m sát vòng cấm địa',
            ])
            base_prob = 0.2
        else:
            dist = round(random.uniform(21.0, 32.0), 1)
            shot_desc = f'liều lĩnh nã đại bác từ cự ly cực xa {dist}m'
            base_prob = 0.04

        shooter_power = shooter.attack * (shooter.stamina / 100.0)
        gk = next((p for p in def_players if p.position == 'GK'), def_players[0])
        gk_power = gk.defense * (gk.stamina / 100.0)
        ratio = shooter_power / max(1.0, gk_power)
        final_prob = base_prob * ratio

        if random.random() < final_prob:
            if is_home_attack:
                match.home_goals += 1
            else:
                match.away_goals += 1
            shooter.goals += 1
            assist_text = f' (kiến tạo: {passer.name})' if passer else ''
            match.add_event(minute, f'⚽ VÀOOO! Phút {minute}: {shooter.name} ({att_team.name}) '
                                    f'{shot_desc}{assist_text}! Tỉ số: {match.home_goals}-{match.away_goals}')
        else:
            reasons = [f'nhưng thủ môn {gk.name} đã xuất sắc bay người cản phá',
                       'nhưng bóng đi chệch cột dọc trong gang tấc',
                       'nhưng bóng đập trúng xà ngang bật ra ngoài']
            match.add_event(minute, f'🧤 Cơ hội! Phút {minute}: {shooter.name} ({att_team.name}) '
                                    f'{shot_desc}, {random.choice(reasons)}.')
    return match


def simulate_half(match, half_number, home_tactic, away_tactic):
    start_min = 1 if half_number == 1 else 46
    end_min = 45 if half_number == 1 else 90
    return run_minutes(match, start_min, end_min, home_tactic, away_tactic)


def simulate_match(home_team, away_team, round_number, home_tactic, away_tactic):
    from football.classes import MatchOld
    match = MatchOld(home_team, away_team, round_number)
    match = simulate_half(match, 1, home_tactic, away_tactic)
    match.add_event(45, f'⏱️ Kết thúc hiệp 1! Tỉ số {match.home_goals}-{match.away_goals}')
    match = simulate_half(match, 2, home_tactic, away_tactic)
    match.add_event(90, f'⏱️ Kết thúc trận đấu! Tỉ số chung cuộc {match.home_goals}-{match.away_goals}')
    match.finished = True
    return match
