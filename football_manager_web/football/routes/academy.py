# -*- coding: utf-8 -*-
"""
football.routes.academy - Học viện trẻ & săn tìm Wonderkids.
"""
import ast
import json
import random
from flask import redirect, render_template, request, session, url_for

from football.constants import SCOUT_HUBS
from football.models import Club, Player, YouthPlayer, db


def register_academy_routes(app):
    @app.route('/youth_academy', endpoint='youth_academy')
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

    @app.route('/scout_wonderkids', methods=['POST'], endpoint='scout_wonderkids')
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

    @app.route('/sign_youth_player', methods=['POST'], endpoint='sign_youth_player')
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

        session['scout_results'] = [t for t in scout_results if t.get('name') != talent['name']]
        session['youth_message'] = f"Đã ký hợp đồng đưa tài năng trẻ {talent['name']} (Tiềm năng: {talent['potential']}) vào Học viện!"
        return redirect(url_for('youth_academy'))

    @app.route('/train_youth_player', methods=['POST'], endpoint='train_youth_player')
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

    @app.route('/promote_youth/<int:youth_id>', methods=['POST'], endpoint='promote_youth')
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

    @app.route('/release_youth/<int:youth_id>', methods=['POST'], endpoint='release_youth')
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
