# schemas/response.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
Pydantic v2 response schemas.
Consistent envelope format: { success, data, message, meta }
"""

from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Generic API envelope ──────────────────────────────────────────────────────

class APIResponse(BaseModel, Generic[T]):
    """Standard response envelope for all endpoints."""

    success: bool = True
    message: str = "OK"
    data: T | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


# ── Auth ──────────────────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    """JWT login response."""

    access_token: str = Field(..., examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."])
    token_type: str = Field(default="bearer")
    expires_in_minutes: int = Field(..., examples=[60])
    user_email: str = Field(..., examples=["admin@atos.com"])


# ── Ingest ────────────────────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    """Response after employee CSV ingestion."""

    employees_loaded: int = Field(..., examples=[150])
    departments_found: list[str] = Field(..., examples=[["Engineering", "HR", "Sales"]])
    graph_nodes: int = Field(..., examples=[150])
    graph_edges: int = Field(..., examples=[423])
    message: str = Field(default="Employees successfully ingested and graph built.")


# ── KPIs ──────────────────────────────────────────────────────────────────────

class KPIResult(BaseModel):
    """Core simulation KPI output block."""

    productivity_increase: float = Field(
        ...,
        description="Simulated productivity change (%)",
        examples=[22.4],
    )
    adoption_rate: float = Field(
        ...,
        description="Fraction of employees who adopted the new tool (0–1)",
        examples=[0.78],
    )
    collaboration_density: float = Field(
        ...,
        description="Ratio of actual edges to maximum possible edges in graph",
        examples=[0.61],
    )
    engagement_score: float = Field(
        ...,
        description="Composite engagement index (0–100)",
        examples=[81.3],
    )
    cross_department_edges_delta: float = Field(
        ...,
        description="Relative change in cross-department collaboration edges",
        examples=[0.34],
    )
    productivity_std_dev: float = Field(
        default=0.0,
        description="Standard deviation across Monte-Carlo runs (confidence indicator)",
        examples=[2.1],
    )
    adoption_confidence: float = Field(
        default=0.0,
        description="95th percentile adoption rate from Monte-Carlo",
        examples=[0.83],
    )


# ── Simulation ────────────────────────────────────────────────────────────────

class SimulationResponse(BaseModel):
    """Full What-If simulation response."""

    run_id: str = Field(..., examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"])
    scenario: str = Field(..., examples=["switch_to_teams"])
    kpis: KPIResult
    llm_explanation: str = Field(
        ...,
        description="Groq LLM bullet-point analysis and recommendation",
        examples=["• Adoption will reach 78% within 6 weeks due to high engineering propensity..."],
    )
    llm_model: str = Field(..., examples=["llama-3.1-70b-versatile"])
    llm_duration_ms: int = Field(..., examples=[642])
    total_duration_ms: int = Field(..., examples=[1240])
    monte_carlo_iterations: int = Field(..., examples=[200])
    employees_simulated: int = Field(..., examples=[150])
    rag_cases_used: int = Field(..., examples=[3])


# ── Graph ─────────────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    """React Flow compatible node."""

    id: str = Field(..., examples=["EMP001"])
    label: str = Field(..., examples=["Arjun Sharma"])
    department: str = Field(..., examples=["Engineering"])
    role: str = Field(..., examples=["Senior Engineer"])
    current_tool: str = Field(..., examples=["Slack"])
    adoption_propensity: float = Field(..., examples=[0.82])
    productivity_base: float = Field(..., examples=[75.0])
    degree: int = Field(..., examples=[12])
    is_bridge: bool = Field(..., examples=[True])


class GraphEdge(BaseModel):
    """React Flow compatible edge."""

    source: str = Field(..., examples=["EMP001"])
    target: str = Field(..., examples=["EMP002"])
    weight: float = Field(default=1.0, examples=[0.75])
    cross_department: bool = Field(default=False)


class GraphResponse(BaseModel):
    """NetworkX graph serialized for React Flow visualization."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]
    total_nodes: int
    total_edges: int
    departments: list[str]
    density: float = Field(..., description="Graph density (0–1)", examples=[0.057])
    avg_clustering: float = Field(..., examples=[0.43])
    connected_components: int = Field(..., examples=[1])


# ── Insights ──────────────────────────────────────────────────────────────────

class InsightResponse(BaseModel):
    """LLM-generated KPI explanation."""

    question: str
    answer: str = Field(..., description="Full LLM natural-language explanation")
    llm_model: str
    duration_ms: int
    simulation_run_id: str | None = None


# ── Feedback ──────────────────────────────────────────────────────────────────

class FeedbackResponse(BaseModel):
    """Response after post-rollout feedback submission."""

    simulation_run_id: str
    prediction_accuracy: float = Field(
        ...,
        description="How close was the simulation to reality (0–100%)",
        examples=[85.3],
    )
    productivity_delta: float = Field(
        ...,
        description="Predicted vs actual productivity gap (%)",
        examples=[3.7],
    )
    adoption_delta: float = Field(
        ...,
        description="Predicted vs actual adoption rate gap",
        examples=[0.07],
    )
    llm_recalibration_notes: str
    model_updated: bool = Field(default=False)
    message: str = Field(default="Feedback recorded. Model recalibration queued.")


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy", examples=["healthy"])
    version: str = Field(..., examples=["1.0.0"])
    database: str = Field(default="connected", examples=["connected"])
    redis: str = Field(default="connected", examples=["connected"])
    llm_provider: str = Field(default="groq", examples=["groq"])
    employees_loaded: int = Field(default=0, examples=[150])
    uptime_seconds: float = Field(..., examples=[3642.5])
