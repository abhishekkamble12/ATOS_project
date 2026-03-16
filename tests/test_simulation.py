# tests/test_simulation.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
Simulation engine and API endpoint tests.
Covers: Monte-Carlo output ranges, KPI validity, scenario variety.
"""

import pytest
from httpx import AsyncClient

from models.employee import Employee
from services.simulation_engine import run_simulation, SCENARIO_PRESETS
from services.graph_builder import build_collaboration_graph
from utils.sample_data import get_sample_employees_dicts


def _make_employee(data: dict) -> Employee:
    """Helper: create an Employee ORM instance from a dict."""
    return Employee(
        employee_id=data["employee_id"],
        name=data["name"],
        role=data["role"],
        department=data["department"],
        current_tool=data["current_tool"],
        adoption_propensity=data["adoption_propensity"],
        productivity_base=data["productivity_base"],
    )


@pytest.fixture
def sample_employees() -> list[Employee]:
    return [_make_employee(d) for d in get_sample_employees_dicts()]


# ── Unit tests: Simulation Engine ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_simulation_returns_all_kpis(sample_employees):
    """Simulation must return all 5 KPI fields."""
    result = await run_simulation(
        employees=sample_employees,
        scenario="switch_to_teams",
        adoption_boost=0.25,
        monte_carlo_iterations=50,  # fewer for speed in tests
    )
    kpis = result["kpis"]
    assert "productivity_increase" in kpis
    assert "adoption_rate" in kpis
    assert "collaboration_density" in kpis
    assert "engagement_score" in kpis
    assert "cross_department_edges_delta" in kpis


@pytest.mark.asyncio
async def test_simulation_adoption_rate_range(sample_employees):
    """Adoption rate must be between 0 and 1."""
    result = await run_simulation(
        employees=sample_employees,
        scenario="add_ai_copilot",
        adoption_boost=0.30,
        monte_carlo_iterations=50,
    )
    rate = result["kpis"]["adoption_rate"]
    assert 0.0 <= rate <= 1.0, f"Adoption rate out of range: {rate}"


@pytest.mark.asyncio
async def test_simulation_productivity_positive_with_boost(sample_employees):
    """High adoption boost should produce a positive productivity increase."""
    result = await run_simulation(
        employees=sample_employees,
        scenario="switch_to_teams",
        adoption_boost=0.5,  # very high boost
        monte_carlo_iterations=100,
    )
    prod = result["kpis"]["productivity_increase"]
    assert prod > 0, f"Expected positive productivity, got: {prod}"


@pytest.mark.asyncio
async def test_simulation_engagement_score_range(sample_employees):
    """Engagement score must be between 0 and 100."""
    result = await run_simulation(
        employees=sample_employees,
        scenario="hybrid_work_policy",
        adoption_boost=0.20,
        monte_carlo_iterations=50,
    )
    eng = result["kpis"]["engagement_score"]
    assert 0.0 <= eng <= 100.0, f"Engagement out of range: {eng}"


@pytest.mark.asyncio
async def test_all_scenarios_execute(sample_employees):
    """All 5 built-in scenarios must complete without error."""
    for scenario_key in SCENARIO_PRESETS.keys():
        result = await run_simulation(
            employees=sample_employees,
            scenario=scenario_key,
            adoption_boost=0.20,
            monte_carlo_iterations=20,
        )
        assert result["kpis"]["adoption_rate"] >= 0


@pytest.mark.asyncio
async def test_simulation_raises_on_empty_employees():
    """Simulation with empty employee list should raise ValueError."""
    with pytest.raises(ValueError, match="No employees available"):
        await run_simulation(
            employees=[],
            scenario="switch_to_teams",
            adoption_boost=0.25,
        )


@pytest.mark.asyncio
async def test_simulation_department_filter(sample_employees):
    """Department filter should limit simulation to specified departments."""
    result = await run_simulation(
        employees=sample_employees,
        scenario="switch_to_teams",
        adoption_boost=0.25,
        monte_carlo_iterations=30,
        departments_affected=["Engineering"],
    )
    assert result["simulation_meta"]["employees_simulated"] > 0
    # Engineering has 10 employees in sample data
    assert result["simulation_meta"]["employees_simulated"] == 10


# ── Integration tests: Simulate API ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_simulate_without_employees_returns_400(
    client: AsyncClient, auth_headers: dict
):
    """Simulation endpoint returns 400 if no employees are loaded."""
    response = await client.post(
        "/simulate/what-if",
        json={
            "scenario": "switch_to_teams",
            "new_tool": "Teams",
            "adoption_boost": 0.25,
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "No employees loaded" in response.json()["detail"]


@pytest.mark.asyncio
async def test_simulate_after_ingest(
    client: AsyncClient, auth_headers: dict
):
    """Full pipeline: ingest CSV → simulate → check KPIs in response."""
    from utils.sample_data import generate_sample_csv_bytes

    # Step 1: Ingest sample employees
    csv_bytes = generate_sample_csv_bytes()
    ingest_response = await client.post(
        "/ingest/employees",
        files={"file": ("employees.csv", csv_bytes, "text/csv")},
        headers=auth_headers,
    )
    assert ingest_response.status_code == 200
    assert ingest_response.json()["data"]["employees_loaded"] > 0

    # Step 2: Run simulation
    sim_response = await client.post(
        "/simulate/what-if",
        json={
            "scenario": "switch_to_teams",
            "new_tool": "Teams",
            "adoption_boost": 0.25,
            "monte_carlo_iterations": 50,
        },
        headers=auth_headers,
    )
    assert sim_response.status_code == 200

    data = sim_response.json()["data"]
    assert "run_id" in data
    assert "kpis" in data
    assert 0.0 <= data["kpis"]["adoption_rate"] <= 1.0
    assert data["total_duration_ms"] < 5000   # must complete within 5 seconds
