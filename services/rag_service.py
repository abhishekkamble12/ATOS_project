# services/rag_service.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
RAG (Retrieval-Augmented Generation) service using FAISS + sentence-transformers.
Pre-loads 7 curated past adoption case studies as the knowledge base.
Retrieves the top-k most similar cases for LLM context injection.
"""

import asyncio
from typing import Any

import numpy as np

from utils.logger import get_logger

logger = get_logger(__name__)

# ── 7 Curated past adoption case studies ─────────────────────────────────────

PAST_CASES: list[dict[str, Any]] = [
    {
        "id": "case_001",
        "title": "Atos Global Teams Migration 2022",
        "scenario": "switch_to_teams",
        "description": (
            "Atos migrated 12,000 employees from Skype for Business to Microsoft Teams "
            "across 15 countries. Phased rollout with change champions in each BU."
        ),
        "adoption_rate": 0.84,
        "productivity_increase": 19.2,
        "key_success_factors": "Executive sponsorship, dedicated training, early adopter incentives",
        "risks": "Resistance in legacy project teams; 6-week productivity dip in first phase",
        "roi_months": 14,
        "tags": ["teams", "large_scale", "global", "phased"],
    },
    {
        "id": "case_002",
        "title": "TCS Slack Adoption — Digital Workspace Initiative",
        "scenario": "switch_to_slack",
        "description": (
            "TCS rolled out Slack to 8,000 engineering and product employees. "
            "Integrated with Jira, GitHub, and CI/CD pipelines."
        ),
        "adoption_rate": 0.79,
        "productivity_increase": 14.8,
        "key_success_factors": "Deep tool integrations, developer community buy-in",
        "risks": "Notification fatigue; informal channel sprawl after 3 months",
        "roi_months": 10,
        "tags": ["slack", "engineering", "integration", "medium_scale"],
    },
    {
        "id": "case_003",
        "title": "Infosys AI Co-pilot Pilot Program",
        "scenario": "add_ai_copilot",
        "description": (
            "Infosys piloted GitHub Copilot + AI writing assistant for 2,500 developers. "
            "90-day trial with clear productivity measurement via sprint velocity."
        ),
        "adoption_rate": 0.71,
        "productivity_increase": 26.3,
        "key_success_factors": "Clear ROI metrics from day 1; voluntary participation",
        "risks": "Data privacy concerns; over-reliance reducing junior developer skill growth",
        "roi_months": 6,
        "tags": ["ai_copilot", "engineering", "pilot", "high_roi"],
    },
    {
        "id": "case_004",
        "title": "Wipro Hybrid Work Policy 2023",
        "scenario": "hybrid_work_policy",
        "description": (
            "Wipro introduced 3-days-office + 2-days-home policy for 40,000 employees. "
            "Included redesigned office spaces for collaboration."
        ),
        "adoption_rate": 0.91,
        "productivity_increase": 11.4,
        "key_success_factors": "Employee choice, redesigned offices, manager trust model",
        "risks": "Coordination overhead; junior employee mentoring gap",
        "roi_months": 18,
        "tags": ["hybrid", "policy", "large_scale", "employee_satisfaction"],
    },
    {
        "id": "case_005",
        "title": "HCL Cross-Department Innovation Program",
        "scenario": "cross_dept_initiative",
        "description": (
            "HCL ran a 6-month cross-functional tiger team initiative linking Engineering, "
            "Sales, and Delivery. Monthly hackathons and shared OKRs."
        ),
        "adoption_rate": 0.65,
        "productivity_increase": 8.9,
        "key_success_factors": "Shared goals, executive visibility, recognition program",
        "risks": "Primary job neglect; difficulty measuring individual contribution",
        "roi_months": 24,
        "tags": ["cross_dept", "innovation", "culture_change"],
    },
    {
        "id": "case_006",
        "title": "Cognizant Teams Rapid Migration — Post-Pandemic Sprint",
        "scenario": "switch_to_teams",
        "description": (
            "Cognizant emergency-migrated 15,000 employees to Teams in 3 weeks during "
            "COVID lockdown. Minimal training due to urgency — organic adoption."
        ),
        "adoption_rate": 0.88,
        "productivity_increase": 7.6,
        "key_success_factors": "Business necessity drove adoption; simple UX",
        "risks": "Meeting fatigue; poor async communication norms initially",
        "roi_months": 8,
        "tags": ["teams", "rapid_migration", "covid", "large_scale"],
    },
    {
        "id": "case_007",
        "title": "Accenture AI + Teams Combined Digital Workplace",
        "scenario": "add_ai_copilot",
        "description": (
            "Accenture deployed Microsoft Copilot within Teams for 20,000 consultants. "
            "AI-assisted meeting summaries, proposal writing, and research."
        ),
        "adoption_rate": 0.77,
        "productivity_increase": 23.1,
        "key_success_factors": "Native integration with existing tools; measurable time savings",
        "risks": "Quality control on AI outputs; licensing cost at scale",
        "roi_months": 9,
        "tags": ["ai_copilot", "teams", "consulting", "large_scale"],
    },
]


class RAGService:
    """
    FAISS-based retrieval service for past adoption case studies.

    Lifecycle:
    1. __init__: Prepare case texts
    2. initialize(): Load sentence-transformer model and build FAISS index
    3. retrieve(): Query top-k similar cases for a given scenario
    """

    def __init__(self) -> None:
        self._model = None
        self._index = None
        self._embeddings: np.ndarray | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """
        Async wrapper to load model and build index in a thread pool
        (sentence-transformers is CPU-bound).
        """
        if self._initialized:
            return
        logger.info("Initializing RAG service (loading sentence-transformer + FAISS)...")
        await asyncio.get_event_loop().run_in_executor(None, self._build_index)
        self._initialized = True
        logger.info("RAG service ready", extra={"cases_loaded": len(PAST_CASES)})

    def _build_index(self) -> None:
        """Builds the FAISS index from case embeddings (runs in thread pool)."""
        try:
            from sentence_transformers import SentenceTransformer
            import faiss

            model = SentenceTransformer("all-MiniLM-L6-v2")

            # Build rich text representations of each case for embedding
            texts = [self._case_to_text(c) for c in PAST_CASES]
            embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

            # L2-normalize for cosine similarity via inner product
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            embeddings = embeddings / np.maximum(norms, 1e-9)

            # Build flat FAISS index (IP = inner product = cosine after normalization)
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)
            index.add(embeddings.astype(np.float32))

            self._model = model
            self._index = index
            self._embeddings = embeddings

        except ImportError as e:
            logger.warning(
                f"RAG dependencies not available ({e}). Falling back to keyword matching."
            )
            self._initialized = True

    async def retrieve(
        self,
        query: str,
        scenario: str | None = None,
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Retrieves top-k most similar past cases for a given query.

        Args:
            query: Natural language query (e.g. scenario description).
            scenario: Optional scenario key for pre-filtering.
            top_k: Number of results to return.

        Returns:
            List of case dicts with similarity scores.
        """
        if not self._initialized:
            await self.initialize()

        if self._model is None or self._index is None:
            return self._keyword_fallback(scenario, top_k)

        return await asyncio.get_event_loop().run_in_executor(
            None,
            self._retrieve_sync,
            query,
            top_k,
        )

    def _retrieve_sync(self, query: str, top_k: int) -> list[dict[str, Any]]:
        """Synchronous FAISS search (runs in thread pool)."""
        query_embedding = self._model.encode([query], convert_to_numpy=True)
        norm = np.linalg.norm(query_embedding, axis=1, keepdims=True)
        query_embedding = (query_embedding / np.maximum(norm, 1e-9)).astype(np.float32)

        scores, indices = self._index.search(query_embedding, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(PAST_CASES):
                case = dict(PAST_CASES[idx])
                case["similarity_score"] = round(float(score), 4)
                results.append(case)

        return results

    def _keyword_fallback(
        self, scenario: str | None, top_k: int
    ) -> list[dict[str, Any]]:
        """Simple keyword filter fallback when FAISS is unavailable."""
        if scenario:
            matches = [c for c in PAST_CASES if c["scenario"] == scenario]
            return matches[:top_k] if matches else PAST_CASES[:top_k]
        return PAST_CASES[:top_k]

    def format_context_for_llm(self, cases: list[dict[str, Any]]) -> str:
        """Formats retrieved cases into a clean LLM-injectable context block."""
        if not cases:
            return "No similar historical cases found."

        lines = ["=== Similar Past Adoption Cases ===\n"]
        for i, case in enumerate(cases, 1):
            similarity = case.get("similarity_score", "N/A")
            lines.append(
                f"Case {i}: {case['title']} (Similarity: {similarity})\n"
                f"  Scenario: {case['scenario']}\n"
                f"  Adoption Rate: {case['adoption_rate'] * 100:.1f}%\n"
                f"  Productivity Increase: {case['productivity_increase']}%\n"
                f"  Success Factors: {case['key_success_factors']}\n"
                f"  Risks: {case['risks']}\n"
                f"  ROI Timeline: {case['roi_months']} months\n"
            )

        return "\n".join(lines)

    @staticmethod
    def _case_to_text(case: dict[str, Any]) -> str:
        """Converts a case dict to a rich text string for embedding."""
        return (
            f"{case['title']}. {case['description']} "
            f"Scenario: {case['scenario']}. "
            f"Adoption: {case['adoption_rate']}. "
            f"Productivity: {case['productivity_increase']}%. "
            f"Success: {case['key_success_factors']}. "
            f"Risks: {case['risks']}. "
            f"Tags: {', '.join(case.get('tags', []))}."
        )


# ── Module-level singleton ────────────────────────────────────────────────────
rag_service = RAGService()
