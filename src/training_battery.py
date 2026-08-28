import sys
import os
import random
import json
from tqdm import tqdm

from src.player_classes import (
    AlwaysCooperatePlayer,
    AlwaysDefectPlayer,
    TitForTatPlayer,
    SuspiciousTitForTatPlayer,
    TitForTwoTatsPlayer,
    TatForTitPlayer,
    RandomPlayer,
    DetectivePlayer
)
from src.game_machine import GameMachine
from src.constants import Move

class TrainingBattery:
    def __init__(self, llm_player, epochs=10, moves_per_match=5, error_rate=0.05):
        self.llm_player = llm_player
        self.epochs = epochs
        self.moves_per_match = moves_per_match
        self.game_machine = GameMachine(error_rate=error_rate)
        
        self.opponent_classes = [
            AlwaysCooperatePlayer,
            AlwaysDefectPlayer,
            TitForTatPlayer,
            SuspiciousTitForTatPlayer,
            TitForTwoTatsPlayer,
            TatForTitPlayer,
            RandomPlayer,
            DetectivePlayer
        ]
        self.history_log = []

    def run_training(self, output_dir="output"):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Starting Training Battery for {self.epochs} matches...")
        
        for epoch in range(self.epochs):
            opponent = random.choice(self.opponent_classes)()
            
            try:
                from src.match_logger import global_logger
                global_logger.log_match_start(epoch + 1, self.epochs, opponent.strategy_name)
            except Exception:
                pass

            try:
                from rich.console import Console
                from rich.panel import Panel
                from rich.rule import Rule
                console = Console()
                console.print(Rule(f"[bold cyan]Match {epoch+1}/{self.epochs}[/bold cyan] vs [bold yellow]{opponent.strategy_name}[/bold yellow]"))
            except Exception:
                print(f"\n--- Match {epoch+1}/{self.epochs} vs {opponent.strategy_name} ---")
            
            # Play a match
            for move in range(self.moves_per_match):
                self.game_machine.play_game(self.llm_player, opponent)
            
            # Log the match results
            match_score_llm = self.llm_player.score
            match_score_opp = opponent.score
            
            # Finish game for both (reflects on match, updates long-lasting notes, resets short notes & score)
            llm_short_notes_snapshot = list(self.llm_player.short_lasting_notes)
            self.llm_player.finish_game()
            opponent.finish_game()
            
            log_entry = {
                "match": epoch + 1,
                "opponent_strategy": opponent.strategy_name,
                "llm_score": match_score_llm,
                "opponent_score": match_score_opp,
                "llm_long_lasting_notes": list(self.llm_player.long_lasting_notes),
                "llm_short_lasting_notes": llm_short_notes_snapshot
            }
            self.history_log.append(log_entry)
            
        # Save log to JSON
        log_path = os.path.join(output_dir, "training_notes_history.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(self.history_log, f, indent=4)
            
        print(f"Training completed. Notes history saved to {log_path}")
