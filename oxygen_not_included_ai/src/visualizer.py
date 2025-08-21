# Placeholder for visualizer.py
# This module will be used for visualizing game state and AI plans.

import wandb
import matplotlib.pyplot as plt

from .models import ColonyState

class Visualizer:
    def __init__(self, use_wandb=False):
        self.use_wandb = use_wandb
        if self.use_wandb:
            wandb.init(project="oxygen-not-included-ai")
            print("Weights & Biases integration enabled.")

    def log_game_state(self, game_state):
        """
        Logs key metrics from the game state.
        """
        state = ColonyState.parse_obj(game_state)
        metrics = {
            "cycle": state.Cycle,
            "num_duplicants": sum(len(world.Duplicants) for world in state.Worlds.values()),
            "total_calories": sum(world.ColonySummary.Calories for world in state.Worlds.values()) if state.Worlds else 0
        }
        if self.use_wandb:
            # wandb.log(metrics)
            print(f"Logging game state to W&B: {metrics}")
        else:
            print(f"Game state at cycle {metrics['cycle']}: {metrics}")

    def log_plan(self, plan):
        """
        Logs the AI's current plan.
        """
        if self.use_wandb:
            # table = wandb.Table(columns=["step", "action", "params"])
            # for i, step in enumerate(plan):
            #     table.add_data(i, step.get("action"), str(step.get("params")))
            # wandb.log({"current_plan": table})
            print(f"Logging plan to W&B: {plan}")
        else:
            print("Current plan:")
            for step in plan:
                print(f"- {step}")

    def create_resource_chart(self, resources):
        fig, ax = plt.subplots()
        ax.bar(list(resources.keys()), list(resources.values()))
        ax.set_xlabel("Resources")
        ax.set_ylabel("Amount")
        ax.set_title("Resource Distribution")
        return wandb.Image(fig)

    def log_performance(self, game_state, success_rate=None):
        state = ColonyState.parse_obj(game_state)
        # Assume using resources from first world
        resources = state.Worlds[list(state.Worlds.keys())[0]].Resources if state.Worlds else {}
        img = self.create_resource_chart(resources)
        if self.use_wandb:
            wandb.log({"Resource Chart": img})
            if success_rate is not None and success_rate < 0.8:
                wandb.alert(title="Low Success Rate", text=f"Success rate dropped to {success_rate}")

def main():
    # Example usage
    visualizer = Visualizer(use_wandb=True)
    
    mock_state = {"Cycle": 10, "TimeInCycle": 0.0, "ResearchState": [], "LatestDailyReport": None, "Worlds": {1: {"WorldId": 1, "WorldName": "Base", "Resources": {"calories": 50000}, "Duplicants": [{"Name": "Stinky", "Stress": 0, "Health": 100}, {"Name": "Hassan", "Stress": 0, "Health": 100}], "ColonySummary": {"DuplicantCount": 2, "Calories": 50000, "CritterCount": {}}}}}
    visualizer.log_game_state(mock_state)

    mock_plan = [
        {"action": "Dig", "params": {"x": 1, "y": 2}},
        {"action": "Build", "params": {"building_type": "cot", "x": 3, "y": 4}}
    ]
    visualizer.log_plan(mock_plan)
    visualizer.log_performance(mock_state)

if __name__ == "__main__":
    main()