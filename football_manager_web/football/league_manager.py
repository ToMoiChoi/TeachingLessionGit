# -*- coding: utf-8 -*-

def generate_round_robin(teams):
    return []

def update_standings(league):
    stats = {}
    for team in league.teams:
        stats[team.name] = {"points": 0, "played": 0, "wins": 0, "draws": 0, "losses": 0,
                            "goals_for": 0, "goals_against": 0}
    for round_matches in league.schedule:
        for match in round_matches:
            if not match.finished:
                continue
            home, away = match.home_team.name, match.away_team.name
            hg, ag = match.home_goals, match.away_goals
            stats[home]["goals_for"] += hg
            stats[home]["goals_against"] += ag
            stats[away]["goals_for"] += ag
            stats[away]["goals_against"] += hg
            stats[home]["played"] += 1
            stats[away]["played"] += 1
            if hg > ag:
                stats[home]["points"] += 3
                stats[home]["wins"] += 1
                stats[away]["losses"] += 1
            elif hg < ag:
                stats[away]["points"] += 3
                stats[away]["wins"] += 1
                stats[home]["losses"] += 1
            else:
                stats[home]["points"] += 1
                stats[away]["points"] += 1
                stats[home]["draws"] += 1
                stats[away]["draws"] += 1
    standings = []
    for team in league.teams:
        s = stats[team.name]
        gd = s["goals_for"] - s["goals_against"]
        standings.append({"team": team, "points": s["points"], "played": s["played"],
                         "wins": s["wins"], "draws": s["draws"], "losses": s["losses"],
                         "goals_for": s["goals_for"], "goals_against": s["goals_against"],
                         "gd": gd})
    standings.sort(key=lambda x: (-x["points"], -x["gd"], -x["goals_for"]))
    league.standing = standings
    return standings