# -*- coding: utf-8 -*-
"""
football.game_engine - Re-export từ football.services.match_engine để giữ tương thích ngược.
"""
from football.services.match_engine import (
    POSITION_WEIGHTS,
    DEFAULT_WEIGHT,
    calculate_team_strength,
    calculate_players_strength,
    simulate_single_minute,
    simulate_match,
    init_other_matches,
    format_minute_label,
)
