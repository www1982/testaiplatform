# Placeholder for planner.py
# This module will be responsible for high-level strategic planning.

from .models import ColonyState, GameEvent

class Planner:
    def __init__(self, game_state: ColonyState):
        self.game_state = game_state
        self.goals = []

    def set_goals(self, goals):
        """
        Sets the high-level goals for the AI.
        Example goals: "achieve_self_sufficiency", "explore_map"
        """
        self.goals = goals
        print(f"Planner goals set to: {self.goals}")

    def create_plan(self):
        """
        Creates a sequence of actions to achieve the goals.
        This is a simplified placeholder. A real implementation would be more complex.
        """
        plan = []
        if "achieve_self_sufficiency" in self.goals:
            plan.extend([
                {"action": "Build", "params": {"building_type": "farm_tile", "x": 5, "y": 5}},
                {"action": "Build", "params": {"building_type": "oxygen_diffuser", "x": 10, "y": 10}},
                {"action": "Research", "params": {"tech_name": "Advanced Farming"}}
            ])
        
        if "explore_map" in self.goals:
            plan.append({"action": "Dig", "params": {"x": 20, "y": 20}})

        # Unified field example in plan creation
        for world in self.game_state.Worlds.values():
            for dup in world.Duplicants:
                if dup.Stress > 50:  # Unified mapping from DuplicantState
                    plan.append({"action": "Assign", "params": {"task": "relax"}})

        return plan

    def handle_event(self, event: GameEvent):
        """
        Handles game events from Mod, adjusting plans accordingly.
        """
        if event.EventType == "Milestone.ResearchComplete":
            tech_id = event.Payload.get("Id") if isinstance(event.Payload, dict) else None
            if tech_id:
                self.goals.append(f"Implement {tech_id}")
                return self.create_plan()
        elif event.EventType == "DuplicantStressHigh":  # Assume this event type
            high_stress = False
            for world in self.game_state.Worlds.values():
                for dup in world.Duplicants:
                    if dup.Stress > 80:
                        high_stress = True
                        break
            if high_stress:
                self.goals.append("Build recreation facility")
                return self.create_plan()
        return []

def main():
    # Example usage
    mock_game_state = ColonyState(Cycle=1, TimeInCycle=0.0, ResearchState=[], LatestDailyReport=None, Worlds={})
    planner = Planner(mock_game_state)
    planner.set_goals(["achieve_self_sufficiency", "explore_map"])
    plan = planner.create_plan()
    print("Generated plan:")
    for step in plan:
        print(step)

if __name__ == "__main__":
    main()