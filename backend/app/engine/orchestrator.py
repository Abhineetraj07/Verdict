import asyncio
import logging
from typing import Annotated, TypedDict

from langgraph.graph import END, StateGraph

from backend.app.engine.aggregator import (
    aggregate_scores,
    compute_dimension_breakdown,
    compute_run_stats,
)
from backend.app.engine.judges import run_judge
from backend.app.models.schemas import (
    AggregationConfig,
    DatasetEntry,
    EntryResult,
    EvalSuiteCreate,
    JudgeConfig,
    JudgeScore,
)
from backend.app.providers.gemini import GeminiProvider

logger = logging.getLogger(__name__)


def _merge_entry_results(
    existing: list[EntryResult], new: list[EntryResult]
) -> list[EntryResult]:
    """Reducer: merge entry results by extending the list."""
    return existing + new


class EvalState(TypedDict):
    suite: EvalSuiteCreate
    entries: list[DatasetEntry]
    provider: GeminiProvider
    entry_results: Annotated[list[EntryResult], _merge_entry_results]
    overall_score: float
    status: str
    error: str


async def evaluate_entry(
    entry_index: int,
    entry: DatasetEntry,
    judges: list[JudgeConfig],
    provider: GeminiProvider,
    aggregation: AggregationConfig,
) -> EntryResult:
    """Evaluate a single entry across all judges."""
    tasks = [run_judge(provider, judge, entry) for judge in judges]
    judge_scores: list[JudgeScore] = await asyncio.gather(*tasks)

    weights = {j.name: j.weight for j in judges}
    agg_score = aggregate_scores(judge_scores, aggregation, weights)

    return EntryResult(
        entry_index=entry_index,
        input=entry.input,
        output=entry.output,
        judge_scores=judge_scores,
        aggregated_score=agg_score,
    )


async def run_evaluation_node(state: EvalState) -> dict:
    """Main evaluation node: evaluates entries sequentially, judges in parallel per entry.

    With Gemini free tier (15 RPM), we process one entry at a time.
    Each entry runs its judges in parallel (typically 3 calls),
    then waits before the next entry to stay within rate limits.
    """
    suite = state["suite"]
    entries = state["entries"]
    provider = state["provider"]
    num_judges = len(suite.judges)

    logger.info("Starting evaluation: %d entries, %d judges", len(entries), num_judges)

    # Calculate delay: with 15 RPM and N judges per entry,
    # we can do floor(15/N) entries per minute
    delay_between_entries = max(1, (num_judges * 60) // 15 + 2)

    all_results: list[EntryResult] = []

    for i, entry in enumerate(entries):
        try:
            result = await evaluate_entry(i, entry, suite.judges, provider, suite.aggregation)
            all_results.append(result)
            logger.info("Entry %d/%d scored: %.2f", i + 1, len(entries), result.aggregated_score)
        except Exception as e:
            logger.error("Entry %d evaluation failed: %s", i, e)

        if i < len(entries) - 1:
            await asyncio.sleep(delay_between_entries)

    return {"entry_results": all_results, "status": "evaluated"}


async def aggregate_node(state: EvalState) -> dict:
    """Aggregate all entry results into overall scores."""
    entry_results = state["entry_results"]

    if not entry_results:
        return {"overall_score": 0.0, "status": "failed", "error": "No results to aggregate"}

    entry_scores = [r.aggregated_score for r in entry_results]
    overall = compute_run_stats(entry_scores).mean

    return {"overall_score": overall, "status": "completed"}


def build_eval_graph() -> StateGraph:
    """Build the LangGraph evaluation workflow."""
    graph = StateGraph(EvalState)

    graph.add_node("evaluate", run_evaluation_node)
    graph.add_node("aggregate", aggregate_node)

    graph.set_entry_point("evaluate")
    graph.add_edge("evaluate", "aggregate")
    graph.add_edge("aggregate", END)

    return graph.compile()


async def run_evaluation(
    suite: EvalSuiteCreate,
    entries: list[DatasetEntry],
    provider: GeminiProvider | None = None,
) -> dict:
    """Execute a full evaluation run.

    Returns:
        Dict with entry_results, overall_score, stats, dimension_breakdown.
    """
    if provider is None:
        provider = GeminiProvider()

    graph = build_eval_graph()

    initial_state: EvalState = {
        "suite": suite,
        "entries": entries,
        "provider": provider,
        "entry_results": [],
        "overall_score": 0.0,
        "status": "running",
        "error": "",
    }

    result = await graph.ainvoke(initial_state)

    all_judge_scores = [r.judge_scores for r in result["entry_results"]]
    entry_agg_scores = [r.aggregated_score for r in result["entry_results"]]

    return {
        "entry_results": result["entry_results"],
        "overall_score": result["overall_score"],
        "stats": compute_run_stats(entry_agg_scores),
        "dimension_breakdown": compute_dimension_breakdown(all_judge_scores),
        "status": result["status"],
        "error": result.get("error", ""),
    }
