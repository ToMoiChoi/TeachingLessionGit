# -*- coding: utf-8 -*-
"""
Package football - Khởi tạo Flask Application Factory `create_app()`.
"""
import os
from flask import Flask

from football.config import configure_app, ensure_schema_migrations
from football.models import db
from football.routes import register_all_routes


def create_app():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        root_path=root_dir,
        template_folder=os.path.join(root_dir, 'templates'),
        static_folder=os.path.join(root_dir, 'static'),
    )
    configure_app(app)
    db.init_app(app)
    ensure_schema_migrations(app)
    register_all_routes(app)
    return app
