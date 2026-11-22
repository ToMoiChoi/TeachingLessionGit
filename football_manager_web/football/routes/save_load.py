# -*- coding: utf-8 -*-
"""
football.routes.save_load - Lưu và nạp tiến trình game qua passcode JSON.
"""
from flask import redirect, render_template, request, session, url_for

from football.models import Club, MatchHistory, Player, db
from football.save_load import load_game, save_game


def register_save_load_routes(app):
    @app.route('/save', methods=['GET', 'POST'], endpoint='save')
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
                "match_history": [{
                    "opponent": m.opponent, "home_goals": m.home_goals,
                    "away_goals": m.away_goals, "result": m.result,
                    "points": m.points, "round": m.round, "events": m.events
                } for m in history],
            }
            save_game(data, passcode)
            return render_template('save.html', success=True)
        return render_template('save.html')

    @app.route('/load', methods=['GET', 'POST'], endpoint='load')
    def load():
        if request.method == 'POST':
            passcode = request.form.get('passcode', '').strip()
            if not passcode:
                return render_template('load.html', error="Vui lòng nhập passcode.")
            data = load_game(passcode)
            if data:
                club = Club(
                    name=data["club_name"], league=data["league"], season=data["season"],
                    money=data["money"], points=data["points"], matches_played=data["matches_played"],
                    position=data["position"], round=data["round"], formation=data["formation"],
                    tactic=data["tactic"]
                )
                db.session.add(club)
                db.session.commit()
                for p_data in data["players"]:
                    p = Player(
                        name=p_data["name"], position=p_data["position"],
                        attack=p_data["attack"], defense=p_data["defense"], speed=p_data["speed"],
                        overall=p_data["overall"], stamina=p_data["stamina"], goals=p_data["goals"],
                        matches_played=p_data["matches_played"],
                        is_starting=p_data.get("is_starting", False),
                        is_substitute=p_data.get("is_substitute", False),
                        preferred_positions=p_data.get("preferred_positions", '[]'),
                        club_id=club.id
                    )
                    db.session.add(p)
                db.session.commit()
                session['club_id'] = club.id
                return redirect(url_for('dashboard'))
            return render_template('load.html', error="Sai passcode hoặc không tìm thấy file.")
        return render_template('load.html')
