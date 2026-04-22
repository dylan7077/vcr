"""Demo parser for CS2 demo files."""

import pandas as pd
from pathlib import Path
from demoparser2 import DemoParser


CS2_MAPS = {
    "de_dust2": {"width": 1024, "height": 1024, "scale": 0.32},
    "de_mirage": {"width": 1024, "height": 1024, "scale": 0.32},
    "de_inferno": {"width": 1024, "height": 1024, "scale": 0.26},
    "de_nuke": {"width": 1024, "height": 1024, "scale": 0.32},
    "de_train": {"width": 1024, "height": 1024, "scale": 0.32},
    "de_ancient": {"width": 1024, "height": 1024, "scale": 0.32},
    "de_anubis": {"width": 1024, "height": 1024, "scale": 0.32},
    "de_vertigo": {"width": 1024, "height": 1024, "scale": 0.32},
}


def get_demo_info(demo_path: Path) -> dict:
    """Get basic demo information."""
    parser = DemoParser(str(demo_path))
    header = parser.parse_header()
    
    rounds = parser.parse_event("round_end")
    if rounds is not None:
        total_rounds = len(rounds)
    else:
        total_rounds = 0
    
    deaths = parser.parse_event("player_death")
    if deaths is not None:
        num_kills = len(deaths)
    else:
        num_kills = 0
    
    return {
        "map_name": header.get("map_name", "Unknown") if header else "Unknown",
        "total_rounds": total_rounds,
        "num_kills": num_kills,
    }


def parse_kills(demo_path: Path) -> pd.DataFrame:
    """Parse kill events from demo."""
    parser = DemoParser(str(demo_path))
    df = parser.parse_event("player_death")
    return df if df is not None else pd.DataFrame()


def parse_rounds(demo_path: Path) -> pd.DataFrame:
    """Parse round events from demo."""
    parser = DemoParser(str(demo_path))
    df = parser.parse_event("round_end")
    return df if df is not None else pd.DataFrame()


def parse_ticks(demo_path: Path) -> pd.DataFrame:
    """Parse tick data for player positions."""
    parser = DemoParser(str(demo_path))
    wanted_fields = ["X", "Y", "Z", "player_steamid", "player_name", "team_num", "health", "tick", "has_bomb"]
    df = parser.parse_ticks(wanted_fields)
    return df if df is not None else pd.DataFrame()


def parse_bomb_events(demo_path: Path) -> pd.DataFrame:
    """Parse bomb events (plant, defuse, explode)."""
    parser = DemoParser(str(demo_path))
    bomb_plant = parser.parse_event("bomb_planted")
    bomb_defuse = parser.parse_event("bomb_defused")
    bomb_explode = parser.parse_event("bomb_exploded")
    bomb_pickup = parser.parse_event("bomb_pickup")
    
    events = []
    for df, event_type in [(bomb_plant, "planted"), (bomb_defuse, "defused"), 
                            (bomb_explode, "exploded"), (bomb_pickup, "picked_up")]:
        if df is not None and len(df) > 0:
            df["event_type"] = event_type
            events.append(df)
    
    if events:
        return pd.concat(events, ignore_index=True)
    return pd.DataFrame()


def get_map_info(map_name: str) -> dict:
    """Get map dimensions and scale."""
    return CS2_MAPS.get(map_name, {"width": 1024, "height": 1024, "scale": 0.32})


def analyze_demo(demo_path: Path, round_num: int | None = None, player: str | None = None):
    """Analyze a demo file."""
    import click
    click.echo(f"Analyzing: {demo_path}")
    
    kills = parse_kills(demo_path)
    rounds = parse_rounds(demo_path)
    
    click.echo(f"Found {len(kills)} kills across {len(rounds)} rounds")
    
    if player and len(kills) > 0:
        player_kills = kills[kills["attacker_name"] == player]
        click.echo(f"Player {player} had {len(player_kills)} kills")