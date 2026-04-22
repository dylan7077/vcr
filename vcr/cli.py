import click
from pathlib import Path

__version__ = "0.1.0"


@click.group()
@click.version_option(version=__version__)
def main():
    """VCR - CS2 Demo Replay Visualization"""
    pass


@main.command()
@click.argument("demo_path", type=click.Path(exists=True, path_type=Path))
@click.option("--no-gui", is_flag=True, help="CLI mode without visualization")
@click.option("--round", type=int, default=None, help="Specific round to analyze")
@click.option("--player", type=str, default=None, help="Filter by player name")
def replay(demo_path: Path, no_gui: bool, round: int | None, player: str | None):
    """Replay a CS2 demo file"""
    click.echo(f"Loading demo: {demo_path}")
    
    if no_gui:
        from vcr.analyzer import analyze_demo
        analyze_demo(demo_path, round=round, player=player)
    else:
        from vcr.gui import run_replay
        run_replay(demo_path, round=round, player=player)


@main.command()
@click.argument("demo_path", type=click.Path(exists=True, path_type=Path))
def info(demo_path: Path):
    """Show demo information"""
    from vcr.parser import get_demo_info
    info = get_demo_info(demo_path)
    click.echo(f"Map: {info['map_name']}")
    click.echo(f"Rounds: {info['total_rounds']}")
    click.echo(f"Kills: {info['num_kills']}")


@main.command()
def demos():
    """Show where to download CS2 demos"""
    click.echo("Where to get CS2 demo files:")
    click.echo("")
    click.echo("1. HLTV.org - Best for pro matches")
    click.echo("   https://www.hltv.org/matches")
    click.echo("   Examples from recent tournaments:")
    click.echo("   - PGL Bucharest 2026: /matches/2393046 (Astralis vs FUT final)")
    click.echo("   - IEM Katowice 2025: /matches/2378917 (Vitality vs Spirit)")
    click.echo("   Steps: Find match -> Click 'Demo' -> Extract .rar -> Use .dem file")
    click.echo("")
    click.echo("2. In-game (Your Matches)")
    click.echo("   CS2 -> Watch -> Your Matches -> Download")
    click.echo("   WARNING: Demos expire after ~30 days!")
    click.echo("")
    click.echo("3. FACEIT")
    click.echo("   faceit.com -> Matchroom -> Watch Demo")
    click.echo("   Extract .rar file to CS2 game folder")
    click.echo("")
    click.echo("4. getreplay.gg - Easy pro demos")
    click.echo("   https://getreplay.gg/en/pro-demos")


if __name__ == "__main__":
    main()