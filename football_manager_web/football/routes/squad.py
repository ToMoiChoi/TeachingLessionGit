# -*- coding: utf-8 -*-
"""
football.routes.squad - Đội hình, chọn 11 đá chính, chi tiết cầu thủ, nâng cấp, tập luyện, thống kê & lương.
"""
from flask import jsonify, redirect, render_template, request, session, url_for

from football.constants import FORMATION_POSITIONS
from football.models import Club, Player, db
from football.services.squad_service import auto_select_xi, enrich_player_fc


def _build_squad_context(club, raw_players):
    enriched = [enrich_player_fc(p, club) for p in raw_players]
    starting = [p for p in enriched if p['is_starting']]
    subs = [p for p in enriched if not p['is_starting']]
    if starting:
        team_ovr = int(round(sum(p['fc_ovr'] for p in starting) / len(starting)))
    else:
        team_ovr = int(round(sum(p['fc_ovr'] for p in enriched[:11]) / max(1, min(11, len(enriched)))))
    team_value = sum(p['market_value'] for p in enriched) * 10
    return enriched, starting, subs, team_ovr, team_value


def register_squad_routes(app):
    @app.route('/squad', endpoint='squad')
    def squad():
        if 'club_id' not in session:
            return redirect(url_for('index'))
        club = db.session.get(Club, session['club_id'])
        if not club:
            return redirect(url_for('index'))
        raw_players = Player.query.filter_by(club_id=club.id).order_by(Player.overall.desc()).all()

        if sum(1 for p in raw_players if p.is_starting) != 11 and len(raw_players) >= 11:
            selected_ids = auto_select_xi(raw_players, club.formation)
            for p in raw_players:
                p.is_starting = (p.id in selected_ids)
                p.is_substitute = not p.is_starting
            db.session.commit()

        enriched, starting, subs, team_ovr, team_value = _build_squad_context(club, raw_players)
        return render_template('squad.html', players=raw_players, enriched_players=enriched,
                               starting_players=starting, sub_players=subs,
                               team_ovr=team_ovr, team_value=team_value, team=club, club=club)

    @app.route('/api/auto_build_squad', methods=['POST'], endpoint='api_auto_build_squad')
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

        _, starting, subs, team_ovr, _ = _build_squad_context(club, raw_players)
        return jsonify({
            'success': True,
            'message': f'Đã tự động tối ưu 11 cầu thủ xuất sắc nhất cho sơ đồ {club.formation}!',
            'starting_players': starting, 'sub_players': subs, 'team_ovr': team_ovr
        })

    @app.route('/api/swap_squad_players', methods=['POST'], endpoint='api_swap_squad_players')
    def api_swap_squad_players():
        if 'club_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        club = db.session.get(Club, session['club_id'])
        if not club:
            return jsonify({'error': 'Club not found'}), 404

        data = request.get_json() or {}
        p1 = db.session.get(Player, data.get('p1_id'))
        p2 = db.session.get(Player, data.get('p2_id'))
        if not p1 or not p2 or p1.club_id != club.id or p2.club_id != club.id:
            return jsonify({'error': 'Không tìm thấy cầu thủ đổi'}), 404

        p1.is_starting, p2.is_starting = p2.is_starting, p1.is_starting
        p1.is_substitute = not p1.is_starting
        p2.is_substitute = not p2.is_starting
        db.session.commit()

        raw_players = Player.query.filter_by(club_id=club.id).all()
        _, starting, subs, team_ovr, _ = _build_squad_context(club, raw_players)
        return jsonify({
            'success': True,
            'message': f'Đã đổi {p1.name} và {p2.name} thành công!',
            'starting_players': starting, 'sub_players': subs, 'team_ovr': team_ovr
        })

    @app.route('/api/change_formation', methods=['POST'], endpoint='api_change_formation')
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

        _, starting, subs, team_ovr, _ = _build_squad_context(club, raw_players)
        return jsonify({
            'success': True, 'message': f'Đã chuyển sang sơ đồ {formation}!',
            'formation': formation, 'starting_players': starting, 'sub_players': subs, 'team_ovr': team_ovr
        })

    @app.route('/player/<int:player_id>', endpoint='player_detail')
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
        return render_template('player_detail.html', player=enrich_player_fc(p, club),
                               club=club, enriched_players=enriched_players)

    @app.route('/api/player/<int:player_id>', endpoint='api_get_player')
    def api_get_player(player_id):
        if 'club_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        club = db.session.get(Club, session['club_id'])
        p = db.session.get(Player, player_id)
        if not p:
            return jsonify({'error': 'Player not found'}), 404
        return jsonify({'success': True, 'player': enrich_player_fc(p, club)})

    @app.route('/api/train_player', methods=['POST'], endpoint='api_train_player')
    def api_train_player():
        if 'club_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        club = db.session.get(Club, session['club_id'])
        if not club:
            return jsonify({'error': 'Club not found'}), 404
        data = request.get_json() or {}
        p = db.session.get(Player, data.get('player_id'))
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
        return jsonify({
            'success': True, 'message': f'Huấn luyện thành công! {p.name} đã lên cấp {p.training_level}/30',
            'player': enrich_player_fc(p, club), 'club_money': club.money
        })

    @app.route('/api/rankup_player', methods=['POST'], endpoint='api_rankup_player')
    def api_rankup_player():
        if 'club_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        club = db.session.get(Club, session['club_id'])
        if not club:
            return jsonify({'error': 'Club not found'}), 404
        data = request.get_json() or {}
        p = db.session.get(Player, data.get('player_id'))
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
        return jsonify({
            'success': True, 'message': f'Thăng hạng thành công! {p.name} đã đạt Hạng {p.rank_level} 🔶',
            'player': enrich_player_fc(p, club), 'club_money': club.money
        })

    @app.route('/api/compare_players', methods=['POST'], endpoint='api_compare_players')
    def api_compare_players():
        if 'club_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        club = db.session.get(Club, session['club_id'])
        data = request.get_json() or {}
        p1 = db.session.get(Player, data.get('p1_id'))
        p2 = db.session.get(Player, data.get('p2_id'))
        if not p1 or not p2:
            return jsonify({'error': 'Không tìm thấy cầu thủ so sánh'}), 404
        return jsonify({
            'success': True, 'player1': enrich_player_fc(p1, club), 'player2': enrich_player_fc(p2, club)
        })

    @app.route('/api/skill_boost_player', methods=['POST'], endpoint='api_skill_boost_player')
    def api_skill_boost_player():
        if 'club_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        club = db.session.get(Club, session['club_id'])
        if not club:
            return jsonify({'error': 'Club not found'}), 404
        data = request.get_json() or {}
        p = db.session.get(Player, data.get('player_id'))
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
        return jsonify({
            'success': True, 'message': f'Nâng cấp Điểm kỹ năng thành công! {p.name} đạt Kỹ năng +{p.skill_boost} 🔥',
            'player': enrich_player_fc(p, club), 'club_money': club.money
        })

    @app.route('/api/transfer_training', methods=['POST'], endpoint='api_transfer_training')
    def api_transfer_training():
        if 'club_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        club = db.session.get(Club, session['club_id'])
        if not club:
            return jsonify({'error': 'Club not found'}), 404
        data = request.get_json() or {}
        p_src = db.session.get(Player, data.get('source_player_id'))
        p_tgt = db.session.get(Player, data.get('target_player_id'))
        if not p_src or not p_tgt or p_src.club_id != club.id or p_tgt.club_id != club.id:
            return jsonify({'error': 'Không tìm thấy cầu thủ'}), 404

        cost = 150000
        if club.money < cost:
            return jsonify({'error': f'Ngân sách CLB không đủ (Cần {cost:,} $)'}), 400
        src_lvl = getattr(p_src, 'training_level', 1) or 1
        tgt_lvl = getattr(p_tgt, 'training_level', 1) or 1
        if src_lvl <= 1:
            return jsonify({'error': f'{p_src.name} chưa có cấp huấn luyện nào để chuyển!'}), 400

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

    @app.route('/select_xi', methods=['GET', 'POST'], endpoint='select_xi')
    def select_xi():
        if 'club_id' not in session:
            return redirect(url_for('index'))
        club = db.session.get(Club, session['club_id'])
        if not club:
            return redirect(url_for('index'))
        raw_players = Player.query.filter_by(club_id=club.id).all()

        if request.method == 'POST':
            new_formation = request.form.get('formation')
            if new_formation in FORMATION_POSITIONS:
                club.formation = new_formation
            if request.form.get('auto') == '1':
                selected_ids = auto_select_xi(raw_players, club.formation)
            else:
                selected_ids = [int(pid) for pid in request.form.getlist('starting')]
                if len(selected_ids) != 11:
                    enriched, starting, subs, team_ovr, team_value = _build_squad_context(club, raw_players)
                    return render_template('select_xi.html', team=club, club=club, players=raw_players,
                                           enriched_players=enriched, starting_players=starting,
                                           sub_players=subs, team_ovr=team_ovr, team_value=team_value,
                                           error="Phải chọn đúng 11 cầu thủ đá chính!")
            for p in raw_players:
                p.is_starting = (p.id in selected_ids)
                p.is_substitute = not p.is_starting
            db.session.commit()
            return redirect(url_for('select_xi'))

        if sum(1 for p in raw_players if p.is_starting) != 11 and len(raw_players) >= 11:
            selected_ids = auto_select_xi(raw_players, club.formation)
            for p in raw_players:
                p.is_starting = (p.id in selected_ids)
                p.is_substitute = not p.is_starting
            db.session.commit()

        enriched, starting, subs, team_ovr, team_value = _build_squad_context(club, raw_players)
        return render_template('select_xi.html', team=club, club=club, players=raw_players,
                               enriched_players=enriched, starting_players=starting,
                               sub_players=subs, team_ovr=team_ovr, team_value=team_value)

    @app.route('/auto_select_xi_api', methods=['POST'], endpoint='auto_select_xi_api')
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
        _, starting, subs, team_ovr, _ = _build_squad_context(club, players)
        return jsonify({
            'success': True, 'selected': selected_ids,
            'starting_players': starting, 'sub_players': subs, 'team_ovr': team_ovr
        })

    @app.route('/training', methods=['GET', 'POST'], endpoint='training')
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

    @app.route('/player_stats', endpoint='player_stats')
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
