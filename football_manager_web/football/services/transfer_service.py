# -*- coding: utf-8 -*-
"""
football.services.transfer_service - Sinh thị trường chuyển nhượng và đề nghị mua cầu thủ.
"""
import random
from football.constants import FIRST_NAMES, LAST_NAMES


def build_transfer_market(club):
    rng = random.Random(f"market-{club.id}-{club.season}-{club.round}")
    positions = ['GK', 'CB', 'LB', 'RB', 'CM', 'CAM', 'LW', 'RW', 'ST']
    candidates = []
    base_ovr = 75 if club.league == "Hang 1" else (84 if club.league == "Champions League" else 64)
    for index in range(6):
        overall = rng.randint(base_ovr - 4, base_ovr + 8)
        candidates.append({
            'id': f'{club.season}-{club.round}-{index}',
            'name': f'{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}',
            'position': rng.choice(positions),
            'overall': overall,
            'attack': min(95, overall + rng.randint(-8, 8)),
            'defense': min(95, overall + rng.randint(-8, 8)),
            'speed': min(95, overall + rng.randint(-8, 8)),
            'price': overall * 75000
        })
    return candidates


def build_incoming_offers(club, squad_players):
    rng = random.Random(f"offers-{club.id}-{club.season}-{club.round}")
    offers = []
    if len(squad_players) > 12 and rng.random() < 0.7:
        target = rng.choice(squad_players)
        opp_names = [
            "Hà Nội FC", "Công An Hà Nội", "Thể Công Viettel",
            "Real Madrid", "Manchester City", "Paris Saint-Germain"
        ]
        offer_club = rng.choice(opp_names)
        premium = rng.uniform(1.1, 1.4)
        offer_price = int(target.overall * 70000 * premium)
        offers.append({
            "id": f"offer-{target.id}-{club.round}",
            "player_id": target.id,
            "player_name": target.name,
            "club_name": offer_club,
            "offer_price": offer_price
        })
    return offers
