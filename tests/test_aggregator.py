import pytest

from backend.app.engine.aggregator import (
    aggregate_scores,
    compute_dimension_breakdown,
    compute_run_stats,
    hybrid,
    majority_vote,
    median_score,
    min_score,
    weighted_average,
)
from backend.app.models.schemas import AggregationConfig, JudgeScore


def _score(name: str, dim: str, score: float) -> JudgeScore:
    return JudgeScore(judge_name=name, dimension=dim, score=score, reasoning="test")


# --- weighted_average ---

class TestWeightedAverage:
    def test_equal_weights(self):
        scores = [_score("a", "acc", 4), _score("b", "help", 2)]
        result = weighted_average(scores, {"a": 1.0, "b": 1.0})
        assert result == pytest.approx(3.0)

    def test_unequal_weights(self):
        scores = [_score("a", "acc", 5), _score("b", "help", 1)]
        result = weighted_average(scores, {"a": 0.8, "b": 0.2})
        assert result == pytest.approx(4.2)

    def test_empty_scores(self):
        result = weighted_average([], {})
        assert result == 0.0

    def test_missing_weight_defaults_to_one(self):
        scores = [_score("a", "acc", 4), _score("b", "help", 2)]
        result = weighted_average(scores, {})  # no weights provided
        assert result == pytest.approx(3.0)


# --- min_score ---

class TestMinScore:
    def test_returns_minimum(self):
        scores = [_score("a", "acc", 5), _score("b", "help", 2), _score("c", "tone", 4)]
        assert min_score(scores) == 2.0

    def test_empty(self):
        assert min_score([]) == 0.0

    def test_all_same(self):
        scores = [_score("a", "acc", 3), _score("b", "help", 3)]
        assert min_score(scores) == 3.0


# --- majority_vote ---

class TestMajorityVote:
    def test_majority_pass(self):
        scores = [_score("a", "acc", 4), _score("b", "help", 3), _score("c", "tone", 5)]
        assert majority_vote(scores, threshold=3) == 1.0

    def test_majority_fail(self):
        scores = [_score("a", "acc", 1), _score("b", "help", 2), _score("c", "tone", 4)]
        assert majority_vote(scores, threshold=3) == 0.0

    def test_empty(self):
        assert majority_vote([], threshold=3) == 0.0


# --- median_score ---

class TestMedianScore:
    def test_odd_count(self):
        scores = [_score("a", "acc", 1), _score("b", "help", 3), _score("c", "tone", 5)]
        assert median_score(scores) == 3.0

    def test_even_count(self):
        scores = [_score("a", "acc", 2), _score("b", "help", 4)]
        assert median_score(scores) == 3.0

    def test_empty(self):
        assert median_score([]) == 0.0


# --- hybrid ---

class TestHybrid:
    def test_passes_critical_gate(self):
        scores = [_score("a", "acc", 4), _score("b", "tone", 3)]
        result = hybrid(scores, {"a": 0.5, "b": 0.5}, ["tone"], critical_threshold=3)
        assert result == pytest.approx(3.5)

    def test_fails_critical_gate(self):
        scores = [_score("a", "acc", 5), _score("b", "tone", 1)]
        result = hybrid(scores, {"a": 0.5, "b": 0.5}, ["tone"], critical_threshold=3)
        assert result == 0.0

    def test_no_critical_dimensions(self):
        scores = [_score("a", "acc", 4), _score("b", "help", 2)]
        result = hybrid(scores, {"a": 0.5, "b": 0.5}, [], critical_threshold=3)
        assert result == pytest.approx(3.0)


# --- aggregate_scores (router) ---

class TestAggregateScores:
    def test_routes_to_weighted_average(self):
        config = AggregationConfig(method="weighted_average")
        scores = [_score("a", "acc", 4), _score("b", "help", 2)]
        result = aggregate_scores(scores, config, {"a": 1.0, "b": 1.0})
        assert result == pytest.approx(3.0)

    def test_routes_to_min_score(self):
        config = AggregationConfig(method="min_score")
        scores = [_score("a", "acc", 5), _score("b", "help", 2)]
        result = aggregate_scores(scores, config, {})
        assert result == 2.0

    def test_routes_to_hybrid(self):
        config = AggregationConfig(
            method="hybrid", critical_dimensions=["tone"], critical_threshold=3
        )
        scores = [_score("a", "acc", 5), _score("b", "tone", 1)]
        result = aggregate_scores(scores, config, {"a": 0.5, "b": 0.5})
        assert result == 0.0

    def test_empty_scores(self):
        config = AggregationConfig(method="weighted_average")
        assert aggregate_scores([], config, {}) == 0.0

    def test_unknown_method_defaults_to_weighted_average(self):
        config = AggregationConfig(method="nonexistent")
        scores = [_score("a", "acc", 4), _score("b", "help", 2)]
        result = aggregate_scores(scores, config, {"a": 1.0, "b": 1.0})
        assert result == pytest.approx(3.0)


# --- compute_run_stats ---

class TestComputeRunStats:
    def test_basic_stats(self):
        stats = compute_run_stats([1.0, 2.0, 3.0, 4.0, 5.0])
        assert stats.mean == pytest.approx(3.0)
        assert stats.median == 3.0
        assert stats.min == 1.0
        assert stats.max == 5.0
        assert stats.std > 0

    def test_single_value(self):
        stats = compute_run_stats([4.0])
        assert stats.mean == 4.0
        assert stats.std == 0.0

    def test_empty(self):
        stats = compute_run_stats([])
        assert stats.mean == 0.0
        assert stats.min == 0.0


# --- compute_dimension_breakdown ---

class TestComputeDimensionBreakdown:
    def test_groups_by_dimension(self):
        all_scores = [
            [_score("a", "accuracy", 4), _score("b", "tone", 3)],
            [_score("a", "accuracy", 2), _score("b", "tone", 5)],
        ]
        breakdown = compute_dimension_breakdown(all_scores)
        dims = {b.dimension: b for b in breakdown}

        assert "accuracy" in dims
        assert dims["accuracy"].mean_score == pytest.approx(3.0)
        assert dims["accuracy"].min_score == 2.0
        assert dims["accuracy"].max_score == 4.0

        assert "tone" in dims
        assert dims["tone"].mean_score == pytest.approx(4.0)

    def test_empty(self):
        assert compute_dimension_breakdown([]) == []
