# -*- coding: utf-8 -*-
"""
football.routes.league - Bảng xếp hạng, lịch thi đấu, lịch sử trận đấu và tổng kết mùa giải.
"""
import json
import random
from flask import redirect, render_template, session, url_for

from football.constants import LEAGUE_OPPONENTS
from football.models import Club, MatchHistory, Player, db
from football.services.squad_service import get_opponent_for_round


def register_league_routes(app):
    @app.route('/standings', endpoint='standings')
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

    @app.route('/schedule', endpoint='schedule')
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
                "round": round_number,
                "home": club.name if is_home else opponent['name'],
                "away": opponent['name'] if is_home else club.name,
                "current": round_number == club.round + 1
            })
        return render_template('schedule.html', rounds=rounds)

    @app.route('/match_history', endpoint='match_history')
    def match_history():
        if 'club_id' not in session:
            return redirect(url_for('index'))
        club = db.session.get(Club, session['club_id'])
        if not club:
            return redirect(url_for('index'))
        matches = MatchHistory.query.filter_by(club_id=club.id).order_by(MatchHistory.round.desc()).all()
        return render_template('match_history.html', matches=matches)

    @app.route('/season_end', endpoint='season_end')
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

        if club.league == "Hang 2" and club.position <= 2:
            msg = f"🎉 Chúc mừng! Bạn xuất sắc cán đích ở vị trí #{club.position}, giành Cúp Thăng Hạng lên Hạng 1 và nhận thưởng $1,500,000!"
            club.league = "Hang 1"
            club.money += 1500000
            if "h2_promotion" not in trophies_list:
                trophies_list.append("h2_promotion")
        elif club.league == "Hang 1" and club.position == 1:
            msg = "🏆 Chúc mừng! Bạn đã ĐOẠT CHỨC VÔ ĐỊCH QUỐC GIA (V-League 1), nhận thưởng $8,000,000 và chính thức tiến vào UEFA CHAMPIONS LEAGUE!"
            club.league = "Champions League"
            club.money += 8000000
            if "h1_champion" not in trophies_list:
                trophies_list.append("h1_champion")
        elif club.league == "Champions League" and club.position == 1:
            msg = "⭐🏆⭐ THẦN KỲ! BẠN ĐÃ ĐĂNG QUANG NGÔI VÔ ĐỊCH UEFA CHAMPIONS LEAGUE! NHẬN THƯỞNG $15,000,000!"
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
