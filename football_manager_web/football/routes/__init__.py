# -*- coding: utf-8 -*-
"""
football.routes - Đăng ký toàn bộ routes theo miền chức năng và hook chèn audio widget.
"""
from flask import render_template

from football.routes.academy import register_academy_routes
from football.routes.club_ops import register_club_ops_routes
from football.routes.core import register_core_routes
from football.routes.league import register_league_routes
from football.routes.match import register_match_routes
from football.routes.save_load import register_save_load_routes
from football.routes.squad import register_squad_routes


def register_all_routes(app):
    register_core_routes(app)
    register_squad_routes(app)
    register_academy_routes(app)
    register_club_ops_routes(app)
    register_league_routes(app)
    register_match_routes(app)
    register_save_load_routes(app)

    @app.after_request
    def auto_inject_audio_system(response):
        """Tự động chèn bộ phát nhạc FIFA + tiếng click từ template partial sạch sẽ."""
        if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
            try:
                html = response.get_data(as_text=True)
                if '</body>' in html and 'id="fifa-player-widget"' not in html:
                    snippet = render_template('partials/audio_widget.html')
                    html = html.replace('</body>', f'{snippet}\n</body>', 1)
                    response.set_data(html)
            except Exception:
                pass
        return response
