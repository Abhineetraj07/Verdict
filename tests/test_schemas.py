import pytest
from pydantic import ValidationError

from backend.app.models.schemas import (
    AggregationConfig,
    DatasetEntry,
    EvalSuiteCreate,
    JudgeConfig,
    JudgeScore,
    EntryResult,
)


class TestJudgeConfig:
    def test_defaults(self):
        j = JudgeConfig(name="test", dimension="acc", rubric="score 1-5")
        assert j.weight == 1.0
        assert j.scoring_scale == 5

    def test_custom_values(self):
        j = JudgeConfig(
            name="judge1", dimension="tone", rubric="r", weight=0.4, scoring_scale=10
        )
        assert j.weight == 0.4
        assert j.scoring_scale == 10


class TestAggregationConfig:
    def test_defaults(self):
        a = AggregationConfig()
        assert a.method == "weighted_average"
        assert a.pass_threshold == 3
        assert a.critical_dimensions == []
        assert a.critical_threshold == 3

    def test_hybrid_config(self):
        a = AggregationConfig(
            method="hybrid", critical_dimensions=["safety"], critical_threshold=2
        )
        assert a.method == "hybrid"
        assert "safety" in a.critical_dimensions


class TestEvalSuiteCreate:
    def test_minimal(self):
        suite = EvalSuiteCreate(
            name="test",
            judges=[JudgeConfig(name="j", dimension="d", rubric="r")],
        )
        assert suite.description == ""
        assert suite.aggregation.method == "weighted_average"

    def test_full(self):
        suite = EvalSuiteCreate(
            name="full",
            description="a suite",
            judges=[
                JudgeConfig(name="a", dimension="acc", rubric="r", weight=0.6),
                JudgeConfig(name="b", dimension="tone", rubric="r", weight=0.4),
            ],
            aggregation=AggregationConfig(method="min_score"),
        )
        assert len(suite.judges) == 2
        assert suite.aggregation.method == "min_score"


class TestDatasetEntry:
    def test_required_fields(self):
        e = DatasetEntry(input="hello", output="world")
        assert e.expected_output is None

    def test_with_expected(self):
        e = DatasetEntry(input="q", output="a", expected_output="ref")
        assert e.expected_output == "ref"

    def test_missing_fields_raises(self):
        with pytest.raises(ValidationError):
            DatasetEntry(input="hello")  # type: ignore


class TestJudgeScore:
    def test_creation(self):
        s = JudgeScore(judge_name="j", dimension="acc", score=4.5, reasoning="good")
        assert s.score == 4.5
        assert s.reasoning == "good"


class TestEntryResult:
    def test_creation(self):
        r = EntryResult(
            entry_index=0,
            input="q",
            output="a",
            judge_scores=[
                JudgeScore(judge_name="j", dimension="acc", score=4, reasoning="ok")
            ],
            aggregated_score=4.0,
        )
        assert r.aggregated_score == 4.0
        assert len(r.judge_scores) == 1
