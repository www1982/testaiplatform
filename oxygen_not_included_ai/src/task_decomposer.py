# oxygen_not_included_ai/src/task_decomposer.py
import numpy as np
from collections import deque

import torch
import json

from pydantic import BaseModel
from typing import Dict, Any

class Action(BaseModel):
    action: str
    params: Dict[str, Any]

class TaskDecomposer:
    def __init__(self, use_llm=False, use_custom_model=False):
        self.use_llm = use_llm
        self.use_custom_model = use_custom_model

    def decompose_task(self, high_level_task, context_slice, use_custom_model=None):
        """
        Decomposes a high-level task into a sequence of primitive actions.
        """
        if use_custom_model is None:
            use_custom_model = self.use_custom_model
        if use_custom_model:
            model = torch.load('model.pth')
            prediction = model.predict(context_slice)
            return json.loads(prediction)
        if self.use_llm:
            actions = self._llm_decompose(high_level_task, context_slice)
        else:
            actions = self._rule_based_decompose(high_level_task, context_slice)
        
        # Validate actions using Pydantic
        validated_actions = []
        for act in actions:
            try:
                validated_actions.append(Action.parse_obj(act).dict())
            except Exception as e:
                print(f"Invalid action: {act}, error: {e}")
        return validated_actions

    def _rule_based_decompose(self, task, context_slice):
        action = task.get("action")
        
        if action == "Build":
            return self._handle_build_task(task, context_slice)
        
        # Default: no decomposition needed, just pass through
        return [task]

    def _handle_build_task(self, task, context_slice):
        params = task.get("params", {})
        building_type = params.get("building_type")
        
        if not building_type:
            print("Error: building_type not specified in Build task.")
            return []

        # In a real scenario, dimensions would come from a config file.
        building_dims = {"oxygen_diffuser": (2, 2)}
        width, height = building_dims.get(building_type, (1, 1))

        grid = context_slice.get('data', {}).get('grid')
        if grid is None:
            print("Error: grid not found in context_slice.")
            return []

        location = None
        prep_actions = []
        
        # Check if a target location is specified in the task
        if "x" in params and "y" in params:
            x, y = params["x"], params["y"]
            
            # Check the target location
            current_prep_actions = self._prepare_space(x, y, width, height, grid)
            
            if current_prep_actions is not None:
                location = (x, y)
                prep_actions = current_prep_actions
            else:
                # Target location is blocked, try adjacent spots
                print(f"Warning: Target location ({x}, {y}) for {building_type} is not usable. Trying adjacent locations.")
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    adj_x, adj_y = x + dx, y + dy
                    adj_prep_actions = self._prepare_space(adj_x, adj_y, width, height, grid)
                    if adj_prep_actions is not None:
                        location = (adj_x, adj_y)
                        prep_actions = adj_prep_actions
                        print(f"Info: Found alternative location at {location}.")
                        break
        else:
            # No location specified, find a suitable one
            location, prep_actions = self._find_suitable_location_2d(width, height, grid)

        if location:
            x, y = location
            build_action = {
                "action": "Build",
                "params": {"building_type": building_type, "x": x, "y": y}
            }
            # Return prerequisite actions (like Dig) followed by the Build action
            return prep_actions + [build_action]
        
        print(f"Error: No suitable location found for {building_type}.")
        return []

    def _find_suitable_location_2d(self, width, height, grid):
        """
        Finds a suitable location for a building by iterating through the grid.
        A suitable location is one that is either clear or can be cleared by digging.
        """
        grid_height, grid_width = grid.shape
        
        for x in range(grid_width - width + 1):
            for y in range(grid_height - height + 1):
                # Check if the space can be prepared (is not permanently blocked)
                prep_actions = self._prepare_space(x, y, width, height, grid)
                if prep_actions is not None:
                    return (x, y), prep_actions
        return None, []

    def _validate_space_bfs(self, start_x, start_y, width, height, grid, max_cells=100):
        """
        Validates the space using BFS to check connectivity or reachability, with a cell limit for performance.
        Returns True if valid within limit, False otherwise.
        """
        grid_height, grid_width = grid.shape
        if start_x + width > grid_width or start_y + height > grid_height:
            return False
        visited = np.zeros((grid_height, grid_width), dtype=bool)
        queue = deque([(start_x, start_y)])
        visited[start_y, start_x] = True
        explored = 1
    
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
        while queue:
            x, y = queue.popleft()
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (0 <= nx < grid_width and 0 <= ny < grid_height and not visited[ny, nx] and
                    start_x <= nx < start_x + width and start_y <= ny < start_y + height):
                    visited[ny, nx] = True
                    queue.append((nx, ny))
                    explored += 1
                    if explored > max_cells:
                        return False
        return True
    
    def _prepare_space(self, start_x, start_y, width, height, grid):
        """
        Checks if a space is clear or can be cleared by digging.
        Returns a list of prerequisite actions (e.g., Dig commands).
        Returns None if the space is permanently blocked (e.g., out of bounds).
        """
        grid_height, grid_width = grid.shape
        if not (0 <= start_x and start_x + width <= grid_width and 0 <= start_y and start_y + height <= grid_height):
            return None  # Out of bounds
    
        prep_actions = []
        for i in range(width):
            for j in range(height):
                x, y = start_x + i, start_y + j
                # Assuming grid contains material IDs. 0 is Vacuum.
                if grid[start_y + j, start_x + i] != 0:
                    return None  # Skip if not empty
        
        # Add BFS validation for performance
        if not self._validate_space_bfs(start_x, start_y, width, height, grid):
            return None
        
        return prep_actions
        
    def _llm_decompose(self, task, context):
        return [task] # Placeholder

def main():
    decomposer = TaskDecomposer(use_llm=False)
    
    mock_grid = np.zeros((20, 20), dtype=int)
    mock_grid[5:8, 5:8] = 1  # An obstacle
    
    mock_context_slice = {
        "data": {
            "grid": mock_grid
        }
    }
    
    high_level_task = {
        "action": "Build",
        "params": {"building_type": "oxygen_diffuser"}
    }
    
    decomposed_actions = decomposer.decompose_task(high_level_task, mock_context_slice)
    print("Decomposed actions:")
    if decomposed_actions:
        for action in decomposed_actions:
            print(action)
    else:
        print("Decomposition failed.")

if __name__ == "__main__":
    main()