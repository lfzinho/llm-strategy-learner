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
    def __init__(self, llm_player, epochs=10, moves_per_match=10):
        self.llm_player = llm_player
        self.epochs = epochs
        self.moves_per_match = moves_per_match
        self.game_machine = GameMachine()
        
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
        
        for epoch in tqdm(range(self.epochs), desc="Training Matches"):
            opponent = random.choice(self.opponent_classes)()
            
            # Play a match
            for move in range(self.moves_per_match):
                self.game_machine.play_game(self.llm_player, opponent)
            
            # Log the match results
            match_score_llm = self.llm_player.score
            match_score_opp = opponent.score
            
            log_entry = {
                "match": epoch + 1,
                "opponent_strategy": opponent.strategy_name,
                "llm_score": match_score_llm,
                "opponent_score": match_score_opp,
                "llm_long_lasting_notes": self.llm_player.long_lasting_notes,
                "llm_short_lasting_notes": self.llm_player.short_lasting_notes
            }
            self.history_log.append(log_entry)
            
            # Finish game for both (this resets game_history, score, and short_lasting_notes)
            self.llm_player.finish_game()
            opponent.finish_game()
            
        # Save log to JSON
        log_path = os.path.join(output_dir, "training_notes_history.json")
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(self.history_log, f, indent=4)
            
        print(f"Training completed. Notes history saved to {log_path}")
