# -*- coding: utf-8 -*-
"""
football.routes.core - Các route nền tảng: trang chủ, tạo CLB, dashboard, hướng dẫn, audio, đăng xuất.
"""
import os
from flask import redirect, render_template, request, send_from_directory, session, url_for

from football.models import Club, Coach, db
from football.services.squad_service import generate_balanced_squad


def register_core_routes(app):
    @app.route('/sounds/<path:filename>', endpoint='serve_sounds')
    def serve_sounds(filename):
        return send_from_directory(os.path.join(app.root_path, 'sounds'), filename)

    @app.route('/', endpoint='index')
    def index():
        return render_template('index.html')

    @app.route('/create_club', methods=['GET', 'POST'], endpoint='create_club')
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

    @app.route('/dashboard', endpoint='dashboard')
    def dashboard():
        if 'club_id' not in session:
            return redirect(url_for('index'))
        club = db.session.get(Club, session['club_id'])
        if not club:
            return redirect(url_for('index'))
        return render_template('dashboard.html', club=club, team=club, season_complete=(club.round >= 18))

    @app.route('/tutorial', endpoint='tutorial')
    def tutorial():
        is_first_visit = session.pop('show_tutorial_welcome', False)
        club = db.session.get(Club, session.get('club_id')) if session.get('club_id') else None
        return render_template('tutorial.html', is_first_visit=is_first_visit, club=club)

    @app.route('/logout', endpoint='logout')
    def logout():
        session.clear()
        return redirect(url_for('index'))
