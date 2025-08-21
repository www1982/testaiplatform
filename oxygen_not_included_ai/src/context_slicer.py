import asyncio
# Placeholder for context_slicer.py
# This module will extract relevant parts of the game state for different tasks.

from .models import CellInfo

class ContextSlicer:
    def __init__(self, full_game_state):
        self.full_game_state = full_game_state

    def get_context_for_task(self, task):
        """
        Extracts the relevant slice of the game state for a given task.
        For example, a "Build" task might need information about available resources
        and the map area around the build site.

        # TODO: As a low-priority optimization, consider using lru_cache if this
        # function performs expensive grid processing. If caching based on a grid
        # dictionary, ensure it's converted to a hashable type (e.g., a tuple of
        # tuples). If using a JSON string of the grid as a key, ensure
        # sort_keys=True is used for consistent hashing.
        """
        if not task or "action" not in task:
            return {}

        action = task.get("action")
        context = {
            "cycle": self.full_game_state.get("cycle"),
            "duplicants": self.full_game_state.get("duplicants")
        }

        if action == "Build":
            context["resources"] = self.full_game_state.get("resources")
            # In a real implementation, we'd also get map data for the build location
            context["map_slice"] = "..." 
        
        elif action == "Research":
            context["research_progress"] = self.full_game_state.get("research_progress")

    async def extract_duplicant_skills(self):
        """
        Extracts duplicant skills from the game state, compatible with mod format using 'skills' key instead of 'attributes'.
        """
        skills = []
        duplicants = self.full_game_state.get("duplicants", [])
        for dup in duplicants:
            # Mod compatibility: use 'skills' key instead of 'attributes'
            skills.extend(dup.get("skills", []))
        return skills
    
    async def analyze_grid(self, planet_id=None):
        """
        Analyzes the grid, updating elementId matching logic to support mod-specific elements like 'Unobtanium' classified as minerals.
        Uses Pydantic CellInfo for parsing each cell.
        """
        grid_analysis = {"minerals": [], "gases": [], "liquids": [], "other": [], "diseases": [], "temperatures": []}
        mod_element_map = {
            "Unobtanium": "minerals",
            "ModGasExample": "gases",
            "ModLiquidExample": "liquids",
            # Add more mod-specific elements as needed
        }
    
        raw_grid = self.full_game_state.get("grid", [])
        if planet_id is not None:
            raw_grid = [cell for cell in raw_grid if cell.get("planet_id") == planet_id]
        grid = [CellInfo.parse_obj(cell) for cell in raw_grid]
        for cell in grid:
            element_id = cell.ElementId
            if element_id in mod_element_map:
                category = mod_element_map[element_id]
            elif "Gas" in element_id:
                category = "gases"
            elif "Liquid" in element_id:
                category = "liquids"
            elif "Ore" in element_id or "Rock" in element_id:
                category = "minerals"
            else:
                category = "other"
            grid_analysis[category].append(element_id)
            
            # Extract disease
            if cell.DiseaseCount > 0:
                grid_analysis["diseases"].append({
                    "location": cell.Cell,
                    "disease_count": cell.DiseaseCount,
                    "disease_type": cell.DiseaseName or "Unknown"
                })
            
            # Extract temperature
            grid_analysis["temperatures"].append({
                "location": cell.Cell,
                "temperature": cell.Temperature
            })
    
        return grid_analysis

    
    async def _extract_farming_tiles(self, planet_id=None):
        """
        Extracts farming tiles from the grid, filtered by planet_id if provided.
        Uses Pydantic CellInfo for parsing.
        """
        raw_grid = self.full_game_state.get("grid", [])
        if planet_id is not None:
            raw_grid = [cell for cell in raw_grid if cell.get("planet_id") == planet_id]
        grid = [CellInfo.parse_obj(cell) for cell in raw_grid]
        # Placeholder logic for farming tiles
        farming_tiles = [cell for cell in grid if "Farm" in cell.ElementId or "Soil" in cell.ElementId]
        return farming_tiles

    async def _extract_available_space(self, planet_id=None):
        """
        Extracts available space from the grid, filtered by planet_id if provided.
        Uses Pydantic CellInfo for parsing.
        """
        raw_grid = self.full_game_state.get("grid", [])
        if planet_id is not None:
            raw_grid = [cell for cell in raw_grid if cell.get("planet_id") == planet_id]
        grid = [CellInfo.parse_obj(cell) for cell in raw_grid]
        # Placeholder logic for available space
        available_space = [cell for cell in grid if cell.ElementId == "Vacuum" or cell.Mass == 0]
        return available_space

    
    async def _extract_water_sources(self, planet_id=None):
        """
        Extracts water sources from the grid, filtered by planet_id if provided.
        Uses Pydantic CellInfo for parsing.
        """
        raw_grid = self.full_game_state.get("grid", [])
        if planet_id is not None:
            raw_grid = [cell for cell in raw_grid if cell.get("planet_id") == planet_id]
        grid = [CellInfo.parse_obj(cell) for cell in raw_grid]
        # Placeholder logic for water sources
        water_sources = [cell for cell in grid if "Water" in cell.ElementId]
        return water_sources


def main():
    # Example usage
    mock_game_state = {
        "cycle": 5,
        "duplicants": [
            {"name": "Dup1", "skills": ["Digging", "Building"]},
            {"name": "Dup2", "skills": ["Cooking"]},
        ],
        "resources": {"Copper": 1000, "Algae": 500},
        "research_progress": {"Advanced Farming": 0.5},
        "grid": [
            {"Cell": 1, "ElementId": "Unobtanium", "ElementState": "Solid", "Mass": 100, "Temperature": 300, "DiseaseName": None, "DiseaseCount": 0, "GameObjects": []},
            {"Cell": 2, "ElementId": "Oxygen", "ElementState": "Gas", "Mass": 1, "Temperature": 293, "DiseaseName": None, "DiseaseCount": 0, "GameObjects": []},
            {"Cell": 3, "ElementId": "Water", "ElementState": "Liquid", "Mass": 500, "Temperature": 283, "DiseaseName": None, "DiseaseCount": 0, "GameObjects": []},
            {"Cell": 4, "ElementId": "CopperOre", "ElementState": "Solid", "Mass": 200, "Temperature": 300, "DiseaseName": None, "DiseaseCount": 0, "GameObjects": []},
        ]
    }
    slicer = ContextSlicer(mock_game_state)
    
    build_task = {"action": "Build", "params": {"building_type": "battery", "x": 1, "y": 1}}
    build_context = slicer.get_context_for_task(build_task)
    print(f"Context for Build task: {build_context}")

    research_task = {"action": "Research", "params": {"tech_name": "Advanced Farming"}}
    research_context = slicer.get_context_for_task(research_task)
    print(f"Context for Research task: {research_context}")

    skills, grid_analysis = asyncio.run(asyncio.gather(slicer.extract_duplicant_skills(), slicer.analyze_grid()))  # type: ignore
    print(f"Extracted duplicant skills: {skills}")
    print(f"Grid analysis: {grid_analysis}")
    
if __name__ == "__main__":
    main()