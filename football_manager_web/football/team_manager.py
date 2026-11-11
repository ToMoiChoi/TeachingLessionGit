from collections import Counter
from .models import Player  # noqa: F401  (giữ như bản gốc)

FORMATION_REQUIREMENTS = {
    '4-3-3': ['GK', 'CB', 'CB', 'LB', 'RB', 'CM', 'CM', 'CM', 'LW', 'RW', 'ST'],
    '4-2-3-1': ['GK', 'CB', 'CB', 'LB', 'RB', 'CDM', 'CDM', 'LW', 'CAM', 'RW', 'ST'],
    '5-3-2': ['GK', 'CB', 'CB', 'CB', 'LWB', 'RWB', 'CM', 'CM', 'CM', 'ST', 'ST'],
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
    if player.position == required_position:
        return 1.0
    return 0.7


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
