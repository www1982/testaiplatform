from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import numpy as np

from oni_api_client import ColonyState


class BaseAgent(ABC):
    """Abstract base class for all AI agents"""
    
    def __init__(self, name: str = "BaseAgent"):
        self.name = name
        self.last_state: Optional[ColonyState] = None
        self.last_action: Optional[Dict[str, Any]] = None
        self.episode_reward = 0.0
        self.total_steps = 0
        
    @abstractmethod
    def observe(self, state: ColonyState) -> None:
        """
        Process and store the current colony state
        
        Args:
            state: Current colony state
        """
        self.last_state = state
        
    @abstractmethod
    def decide_action(self) -> Dict[str, Any]:
        """
        Decide on the next action to take
        
        Returns:
            Dictionary describing the action, e.g.:
            {"action": "Global.Build", "payload": {"buildingId": "Ladder", "cellX": 10, "cellY": 20}}
        """
        pass
        
    @abstractmethod
    def learn(self, state: ColonyState, action: Dict[str, Any], 
              reward: float, next_state: ColonyState, done: bool) -> None:
        """
        Learn from the experience
        
        Args:
            state: Previous state
            action: Action taken
            reward: Reward received
            next_state: Resulting state
            done: Whether episode is done
        """
        pass
        
    def reset(self) -> None:
        """Reset agent for new episode"""
        self.last_state = None
        self.last_action = None
        self.episode_reward = 0.0
        
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            "name": self.name,
            "total_steps": self.total_steps,
            "episode_reward": self.episode_reward
        }