# api/endpoints/simulate.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
What-If simulation endpoint.
POST /simulate/what-if → Runs Monte-Carlo agent simulation + Groq LLM explanation.
"""

import json
import time
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.security import get_current_user
from core.groq_client import explain_simulation
from services.data_ingestion import get_all_employees, get_employee_count
from services.simulation_engine import run_simulation
from services.rag_service import rag_service
from models.simulation import SimulationRun
from schemas.request import WhatIfRequest
from schemas.response import SimulationResponse, KPIResult, APIResponse
from utils.logger import get_logger
from database import get_db

router = APIRouter(prefix="/simulate", tags=["Simulation"])
logger = get_logger(__name__)


@router.post(
    "/what-if",
    response_model=APIResponse[SimulationResponse],
    summary="Run a What-If workforce scenario simulation",
    description=(
        "Executes an agent-based Monte-Carlo simulation on the loaded workforce graph, "
        "then calls the Groq LLM for a natural-language explanation of the results.\n\n"
        "**Supported scenarios:**\n"
        "- `switch_to_teams` — Migrate to Microsoft Teams\n"
        "- `switch_to_slack` — Migrate to Slack\n"
        "- `add_ai_copilot` — Deploy AI assistant layer\n"
        "- `hybrid_work_policy` — 3+2 hybrid schedule\n"
        "- `cross_dept_initiative` — Cross-functional collaboration program\n"
        "- `custom` — Any scenario with `custom_description`\n\n"
        "**Target:** Total response time <2 seconds."
    ),
    responses={
        200: {
            "description": "Simulation completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "run_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            "scenario": "switch_to_teams",
                            "kpis": {
                                "productivity_increase": 22.4,
                                "adoption_rate": 0.78,
                                "collaboration_density": 0.061,
                                "engagement_score": 81.3,
                                "cross_department_edges_delta": 0.34,
                            },
                            "llm_explanation": "• Adoption will reach 78% within 6 weeks...",
                            "total_duration_ms": 1240,
                        },
                    }
                }
            },
        },
        400: {"description": "No employees loaded — please ingest CSV first"},
    },
)
async def run_what_if_simulation(
    request: WhatIfRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[SimulationResponse]:
    """
    ## What-If Simulation

    Runs the full simulation pipeline:
    1. Loads employees from DB
    2. Runs N Monte-Carlo agent iterations (default: 200)
    3. Retrieves similar past cases from RAG knowledge base
    4. Calls Groq LLM for explainable analysis
    5. Persists results to DB for later retrieval

    Returns KPIs + AI explanation in <2 seconds.
    """
    t_start = time.perf_counter()

    # Ensure employees are loaded
    count = await get_employee_count(db)
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No employees loaded. Please POST to /ingest/employees with a CSV file first. "
                "Download a sample from GET /ingest/sample-csv."
            ),
        )

    employees = await get_all_employees(db)

    # ── Step 1: Run Monte-Carlo simulation ────────────────────────────────
    logger.info(
        f"Running simulation: {request.scenario}",
        extra={"user": current_user.get("email"), "employees": count},
    )

    sim_result = await run_simulation(
        employees=employees,
        scenario=request.scenario,
        adoption_boost=request.adoption_boost,
        new_tool=request.new_tool,
        monte_carlo_iterations=request.monte_carlo_iterations,
        departments_affected=request.departments_affected,
    )

    kpis = sim_result["kpis"]

    # ── Step 2: RAG retrieval ─────────────────────────────────────────────
    rag_query = (
        request.custom_description
        or f"{request.scenario} {request.new_tool or ''} workforce tool adoption"
    )
    rag_cases = await rag_service.retrieve(
        query=rag_query,
        scenario=request.scenario,
        top_k=3,
    )
    rag_context = rag_service.format_context_for_llm(rag_cases)

    # ── Step 3: Groq LLM explanation ──────────────────────────────────────
    try:
        llm_result = await explain_simulation(
            simulation_results=kpis,
            scenario_name=sim_result["scenario_label"],
            rag_context=rag_context,
        )
        llm_explanation = llm_result["content"]
        llm_duration_ms = llm_result["duration_ms"]
        llm_model = llm_result["model"]
    except RuntimeError as exc:
        logger.warning(f"LLM call failed: {exc}. Using fallback explanation.")
        llm_explanation = _fallback_explanation(kpis, request.scenario)
        llm_duration_ms = 0
        llm_model = "fallback"

    total_duration_ms = int((time.perf_counter() - t_start) * 1000)

    # ── Step 4: Persist to DB (background task) ───────────────────────────
    run_id = sim_result["run_id"]
    background_tasks.add_task(
        _persist_simulation_result,
        db=db,
        run_id=run_id,
        request=request,
        kpis=kpis,
        sim_result=sim_result,
        llm_explanation=llm_explanation,
        llm_model=llm_model,
        llm_duration_ms=llm_duration_ms,
        total_duration_ms=total_duration_ms,
        employee_count=count,
    )

    # ── Build response ────────────────────────────────────────────────────
    kpi_model = KPIResult(
        productivity_increase=kpis["productivity_increase"],
        adoption_rate=kpis["adoption_rate"],
        collaboration_density=kpis["collaboration_density"],
        engagement_score=kpis["engagement_score"],
        cross_department_edges_delta=kpis["cross_department_edges_delta"],
        productivity_std_dev=kpis.get("productivity_std_dev", 0.0),
        adoption_confidence=kpis.get("adoption_confidence", 0.0),
    )

    return APIResponse(
        success=True,
        message=f"Simulation '{request.scenario}' completed in {total_duration_ms}ms.",
        data=SimulationResponse(
            run_id=run_id,
            scenario=request.scenario,
            kpis=kpi_model,
            llm_explanation=llm_explanation,
            llm_model=llm_model,
            llm_duration_ms=llm_duration_ms,
            total_duration_ms=total_duration_ms,
            monte_carlo_iterations=request.monte_carlo_iterations,
            employees_simulated=count,
            rag_cases_used=len(rag_cases),
        ),
        meta={
            "scenario_label": sim_result["scenario_label"],
            "graph_baseline": sim_result.get("graph_baseline", {}),
            "rag_cases_retrieved": len(rag_cases),
        },
    )


@router.get(
    "/history",
    summary="Get past simulation runs",
    tags=["Simulation"],
)
async def get_simulation_history(
    limit: int = 10,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Returns the last N simulation runs from the database."""
    result = await db.execute(
        select(SimulationRun)
        .order_by(SimulationRun.created_at.desc())
        .limit(limit)
    )
    runs = result.scalars().all()

    return {
        "success": True,
        "runs": [
            {
                "run_id": r.run_id,
                "scenario": r.scenario,
                "productivity_increase": r.productivity_increase,
                "adoption_rate": r.adoption_rate,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ],
    }


# ── Background task ───────────────────────────────────────────────────────────

async def _persist_simulation_result(
    db: AsyncSession,
    run_id: str,
    request: WhatIfRequest,
    kpis: dict,
    sim_result: dict,
    llm_explanation: str,
    llm_model: str,
    llm_duration_ms: int,
    total_duration_ms: int,
    employee_count: int,
) -> None:
    """Persists simulation results asynchronously after response is sent."""
    try:
        sim_run = SimulationRun(
            run_id=run_id,
            scenario=request.scenario,
            new_tool=request.new_tool,
            adoption_boost=request.adoption_boost,
            parameters=json.dumps(request.model_dump()),
            productivity_increase=kpis.get("productivity_increase"),
            adoption_rate=kpis.get("adoption_rate"),
            collaboration_density=kpis.get("collaboration_density"),
            engagement_score=kpis.get("engagement_score"),
            kpi_results=json.dumps(kpis),
            llm_explanation=llm_explanation,
            llm_model=llm_model,
            llm_duration_ms=llm_duration_ms,
            total_duration_ms=total_duration_ms,
            employee_count=employee_count,
            monte_carlo_iterations=request.monte_carlo_iterations,
            status="completed",
        )
        db.add(sim_run)
        await db.commit()
        logger.info(f"Simulation {run_id} persisted to DB")
    except Exception as exc:
        logger.error(f"Failed to persist simulation {run_id}: {exc}")


def _fallback_explanation(kpis: dict, scenario: str) -> str:
    """Local fallback explanation when Groq API is unavailable."""
    prod = kpis.get("productivity_increase", 0)
    adopt = kpis.get("adoption_rate", 0) * 100
    return (
        f"• Productivity is projected to increase by {prod:.1f}% following the '{scenario}' rollout.\n"
        f"• Employee adoption rate is estimated at {adopt:.1f}%, driven by high adoption propensity "
        f"in technical departments.\n"
        f"• Cross-department collaboration edges grew by "
        f"{kpis.get('cross_department_edges_delta', 0) * 100:.1f}%, indicating stronger org-wide connectivity.\n\n"
        f"**Recommendation:** Prioritize the top 20% of early adopters as change champions "
        f"to accelerate peer-driven adoption.\n\n"
        f"**Estimated ROI:** Break-even within 12–15 months based on productivity gains."
    )
