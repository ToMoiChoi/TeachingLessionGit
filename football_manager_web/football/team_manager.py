from collections import Counter
from .models import Player

FORMATION_REQUIREMENTS = {
    "4-3-3": ["GK", "CB", "CB", "LB", "RB", "CM", "CM", "CM", "LW", "RW", "ST"],
    "4-2-3-1": ["GK", "CB", "CB", "LB", "RB", "CDM", "CDM", "LW", "CAM", "RW", "ST"],
    "4-4-2": ["GK", "CB", "CB", "LB", "RB", "LM", "CM", "CM", "RM", "ST", "ST"],
    "4-3-2-1": ["GK", "CB", "CB", "LB", "RB", "CDM", "CM", "CM", "CAM", "CAM", "ST"],
    "3-4-3": ["GK", "CB", "CB", "CB", "LM", "CM", "CM", "RM", "LW", "RW", "ST"],
    "3-5-2": ["GK", "CB", "CB", "CB", "LWB", "CDM", "CM", "CM", "RWB", "ST", "ST"],
    "5-3-2": ["GK", "CB", "CB", "CB", "LWB", "RWB", "CM", "CM", "CM", "ST", "ST"],
    "5-4-1": ["GK", "CB", "CB", "CB", "LWB", "RWB", "LM", "CM", "CM", "RM", "ST"]
}

def is_valid_formation(team, formation):
    required = FORMATION_REQUIREMENTS.get(formation)
    if not required:
        return False
    xi = team.get_starting_xi()
    if len(xi) != 11:
        return False
    positions = [p.position for p in xi]
    return Counter(positions) == Counter(required)

def get_effectiveness(player, required_position):
    return 1.0 if player.position == required_position else 0.7

def substitute(team, player_out, player_in):
    xi = team.get_starting_xi()
    if player_out not in xi or player_in in xi:
        return False
    idx = xi.index(player_out)
    xi[idx] = player_in
    players = team.players
    in_idx = players.index(player_in)
    out_idx = players.index(player_out)
    players[out_idx], players[in_idx] = players[in_idx], players[out_idx]
    return True
