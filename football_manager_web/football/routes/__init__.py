# -*- coding: utf-8 -*-
"""
football.routes - Đăng ký toàn bộ routes theo miền chức năng, shim prefix Vercel (/football) và hook chèn audio widget.
"""
from flask import render_template, request

from football.routes.academy import register_academy_routes
from football.routes.club_ops import register_club_ops_routes
from football.routes.core import register_core_routes
from football.routes.league import register_league_routes
from football.routes.match import register_match_routes
from football.routes.save_load import register_save_load_routes
from football.routes.squad import register_squad_routes

_PREFIX_SHIM_TEMPLATE = """<script id="fm-prefix-shim">
(function() {
  var base = __BASE__;
  window.FM_BASE = base;
  if (!base) return;
  function fixUrl(u) {
    if (typeof u !== 'string') return u;
    if (u.startsWith(base + '/') || u === base || u.startsWith('/api/online')) return u;
    if (u.startsWith('/api/') || u.startsWith('/sounds/') || u.startsWith('/static/') ||
        u === '/start_second_half' || u === '/get_players' || u === '/substitute_api' ||
        u.startsWith('/player/')) {
      return base + u;
    }
    return u;
  }
  var origFetch = window.fetch;
  if (origFetch) {
    window.fetch = function(input, init) {
      if (typeof input === 'string') input = fixUrl(input);
      return origFetch.call(this, input, init);
    };
  }
  var OrigAudio = window.Audio;
  if (OrigAudio) {
    window.Audio = function(src) {
      return src !== undefined ? new OrigAudio(fixUrl(src)) : new OrigAudio();
    };
    window.Audio.prototype = OrigAudio.prototype;
  }
})();
</script>"""


def register_all_routes(app):
    register_core_routes(app)
    register_squad_routes(app)
    register_academy_routes(app)
    register_club_ops_routes(app)
    register_league_routes(app)
    register_match_routes(app)
    register_save_load_routes(app)

    @app.after_request
    def auto_inject_audio_and_prefix(response):
        """Tự động chèn shim đường dẫn /football (khi chạy trên Vercel) và bộ phát nhạc FIFA."""
        if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
            try:
                html = response.get_data(as_text=True)
                changed = False

                script_root = (request.script_root or '').rstrip('/')
                if script_root and 'id="fm-prefix-shim"' not in html:
                    import json
                    shim = _PREFIX_SHIM_TEMPLATE.replace('__BASE__', json.dumps(script_root))
                    if '<head>' in html:
                        html = html.replace('<head>', f'<head>\n{shim}', 1)
                    else:
                        html = shim + html
                    html = html.replace('href="/player/', f'href="{script_root}/player/')
                    changed = True

                if '</body>' in html and 'id="fifa-player-widget"' not in html:
                    snippet = render_template('partials/audio_widget.html')
                    html = html.replace('</body>', f'{snippet}\n</body>', 1)
                    changed = True

                if changed:
                    response.set_data(html)
            except Exception:
                pass
        return response
