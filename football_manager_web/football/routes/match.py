# -*- coding: utf-8 -*-
"""
football.routes.match - Toàn bộ luồng thi đấu & tường thuật trực tiếp (live_match).
Sử dụng match_store phía server (chỉ lưu match_id vào session cookie) để không bao giờ bị tràn 4KB.
"""
import json
from flask import jsonify, redirect, render_template, request, session, url_for

from football.constants import FORMATION_POSITIONS
from football.models import Club, MatchHistory, Player, db
from football.services import audio_service
from football.services.match_engine import format_minute_label, init_other_matches, simulate_single_minute
from football.services.match_store import match_store
from football.services.squad_service import auto_select_xi, get_opponent_for_round


def _get_active_match():
    match_id = session.get('live_match_id')
    if not match_id:
        return None, None
    return match_id, match_store.get(match_id)


def _match_result_str(home_goals, away_goals):
    if home_goals > away_goals:
        return "Thắng"
    if home_goals < away_goals:
        return "Thua"
    return "Hòa"


def _match_points(home_goals, away_goals):
    if home_goals > away_goals:
        return 3
    if home_goals == away_goals:
        return 1
    return 0


def _finalize_live_match(club, state):
    """Lưu kết quả, tiền tài trợ, thể lực, bàn thắng, thẻ phạt và lịch sử trận đấu vào DB."""
    if state.get('finalized'):
        return

    hg = state['home_goals']
    ag = state['away_goals']
    res = _match_result_str(hg, ag)
    pts = _match_points(hg, ag)

    club.points += pts
    club.matches_played += 1
    club.round += 1

    weekly_payout = club.sponsor_weekly or 250000
    win_bonus = (club.sponsor_bonus or 150000) if res == 'Thắng' else 0
    club.money += (weekly_payout + win_bonus)

    # Cập nhật toàn bộ cầu thủ đã ra sân (kể cả người bị thay ra)
    tracked_players = list(state.get('home_players', [])) + list(state.get('home_subbed_out', []))
    seen_ids = set()
    for p_info in tracked_players:
        pid = p_info.get('id')
        if not pid or pid in seen_ids:
            continue
        seen_ids.add(pid)
        p_db = db.session.get(Player, pid)
        if p_db and p_db.club_id == club.id:
            p_db.stamina = float(p_info.get('stamina', p_db.stamina))
            p_db.goals = (p_db.goals or 0) + int(p_info.get('goals', 0))
            p_db.yellow_cards = (p_db.yellow_cards or 0) + int(p_info.get('yellow_cards', 0))
            p_db.red_cards = (p_db.red_cards or 0) + int(p_info.get('red_cards', 0))
            p_db.matches_played = (p_db.matches_played or 0) + 1
            p_db.experience = (p_db.experience or 0) + 5

    state['finished'] = True
    state['finalized'] = True
    state['phase'] = 'finished'

    db.session.add(MatchHistory(
        club_id=club.id,
        opponent=state['away_team'],
        home_goals=hg,
        away_goals=ag,
        result=res,
        points=pts,
        round=state.get('round', club.round),
        events=json.dumps(state.get('events', []), ensure_ascii=False)
    ))
    db.session.commit()

    # Lưu bản tóm tắt gọn nhẹ vào session cho trang /result (không nhồi hàng trăm event)
    key_events = [e for e in state.get('events', []) if e.get('is_key') or e.get('event_type') in ('goal', 'red_card', 'yellow_card', 'penalty_kick', 'halftime', 'fulltime')]
    session['last_match'] = {
        'home': state['home_team'],
        'away': state['away_team'],
        'home_goals': hg,
        'away_goals': ag,
        'result': res,
        'points': pts,
        'round': state.get('round', club.round),
        'events': key_events[:25]
    }
    session.modified = True


