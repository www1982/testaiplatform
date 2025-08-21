# Placeholder for mock_data.py
# This file contains mock game state data for testing purposes.

def get_mock_game_state(cycle=1):
    """
    Returns a dictionary representing a mock game state.
    """
    return {
        "cycle": cycle,
        "planet_id": 0,
        "duplicants": [
            {"name": "Stinky", "skills": {"Digging": 5}, "stress": 10},
            {"name": "Hassan", "skills": {"Building": 3}, "stress": 5},
            {"name": "Meep", "skills": {"Research": 7}, "stress": 0},
        ],
        "resources": {
            "Copper": 5000,
            "Algae": 2000,
            "Water": 10000,
            "Calories": 150000,
        },
        "buildings": [
            {"type": "PrintingPod", "x": 0, "y": 0},
            {"type": "RationBox", "x": 2, "y": 0},
        ],
        "research_progress": {
            "BasicFarming": 1.0, # Completed
            "AdvancedResearch": 0.25,
        },
        "map_tiles": [
            # A real implementation would have a more detailed map representation
            {"x": 0, "y": 0, "element": "Sandstone"},
            {"x": 1, "y": 0, "element": "CopperOre"},
        ]
    }

if __name__ == "__main__":
    # Print an example of the mock data
    mock_state = get_mock_game_state(cycle=10)
    import json
    print(json.dumps(mock_state, indent=2))