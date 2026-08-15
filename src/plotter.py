import csv
import os
from collections import defaultdict
import matplotlib.pyplot as plt


class Plotter:
    def __init__(self):
        self.history = defaultdict(list)

    def record_epoch(self, game_name, epoch, players):
        counts = defaultdict(int)
        for p in players:
            counts[p.strategy_name] += 1
        counts["epoch"] = epoch
        self.history[game_name].append(counts)

    def export_and_plot(self, output_dir="output"):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for game_name, data in self.history.items():
            # Gather all unique strategy names seen in this game
            all_strategies = set()
            for row in data:
                all_strategies.update(row.keys())
            all_strategies.discard("epoch")
            all_strategies = sorted(list(all_strategies))

            header = ["epoch"] + all_strategies

            file_name_base = game_name.replace(" ", "_").replace("`", "").lower()

            # Export CSV
            csv_path = os.path.join(output_dir, f"{file_name_base}.csv")
            with open(csv_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=header)
                writer.writeheader()
                for row in data:
                    # Fill missing values with 0
                    row_data = {col: row.get(col, 0) for col in header}
                    row_data["epoch"] = row["epoch"]
                    writer.writerow(row_data)

            # Generate PNG using matplotlib
            epochs = [row["epoch"] for row in data]
            plt.figure(figsize=(10, 6))
            for strategy in all_strategies:
                y_values = [row.get(strategy, 0) for row in data]
                plt.plot(epochs, y_values, label=strategy, marker="o")

            plt.title(f"Population Evolution - {game_name}")
            plt.xlabel("Epoch")
            plt.ylabel("Number of Players")

            # Put a legend to the right of the current axis
            plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
            plt.grid(True)
            plt.tight_layout()

            png_path = os.path.join(output_dir, f"{file_name_base}.png")
            plt.savefig(png_path)
            plt.close()