def _build_tick_payload(state, new_events):
    return {
        'home_goals': state['home_goals'],
        'away_goals': state['away_goals'],
        'current_minute': state['current_minute'],
        'injury_minute': state.get('injury_minute', 0),
        'injury_time_h1': state.get('injury_time_h1', 0),
        'injury_time_h2': state.get('injury_time_h2', 0),
        'minute_label': format_minute_label(state['current_minute'], state.get('injury_minute', 0)),
        'half': state.get('half', 1),
        'phase': state.get('phase', 'first_half'),
        'halftime': state.get('phase') == 'halftime',
        'finished': state.get('finished', False),
        'ball_zone': state.get('ball_zone', 50),
        'tactic': state.get('tactic', 'Can bang'),
        'away_tactic': state.get('away_tactic', 'Can bang'),
        'home_formation': state.get('home_formation', '4-3-3'),
        'subs_used': state.get('subs_used', 0),
        'new_events': new_events,
        'scorers_home': state.get('scorers_home', []),
        'scorers_away': state.get('scorers_away', []),
        'red_cards_home': state.get('red_cards_home', []),
        'red_cards_away': state.get('red_cards_away', []),
        'momentum': state.get('momentum', [])[-30:],
        'other_matches': state.get('other_matches', []),
        'stats': {
            'possession_home': state.get('possession_home', 50),
            'possession_away': state.get('possession_away', 50),
            'xg_home': state.get('xg_home', 0.0),
            'xg_away': state.get('xg_away', 0.0),
            'shots_home': state.get('shots_home', 0),
            'shots_away': state.get('shots_away', 0),
            'target_home': state.get('target_home', 0),
            'target_away': state.get('target_away', 0),
            'saves_home': state.get('saves_home', 0),
            'saves_away': state.get('saves_away', 0),
            'corners_home': state.get('corners_home', 0),
            'corners_away': state.get('corners_away', 0),
            'passes_home': state.get('passes_home', 0),
            'passes_away': state.get('passes_away', 0),
            'fouls_home': state.get('fouls_home', 0),
            'fouls_away': state.get('fouls_away', 0),
            'yellow_home': state.get('yellow_home', 0),
            'yellow_away': state.get('yellow_away', 0),
            'red_home': state.get('red_home', 0),
            'red_away': state.get('red_away', 0),
        },
        'home_players': [
            {
                'id': p['id'], 'name': p['name'], 'position': p['position'],
                'stamina': p['stamina'], 'overall': p['overall'],
                'goals': p.get('goals', 0),
                'yellow_cards': p.get('yellow_cards', 0),
                'red_cards': p.get('red_cards', 0),
            }
            for p in state.get('home_players', [])
        ],
        'away_players': [
            {
                'id': idx + 1000, 'name': p['name'], 'position': p['position'],
                'stamina': p['stamina'], 'overall': p['overall'],
                'goals': p.get('goals', 0),
                'yellow_cards': p.get('yellow_cards', 0),
                'red_cards': p.get('red_cards', 0),
            }
            for idx, p in enumerate(state.get('away_players', []))
        ],
        'low_stamina_home': [p['name'] for p in state.get('home_players', []) if p.get('stamina', 100) < 65],
    }


