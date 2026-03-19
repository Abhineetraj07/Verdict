import statistics
from collections import Counter

from backend.app.models.schemas import (
    AggregationConfig,
    DimensionBreakdown,
    JudgeScore,
    RunStats,
)


def weighted_average(scores: list[JudgeScore], weights: dict[str, float]) -> float:
    """Weighted average of judge scores."""
    total_weight = sum(weights.get(s.judge_name, 1.0) for s in scores)
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(s.score * weights.get(s.judge_name, 1.0) for s in scores)
    return weighted_sum / total_weight


def min_score(scores: list[JudgeScore], **_kwargs) -> float:
    """Take the minimum score across all judges (conservative)."""
    if not scores:
        return 0.0
    return min(s.score for s in scores)


def majority_vote(scores: list[JudgeScore], threshold: int = 3, **_kwargs) -> float:
    """Convert to pass/fail using threshold, return fraction that passed."""
    if not scores:
        return 0.0
    votes = [1 if s.score >= threshold else 0 for s in scores]
    counter = Counter(votes)
    majority = counter.most_common(1)[0][0]
    return float(majority)


def median_score(scores: list[JudgeScore], **_kwargs) -> float:
    """Take the median score across all judges."""
    if not scores:
        return 0.0
    return statistics.median(s.score for s in scores)


def hybrid(
    scores: list[JudgeScore],
    weights: dict[str, float],
    critical_dimensions: list[str],
    critical_threshold: int = 3,
) -> float:
    """Hard-gate on critical dimensions, then weighted average on the rest.

    If any critical dimension is below the threshold, return 0 (FAIL).
    Otherwise, compute the weighted average.
    """
    for s in scores:
        if s.dimension in critical_dimensions and s.score < critical_threshold:
            return 0.0
    return weighted_average(scores, weights)


def aggregate_scores(
    scores: list[JudgeScore],
    config: AggregationConfig,
    weights: dict[str, float],
) -> float:
    """Aggregate judge scores using the configured method."""
    if not scores:
        return 0.0

    match config.method:
        case "weighted_average":
            return weighted_average(scores, weights)
        case "min_score":
            return min_score(scores)
        case "majority_vote":
            return majority_vote(scores, threshold=config.pass_threshold)
        case "median":
            return median_score(scores)
        case "hybrid":
            return hybrid(
                scores,
                weights,
                config.critical_dimensions,
                config.critical_threshold,
            )
        case _:
            return weighted_average(scores, weights)


def compute_run_stats(entry_scores: list[float]) -> RunStats:
    """Compute statistics across all entry aggregated scores."""
    if not entry_scores:
        return RunStats(mean=0, median=0, std=0, min=0, max=0, q25=0, q75=0)

    sorted_scores = sorted(entry_scores)
    n = len(sorted_scores)

    return RunStats(
        mean=statistics.mean(sorted_scores),
        median=statistics.median(sorted_scores),
        std=statistics.stdev(sorted_scores) if n > 1 else 0.0,
        min=sorted_scores[0],
        max=sorted_scores[-1],
        q25=sorted_scores[n // 4] if n >= 4 else sorted_scores[0],
        q75=sorted_scores[3 * n // 4] if n >= 4 else sorted_scores[-1],
    )


def compute_dimension_breakdown(
    all_scores: list[list[JudgeScore]],
) -> list[DimensionBreakdown]:
    """Compute per-dimension stats across all entries."""
    dim_scores: dict[str, list[float]] = {}

    for entry_scores in all_scores:
        for s in entry_scores:
            dim_scores.setdefault(s.dimension, []).append(s.score)

    breakdowns = []
    for dim, scores in dim_scores.items():
        breakdowns.append(
            DimensionBreakdown(
                dimension=dim,
                mean_score=statistics.mean(scores),
                min_score=min(scores),
                max_score=max(scores),
            )
        )

    return breakdowns
