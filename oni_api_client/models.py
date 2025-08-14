from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


@dataclass
class Vector2:
    x: float
    y: float
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Vector2':
        return cls(x=data.get('x', 0), y=data.get('y', 0))


@dataclass
class CellInfo:
    position: Vector2
    temperature: float
    pressure: float
    mass: float
    element: str
    solid: bool
    liquid: bool
    gas: bool
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CellInfo':
        return cls(
            position=Vector2.from_dict(data.get('position', {})),
            temperature=data.get('temperature', 0),
            pressure=data.get('pressure', 0),
            mass=data.get('mass', 0),
            element=data.get('element', ''),
            solid=data.get('solid', False),
            liquid=data.get('liquid', False),
            gas=data.get('gas', False)
        )


@dataclass
class BuildingInfo:
    id: str
    name: str
    position: Vector2
    enabled: bool
    health: float
    max_health: float
    temperature: float
    storage: Dict[str, float] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BuildingInfo':
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            position=Vector2.from_dict(data.get('position', {})),
            enabled=data.get('enabled', False),
            health=data.get('health', 0),
            max_health=data.get('maxHealth', 100),
            temperature=data.get('temperature', 0),
            storage=data.get('storage', {})
        )


@dataclass
class ChoreStatusInfo:
    id: str
    name: str
    priority: int
    assigned_to: Optional[str]
    progress: float
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChoreStatusInfo':
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            priority=data.get('priority', 0),
            assigned_to=data.get('assignedTo'),
            progress=data.get('progress', 0)
        )


@dataclass
class DuplicantState:
    id: str
    name: str
    position: Vector2
    health: float
    stress: float
    calories: float
    oxygen: float
    bladder: float
    stamina: float
    current_task: Optional[str]
    skills: List[str]
    traits: List[str]
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DuplicantState':
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            position=Vector2.from_dict(data.get('position', {})),
            health=data.get('health', 100),
            stress=data.get('stress', 0),
            calories=data.get('calories', 4000),
            oxygen=data.get('oxygen', 100),
            bladder=data.get('bladder', 0),
            stamina=data.get('stamina', 100),
            current_task=data.get('currentTask'),
            skills=data.get('skills', []),
            traits=data.get('traits', [])
        )


@dataclass
class ResourceInfo:
    name: str
    available: float
    capacity: float
    delta_per_cycle: float
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ResourceInfo':
        return cls(
            name=data.get('name', ''),
            available=data.get('available', 0),
            capacity=data.get('capacity', 0),
            delta_per_cycle=data.get('deltaPerCycle', 0)
        )


@dataclass
class WorldState:
    cycle: int
    time_of_day: float
    world_seed: int
    asteroid_name: str
    temperature_range: tuple
    pressure_range: tuple
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WorldState':
        temp_range = data.get('temperatureRange', [0, 0])
        pressure_range = data.get('pressureRange', [0, 0])
        return cls(
            cycle=data.get('cycle', 0),
            time_of_day=data.get('timeOfDay', 0),
            world_seed=data.get('worldSeed', 0),
            asteroid_name=data.get('asteroidName', ''),
            temperature_range=(temp_range[0], temp_range[1]) if len(temp_range) >= 2 else (0, 0),
            pressure_range=(pressure_range[0], pressure_range[1]) if len(pressure_range) >= 2 else (0, 0)
        )


@dataclass
class ColonyState:
    timestamp: datetime
    world: WorldState
    duplicants: List[DuplicantState]
    buildings: List[BuildingInfo]
    resources: List[ResourceInfo]
    chores: List[ChoreStatusInfo]
    cells: List[CellInfo]
    alerts: List[str]
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ColonyState':
        return cls(
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            world=WorldState.from_dict(data.get('world', {})),
            duplicants=[DuplicantState.from_dict(d) for d in data.get('duplicants', [])],
            buildings=[BuildingInfo.from_dict(b) for b in data.get('buildings', [])],
            resources=[ResourceInfo.from_dict(r) for r in data.get('resources', [])],
            chores=[ChoreStatusInfo.from_dict(c) for c in data.get('chores', [])],
            cells=[CellInfo.from_dict(c) for c in data.get('cells', [])],
            alerts=data.get('alerts', [])
        )
    
    def to_dict(self) -> dict:
        """Convert state back to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'world': {
                'cycle': self.world.cycle,
                'timeOfDay': self.world.time_of_day,
                'worldSeed': self.world.world_seed,
                'asteroidName': self.world.asteroid_name,
                'temperatureRange': list(self.world.temperature_range),
                'pressureRange': list(self.world.pressure_range)
            },
            'duplicants': [
                {
                    'id': d.id,
                    'name': d.name,
                    'position': {'x': d.position.x, 'y': d.position.y},
                    'health': d.health,
                    'stress': d.stress,
                    'calories': d.calories,
                    'oxygen': d.oxygen,
                    'bladder': d.bladder,
                    'stamina': d.stamina,
                    'currentTask': d.current_task,
                    'skills': d.skills,
                    'traits': d.traits
                } for d in self.duplicants
            ],
            'buildings': [
                {
                    'id': b.id,
                    'name': b.name,
                    'position': {'x': b.position.x, 'y': b.position.y},
                    'enabled': b.enabled,
                    'health': b.health,
                    'maxHealth': b.max_health,
                    'temperature': b.temperature,
                    'storage': b.storage
                } for b in self.buildings
            ],
            'resources': [
                {
                    'name': r.name,
                    'available': r.available,
                    'capacity': r.capacity,
                    'deltaPerCycle': r.delta_per_cycle
                } for r in self.resources
            ],
            'chores': [
                {
                    'id': c.id,
                    'name': c.name,
                    'priority': c.priority,
                    'assignedTo': c.assigned_to,
                    'progress': c.progress
                } for c in self.chores
            ],
            'cells': [
                {
                    'position': {'x': c.position.x, 'y': c.position.y},
                    'temperature': c.temperature,
                    'pressure': c.pressure,
                    'mass': c.mass,
                    'element': c.element,
                    'solid': c.solid,
                    'liquid': c.liquid,
                    'gas': c.gas
                } for c in self.cells
            ],
            'alerts': self.alerts
        }