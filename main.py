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

CONSECUTIVE_MOVES = 5
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
    try:
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        console.print(Panel.fit(
            "[bold cyan]🎯 LLM Strategy Learner[/bold cyan]\n[dim]Iterated Prisoner's Dilemma with Real-time Reflection[/dim]",
            border_style="cyan"
        ))
    except Exception:
        print("=== LLM Strategy Learner ===")

    provider = os.getenv("LLM_PROVIDER")
    if not provider:
        use_gemini = os.getenv("USE_GEMINI", "false").lower() in ("true", "1", "yes")
        provider = "gemini" if use_gemini else "ollama"

    llm_agent = LLMPlayer(provider=provider)
    print(f"Provider: {llm_agent.provider} | Model: {llm_agent.model_name}")
    print("\n=== Phase 1: Training ===")
    
    memory_file = os.path.join(OUTPUT_DIR, "agent_memory.txt")
    if os.path.exists(memory_file):
        with open(memory_file, "r", encoding="utf-8") as f:
            lines = [line.strip().lstrip("- ").strip() for line in f if line.strip()]
            if lines:
                llm_agent.long_lasting_notes = lines
                print(f"Loaded {len(lines)} memory entries from {memory_file}")
    
    # Run training for 10 matches (5 rounds per match) against random classical strategies with 5% noise
    training = TrainingBattery(llm_player=llm_agent, epochs=10, moves_per_match=5, error_rate=0.05)
    
    try:
        training.run_training(output_dir=OUTPUT_DIR)
    except DailyLimitReachedException as e:
        print(f"\nTraining interrupted: {e}")
        print("Saving current progress and halting execution for today.")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(memory_file, "w", encoding="utf-8") as f:
            f.write(llm_agent._format_notes(llm_agent.long_lasting_notes) + "\n")
        print(f"Agent memory saved to {memory_file}")
        sys.exit(0)
    
    # If training completes successfully without exception
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(memory_file, "w", encoding="utf-8") as f:
        f.write(llm_agent._format_notes(llm_agent.long_lasting_notes) + "\n")
    print(f"Agent memory saved to {memory_file}")
    
    print("\nTraining complete. Freezing notes for evaluation.")
    llm_agent.freeze_notes = True
    print(f"Final Long-lasting Notes:\n{llm_agent._format_notes(llm_agent.long_lasting_notes)}\n")
    
    print("=== Phase 2: Evaluation ===")
    game_plotter = Plotter()
    
    # Create the population: 5 instances of each classical strategy to avoid excessive API calls
    players = generate_players(instances_per_class=5)
    
    # Add 5 instances of the trained LLM agent
    for _ in range(5):
        players.append(llm_agent.copy())
        
    baseline_nodes = len(players)
    game_graph = SmallWorldGraph(baseline_nodes, k=4, p=0.1) # Small World reduces edge count significantly vs Fully Connected
    game_machine = GameMachine(error_rate=0.05)
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
    print("Generating CSVs, Plots, Markdown, and HTML report...")
    game_plotter.export_and_plot(output_dir=OUTPUT_DIR)
    
    try:
        from src.match_logger import global_logger
        global_logger.export_html()
        print(f"Generated Markdown log: {global_logger.md_file}")
        print(f"Generated HTML report:   {global_logger.html_file}")
    except Exception as e:
        print(f"HTML export error: {e}")

    print("Export complete. Check the 'output' directory.")

if __name__ == "__main__":
    main()
