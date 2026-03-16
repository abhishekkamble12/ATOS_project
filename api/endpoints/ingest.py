# api/endpoints/ingest.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
Data ingestion endpoints.
POST /ingest/employees → Upload employee CSV, build collaboration graph.
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import get_current_user
from services.data_ingestion import ingest_employees_from_csv, get_all_employees
from services.graph_builder import build_collaboration_graph, get_graph_metrics
from schemas.response import IngestResponse, APIResponse
from utils.logger import get_logger
from database import get_db

router = APIRouter(prefix="/ingest", tags=["Data Ingestion"])
logger = get_logger(__name__)

MAX_CSV_SIZE_MB = 10


@router.post(
    "/employees",
    response_model=APIResponse[IngestResponse],
    summary="Upload employee CSV and build collaboration graph",
    description=(
        "Accepts a CSV file with employee data. Validates schema, persists to DB, "
        "and automatically builds the NetworkX collaboration graph.\n\n"
        "**Required CSV columns:** `employee_id`, `name`, `role`, `department`, "
        "`current_tool`, `adoption_propensity` (0–1), `productivity_base` (0–100)\n\n"
        "Download sample CSV from `/ingest/sample-csv`."
    ),
    responses={
        200: {
            "description": "Employees loaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "150 employees loaded and graph built.",
                        "data": {
                            "employees_loaded": 150,
                            "departments_found": ["Engineering", "HR", "Sales", "Finance"],
                            "graph_nodes": 150,
                            "graph_edges": 423,
                        },
                    }
                }
            },
        },
        400: {"description": "Invalid CSV schema or empty file"},
        413: {"description": "File too large (>10 MB)"},
    },
)
async def ingest_employees(
    file: UploadFile = File(
        ...,
        description="CSV file with employee data",
    ),
    replace_existing: bool = Query(
        default=True,
        description="If true, clears existing employees before loading",
    ),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[IngestResponse]:
    """
    ## Upload Employee CSV

    Parses, validates, and stores employee data, then automatically
    builds the collaboration graph for simulation.

    Accepts `.csv` or `.txt` files. Handles UTF-8 and Excel BOM encoding.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith((".csv", ".txt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only .csv files are accepted.",
        )

    # Read and size-check
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_CSV_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {size_mb:.1f} MB exceeds maximum of {MAX_CSV_SIZE_MB} MB.",
        )

    logger.info(
        f"CSV upload received: {file.filename} ({size_mb:.2f} MB)",
        extra={"user": current_user.get("email")},
    )

    # Ingest employees
    try:
        ingest_result = await ingest_employees_from_csv(content, db, replace_existing)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # Build collaboration graph
    employees = await get_all_employees(db)
    G = build_collaboration_graph(employees)
    metrics = get_graph_metrics(G)

    response_data = IngestResponse(
        employees_loaded=ingest_result["employees_loaded"],
        departments_found=ingest_result["departments"],
        graph_nodes=metrics.get("total_nodes", 0),
        graph_edges=metrics.get("total_edges", 0),
        message=(
            f"{ingest_result['employees_loaded']} employees loaded and "
            f"collaboration graph built ({metrics.get('total_edges', 0)} edges)."
        ),
    )

    return APIResponse(
        success=True,
        message=response_data.message,
        data=response_data,
        meta={
            "graph_density": metrics.get("density"),
            "departments": ingest_result["departments"],
            "warnings": ingest_result.get("warnings", []),
            "errors_skipped": len(ingest_result.get("errors", [])),
        },
    )


@router.get(
    "/sample-csv",
    summary="Download sample employee CSV",
    description="Returns a pre-built sample CSV with 20 realistic employees for demo purposes.",
    tags=["Data Ingestion"],
    include_in_schema=True,
)
async def download_sample_csv():
    """Returns a sample CSV file for download."""
    from fastapi.responses import StreamingResponse
    from utils.sample_data import generate_sample_csv_bytes
    import io

    csv_bytes = generate_sample_csv_bytes()

    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_employees.csv"},
    )
