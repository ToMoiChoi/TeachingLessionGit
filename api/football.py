"""Vercel Python function: chạy app Flask Football Manager dưới đường dẫn /football.

vercel.json chuyển mọi request /football/... vào file này.
Server Vercel chỉ ghi được vào /tmp nên database và file lưu game nằm ở đó
(dữ liệu tạm: có thể mất khi server khởi động lại).
"""
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'football_manager_web')
sys.path.insert(0, os.path.abspath(ROOT))
os.environ.setdefault('FM_DB_URI', 'sqlite:////tmp/football_manager.db')
os.environ.setdefault('FM_DATA_DIR', '/tmp/fm_data')
os.environ.setdefault('FM_UPLOAD_DIR', '/tmp/fm_uploads')
os.chdir(os.path.abspath(ROOT))

from app import app as flask_app  # noqa: E402

PREFIX = '/football'


class PrefixMiddleware:
    """Cho Flask biết nó đang chạy dưới /football và bỏ dấu '/' cuối do vercel.json (trailingSlash) thêm vào."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '') or '/'
        if path == '/api/football' or path.startswith('/api/football/'):
            path = path[len('/api'):]
        if path == PREFIX or path.startswith(PREFIX + '/'):
            path = path[len(PREFIX):] or '/'
        if len(path) > 1 and path.endswith('/'):
            path = path.rstrip('/')
        environ['PATH_INFO'] = path
        environ['SCRIPT_NAME'] = PREFIX
        return self.wsgi_app(environ, start_response)


flask_app.wsgi_app = PrefixMiddleware(flask_app.wsgi_app)
app = flask_app
