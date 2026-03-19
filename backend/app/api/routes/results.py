import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.database import EvalRunDB, get_session
from backend.app.models.schemas import CompareResponse, EvalRunResponse

router = APIRouter(prefix="/api/compare", tags=["compare"])


@router.get("", response_model=CompareResponse)
async def compare_runs(
    run_ids: str = Query(..., description="Comma-separated run IDs to compare"),
    session: AsyncSession = Depends(get_session),
):
    ids = [rid.strip() for rid in run_ids.split(",")]
    if len(ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 run IDs to compare")

    runs: list[EvalRunResponse] = []
    for run_id in ids:
        db_run = await session.get(EvalRunDB, run_id)
        if not db_run:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        if db_run.status != "completed":
            raise HTTPException(status_code=400, detail=f"Run {run_id} is not completed")

        response = EvalRunResponse(
            id=db_run.id,
            suite_id=db_run.suite_id,
            dataset_id=db_run.dataset_id,
            status=db_run.status,
            overall_score=db_run.overall_score,
            created_at=db_run.created_at,
            completed_at=db_run.completed_at,
        )

        if db_run.results_json:
            results = json.loads(db_run.results_json)
            response.entry_results = results.get("entry_results")
            response.stats = results.get("stats")
            response.dimension_breakdown = results.get("dimension_breakdown")

        runs.append(response)

    score_deltas = None
    if all(r.overall_score is not None for r in runs) and len(runs) == 2:
        score_deltas = [runs[1].overall_score - runs[0].overall_score]

    return CompareResponse(runs=runs, score_deltas=score_deltas)
