from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Judge Config ---

class JudgeConfig(BaseModel):
    name: str
    dimension: str
    rubric: str
    weight: float = 1.0
    scoring_scale: int = Field(default=5, description="Max score (e.g., 5 for 1-5 scale)")


# --- Aggregation Config ---

class AggregationConfig(BaseModel):
    method: str = Field(
        default="weighted_average",
        description="One of: weighted_average, min_score, majority_vote, median, hybrid",
    )
    pass_threshold: int = Field(default=3, description="Score >= this is 'pass' for majority_vote")
    critical_dimensions: list[str] = Field(
        default_factory=list,
        description="Dimensions that must pass threshold for hybrid method",
    )
    critical_threshold: int = Field(default=3, description="Min score for critical dimensions in hybrid")


# --- Eval Suite ---

class EvalSuiteCreate(BaseModel):
    name: str
    description: str = ""
    judges: list[JudgeConfig]
    aggregation: AggregationConfig = Field(default_factory=AggregationConfig)


class EvalSuiteResponse(BaseModel):
    id: str
    name: str
    description: str
    judges: list[JudgeConfig]
    aggregation: AggregationConfig
    created_at: datetime


# --- Dataset ---

class DatasetEntry(BaseModel):
    input: str
    output: str
    expected_output: Optional[str] = None


class DatasetCreate(BaseModel):
    name: str
    entries: list[DatasetEntry]


class DatasetResponse(BaseModel):
    id: str
    name: str
    entry_count: int
    created_at: datetime


# --- Eval Run ---

class EvalRunRequest(BaseModel):
    suite_id: str
    dataset_id: str


class JudgeScore(BaseModel):
    judge_name: str
    dimension: str
    score: float
    reasoning: str


class EntryResult(BaseModel):
    entry_index: int
    input: str
    output: str
    judge_scores: list[JudgeScore]
    aggregated_score: float


class RunStats(BaseModel):
    mean: float
    median: float
    std: float
    min: float
    max: float
    q25: float
    q75: float


class DimensionBreakdown(BaseModel):
    dimension: str
    mean_score: float
    min_score: float
    max_score: float


class EvalRunResponse(BaseModel):
    id: str
    suite_id: str
    dataset_id: str
    status: str
    overall_score: Optional[float] = None
    entry_results: Optional[list[EntryResult]] = None
    stats: Optional[RunStats] = None
    dimension_breakdown: Optional[list[DimensionBreakdown]] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class EvalRunSummary(BaseModel):
    id: str
    suite_name: str
    dataset_name: str
    status: str
    overall_score: Optional[float] = None
    created_at: datetime


# --- Compare ---

class CompareResponse(BaseModel):
    runs: list[EvalRunResponse]
    score_deltas: Optional[list[float]] = None
    dimension_deltas: Optional[list[DimensionBreakdown]] = None
