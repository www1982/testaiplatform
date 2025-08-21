# main.py - Main coordinator for the Oxygen Not Included AI

import asyncio
import os
import json
from dotenv import load_dotenv

from src.game_interface import GameInterface
from src.planner import Planner
from src.context_slicer import ContextSlicer
from src.task_decomposer import TaskDecomposer
from src.executor import Executor
from src.visualizer import Visualizer
from src.models import ColonyState
from tests.mock_data import get_mock_game_state

import argparse
import logging

# Load environment variables
load_dotenv()

class AI_Coordinator:
    def __init__(self):
        self.game_ws_uri = os.getenv("GAME_WS_URI", "ws://localhost:8080")
        self.use_llm = os.getenv("USE_LLM_DECOMPOSER", "false").lower() == "true"
        
        # Initialize components
        self.game_interface = GameInterface(self.game_ws_uri)
        self.visualizer = Visualizer(use_wandb=bool(os.getenv("WANDB_API_KEY")))
        # Other components will be initialized within the main loop
        
    async def run(self):
        # await self.game_interface.connect() # Uncomment when connecting to a real game
        
        cycle = 0
        while True:
            print(f"\n--- Cycle {cycle} ---")
            
            # 1. Get game state
            # game_state = await self.game_interface.get_game_state()
            game_state = get_mock_game_state(cycle) # Using mock data for now
            self.visualizer.log_game_state(game_state)
            
            # 2. Strategic Planner
            planner = Planner(ColonyState.parse_obj(game_state))
            planner.set_goals(["achieve_self_sufficiency", "explore_map"]) # Example goals
            high_level_plan = planner.create_plan()
            self.visualizer.log_plan(high_level_plan)
            
            # Initialize components that need the current game state
            context_slicer = ContextSlicer(game_state)
            task_decomposer = TaskDecomposer(use_llm=self.use_llm)
            executor = Executor(self.game_interface, "config/actions.yaml")

            # 3. Execute the plan
            for task in high_level_plan:
                # 3a. Get context for the task
                context = context_slicer.get_context_for_task(task)
                
                # 3b. Decompose task if necessary
                decomposed_actions = task_decomposer.decompose_task(task, context)
                
                # 3c. Execute actions
                for action in decomposed_actions:
                    await executor.execute_action(action)
            
            # Wait for the next cycle
            await asyncio.sleep(5) # Placeholder for waiting for the next game tick
            cycle += 1
            if cycle > 2: # Stop after a few cycles for this example
                print("\nSimulation finished.")
                break

async def main():
    coordinator = AI_Coordinator()
    await coordinator.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', default=False)
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    asyncio.run(main())