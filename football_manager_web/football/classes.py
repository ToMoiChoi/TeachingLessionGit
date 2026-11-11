"""
football.classes - Các class dùng cho mô phỏng trận đấu (không lưu DB)
"""
import json


class PlayerOld:
    def __init__(self, name, position, attack, defense, speed):
        self.name = name
        self.position = position
        self.attack = attack
        self.defense = defense
        self.speed = speed
        self.overall = round((attack + defense + speed) / 3, 2)
        self.stamina = 100.0
        self.goals = 0
        self.matches_played = 0
        self.yellow_cards = 0
        self.red_cards = 0
        self.preferred_positions = json.dumps([position])

    def to_dict(self):
        return {
            'name': self.name, 'position': self.position, 'attack': self.attack,
            'defense': self.defense, 'speed': self.speed, 'overall': self.overall,
            'stamina': self.stamina, 'goals': self.goals,
            'matches_played': self.matches_played,
            'yellow_cards': self.yellow_cards, 'red_cards': self.red_cards,
        }


class TeamOld:
    def __init__(self, name, players):
        self.name = name
        self.players = players if players else []
        self.formation = '4-3-3'
        self.tactic = 'Can bang'
        self.starting_xi = []
        self.substitutes = []

    def get_starting_xi(self):
        if self.starting_xi:
            return [self.players[i] for i in self.starting_xi]
        return self.players[:11]

    def get_subs(self):
        if self.substitutes:
            return [self.players[i] for i in self.substitutes]
        return self.players[11:16]


class MatchOld:
    def __init__(self, home, away, round_num):
        self.home_team = home
        self.away_team = away
        self.round = round_num
        self.home_goals = 0
        self.away_goals = 0
        self.events = []
        self.finished = False
        self.subs_used = 0

    def add_event(self, minute, desc):
        self.events.append({'minute': minute, 'description': desc})

    def result(self):
        if not self.finished:
            return 'Chưa diễn ra'
        if self.home_goals > self.away_goals:
            return 'Thắng'
        if self.home_goals < self.away_goals:
            return 'Thua'
        return 'Hòa'

    def points(self):
        if not self.finished:
            return 0
        if self.home_goals > self.away_goals:
            return 3
        if self.home_goals < self.away_goals:
            return 0
        return 1
