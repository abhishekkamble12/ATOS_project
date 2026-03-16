# services/graph_builder.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
NetworkX collaboration graph builder.
Models employees as nodes and collaboration relationships as weighted edges.
Generates realistic collaboration topology using department clustering,
role-based affinity, and adoption propensity.
"""

import random
from typing import Any

import networkx as nx

from models.employee import Employee
from utils.logger import get_logger

logger = get_logger(__name__)

# Module-level graph cache (refreshed on each ingestion)
_collaboration_graph: nx.Graph | None = None


def get_graph() -> nx.Graph | None:
    """Returns the current cached collaboration graph."""
    return _collaboration_graph


def build_collaboration_graph(employees: list[Employee]) -> nx.Graph:
    """
    Constructs a weighted undirected collaboration graph from employee data.

    Edge generation rules:
    1. Intra-department edges: high probability (0.35) — team collaboration
    2. Inter-department edges: low probability (0.06) — cross-functional work
    3. Weight = average adoption_propensity of both employees
    4. Managers (degree > 8) become natural hubs

    Args:
        employees: List of Employee ORM objects.

    Returns:
        nx.Graph with node attributes and weighted edges.
    """
    global _collaboration_graph

    G = nx.Graph()

    # ── Add all employees as nodes ────────────────────────────────────────
    for emp in employees:
        G.add_node(
            emp.employee_id,
            name=emp.name,
            role=emp.role,
            department=emp.department,
            current_tool=emp.current_tool,
            adoption_propensity=emp.adoption_propensity,
            productivity_base=emp.productivity_base,
            label=emp.name,
        )

    # ── Generate edges using probability model ────────────────────────────
    departments: dict[str, list[Employee]] = {}
    for emp in employees:
        departments.setdefault(emp.department, []).append(emp)

    rng = random.Random(42)  # seeded for reproducibility

    # Intra-department edges (team collaboration)
    for dept, members in departments.items():
        for i, emp_a in enumerate(members):
            for emp_b in members[i + 1 :]:
                if rng.random() < 0.35:
                    weight = round(
                        (emp_a.adoption_propensity + emp_b.adoption_propensity) / 2,
                        3,
                    )
                    G.add_edge(
                        emp_a.employee_id,
                        emp_b.employee_id,
                        weight=weight,
                        cross_department=False,
                    )

    # Inter-department edges (cross-functional collaboration)
    dept_list = list(departments.keys())
    for i, dept_a in enumerate(dept_list):
        for dept_b in dept_list[i + 1 :]:
            members_a = departments[dept_a]
            members_b = departments[dept_b]
            # Only connect a subset of cross-dept pairs
            for emp_a in rng.sample(members_a, min(3, len(members_a))):
                for emp_b in rng.sample(members_b, min(3, len(members_b))):
                    if rng.random() < 0.06:
                        weight = round(
                            (emp_a.adoption_propensity + emp_b.adoption_propensity) / 2,
                            3,
                        )
                        G.add_edge(
                            emp_a.employee_id,
                            emp_b.employee_id,
                            weight=weight,
                            cross_department=True,
                        )

    # ── Tag bridge nodes (cross-department connectors) ────────────────────
    cross_dept_nodes: set[str] = set()
    for u, v, data in G.edges(data=True):
        if data.get("cross_department"):
            cross_dept_nodes.add(u)
            cross_dept_nodes.add(v)

    for node in G.nodes():
        G.nodes[node]["is_bridge"] = node in cross_dept_nodes
        G.nodes[node]["degree"] = G.degree(node)

    _collaboration_graph = G

    logger.info(
        "Collaboration graph built",
        extra={
            "nodes": G.number_of_nodes(),
            "edges": G.number_of_edges(),
            "density": round(nx.density(G), 4),
            "departments": len(departments),
        },
    )

    return G


def get_graph_metrics(G: nx.Graph) -> dict[str, Any]:
    """
    Computes key graph topology metrics for simulation and API response.

    Returns:
        dict with density, avg_clustering, connected_components, cross_dept_edges.
    """
    if G.number_of_nodes() == 0:
        return {}

    cross_dept_edges = sum(
        1 for _, _, d in G.edges(data=True) if d.get("cross_department")
    )

    try:
        avg_clustering = round(nx.average_clustering(G, weight="weight"), 4)
    except Exception:
        avg_clustering = 0.0

    return {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "density": round(nx.density(G), 4),
        "avg_clustering": avg_clustering,
        "connected_components": nx.number_connected_components(G),
        "cross_department_edges": cross_dept_edges,
        "cross_dept_ratio": round(
            cross_dept_edges / max(G.number_of_edges(), 1), 4
        ),
        "avg_degree": round(
            sum(d for _, d in G.degree()) / max(G.number_of_nodes(), 1), 2
        ),
    }


def graph_to_react_flow(G: nx.Graph) -> dict[str, Any]:
    """
    Serializes the NetworkX graph into React Flow compatible format.

    Returns:
        dict with nodes (list) and edges (list).
    """
    nodes = []
    for node_id, attrs in G.nodes(data=True):
        nodes.append({
            "id": node_id,
            "label": attrs.get("name", node_id),
            "department": attrs.get("department", "Unknown"),
            "role": attrs.get("role", ""),
            "current_tool": attrs.get("current_tool", ""),
            "adoption_propensity": attrs.get("adoption_propensity", 0.5),
            "productivity_base": attrs.get("productivity_base", 70.0),
            "degree": attrs.get("degree", G.degree(node_id)),
            "is_bridge": attrs.get("is_bridge", False),
        })

    edges = []
    for u, v, data in G.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "weight": data.get("weight", 1.0),
            "cross_department": data.get("cross_department", False),
        })

    departments = sorted({attrs.get("department", "") for _, attrs in G.nodes(data=True)})

    return {
        "nodes": nodes,
        "edges": edges,
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "departments": departments,
        "density": round(nx.density(G), 4),
        "avg_clustering": round(nx.average_clustering(G), 4) if G.number_of_nodes() > 1 else 0.0,
        "connected_components": nx.number_connected_components(G),
    }
