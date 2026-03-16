# core/groq_client.py
# Digital Twin of the Workforce Backend
# Built for National Hackathon Winning Entry
# Team Eklavya | Atos Srijan 2026

"""
Groq LLM client wrapper.
Achieves <800ms inference using llama-3.1-70b-versatile on Groq cloud.
Includes the mandatory prompt template for workforce scenario explanation.
"""

import json
import time
from typing import Any

from groq import AsyncGroq

from core.config import get_settings
from utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

# ── Singleton async Groq client ───────────────────────────────────────────────
_groq_client: AsyncGroq | None = None


def get_groq_client() -> AsyncGroq:
    """Returns the cached AsyncGroq client (lazy init)."""
    global _groq_client
    if _groq_client is None:
        _groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    return _groq_client


# ── Mandatory prompt template ─────────────────────────────────────────────────
WORKFORCE_ANALYSIS_PROMPT = """You are an expert workforce transformation consultant. \
Given simulation results {simulation_json}, explain in 3 short bullet points + one \
recommendation why this scenario will succeed or fail. Use simple business language. \
Always be optimistic but realistic. End with ROI estimate.

Context from similar past cases:
{rag_context}

Simulation Results:
{simulation_json}

Scenario: {scenario_name}
"""

INSIGHTS_EXPLAIN_PROMPT = """You are a data-driven HR analytics expert.
Given the following KPI changes from a workforce simulation:

{kpi_summary}

Answer the question: "{question}"

Provide:
1. Root cause analysis (2-3 sentences, use the graph metrics)
2. Key drivers behind the change
3. Risk factors to watch
4. Concrete next steps for leadership

Use numbers where possible. Be concise and business-friendly.
"""

FEEDBACK_RECALIBRATION_PROMPT = """You are a continuous learning AI agent for workforce analytics.

Pre-rollout prediction:
{prediction}

Actual post-rollout data:
{actual}

Analyze the gap between prediction and reality. Provide:
1. Accuracy assessment (was the simulation close?)
2. Key factors that were under/over-estimated
3. Recommended model recalibration steps
4. Updated confidence score for next simulation

Be precise with percentages and metrics.
"""


# ── Core inference function ───────────────────────────────────────────────────

async def call_groq_llm(
    prompt: str,
    system_message: str = "You are a helpful workforce analytics AI assistant.",
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """
    Calls the Groq LLM API and returns the response with timing metadata.

    Args:
        prompt: The user-facing prompt.
        system_message: System-level instruction.
        temperature: Override default temperature (default from settings).
        max_tokens: Override default max tokens (default from settings).

    Returns:
        dict with keys: content (str), model (str), duration_ms (int),
                        prompt_tokens (int), completion_tokens (int)

    Raises:
        RuntimeError if the Groq call fails.
    """
    client = get_groq_client()
    t_start = time.perf_counter()

    try:
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature if temperature is not None else settings.GROQ_TEMPERATURE,
            max_tokens=max_tokens if max_tokens is not None else settings.GROQ_MAX_TOKENS,
            stream=False,
        )
    except Exception as exc:
        logger.error(f"Groq API error: {exc}")
        raise RuntimeError(f"LLM inference failed: {exc}") from exc

    duration_ms = int((time.perf_counter() - t_start) * 1000)
    content = response.choices[0].message.content or ""
    usage = response.usage

    logger.info(
        "Groq inference complete",
        extra={
            "duration_ms": duration_ms,
            "model": settings.GROQ_MODEL,
            "prompt_tokens": usage.prompt_tokens if usage else 0,
            "completion_tokens": usage.completion_tokens if usage else 0,
        },
    )

    return {
        "content": content.strip(),
        "model": settings.GROQ_MODEL,
        "duration_ms": duration_ms,
        "prompt_tokens": usage.prompt_tokens if usage else 0,
        "completion_tokens": usage.completion_tokens if usage else 0,
    }


async def explain_simulation(
    simulation_results: dict[str, Any],
    scenario_name: str,
    rag_context: str = "No similar cases found.",
) -> dict[str, Any]:
    """
    Uses the mandatory workforce analysis prompt template to explain simulation results.

    Args:
        simulation_results: KPI dict from the simulation engine.
        scenario_name: Human-readable scenario identifier.
        rag_context: Retrieved similar past adoption cases from RAG.

    Returns:
        LLM response dict.
    """
    prompt = WORKFORCE_ANALYSIS_PROMPT.format(
        simulation_json=json.dumps(simulation_results, indent=2),
        scenario_name=scenario_name,
        rag_context=rag_context,
    )
    return await call_groq_llm(prompt)


async def explain_kpi_change(
    kpi_summary: dict[str, Any],
    question: str,
) -> dict[str, Any]:
    """Generates a natural-language explanation for a KPI shift."""
    prompt = INSIGHTS_EXPLAIN_PROMPT.format(
        kpi_summary=json.dumps(kpi_summary, indent=2),
        question=question,
    )
    return await call_groq_llm(prompt)


async def analyze_feedback_gap(
    prediction: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:
    """Compares predicted vs actual results for continuous learning."""
    prompt = FEEDBACK_RECALIBRATION_PROMPT.format(
        prediction=json.dumps(prediction, indent=2),
        actual=json.dumps(actual, indent=2),
    )
    return await call_groq_llm(prompt)