def register_match_routes(app):
    @app.route('/match', methods=['GET', 'POST'], endpoint='play_match')
    @app.route('/match_alias', methods=['GET', 'POST'], endpoint='match')
    def play_match():
        if 'club_id' not in session:
            return redirect(url_for('index'))
        club = db.session.get(Club, session['club_id'])
        if not club:
            return redirect(url_for('index'))
        players = Player.query.filter_by(club_id=club.id).all()

        # Bảo đảm có đúng 11 cầu thủ đá chính
        starting_players = [p for p in players if p.is_starting]
        if len(starting_players) != 11 and len(players) >= 11:
            selected_ids = auto_select_xi(players, club.formation)
            for p in players:
                p.is_starting = (p.id in selected_ids)
                p.is_substitute = not p.is_starting
            db.session.commit()
            starting_players = [p for p in players if p.is_starting]

        opponent = get_opponent_for_round(club.league, club.round + 1)
        starting_players_data = [
            {
                'id': p.id, 'name': p.name, 'position': p.position,
                'attack': p.attack, 'defense': p.defense, 'speed': p.speed,
                'overall': p.overall, 'stamina': p.stamina,
                'goals': 0, 'yellow_cards': 0, 'red_cards': 0
            }
            for p in starting_players
        ]

        if request.method == 'POST':
            for player in players:
                player.stamina = min(100.0, player.stamina + 20.0)
            tactic = request.form.get('tactic', 'Can bang')
            club.tactic = tactic
            db.session.commit()

            # Làm mới stamina sau hồi phục
            for sp in starting_players_data:
                p_db = db.session.get(Player, sp['id'])
                if p_db:
                    sp['stamina'] = p_db.stamina

            # Xóa trận cũ nếu còn
            old_id = session.pop('live_match_id', None)
            if old_id:
                match_store.delete(old_id)
            session.pop('live_match', None)

            match_state = {
                'club_id': club.id,
                'league': club.league,
                'round': club.round + 1,
                'home_team': club.name,
                'home_formation': club.formation or '4-3-3',
                'away_team': opponent['name'],
                'away_formation': opponent['formation'],
                'away_tactic': opponent['tactic'],
                'tactic': tactic,
                'home_goals': 0,
                'away_goals': 0,
                'current_minute': 0,
                'injury_minute': 0,
                'injury_time_h1': 0,
                'injury_time_h2': 0,
                'half': 1,
                'phase': 'first_half',
                'finished': False,
                'finalized': False,
                'subs_used': 0,
                'away_subs_used': 0,
                'home_players': starting_players_data,
                'home_subbed_out': [],
                'away_players': opponent['players'],
                'away_subs': opponent.get('subs', []),
                'events': [{
                    'minute': 0, 'injury_minute': 0, 'minute_label': "0'", 'second': 0, 'clock': '00:00',
                    'description': f"🏟️ Trận đấu Vòng {club.round + 1} giữa {club.name} và {opponent['name']} chuẩn bị bắt đầu!",
                    'type': 'kickoff', 'event_type': 'kickoff', 'is_key': True
                }],
                'scorers_home': [],
                'scorers_away': [],
                'red_cards_home': [],
                'red_cards_away': [],
                'momentum': [],
                'other_matches': init_other_matches(club.league, club.name, opponent['name']),
                'ball_zone': 50,
                'possession_home': 50,
                'possession_away': 50,
                'poss_sum_home': 0.0,
                'poss_ticks': 0,
                'xg_home': 0.0,
                'xg_away': 0.0,
                'shots_home': 0, 'shots_away': 0,
                'target_home': 0, 'target_away': 0,
                'saves_home': 0, 'saves_away': 0,
                'corners_home': 0, 'corners_away': 0,
                'passes_home': 0, 'passes_away': 0,
                'fouls_home': 0, 'fouls_away': 0,
                'yellow_home': 0, 'yellow_away': 0,
                'red_home': 0, 'red_away': 0,
            }
            match_id = match_store.create(match_state)
            session['live_match_id'] = match_id
            session['subs_used'] = 0
            session.modified = True
            return redirect(url_for('live_match'))

        return render_template('match.html', club=club, starting_players=starting_players_data,
                               round=club.round + 1, formation=club.formation, opponent=opponent)

    @app.route('/live_match', endpoint='live_match')
    def live_match():
        if 'club_id' not in session:
            return redirect(url_for('index'))
        club = db.session.get(Club, session['club_id'])
        _, state = _get_active_match()
        if not club or not state:
            return redirect(url_for('play_match'))
        return render_template('live_match.html', club=club, match=state, match_json=json.dumps(state, ensure_ascii=False))

    @app.route('/api/tick', methods=['POST'], endpoint='tick')
    def tick():
        if 'club_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        match_id, state = _get_active_match()
        if not state:
            return jsonify({'error': 'No active match'}), 400
        club = db.session.get(Club, session['club_id'])
        if not club:
            return jsonify({'error': 'Club not found'}), 404

        if state.get('finished') or state.get('phase') == 'halftime':
            return jsonify(_build_tick_payload(state, []))

        prev_goals = state['home_goals'] + state['away_goals']
        new_events = simulate_single_minute(state)

        if (state['home_goals'] + state['away_goals']) > prev_goals:
            audio_service.play_goal()
        elif new_events:
            audio_service.play_kick()

        if state.get('finished') and not state.get('finalized'):
            _finalize_live_match(club, state)

        match_store.save(match_id, state)
        return jsonify(_build_tick_payload(state, new_events))

    @app.route('/api/skip_half', methods=['POST'], endpoint='skip_half')
    def skip_half():
        """Tua nhanh đến hết hiệp hiện tại (hoặc hết trận) nhưng vẫn mô phỏng đủ từng phút thực tế."""
        if 'club_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        match_id, state = _get_active_match()
        if not state:
            return jsonify({'error': 'No active match'}), 400
        club = db.session.get(Club, session['club_id'])
        if not club:
            return jsonify({'error': 'Club not found'}), 404

        collected = []
        guard = 0
        while not state.get('finished') and state.get('phase') != 'halftime' and guard < 65:
            collected.extend(simulate_single_minute(state))
            guard += 1

        if state.get('finished') and not state.get('finalized'):
            _finalize_live_match(club, state)

        match_store.save(match_id, state)
        return jsonify(_build_tick_payload(state, collected))

    @app.route('/start_second_half', methods=['POST'], endpoint='start_second_half')
    def start_second_half():
        match_id, state = _get_active_match()
        if not state or state.get('phase') != 'halftime':
            return jsonify({'success': False, 'error': 'Not halftime'}), 400
        state['phase'] = 'second_half'
        state['half'] = 2
        state['current_minute'] = 45
        state['injury_minute'] = 0
        ev = {
            'minute': 46, 'injury_minute': 0, 'minute_label': "46'", 'second': 0, 'clock': '46:00',
            'description': '▶️ HIỆP 2 BẮT ĐẦU! Hai đội trở lại sân cho 45 phút quyết định.',
            'type': 'kickoff', 'event_type': 'kickoff', 'is_key': True
        }
        state['events'].append(ev)
        match_store.save(match_id, state)
        return jsonify({'success': True, 'half': 2, 'event': ev})

    @app.route('/api/change_tactic', methods=['POST'], endpoint='change_tactic')
    def change_tactic():
        match_id, state = _get_active_match()
        if not state:
            return jsonify({'error': 'No match'}), 400
        data = request.get_json() or {}
        tactic = data.get('tactic', 'Can bang')
        state['tactic'] = tactic
        cur_min = state.get('current_minute', 0)
        cur_inj = state.get('injury_minute', 0)
        mlabel = format_minute_label(cur_min, cur_inj)
        ev = {
            'minute': cur_min, 'injury_minute': cur_inj, 'minute_label': mlabel, 'second': 0,
            'clock': f"{cur_min:02d}:00",
            'description': f"📋 {mlabel}: HLV điều chỉnh chiến thuật sang {tactic.upper()}.",
            'type': 'tactic', 'event_type': 'tactic', 'is_key': False
        }
        state['events'].append(ev)
        match_store.save(match_id, state)
        return jsonify({'success': True, 'tactic': tactic, 'event': ev})

    @app.route('/api/change_live_formation', methods=['POST'], endpoint='change_live_formation')
    def change_live_formation():
        match_id, state = _get_active_match()
        if not state:
            return jsonify({'error': 'No match'}), 400
        data = request.get_json() or {}
        formation = data.get('formation', '4-3-3')
        if formation not in FORMATION_POSITIONS:
            return jsonify({'error': 'Sơ đồ không hợp lệ'}), 400
        state['home_formation'] = formation
        cur_min = state.get('current_minute', 0)
        cur_inj = state.get('injury_minute', 0)
        mlabel = format_minute_label(cur_min, cur_inj)
        ev = {
            'minute': cur_min, 'injury_minute': cur_inj, 'minute_label': mlabel, 'second': 0,
            'clock': f"{cur_min:02d}:00",
            'description': f"📐 {mlabel}: Đổi sơ đồ chiến thuật trên sân sang {formation}.",
            'type': 'tactic', 'event_type': 'tactic', 'is_key': False
        }
        state['events'].append(ev)
        match_store.save(match_id, state)
        return jsonify({'success': True, 'formation': formation, 'event': ev})

    @app.route('/match_status', endpoint='match_status')
    def match_status():
        _, state = _get_active_match()
        if not state:
            return jsonify({'error': 'No match'}), 404
        return jsonify(state)

    @app.route('/get_players', endpoint='get_players')
    def get_players():
        if 'club_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        club = db.session.get(Club, session['club_id'])
        if not club:
            return jsonify({'error': 'Club not found'}), 404
        _, state = _get_active_match()
        all_players = Player.query.filter_by(club_id=club.id).all()

        if state:
            on_pitch_ids = {p['id'] for p in state.get('home_players', [])}
            subbed_out_ids = {p['id'] for p in state.get('home_subbed_out', [])}
            starting = [
                {'id': p['id'], 'name': p['name'], 'position': p['position'],
                 'stamina': p['stamina'], 'red_cards': p.get('red_cards', 0)}
                for p in state.get('home_players', [])
                if p.get('red_cards', 0) == 0
            ]
            subs = [
                {'id': p.id, 'name': p.name, 'position': p.position, 'stamina': p.stamina}
                for p in all_players
                if p.id not in on_pitch_ids and p.id not in subbed_out_ids
            ]
        else:
            starting = [{'id': p.id, 'name': p.name, 'position': p.position, 'stamina': p.stamina}
                        for p in all_players if p.is_starting]
            subs = [{'id': p.id, 'name': p.name, 'position': p.position, 'stamina': p.stamina}
                    for p in all_players if p.is_substitute]
        return jsonify({'starting': starting, 'subs': subs})

    @app.route('/substitute', methods=['GET', 'POST'], endpoint='substitute')
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
            ok, _ = _perform_live_sub(club, out_id, in_id)
            if ok:
                return redirect(url_for('live_match'))
        return render_template('substitution.html', xi=xi, subs=subs, subs_used=subs_used)

    @app.route('/substitute_api', methods=['POST'], endpoint='substitute_api')
    def substitute_api():
        if 'club_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        club = db.session.get(Club, session['club_id'])
        if not club:
            return jsonify({'error': 'Club not found'}), 404
        data = request.get_json() or {}
        out_id = data.get('player_out')
        in_id = data.get('player_in')
        ok, payload = _perform_live_sub(club, out_id, in_id)
        if not ok:
            return jsonify(payload), 400
        return jsonify(payload)

    def _perform_live_sub(club, out_id, in_id):
        match_id, state = _get_active_match()
        if not state:
            return False, {'error': 'Không có trận đấu đang diễn ra'}
        subs_used = state.get('subs_used', 0)
        if subs_used >= 3:
            return False, {'error': 'Đã thay đủ 3 người!'}

        p_out_db = db.session.get(Player, out_id)
        p_in_db = db.session.get(Player, in_id)
        if not p_out_db or not p_in_db or p_out_db.club_id != club.id or p_in_db.club_id != club.id:
            return False, {'error': 'Cầu thủ không hợp lệ'}

        home_players = state.get('home_players', [])
        idx_out = next((i for i, p in enumerate(home_players) if p['id'] == p_out_db.id), None)
        if idx_out is None:
            return False, {'error': 'Cầu thủ rút ra không có trên sân'}

        old_slot = home_players[idx_out]
        if old_slot.get('red_cards', 0) > 0:
            return False, {'error': 'Không thể thay cầu thủ đã bị thẻ đỏ!'}

        state.setdefault('home_subbed_out', []).append(old_slot)
        new_slot = {
            'id': p_in_db.id, 'name': p_in_db.name, 'position': p_in_db.position,
            'attack': p_in_db.attack, 'defense': p_in_db.defense, 'speed': p_in_db.speed,
            'overall': p_in_db.overall, 'stamina': p_in_db.stamina,
            'goals': 0, 'yellow_cards': 0, 'red_cards': 0
        }
        home_players[idx_out] = new_slot
        state['subs_used'] = subs_used + 1
        session['subs_used'] = state['subs_used']

        cur_min = state.get('current_minute', 0)
        cur_inj = state.get('injury_minute', 0)
        mlabel = format_minute_label(cur_min, cur_inj)
        ev = {
            'minute': cur_min, 'injury_minute': cur_inj, 'minute_label': mlabel, 'second': 0,
            'clock': f"{cur_min:02d}:00",
            'description': f"🔄 {mlabel}: {club.name} thay người — {p_out_db.name} rời sân, {p_in_db.name} vào thay ({state['subs_used']}/3).",
            'type': 'substitution', 'event_type': 'substitution', 'is_key': True,
            'data': {'is_home': True, 'player_out': p_out_db.name, 'player_in': p_in_db.name}
        }
        state['events'].append(ev)
        match_store.save(match_id, state)

        return True, {
            'success': True,
            'subs_used': state['subs_used'],
            'event': ev,
            'player_out': {'id': p_out_db.id, 'name': p_out_db.name},
            'player_in': {'id': p_in_db.id, 'name': p_in_db.name, 'stamina': p_in_db.stamina, 'position': p_in_db.position}
        }

    @app.route('/low_stamina', endpoint='low_stamina')
    def low_stamina():
        if 'club_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        _, state = _get_active_match()
        if state:
            low = [{'name': p['name'], 'stamina': p['stamina']} for p in state.get('home_players', []) if p.get('stamina', 100) < 65]
            return jsonify({'home': low})
        club = db.session.get(Club, session['club_id'])
        if not club:
            return jsonify({'error': 'Club not found'}), 404
        players = Player.query.filter_by(club_id=club.id, is_starting=True).all()
        return jsonify({'home': [{'name': p.name, 'stamina': p.stamina} for p in players if p.stamina < 65]})

    @app.route('/result', endpoint='result')
    def result():
        if 'last_match' not in session:
            return redirect(url_for('dashboard'))
        return render_template('result.html', match=session['last_match'])
