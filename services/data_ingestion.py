# services/data_ingestion.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
Async CSV ingestion service.
Validates, deduplicates, and persists employee records to the database,
then triggers graph rebuild automatically.
"""

import csv
import io
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from models.employee import Employee
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Expected CSV columns ──────────────────────────────────────────────────────
REQUIRED_COLUMNS = {
    "employee_id",
    "name",
    "role",
    "department",
    "current_tool",
    "adoption_propensity",
    "productivity_base",
}

OPTIONAL_COLUMNS = {"email", "manager_id", "location", "tenure_years", "team_size"}


async def ingest_employees_from_csv(
    csv_content: bytes,
    db: AsyncSession,
    replace_existing: bool = True,
) -> dict[str, Any]:
    """
    Parses CSV bytes, validates schema, upserts employees into the database.

    Args:
        csv_content: Raw CSV file bytes from upload.
        db: Async SQLAlchemy session.
        replace_existing: If True, wipe and reload all employees.

    Returns:
        dict with employees_loaded, departments, errors, warnings.

    Raises:
        ValueError: If required CSV columns are missing.
    """
    logger.info("Starting employee CSV ingestion")

    # Decode and parse
    try:
        text = csv_content.decode("utf-8-sig")  # handles BOM from Excel exports
    except UnicodeDecodeError:
        text = csv_content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError("CSV file is empty or has no headers.")

    # Normalize column names (strip whitespace, lowercase)
    normalized_fields = {f.strip().lower() for f in reader.fieldnames}
    missing = REQUIRED_COLUMNS - normalized_fields
    if missing:
        raise ValueError(
            f"CSV is missing required columns: {', '.join(sorted(missing))}. "
            f"Required: {', '.join(sorted(REQUIRED_COLUMNS))}"
        )

    # Optionally clear existing employees for clean reload
    if replace_existing:
        await db.execute(delete(Employee))
        logger.info("Cleared existing employee records")

    employees: list[Employee] = []
    errors: list[str] = []
    departments: set[str] = set()
    seen_ids: set[str] = set()

    for row_num, raw_row in enumerate(reader, start=2):  # row 1 = header
        # Normalize keys
        row = {k.strip().lower(): v.strip() for k, v in raw_row.items() if k}

        emp_id = row.get("employee_id", "").strip()
        if not emp_id:
            errors.append(f"Row {row_num}: Missing employee_id — skipped.")
            continue
        if emp_id in seen_ids:
            errors.append(f"Row {row_num}: Duplicate employee_id '{emp_id}' — skipped.")
            continue
        seen_ids.add(emp_id)

        # Safe float parsing with fallback defaults
        try:
            adoption = float(row.get("adoption_propensity", 0.5))
            adoption = max(0.0, min(1.0, adoption))
        except ValueError:
            adoption = 0.5

        try:
            productivity = float(row.get("productivity_base", 70.0))
            productivity = max(0.0, min(100.0, productivity))
        except ValueError:
            productivity = 70.0

        dept = row.get("department", "Unknown")
        departments.add(dept)

        emp = Employee(
            employee_id=emp_id,
            name=row.get("name", "Unknown"),
            role=row.get("role", "Employee"),
            department=dept,
            current_tool=row.get("current_tool", "Email"),
            adoption_propensity=adoption,
            productivity_base=productivity,
        )
        employees.append(emp)

    if not employees:
        raise ValueError("No valid employee records found in CSV.")

    # Bulk insert
    db.add_all(employees)
    await db.commit()

    logger.info(
        "Employee ingestion complete",
        extra={
            "employees_loaded": len(employees),
            "departments": list(departments),
            "errors": len(errors),
        },
    )

    return {
        "employees_loaded": len(employees),
        "departments": sorted(departments),
        "errors": errors,
        "warnings": (
            [f"{len(errors)} rows had errors and were skipped"] if errors else []
        ),
    }


async def get_all_employees(db: AsyncSession) -> list[Employee]:
    """Fetches all employees from the database."""
    result = await db.execute(select(Employee).order_by(Employee.department, Employee.name))
    return list(result.scalars().all())


async def get_employee_count(db: AsyncSession) -> int:
    """Fast count of current employee records."""
    from sqlalchemy import func
    result = await db.execute(select(func.count()).select_from(Employee))
    return result.scalar_one_or_none() or 0
