# schemas/request.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
Pydantic v2 request schemas with full OpenAPI documentation.
Every field has description, example, and validation constraints.
"""

from typing import Annotated, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Login payload for JWT token generation."""

    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["admin@atos.com"],
    )
    password: str = Field(
        ...,
        min_length=6,
        description="Account password",
        examples=["password123"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"email": "admin@atos.com", "password": "password123"}
            ]
        }
    }


# ── Simulation ────────────────────────────────────────────────────────────────

class WhatIfRequest(BaseModel):
    """
    What-If scenario simulation request.

    Supported scenario keys:
    - switch_to_teams       : Migrate from current tool to Microsoft Teams
    - switch_to_slack       : Migrate to Slack
    - add_ai_copilot        : Overlay AI assistant on current workflow
    - hybrid_work_policy    : Introduce flexible remote/office schedule
    - cross_dept_initiative : Launch cross-functional collaboration program
    - custom                : Any user-defined scenario (requires description)
    """

    scenario: str = Field(
        ...,
        description="Scenario identifier key",
        examples=["switch_to_teams"],
    )
    new_tool: str | None = Field(
        default=None,
        description="The new collaboration tool being introduced",
        examples=["Teams"],
    )
    adoption_boost: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        default=0.25,
        description="Expected adoption propensity boost (0.0–1.0)",
        examples=[0.25],
    )
    monte_carlo_iterations: Annotated[int, Field(ge=10, le=1000)] = Field(
        default=200,
        description="Number of Monte-Carlo simulation runs for statistical confidence",
        examples=[200],
    )
    custom_description: str | None = Field(
        default=None,
        description="Free-text description for custom scenarios",
        examples=["Introduce a 4-day work week policy"],
    )
    departments_affected: list[str] | None = Field(
        default=None,
        description="Limit simulation to specific departments (None = all)",
        examples=[["Engineering", "Product"]],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "scenario": "switch_to_teams",
                    "new_tool": "Teams",
                    "adoption_boost": 0.25,
                    "monte_carlo_iterations": 200,
                }
            ]
        }
    }


# ── Insights ──────────────────────────────────────────────────────────────────

class InsightExplainRequest(BaseModel):
    """Request for LLM-powered KPI explanation."""

    simulation_run_id: str | None = Field(
        default=None,
        description="UUID of a previous simulation run to explain",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )
    kpi_snapshot: dict | None = Field(
        default=None,
        description="Inline KPI snapshot if no run_id provided",
        examples=[{
            "productivity_increase": 22.4,
            "adoption_rate": 0.78,
            "collaboration_density": 0.61,
            "engagement_score": 81.3,
            "cross_department_edges_delta": 0.34,
        }],
    )
    question: str = Field(
        default="Why did productivity increase?",
        description="Natural-language question for the AI to answer",
        examples=["Why did productivity increase 22%?"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "simulation_run_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "question": "Why did productivity increase 22%?",
                }
            ]
        }
    }


# ── Feedback Loop ─────────────────────────────────────────────────────────────

class FeedbackLoopRequest(BaseModel):
    """
    Post-rollout actual data submission for continuous learning recalibration.
    Compares against the original simulation prediction.
    """

    simulation_run_id: str = Field(
        ...,
        description="UUID of the original simulation run to compare against",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )
    actual_productivity_increase: float = Field(
        ...,
        description="Observed productivity change (%) after actual rollout",
        examples=[18.7],
    )
    actual_adoption_rate: Annotated[float, Field(ge=0.0, le=1.0)] = Field(
        ...,
        description="Observed tool adoption rate (0.0–1.0)",
        examples=[0.71],
    )
    actual_engagement_score: float | None = Field(
        default=None,
        description="Observed engagement score (0–100)",
        examples=[76.5],
    )
    rollout_weeks: int | None = Field(
        default=None,
        description="Number of weeks since rollout began",
        examples=[8],
    )
    notes: str | None = Field(
        default=None,
        description="Qualitative notes from HR / change management team",
        examples=["Resistance in Finance dept due to legacy processes."],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "simulation_run_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "actual_productivity_increase": 18.7,
                    "actual_adoption_rate": 0.71,
                    "rollout_weeks": 8,
                }
            ]
        }
    }
