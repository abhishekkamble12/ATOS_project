# api/router.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
Central API router — aggregates all endpoint routers.
Mount this on the FastAPI app in main.py.
"""

from fastapi import APIRouter

from api.endpoints.auth import router as auth_router
from api.endpoints.ingest import router as ingest_router
from api.endpoints.simulate import router as simulate_router
from api.endpoints.graph import router as graph_router
from api.endpoints.insights import router as insights_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(ingest_router)
api_router.include_router(simulate_router)
api_router.include_router(graph_router)
api_router.include_router(insights_router)
