from typing import Dict, Any, List
import random

from .base_agent import BaseAgent
from oni_api_client import ColonyState


class RuleBasedAgent(BaseAgent):
    """Simple rule-based agent for baseline performance"""
    
    def __init__(self):
        super().__init__(name="RuleBasedAgent")
        self.action_cooldown = {}
        self.priority_queue = []
        
    def observe(self, state: ColonyState) -> None:
        """Analyze state and update priorities"""
        super().observe(state)
        self._update_priorities(state)
        
    def _update_priorities(self, state: ColonyState) -> None:
        """Update action priorities based on colony needs"""
        self.priority_queue.clear()
        
        # Check oxygen levels
        avg_oxygen = sum(d.oxygen for d in state.duplicants) / len(state.duplicants) if state.duplicants else 100
        if avg_oxygen < 80:
            self.priority_queue.append(("oxygen", avg_oxygen))
            
        # Check food
        food_available = sum(r.available for r in state.resources if 'food' in r.name.lower())
        duplicant_count = len(state.duplicants)
        if duplicant_count > 0 and food_available < duplicant_count * 1000:
            self.priority_queue.append(("food", food_available))
            
        # Check power
        power_production = sum(1 for b in state.buildings if 'generator' in b.name.lower())
        if power_production < 2:
            self.priority_queue.append(("power", power_production))
            
        # Check water
        water_available = sum(r.available for r in state.resources if r.name.lower() == 'water')
        if water_available < 1000:
            self.priority_queue.append(("water", water_available))
            
        # Sort by urgency (lower value = more urgent)
        self.priority_queue.sort(key=lambda x: x[1])
        
    def decide_action(self) -> Dict[str, Any]:
        """Make decision based on rules and priorities"""
        if not self.last_state or not self.priority_queue:
            return {"action": "noop", "payload": {}}
            
        # Get highest priority need
        need, value = self.priority_queue[0]
        
        # Check cooldown
        if need in self.action_cooldown and self.action_cooldown[need] > 0:
            self.action_cooldown[need] -= 1
            return {"action": "noop", "payload": {}}
            
        # Decide action based on need
        action = self._get_action_for_need(need)
        
        # Set cooldown
        if action["action"] != "noop":
            self.action_cooldown[need] = 10  # Wait 10 steps before trying again
            
        self.last_action = action
        return action
        
    def _get_action_for_need(self, need: str) -> Dict[str, Any]:
        """Get specific action for a need"""
        # Find a suitable location (simplified)
        x = random.randint(-50, 50)
        y = random.randint(-30, 30)
        
        if need == "oxygen":
            return {
                "action": "Global.Build",
                "payload": {
                    "buildingId": "Electrolyzer",
                    "cellX": x,
                    "cellY": y
                }
            }
        elif need == "food":
            return {
                "action": "Global.Build",
                "payload": {
                    "buildingId": "MicrobeMusher",
                    "cellX": x,
                    "cellY": y
                }
            }
        elif need == "power":
            return {
                "action": "Global.Build",
                "payload": {
                    "buildingId": "Generator",
                    "cellX": x,
                    "cellY": y
                }
            }
        elif need == "water":
            # Dig to find water
            return {
                "action": "Global.Dig",
                "payload": {
                    "cellX": x,
                    "cellY": y - 10  # Dig downward
                }
            }
        else:
            return {"action": "noop", "payload": {}}
            
    def learn(self, state: ColonyState, action: Dict[str, Any],
              reward: float, next_state: ColonyState, done: bool) -> None:
        """Rule-based agent doesn't learn, but track statistics"""
        self.episode_reward += reward
        self.total_steps += 1
        
        # Could adjust rules based on success/failure rates here
        pass