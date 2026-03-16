# api/endpoints/graph.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
Graph endpoint.
GET /graph → Returns NetworkX collaboration graph as React Flow JSON.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query

from core.security import get_current_user
from services.graph_builder import get_graph, graph_to_react_flow, get_graph_metrics
from schemas.response import GraphResponse, GraphNode, GraphEdge, APIResponse
from utils.logger import get_logger

router = APIRouter(prefix="/graph", tags=["Collaboration Graph"])
logger = get_logger(__name__)


@router.get(
    "",
    response_model=APIResponse[GraphResponse],
    summary="Get collaboration graph for visualization",
    description=(
        "Returns the full employee collaboration graph in React Flow compatible format.\n\n"
        "**Node fields:** id, label, department, role, adoption_propensity, degree, is_bridge\n\n"
        "**Edge fields:** source, target, weight, cross_department\n\n"
        "Use `department` query param to filter by department. "
        "Use `max_nodes` to limit graph size for performance."
    ),
    responses={
        200: {
            "description": "Graph returned successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "total_nodes": 150,
                            "total_edges": 423,
                            "density": 0.038,
                            "nodes": [{"id": "EMP001", "label": "Arjun Sharma", "department": "Engineering"}],
                            "edges": [{"source": "EMP001", "target": "EMP002", "weight": 0.75}],
                        },
                    }
                }
            },
        },
        404: {"description": "No graph found — ingest employees first"},
    },
)
async def get_collaboration_graph(
    department: str | None = Query(
        default=None,
        description="Filter graph to a specific department",
        examples=["Engineering"],
    ),
    max_nodes: int = Query(
        default=500,
        ge=1,
        le=2000,
        description="Maximum number of nodes to return (for frontend performance)",
    ),
    include_isolated: bool = Query(
        default=False,
        description="Include nodes with no edges",
    ),
    current_user: dict = Depends(get_current_user),
) -> APIResponse[GraphResponse]:
    """
    ## Get Collaboration Graph

    Returns the full NetworkX graph serialized for React Flow.

    Supports department filtering and node count limits for
    smooth frontend rendering even with large workforces.
    """
    G = get_graph()

    if G is None or G.number_of_nodes() == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "No collaboration graph found. "
                "Please ingest employee data via POST /ingest/employees first."
            ),
        )

    # Apply department filter (subgraph)
    if department:
        nodes_in_dept = [
            n for n, attrs in G.nodes(data=True)
            if attrs.get("department", "").lower() == department.lower()
        ]
        if not nodes_in_dept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department '{department}' not found in graph.",
            )
        G = G.subgraph(nodes_in_dept).copy()

    # Remove isolated nodes if requested
    if not include_isolated:
        isolated = list(nx_isolated(G))
        if isolated and G.number_of_nodes() > len(isolated):
            G = G.subgraph([n for n in G.nodes() if n not in isolated]).copy()

    # Limit node count
    if G.number_of_nodes() > max_nodes:
        import networkx as nx
        # Keep highest-degree nodes
        top_nodes = sorted(G.degree(), key=lambda x: x[1], reverse=True)[:max_nodes]
        G = G.subgraph([n for n, _ in top_nodes]).copy()

    graph_data = graph_to_react_flow(G)
    metrics = get_graph_metrics(G)

    nodes = [GraphNode(**n) for n in graph_data["nodes"]]
    edges = [GraphEdge(**e) for e in graph_data["edges"]]

    response = GraphResponse(
        nodes=nodes,
        edges=edges,
        total_nodes=graph_data["total_nodes"],
        total_edges=graph_data["total_edges"],
        departments=graph_data["departments"],
        density=graph_data["density"],
        avg_clustering=graph_data["avg_clustering"],
        connected_components=graph_data["connected_components"],
    )

    logger.info(
        "Graph served",
        extra={
            "nodes": graph_data["total_nodes"],
            "edges": graph_data["total_edges"],
            "filtered_by": department or "all",
        },
    )

    return APIResponse(
        success=True,
        message=f"Graph with {graph_data['total_nodes']} nodes and {graph_data['total_edges']} edges.",
        data=response,
        meta=metrics,
    )


@router.get(
    "/metrics",
    summary="Get graph topology metrics only",
    tags=["Collaboration Graph"],
)
async def get_graph_metrics_endpoint(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Returns lightweight graph metrics without full node/edge data."""
    G = get_graph()
    if G is None or G.number_of_nodes() == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No graph found. Ingest employees first.",
        )
    return {"success": True, "data": get_graph_metrics(G)}


def nx_isolated(G) -> list:
    """Returns isolated (degree-0) nodes from the graph."""
    return [n for n in G.nodes() if G.degree(n) == 0]
