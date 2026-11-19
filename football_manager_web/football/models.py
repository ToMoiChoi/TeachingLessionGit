# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Club(db.Model):
    __tablename__ = 'clubs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    league = db.Column(db.String(50), default='Hang 2')
    season = db.Column(db.Integer, default=1)
    money = db.Column(db.Integer, default=5000000)
    points = db.Column(db.Integer, default=0)
    matches_played = db.Column(db.Integer, default=0)
    position = db.Column(db.Integer, default=0)
    round = db.Column(db.Integer, default=0)
    formation = db.Column(db.String(10), default='4-3-3')
    tactic = db.Column(db.String(20), default='Can bang')
    sponsor_name = db.Column(db.String(100), default="VietinBank Sport")
    sponsor_weekly = db.Column(db.Integer, default=250000)
    sponsor_bonus = db.Column(db.Integer, default=150000)
    trophies = db.Column(db.Text, default='[]')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    coach_id = db.Column(db.Integer, db.ForeignKey('coaches.id'))
    coach = db.relationship('Coach', backref='clubs', lazy=True)
    players = db.relationship('Player', backref='club', lazy=True)

class YouthPlayer(db.Model):
    __tablename__ = 'youth_players'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(10), nullable=False)
    age = db.Column(db.Integer, default=16)
    attack = db.Column(db.Integer, default=50)
    defense = db.Column(db.Integer, default=50)
    speed = db.Column(db.Integer, default=50)
    overall = db.Column(db.Float, default=50.0)
    potential = db.Column(db.Integer, default=85)
    scout_origin = db.Column(db.String(100), default="Lò đào tạo CLB")
    training_points = db.Column(db.Integer, default=0)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=False)
    club = db.relationship('Club', backref=db.backref('youth_players', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "age": self.age,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "overall": self.overall,
            "potential": self.potential,
            "scout_origin": self.scout_origin,
            "training_points": self.training_points
        }

class Player(db.Model):
    __tablename__ = 'players'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(10), nullable=False)
    attack = db.Column(db.Integer, default=50)
    defense = db.Column(db.Integer, default=50)
    speed = db.Column(db.Integer, default=50)
    overall = db.Column(db.Float, default=50.0)
    stamina = db.Column(db.Float, default=100.0)
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    yellow_cards = db.Column(db.Integer, default=0)
    red_cards = db.Column(db.Integer, default=0)
    matches_played = db.Column(db.Integer, default=0)
    experience = db.Column(db.Integer, default=0)
    image_filename = db.Column(db.String(100), nullable=True)
    is_starting = db.Column(db.Boolean, default=False)
    is_substitute = db.Column(db.Boolean, default=False)
    preferred_positions = db.Column(db.Text, default='[]')
    contract_wage = db.Column(db.Integer, default=50000)
    market_value = db.Column(db.Integer, default=500000)
    training_level = db.Column(db.Integer, default=10)
    rank_level = db.Column(db.Integer, default=1)
    skill_boost = db.Column(db.Integer, default=2)
    age = db.Column(db.Integer, default=24)
    height = db.Column(db.Integer, default=178)
    weight = db.Column(db.Integer, default=72)
    nationality = db.Column(db.String(50), default="Việt Nam")
    skill_moves = db.Column(db.Integer, default=4)
    weak_foot = db.Column(db.Integer, default=4)
    playstyle = db.Column(db.String(100), default="Rê bóng thần tốc")
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "attack": self.attack,
            "defense": self.defense,
            "speed": self.speed,
            "overall": self.overall,
            "stamina": self.stamina,
            "goals": self.goals,
            "assists": self.assists,
            "yellow_cards": self.yellow_cards,
            "red_cards": self.red_cards,
            "matches_played": self.matches_played,
            "experience": self.experience,
            "preferred_positions": self.preferred_positions,
            "is_starting": self.is_starting,
            "is_substitute": self.is_substitute,
            "contract_wage": self.contract_wage,
            "market_value": self.market_value,
            "training_level": getattr(self, 'training_level', 10),
            "rank_level": getattr(self, 'rank_level', 1),
            "skill_boost": getattr(self, 'skill_boost', 2),
            "age": getattr(self, 'age', 24),
            "height": getattr(self, 'height', 178),
            "weight": getattr(self, 'weight', 72),
            "nationality": getattr(self, 'nationality', "Việt Nam"),
            "skill_moves": getattr(self, 'skill_moves', 4),
            "weak_foot": getattr(self, 'weak_foot', 4),
            "playstyle": getattr(self, 'playstyle', "Rê bóng thần tốc")
        }

class Coach(db.Model):
    __tablename__ = 'coaches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    nationality = db.Column(db.String(50))
    tactic_preference = db.Column(db.String(20))
    image_filename = db.Column(db.String(100), nullable=True)

class MatchHistory(db.Model):
    __tablename__ = 'match_history'
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'))
    opponent = db.Column(db.String(100))
    home_goals = db.Column(db.Integer)
    away_goals = db.Column(db.Integer)
    result = db.Column(db.String(10))
    points = db.Column(db.Integer)
    round = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    events = db.Column(db.Text)

class LeagueStanding(db.Model):
    __tablename__ = 'league_standings'
    id = db.Column(db.Integer, primary_key=True)
    club_id = db.Column(db.Integer, db.ForeignKey('clubs.id'))
    points = db.Column(db.Integer, default=0)
    played = db.Column(db.Integer, default=0)
    wins = db.Column(db.Integer, default=0)
    draws = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    goals_for = db.Column(db.Integer, default=0)
    goals_against = db.Column(db.Integer, default=0)
    gd = db.Column(db.Integer, default=0)
