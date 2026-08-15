import sys
import os

# Ensure the simulation can find modules in the src/ directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from collections import Counter
from tqdm import tqdm

from src.usage_tracker import DailyLimitReachedException
from src.llm_player import LLMPlayer
from src.training_battery import TrainingBattery
from src.player_classes import (
    AlwaysCooperatePlayer,
    AlwaysDefectPlayer,
    TitForTatPlayer,
    SuspiciousTitForTatPlayer,
    TitForTwoTatsPlayer,
    TatForTitPlayer,
    RandomPlayer,
)
from src.game_machine import GameMachine
from src.graph import FullyConnectedGraph, CycleGraph, SmallWorldGraph, BarabasiAlbertGraph, ErdosRenyiGraph, GridGraph
from src.plotter import Plotter

CONSECUTIVE_MOVES = 10
EPOCHS = 10
OUTPUT_DIR = "output"

def generate_players(instances_per_class=10):
    classes = [
        AlwaysCooperatePlayer,
        AlwaysDefectPlayer,
        TitForTatPlayer,
        SuspiciousTitForTatPlayer,
        TitForTwoTatsPlayer,
        TatForTitPlayer,
        RandomPlayer,
    ]
    players = []
    for cls in classes:
        for _ in range(instances_per_class):
            players.append(cls())
    return players

def run_epoch(players, game_machine, game_graph):
    results = {}
    for edge in game_graph.get_edges():
        player_1 = players[edge[0]]
        player_2 = players[edge[1]]
        for i in range(CONSECUTIVE_MOVES):
            game_machine.play_game(player_1, player_2)
        results[(edge[0], edge[1])] = (player_1.score, player_2.score)
        player_1.finish_game()
        player_2.finish_game()
    return results

def simulation_step(players, death_threshold=0.25, reproduction_threshold=0.75):
    import random
    n = len(players)

    players_copy = players.copy()
    random.shuffle(players_copy)
    players_copy.sort(key=lambda x: x.run_score, reverse=False)
    for i, player in enumerate(players_copy):
        player.survivability_score = i / (n - 1) if n > 1 else 0.5

    new_generation = []
    for i in range(n):
        player_i = players[i]
        if player_i.survivability_score < death_threshold:
            pass
        elif (
            player_i.survivability_score >= death_threshold
            and player_i.survivability_score < reproduction_threshold
        ):
            new_generation.append(player_i)
        else:
            new_generation.append(player_i)
            new_generation.append(player_i.copy())

    for player in new_generation:
        player.run_score = 0

    return new_generation

def main():
    print("=== Phase 1: Training ===")
    # Initialize the LLM Player (using Gemini API by default)
    llm_agent = LLMPlayer(use_gemini=True, model_name="gemini-3.6-flash")
    
    memory_file = os.path.join(OUTPUT_DIR, "agent_memory.txt")
    if os.path.exists(memory_file):
        with open(memory_file, "r") as f:
            llm_agent.long_lasting_notes = f.read()
            print(f"Loaded previous training memory from {memory_file}")
    
    # Run training for 10 matches against random classical strategies
    training = TrainingBattery(llm_player=llm_agent, epochs=10, moves_per_match=10)
    
    try:
        training.run_training(output_dir=OUTPUT_DIR)
    except DailyLimitReachedException as e:
        print(f"\nTraining interrupted: {e}")
        print("Saving current progress and halting execution for today.")
        # We can explicitly exit or just allow the script to gracefully end
        # Since the user wants it to stop completely for the day if it hits the limit,
        # we shouldn't proceed to Phase 2.
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(memory_file, "w") as f:
            f.write(llm_agent.long_lasting_notes)
        print(f"Agent memory saved to {memory_file}")
        sys.exit(0)
    
    # If training completes successfully without exception
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(memory_file, "w") as f:
        f.write(llm_agent.long_lasting_notes)
    print(f"Agent memory saved to {memory_file}")
    
    print("\nTraining complete. Freezing notes for evaluation.")
    llm_agent.freeze_notes = True
    print(f"Final Long-lasting Notes:\n{llm_agent.long_lasting_notes}\n")
    
    print("=== Phase 2: Evaluation ===")
    game_plotter = Plotter()
    
    # Create the population: 5 instances of each classical strategy to avoid excessive API calls
    players = generate_players(instances_per_class=5)
    
    # Add 5 instances of the trained LLM agent
    for _ in range(5):
        players.append(llm_agent.copy())
        
    baseline_nodes = len(players)
    game_graph = SmallWorldGraph(baseline_nodes, k=4, p=0.1) # Small World reduces edge count significantly vs Fully Connected
    game_machine = GameMachine()
    run_name = "LLM Learner vs Classical (Small World)"
    
    game_plotter.record_epoch(run_name, 0, players)
    
    EVAL_EPOCHS = 5
    for i in tqdm(range(EVAL_EPOCHS), desc=f"Simulating {run_name}", unit="epoch"):
        run_epoch(players, game_machine, game_graph)
        players = simulation_step(players)
        game_plotter.record_epoch(run_name, i + 1, players)
        
    counts = Counter(p.strategy_name for p in players)
    print(f"\nFinal population for {run_name}:")
    for strategy, count in counts.most_common():
        print(f"  {strategy}: {count}")
    print()
    
    print("Generating CSVs and Plots...")
    game_plotter.export_and_plot(output_dir=OUTPUT_DIR)
    print("Export complete. Check the 'output' directory.")

if __name__ == "__main__":
    main()
