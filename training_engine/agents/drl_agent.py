import numpy as np
import torch
import torch.nn as nn
from typing import Dict, Any, Optional
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import gymnasium as gym
from gymnasium import spaces

from .base_agent import BaseAgent
from oni_api_client import ColonyState


class ColonyEnvironment(gym.Env):
    """Custom Gym environment wrapper for colony state"""
    
    def __init__(self, state_dim: int, action_dim: int):
        super().__init__()
        
        # Define action and observation spaces
        self.action_space = spaces.Discrete(action_dim)
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(state_dim,),
            dtype=np.float32
        )
        
        self.current_state = None
        
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        # Return initial observation
        obs = np.zeros(self.observation_space.shape, dtype=np.float32)
        return obs, {}
        
    def step(self, action):
        # This is a dummy implementation
        # Real step will be handled by DRLAgent
        obs = np.zeros(self.observation_space.shape, dtype=np.float32)
        reward = 0.0
        done = False
        truncated = False
        info = {}
        return obs, reward, done, truncated, info


class DRLAgent(BaseAgent):
    """Deep Reinforcement Learning agent using Stable Baselines3"""
    
    # Define macro actions
    ACTIONS = [
        {"action": "noop", "payload": {}},
        {"action": "Global.Build", "payload": {"buildingId": "Ladder"}},
        {"action": "Global.Build", "payload": {"buildingId": "Tile"}},
        {"action": "Global.Build", "payload": {"buildingId": "Generator"}},
        {"action": "Global.Build", "payload": {"buildingId": "Battery"}},
        {"action": "Global.Build", "payload": {"buildingId": "Wire"}},
        {"action": "Global.Build", "payload": {"buildingId": "Electrolyzer"}},
        {"action": "Global.Build", "payload": {"buildingId": "LiquidPump"}},
        {"action": "Global.Build", "payload": {"buildingId": "GasPump"}},
        {"action": "Global.Build", "payload": {"buildingId": "StorageLocker"}},
        {"action": "Global.Build", "payload": {"buildingId": "MicrobeMusher"}},
        {"action": "Global.Build", "payload": {"buildingId": "Bed"}},
        {"action": "Global.Build", "payload": {"buildingId": "ToiletFlush"}},
        {"action": "Global.Dig", "payload": {}},
        {"action": "Global.SetPriority", "payload": {"priority": 9}},
        {"action": "Global.SetPriority", "payload": {"priority": 5}},
        {"action": "Global.SetPriority", "payload": {"priority": 1}},
    ]
    
    def __init__(self, state_dim: int = 128, learning_rate: float = 3e-4):
        super().__init__(name="DRLAgent")
        
        self.state_dim = state_dim
        self.action_dim = len(self.ACTIONS)
        
        # Create environment
        self.env = DummyVecEnv([lambda: ColonyEnvironment(state_dim, self.action_dim)])
        
        # Create PPO model
        self.model = PPO(
            "MlpPolicy",
            self.env,
            learning_rate=learning_rate,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            verbose=1,
            tensorboard_log="./tensorboard_logs/"
        )
        
        self.current_obs = None
        self.last_action_idx = None
        
    def observe(self, state: ColonyState) -> None:
        """Process and vectorize the colony state"""
        super().observe(state)
        self.current_obs = self._state_to_vector(state)
        
    def _state_to_vector(self, state: ColonyState) -> np.ndarray:
        """Convert ColonyState to a fixed-size feature vector"""
        features = []
        
        # World features
        features.extend([
            float(state.world.cycle),
            state.world.time_of_day,
            state.world.temperature_range[0],
            state.world.temperature_range[1],
            state.world.pressure_range[0],
            state.world.pressure_range[1]
        ])
        
        # Duplicant aggregate features
        if state.duplicants:
            features.extend([
                len(state.duplicants),
                np.mean([d.health for d in state.duplicants]),
                np.mean([d.stress for d in state.duplicants]),
                np.mean([d.calories for d in state.duplicants]),
                np.mean([d.oxygen for d in state.duplicants]),
                np.mean([d.bladder for d in state.duplicants]),
                np.mean([d.stamina for d in state.duplicants]),
                np.min([d.health for d in state.duplicants]),
                np.min([d.calories for d in state.duplicants]),
                np.min([d.oxygen for d in state.duplicants])
            ])
        else:
            features.extend([0] * 10)
            
        # Building counts by type
        building_types = {}
        for building in state.buildings:
            building_types[building.name] = building_types.get(building.name, 0) + 1
            
        # Add counts for important building types
        important_buildings = [
            "Generator", "Battery", "Wire", "Electrolyzer",
            "LiquidPump", "GasPump", "StorageLocker", "Bed",
            "ToiletFlush", "MicrobeMusher"
        ]
        for building_type in important_buildings:
            features.append(float(building_types.get(building_type, 0)))
            
        # Resource features
        resource_dict = {r.name: r for r in state.resources}
        important_resources = ["Oxygen", "Water", "Food", "Power"]
        for resource_name in important_resources:
            if resource_name in resource_dict:
                r = resource_dict[resource_name]
                features.extend([r.available, r.capacity, r.delta_per_cycle])
            else:
                features.extend([0, 0, 0])
                
        # Alert count
        features.append(float(len(state.alerts)))
        
        # Chore statistics
        if state.chores:
            features.extend([
                len(state.chores),
                np.mean([c.priority for c in state.chores]),
                sum(1 for c in state.chores if c.assigned_to is not None)
            ])
        else:
            features.extend([0, 0, 0])
            
        # Pad or truncate to state_dim
        if len(features) < self.state_dim:
            features.extend([0] * (self.state_dim - len(features)))
        else:
            features = features[:self.state_dim]
            
        return np.array(features, dtype=np.float32)
        
    def decide_action(self) -> Dict[str, Any]:
        """Use the DRL model to decide on an action"""
        if self.current_obs is None:
            return {"action": "noop", "payload": {}}
            
        # Get action from model
        action_idx, _ = self.model.predict(self.current_obs, deterministic=False)
        self.last_action_idx = int(action_idx[0])
        
        # Convert to action dictionary
        action = self.ACTIONS[self.last_action_idx].copy()
        
        # Add position for actions that need it
        if action["action"] in ["Global.Build", "Global.Dig", "Global.SetPriority"]:
            # Use a simple heuristic or learned position
            # For now, use random positions near the center
            x = np.random.randint(-30, 30)
            y = np.random.randint(-20, 20)
            action["payload"]["cellX"] = int(x)
            action["payload"]["cellY"] = int(y)
            
        self.last_action = action
        return action
        
    def learn(self, state: ColonyState, action: Dict[str, Any],
              reward: float, next_state: ColonyState, done: bool) -> None:
        """Update the model based on experience"""
        self.episode_reward += reward
        self.total_steps += 1
        
        # Note: With Stable Baselines3, learning happens automatically
        # during model.learn() calls in the training loop
        
    def train(self, total_timesteps: int):
        """Train the model"""
        self.model.learn(total_timesteps=total_timesteps)
        
    def save(self, path: str):
        """Save the model"""
        self.model.save(path)
        
    def load(self, path: str):
        """Load a saved model"""
        self.model = PPO.load(path, env=self.env)