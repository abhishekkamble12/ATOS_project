# models/employee.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
SQLAlchemy ORM model for Employee.
Uses aiosqlite for async SQLite (swap DATABASE_URL for PostgreSQL in prod).
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    DateTime,
    Boolean,
    Text,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    """Base class with AsyncAttrs mixin for async lazy-loading support."""
    pass


class Employee(Base):
    """
    Represents a single workforce member in the Digital Twin.

    Columns mirror the required CSV schema:
        employee_id, name, role, department, current_tool,
        adoption_propensity, productivity_base

    Additional computed/enriched fields are stored after simulation.

    To migrate to PostgreSQL:
        1. pip install asyncpg
        2. Set DATABASE_URL=postgresql+asyncpg://user:pass@host/db in .env
        3. Run: alembic upgrade head
    """

    __tablename__ = "employees"

    # ── Primary identity ──────────────────────────────────────────────────
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    employee_id: str = Column(String(50), unique=True, nullable=False, index=True)
    name: str = Column(String(200), nullable=False)
    role: str = Column(String(100), nullable=False)
    department: str = Column(String(100), nullable=False, index=True)

    # ── Tool usage ────────────────────────────────────────────────────────
    current_tool: str = Column(String(100), nullable=False, default="Email")
    # 0.0 → resistant to change | 1.0 → early adopter
    adoption_propensity: float = Column(Float, nullable=False, default=0.5)

    # ── Productivity baseline (0–100 scale) ───────────────────────────────
    productivity_base: float = Column(Float, nullable=False, default=70.0)

    # ── Post-simulation / post-rollout fields ─────────────────────────────
    productivity_post: float | None = Column(Float, nullable=True)
    adopted_new_tool: bool = Column(Boolean, default=False)
    engagement_score: float | None = Column(Float, nullable=True)

    # ── Graph metadata ────────────────────────────────────────────────────
    collaboration_degree: int = Column(Integer, default=0)   # NetworkX degree
    department_bridge: bool = Column(Boolean, default=False)  # cross-dept connector

    # ── Raw JSON for flexible extra attributes ────────────────────────────
    extra_attributes: str | None = Column(Text, nullable=True)  # JSON string

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<Employee id={self.employee_id} name={self.name!r} "
            f"dept={self.department!r} tool={self.current_tool!r}>"
        )
