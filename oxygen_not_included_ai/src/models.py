from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class TechData(BaseModel):
    Id: str
    Name: str
    Status: str
    ProgressPercent: float


class DailyReportData(BaseModel):
    CycleNumber: int
    OxygenChange: float
    CalorieChange: float
    PowerChange: float


class DuplicantState(BaseModel):
    Name: str
    Stress: float
    Health: float


class ColonySummaryData(BaseModel):
    DuplicantCount: int
    Calories: float
    CritterCount: Dict[str, int]


class WorldState(BaseModel):
    WorldId: int
    WorldName: str
    Resources: Dict[str, float]
    Duplicants: List[DuplicantState]
    ColonySummary: ColonySummaryData


class ColonyState(BaseModel):
    Cycle: int
    TimeInCycle: float
    ResearchState: List[TechData]
    LatestDailyReport: Optional[DailyReportData]
    Worlds: Dict[int, WorldState]


class CellInfo(BaseModel):
    Cell: int
    ElementId: str
    ElementState: str
    Mass: float
    Temperature: float
    DiseaseName: Optional[str]
    DiseaseCount: int
    GameObjects: List[str]


class GameEvent(BaseModel):
    EventType: str
    Cycle: int
    Payload: Any