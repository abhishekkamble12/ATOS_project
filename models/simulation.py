# models/simulation.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
SQLAlchemy ORM model for Simulation runs.
Stores every What-If scenario with its inputs, KPI outputs, and LLM explanation.
"""

import json
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, JSON

from models.employee import Base


class SimulationRun(Base):
    """
    Persists one complete What-If simulation execution.

    Fields:
        scenario       : Scenario key (e.g. 'switch_to_teams', 'add_ai_copilot')
        parameters     : JSON blob of input parameters
        kpi_results    : JSON blob of computed KPIs
        llm_explanation: Groq LLM natural-language analysis
        duration_ms    : Total server-side computation time
        status         : 'completed' | 'failed' | 'running'
    """

    __tablename__ = "simulation_runs"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    run_id: str = Column(String(36), unique=True, nullable=False, index=True)  # UUID

    # ── Inputs ────────────────────────────────────────────────────────────
    scenario: str = Column(String(100), nullable=False)
    new_tool: str | None = Column(String(100), nullable=True)
    adoption_boost: float | None = Column(Float, nullable=True)
    # Stores full JSON parameter dict for reproducibility
    parameters: str = Column(Text, nullable=False, default="{}")

    # ── Outputs ───────────────────────────────────────────────────────────
    productivity_increase: float | None = Column(Float, nullable=True)
    adoption_rate: float | None = Column(Float, nullable=True)
    collaboration_density: float | None = Column(Float, nullable=True)
    engagement_score: float | None = Column(Float, nullable=True)

    # ── Raw JSON results (full graph snapshot etc.) ────────────────────────
    kpi_results: str | None = Column(Text, nullable=True)

    # ── LLM analysis ──────────────────────────────────────────────────────
    llm_explanation: str | None = Column(Text, nullable=True)
    llm_model: str | None = Column(String(100), nullable=True)
    llm_duration_ms: int | None = Column(Integer, nullable=True)

    # ── Feedback loop (post-rollout actuals) ─────────────────────────────
    actual_productivity_increase: float | None = Column(Float, nullable=True)
    actual_adoption_rate: float | None = Column(Float, nullable=True)
    feedback_llm_analysis: str | None = Column(Text, nullable=True)

    # ── Metadata ──────────────────────────────────────────────────────────
    total_duration_ms: int | None = Column(Integer, nullable=True)
    employee_count: int | None = Column(Integer, nullable=True)
    monte_carlo_iterations: int | None = Column(Integer, nullable=True)
    status: str = Column(String(20), default="running")

    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_parameters(self) -> dict:
        """Deserializes the parameters JSON field."""
        return json.loads(self.parameters or "{}")

    def get_kpi_results(self) -> dict:
        """Deserializes the kpi_results JSON field."""
        return json.loads(self.kpi_results or "{}")

    def __repr__(self) -> str:
        return (
            f"<SimulationRun run_id={self.run_id!r} scenario={self.scenario!r} "
            f"productivity_increase={self.productivity_increase}>"
        )
