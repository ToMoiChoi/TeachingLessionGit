# -*- coding: utf-8 -*-
"""
football.config - Cấu hình ứng dụng Flask & tự động kiểm tra/bổ sung cột DB.
"""
import os
import shutil
from sqlalchemy import text, inspect

from football.models import db


def configure_app(app):
    """Cấu hình đường dẫn lưu trữ (hỗ trợ cả máy cục bộ lẫn Vercel Serverless)."""
    app.secret_key = os.environ.get('FM_SECRET_KEY', 'doimaykhongla')

    is_vercel = bool(os.environ.get('VERCEL'))
    if is_vercel:
        db_path = '/tmp/football_manager.db'
        upload_folder = '/tmp/uploads'
        data_folder = '/tmp/data'
        if not os.path.exists(db_path):
            src_db = os.path.join(app.root_path, 'instance', 'football_manager.db')
            if os.path.exists(src_db):
                try:
                    shutil.copy2(src_db, db_path)
                except Exception:
                    pass
    else:
        instance_dir = os.path.join(app.root_path, 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        db_path = os.path.join(instance_dir, 'football_manager.db')
        upload_folder = os.path.join(app.root_path, 'static', 'uploads')
        data_folder = os.path.join(app.root_path, 'data')

    os.makedirs(upload_folder, exist_ok=True)
    os.makedirs(data_folder, exist_ok=True)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('FM_DB_URI') or f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.environ.get('FM_UPLOAD_DIR') or upload_folder
    app.config['DATA_FOLDER'] = os.environ.get('FM_DATA_DIR') or data_folder


def ensure_schema_migrations(app):
    """Tạo bảng và tự động thêm các cột mới nếu database cũ chưa có."""
    player_migrations = [
        ('preferred_positions', 'TEXT DEFAULT "[]"'),
        ('assists', 'INTEGER DEFAULT 0'),
        ('contract_wage', 'INTEGER DEFAULT 50000'),
        ('market_value', 'INTEGER DEFAULT 500000'),
        ('training_level', 'INTEGER DEFAULT 10'),
        ('rank_level', 'INTEGER DEFAULT 1'),
        ('skill_boost', 'INTEGER DEFAULT 2'),
        ('age', 'INTEGER DEFAULT 24'),
        ('height', 'INTEGER DEFAULT 178'),
        ('weight', 'INTEGER DEFAULT 72'),
        ('nationality', 'VARCHAR(50) DEFAULT "Việt Nam"'),
        ('skill_moves', 'INTEGER DEFAULT 4'),
        ('weak_foot', 'INTEGER DEFAULT 4'),
        ('playstyle', 'VARCHAR(100) DEFAULT "Rê bóng thần tốc"'),
        ('yellow_cards', 'INTEGER DEFAULT 0'),
        ('red_cards', 'INTEGER DEFAULT 0'),
    ]

    club_migrations = [
        ('sponsor_name', 'VARCHAR(100) DEFAULT "VietinBank Sport"'),
        ('sponsor_weekly', 'INTEGER DEFAULT 250000'),
        ('sponsor_bonus', 'INTEGER DEFAULT 150000'),
        ('trophies', 'TEXT DEFAULT "[]"'),
    ]

    with app.app_context():
        db.create_all()
        try:
            inspector = inspect(db.engine)
            player_cols = {col['name'] for col in inspector.get_columns('players')}
            for col_name, col_def in player_migrations:
                if col_name not in player_cols:
                    db.session.execute(text(f'ALTER TABLE players ADD COLUMN {col_name} {col_def}'))

            club_cols = {col['name'] for col in inspector.get_columns('clubs')}
            for col_name, col_def in club_migrations:
                if col_name not in club_cols:
                    db.session.execute(text(f'ALTER TABLE clubs ADD COLUMN {col_name} {col_def}'))

            db.session.commit()
        except Exception:
            db.session.rollback()
