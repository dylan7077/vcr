"""Demo analyzer for CS2 demos."""

from pathlib import Path
from vcr.parser import parse_kills, parse_rounds


def analyze_demo(demo_path: Path, round_num: int | None = None, player: str | None = None):
    """Analyze a demo file."""
    kills = parse_kills(demo_path)
    rounds = parse_rounds(demo_path)
    
    print(f"Analyzing: {demo_path}")
    print(f"Found {len(kills)} kills across {len(rounds)} rounds")
    
    if player:
        player_kills = [k for k in kills if k.get("attacker_name") == player]
        print(f"Player {player} had {len(player_kills)} kills")