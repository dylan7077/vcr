"""GUI visualization for CS2 demo replay."""

import arcade
from pathlib import Path
import pandas as pd
from vcr.parser import parse_kills, parse_rounds, parse_ticks, parse_bomb_events


class ReplayWindow(arcade.Window):
    def __init__(self, demo_path: Path, kills: pd.DataFrame, rounds: pd.DataFrame, ticks: pd.DataFrame, bomb_events: pd.DataFrame):
        super().__init__(1280, 960, "VCR - CS2 Replay")
        self.demo_path = demo_path
        self.kills = kills
        self.rounds = rounds
        self.ticks = ticks
        self.bomb_events = bomb_events
        
        self.current_tick = 0
        self.total_ticks = 0
        self.paused = False
        self.playback_speed = 2.0
        self.current_round = 1
        
        self.show_killfeed = True
        self.show_heatmap = False
        self.show_bomb = True
        
        self.player_stats = {}
        self.team_scores = {2: 0, 3: 0}
        
        self.bomb_carrier = None
        self.bomb_planted_tick = None
        self.bomb_position = None
        
        self.heatmap_data = []
        
        self.build_indexes()
        
    def build_indexes(self):
        import sys
        
        if self.ticks is not None and len(self.ticks) > 0:
            self.unique_ticks = sorted(self.ticks["tick"].unique())
            self.total_ticks = len(self.unique_ticks)
            print(f"Unique ticks: {self.total_ticks}", file=sys.stderr)
            print(f"Tick range: {self.unique_ticks[0]} to {self.unique_ticks[-1]}", file=sys.stderr)
            if self.total_ticks > 0:
                self.current_tick = int(self.unique_ticks[0])
        
        print(f"Kills: {len(self.kills) if self.kills is not None else 0}", file=sys.stderr)
        print(f"Bomb events: {len(self.bomb_events) if self.bomb_events is not None else 0}", file=sys.stderr)
        
        if self.kills is not None and len(self.kills) > 0:
            for _, row in self.kills.iterrows():
                attacker = row.get("attacker_name", "")
                victim = row.get("victim_name", "")
                
                if attacker and attacker not in self.player_stats:
                    self.player_stats[attacker] = {"kills": 0, "deaths": 0, "hs": 0}
                if attacker:
                    self.player_stats[attacker]["kills"] += 1
                    if row.get("headshot", False):
                        self.player_stats[attacker]["hs"] += 1
                
                if victim and victim not in self.player_stats:
                    self.player_stats[victim] = {"kills": 0, "deaths": 0, "hs": 0}
                if victim:
                    self.player_stats[victim]["deaths"] += 1
        
        self.current_round = 1
        if self.rounds is not None and len(self.rounds) > 0:
            for _, row in self.rounds.iterrows():
                team = row.get("winner_team", 0)
                if team in self.team_scores:
                    self.team_scores[team] += 1
                    
    def screen_to_map(self, x: float, y: float) -> tuple:
        # Game coords are roughly -2000 to +2000, center around 0
        scale = 0.22
        offset_x = 510
        offset_y = 470
        screen_x = offset_x + x * scale
        screen_y = offset_y + y * scale
        return screen_x, screen_y
        
    def get_players_at_tick(self, tick: int) -> dict:
        positions = {}
        if self.ticks is None or len(self.ticks) == 0:
            return positions
        tick_data = self.ticks[self.ticks["tick"] == tick]
        if len(tick_data) == 0:
            return positions
        for _, row in tick_data.iterrows():
            name = row.get("player_name", "")
            if name:
                x = row.get("X", 0)
                y = row.get("Y", 0)
                positions[name] = {
                    "x": x,
                    "y": y,
                    "team": row.get("team_num", 0),
                    "health": row.get("health", 100),
                    "has_bomb": row.get("has_bomb", False),
                }
        return positions
    
    def get_current_kills(self, tick: int) -> list:
        if self.kills is None or len(self.kills) == 0:
            return []
        return self.kills[self.kills["tick"].between(tick - 100, tick + 100)].to_dict("records")
    
    def on_draw(self):
        self.clear()
        self.draw_map()
        self.draw_current_players()
        self.draw_hud()
        self.draw_side_panel()
        self.draw_killfeed()
        
    def draw_map(self):
        arcade.draw_lbwh_rectangle_filled(110, 70, 800, 800, (180, 180, 180))
        
        # Grid lines every 512 units
        for i in range(-2048, 2049, 512):
            x1, y1 = self.screen_to_map(i, -2048)
            x2, y2 = self.screen_to_map(i, 2048)
            arcade.draw_line(x1, y1, x2, y2, (140, 140, 140), 1)
        for i in range(-2048, 2049, 512):
            x1, y1 = self.screen_to_map(-2048, i)
            x2, y2 = self.screen_to_map(2048, i)
            arcade.draw_line(x1, y1, x2, y2, (140, 140, 140), 1)
        
        # A and B site labels
        arcade.draw_text("A", 180, 750, arcade.color.BLUE, 20)
        arcade.draw_text("B", 750, 180, arcade.color.RED, 20)
        
    def draw_current_players(self):
        if self.current_tick <= 0:
            return
        
        if self.show_heatmap and len(self.heatmap_data) > 0:
            self.draw_heatmap()
        
        players = self.get_players_at_tick(int(self.current_tick))
        
        if not players:
            return
            
        for name, pos in players.items():
            if pos["health"] <= 0:
                continue
            x, y = self.screen_to_map(pos["x"], pos["y"])
            color = arcade.color.RED if pos["team"] == 2 else arcade.color.CYAN if pos["team"] == 3 else arcade.color.YELLOW
            
            is_bomb_carrier = name == self.bomb_carrier
            if is_bomb_carrier:
                arcade.draw_circle_filled(x, y, 14, arcade.color.BLACK)
                arcade.draw_circle_outline(x, y, 14, arcade.color.RED, 3)
            
            arcade.draw_circle_filled(x, y, 10, color)
            arcade.draw_circle_outline(x, y, 12, arcade.color.WHITE, 1)
            arcade.draw_text(name[:8], x - 20, y - 22, color, 9)
        
        if self.show_bomb and self.bomb_position:
            bx, by = self.screen_to_map(self.bomb_position[0], self.bomb_position[1])
            arcade.draw_circle_filled(bx, by, 8, arcade.color.RED)
            arcade.draw_circle_outline(bx, by, 10, arcade.color.YELLOW, 2)
            arcade.draw_text("BOMB", bx - 20, by - 20, arcade.color.RED, 10)
    
    def draw_heatmap(self):
        if len(self.heatmap_data) < 2:
            return
        heatmap_grid = {}
        cell_size = 64
        for x, y in self.heatmap_data:
            gx = int(x / cell_size)
            gy = int(y / cell_size)
            key = (gx, gy)
            heatmap_grid[key] = heatmap_grid.get(key, 0) + 1
        
        max_val = max(heatmap_grid.values()) if heatmap_grid else 1
        for (gx, gy), count in heatmap_grid.items():
            alpha = int(100 + 155 * (count / max_val))
            px = 510 + gx * cell_size * 0.22
            py = 470 + gy * cell_size * 0.22
            arcade.draw_lbwh_rectangle_filled(px - 5, py - 5, 10, 10, (255, 0, 0, alpha))
            
    def draw_hud(self):
        arcade.draw_lbwh_rectangle_filled(0, 920, 1024, 40, (20, 20, 25))
        arcade.draw_text("VCR - CS2", 20, 928, arcade.color.WHITE, 16)
        
        status = ">" if not self.paused else "||"
        color = arcade.color.GREEN if not self.paused else arcade.color.YELLOW
        arcade.draw_text(f"{status} {self.playback_speed}x", 250, 928, color, 14)
        
        tick_display = f"{self.current_tick}"
        if hasattr(self, 'unique_ticks') and len(self.unique_ticks) > 0:
            tick_display += f" / {self.unique_ticks[-1]}"
        arcade.draw_text(f"Tick: {tick_display}", 400, 928, arcade.color.WHITE, 14)
        
        if self.bomb_carrier:
            arcade.draw_text(f"Bomb: {self.bomb_carrier[:8]}", 600, 928, arcade.color.RED, 14)
        
    def draw_side_panel(self):
        panel_x = 1024
        arcade.draw_lbwh_rectangle_filled(panel_x, 0, 256, 960, (25, 27, 32))
        
        t_score = self.team_scores.get(2, 0)
        ct_score = self.team_scores.get(3, 0)
        arcade.draw_text(f"CT {ct_score} - {t_score} T", panel_x + 20, 910, arcade.color.YELLOW, 18)
        arcade.draw_text("PLAYERS", panel_x + 20, 700, arcade.color.WHITE, 14)
        
        sorted_stats = sorted(self.player_stats.items(), key=lambda x: x[1]["kills"], reverse=True)
        y = 680
        for name, stats in sorted_stats[:8]:
            k, d = stats["kills"], stats["deaths"]
            color = arcade.color.GREEN if k >= d else arcade.color.RED if d > k else arcade.color.WHITE
            arcade.draw_text(f"{name[:10]}", panel_x + 20, y, color, 12)
            arcade.draw_text(f"{k}/{d}", panel_x + 120, y, arcade.color.LIGHT_GRAY, 12)
            y -= 16
            
    def draw_killfeed(self):
        if not self.show_killfeed:
            return
        recent = self.get_current_kills(int(self.current_tick))
        if not recent:
            return
        x, y = 450, 870
        for k in recent[:3]:
            attacker = k.get("attacker_name", "")
            victim = k.get("victim_name", "")
            weapon = k.get("weapon", "")
            if attacker and victim:
                text = f"{attacker} -> {victim} ({weapon})"
                arcade.draw_text(text, x, y, arcade.color.WHITE, 13)
                y -= 18
                
    def update(self, delta_time: float):
        if not self.paused and hasattr(self, 'unique_ticks') and len(self.unique_ticks) > 0:
            for _ in range(int(self.playback_speed)):
                try:
                    idx = list(self.unique_ticks).index(self.current_tick)
                    if idx < len(self.unique_ticks) - 1:
                        self.current_tick = int(self.unique_ticks[idx + 1])
                    else:
                        self.paused = True
                        break
                except (ValueError, IndexError):
                    break
        
        if not self.paused:
            self.update_bomb()
        
        if self.show_heatmap:
            players = self.get_players_at_tick(int(self.current_tick))
            for name, pos in players.items():
                if pos["health"] > 0:
                    self.heatmap_data.append((pos["x"], pos["y"]))
    
    def update_bomb(self):
        self.bomb_carrier = None
        self.bomb_position = None
        
        if self.bomb_events is not None and len(self.bomb_events) > 0:
            for _, event in self.bomb_events.iterrows():
                event_tick = event.get("tick", 0)
                if event_tick <= self.current_tick:
                    event_type = event.get("event_type", "")
                    if event_type == "planted":
                        self.bomb_position = (event.get("X", 0), event.get("Y", 0))
                        self.bomb_planted_tick = event_tick
                    elif event_type == "exploded":
                        self.bomb_position = None
                        self.bomb_planted_tick = None
        
        if self.bomb_position is None:
            players = self.get_players_at_tick(int(self.current_tick))
            for name, pos in players.items():
                if pos.get("has_bomb", False):
                    self.bomb_carrier = name
                    self.bomb_position = (pos["x"], pos["y"])
                    break
                    
    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.SPACE:
            self.paused = not self.paused
        elif symbol == arcade.key.LEFT:
            try:
                idx = list(self.unique_ticks).index(self.current_tick)
                self.current_tick = int(max(self.unique_ticks[0], self.unique_ticks[max(0, idx - 50)]))
            except:
                pass
        elif symbol == arcade.key.RIGHT:
            try:
                idx = list(self.unique_ticks).index(self.current_tick)
                self.current_tick = int(min(self.unique_ticks[-1], self.unique_ticks[min(len(self.unique_ticks)-1, idx + 50)]))
            except:
                pass
        elif symbol == arcade.key.UP:
            self.playback_speed = min(8, self.playback_speed * 2)
        elif symbol == arcade.key.DOWN:
            self.playback_speed = max(0.25, self.playback_speed / 2)
        elif symbol == arcade.key.R:
            self.current_tick = int(self.unique_ticks[0]) if self.unique_ticks else 0
        elif symbol == arcade.key.HOME:
            self.current_tick = int(self.unique_ticks[0]) if self.unique_ticks else 0
            self.paused = False
        elif symbol == arcade.key.K:
            self.show_killfeed = not self.show_killfeed
        elif symbol == arcade.key.H:
            self.show_heatmap = not self.show_heatmap
        elif symbol == arcade.key.B:
            self.show_bomb = not self.show_bomb
        elif symbol == arcade.key.ESCAPE:
            self.close()


def run_replay(demo_path: Path, round: int | None = None, player: str | None = None):
    from vcr.parser import parse_kills, parse_rounds, parse_ticks, parse_bomb_events
    print(f"Loading: {demo_path}")
    kills = parse_kills(demo_path)
    rounds = parse_rounds(demo_path)
    ticks = parse_ticks(demo_path)
    bomb_events = parse_bomb_events(demo_path)
    print(f"Loaded: {len(kills)} kills, {len(rounds)} rounds")
    if ticks is not None:
        print(f"Ticks: {len(ticks)}")
    if bomb_events is not None:
        print(f"Bomb events: {len(bomb_events)}")
    ReplayWindow(demo_path, kills, rounds, ticks, bomb_events).run()
