import numpy as np
from typing import Callable
from oni_api_client import ColonyState


def survival_reward(state: ColonyState, prev_state: ColonyState = None) -> float:
    """
    Basic survival reward function
    
    Rewards:
    - Keeping duplicants alive and healthy
    - Maintaining resources
    - Avoiding alerts
    """
    reward = 0.0
    
    if not state.duplicants:
        return -100.0  # Colony wiped out
        
    # Health and well-being
    avg_health = np.mean([d.health for d in state.duplicants])
    avg_stress = np.mean([d.stress for d in state.duplicants])
    avg_calories = np.mean([d.calories for d in state.duplicants])
    avg_oxygen = np.mean([d.oxygen for d in state.duplicants])
    
    reward += avg_health / 100.0  # 0 to 1
    reward += (100 - avg_stress) / 100.0  # 0 to 1
    reward += min(avg_calories / 4000.0, 1.0)  # 0 to 1
    reward += avg_oxygen / 100.0  # 0 to 1
    
    # Penalty for alerts
    reward -= len(state.alerts) * 0.1
    
    # Bonus for cycle progression
    reward += state.world.cycle * 0.01
    
    # Compare with previous state if available
    if prev_state:
        # Reward for improving health
        prev_avg_health = np.mean([d.health for d in prev_state.duplicants])
        if avg_health > prev_avg_health:
            reward += 0.5
            
        # Penalty for losing duplicants
        if len(state.duplicants) < len(prev_state.duplicants):
            reward -= 10.0
            
    return reward


def efficiency_reward(state: ColonyState, prev_state: ColonyState = None) -> float:
    """
    Reward function focused on colony efficiency
    
    Rewards:
    - Resource production rates
    - Building utilization
    - Task completion
    """
    reward = 0.0
    
    # Resource production efficiency
    for resource in state.resources:
        if resource.delta_per_cycle > 0:
            reward += min(resource.delta_per_cycle / 100.0, 1.0)
        elif resource.delta_per_cycle < 0 and resource.available < resource.capacity * 0.2:
            # Penalty for depleting critical resources
            reward -= 0.5
            
    # Building efficiency
    active_buildings = sum(1 for b in state.buildings if b.enabled)
    total_buildings = len(state.buildings)
    if total_buildings > 0:
        reward += (active_buildings / total_buildings) * 2.0
        
    # Chore completion rate
    if state.chores:
        assigned_chores = sum(1 for c in state.chores if c.assigned_to is not None)
        completion_rate = assigned_chores / len(state.chores)
        reward += completion_rate * 2.0
        
    return reward


def expansion_reward(state: ColonyState, prev_state: ColonyState = None) -> float:
    """
    Reward function focused on colony expansion
    
    Rewards:
    - Building new structures
    - Exploring new areas
    - Increasing colony capacity
    """
    reward = 0.0
    
    # Reward for number of buildings
    reward += len(state.buildings) * 0.1
    
    # Reward for diverse building types
    building_types = set(b.name for b in state.buildings)
    reward += len(building_types) * 0.5
    
    # Compare with previous state
    if prev_state:
        # Reward for new buildings
        new_buildings = len(state.buildings) - len(prev_state.buildings)
        if new_buildings > 0:
            reward += new_buildings * 2.0
            
        # Reward for new building types
        prev_types = set(b.name for b in prev_state.buildings)
        new_types = building_types - prev_types
        reward += len(new_types) * 5.0
        
    # Capacity bonuses
    for resource in state.resources:
        if resource.capacity > 0:
            reward += np.log(resource.capacity + 1) * 0.01
            
    return reward


def balanced_reward(state: ColonyState, prev_state: ColonyState = None) -> float:
    """
    Balanced reward function combining multiple objectives
    """
    survival = survival_reward(state, prev_state)
    efficiency = efficiency_reward(state, prev_state)
    expansion = expansion_reward(state, prev_state)
    
    # Weighted combination
    return 0.5 * survival + 0.3 * efficiency + 0.2 * expansion


# Registry of available reward functions
REWARD_FUNCTIONS = {
    "survival": survival_reward,
    "efficiency": efficiency_reward,
    "expansion": expansion_reward,
    "balanced": balanced_reward
}


def get_reward_function(name: str) -> Callable:
    """Get a reward function by name"""
    if name not in REWARD_FUNCTIONS:
        raise ValueError(f"Unknown reward function: {name}")
    return REWARD_FUNCTIONS[name]