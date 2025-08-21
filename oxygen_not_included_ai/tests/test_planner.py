# Placeholder for test_planner.py
# This file will contain tests for the Planner module.

import pytest
from oxygen_not_included_ai.src.planner import Planner
from oxygen_not_included_ai.src.models import ColonyState

def test_planner_goal_setting():
    planner = Planner(ColonyState(Cycle=0, TimeInCycle=0.0, ResearchState=[], LatestDailyReport=None, Worlds={}))
    goals = ["test_goal_1", "test_goal_2"]
    planner.set_goals(goals)
    assert planner.goals == goals

def test_planner_plan_creation():
    mock_state = ColonyState(Cycle=1, TimeInCycle=0.0, ResearchState=[], LatestDailyReport=None, Worlds={})
    planner = Planner(mock_state)
    planner.set_goals(["achieve_self_sufficiency"])
    plan = planner.create_plan()
    
    # Check that the plan is a list
    assert isinstance(plan, list)
    
    # Check that the plan is not empty for a known goal
    assert len(plan) > 0
    
    # Check for a specific action in the plan
    assert any(p["action"] == "Build" and p["params"]["building_type"] == "farm_tile" for p in plan)

def test_empty_goals_produce_empty_plan():
    planner = Planner(ColonyState(Cycle=0, TimeInCycle=0.0, ResearchState=[], LatestDailyReport=None, Worlds={}))
    planner.set_goals([])
    plan = planner.create_plan()
    assert plan == []

if __name__ == "__main__":
    pytest.main()