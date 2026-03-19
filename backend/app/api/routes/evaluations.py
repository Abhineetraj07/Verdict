import json
from datetime import datetime, timezone

import yaml
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.engine.orchestrator import run_evaluation
from backend.app.models.database import (
    DatasetDB,
    EvalRunDB,
    EvalSuiteDB,
    JudgeResultDB,
    async_session,
    get_session,
)
from backend.app.models.schemas import (
    DatasetEntry,
    EvalRunRequest,
    EvalRunResponse,
    EvalRunSummary,
    EvalSuiteCreate,
)

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])


async def _execute_eval_run(run_id: str, suite_config: dict, entries_data: list[dict]):
    """Background task that executes the evaluation."""
    async with async_session() as session:
        db_run = await session.get(EvalRunDB, run_id)
        if not db_run:
            return

        try:
            db_run.status = "running"
            await session.commit()

            suite = EvalSuiteCreate(**suite_config)
            entries = [DatasetEntry(**e) for e in entries_data]

            result = await run_evaluation(suite, entries)

            db_run.status = result["status"]
            db_run.overall_score = result["overall_score"]
            db_run.results_json = json.dumps(
                {
                    "entry_results": [r.model_dump() for r in result["entry_results"]],
                    "stats": result["stats"].model_dump(),
                    "dimension_breakdown": [d.model_dump() for d in result["dimension_breakdown"]],
                }
            )
            db_run.completed_at = datetime.now(timezone.utc)

            for entry_result in result["entry_results"]:
                for js in entry_result.judge_scores:
                    judge_result = JudgeResultDB(
                        run_id=run_id,
                        entry_index=entry_result.entry_index,
                        judge_name=js.judge_name,
                        dimension=js.dimension,
                        score=js.score,
                        reasoning=js.reasoning,
                    )
                    session.add(judge_result)

            await session.commit()

        except Exception as e:
            db_run.status = "failed"
            db_run.error_message = str(e)
            db_run.completed_at = datetime.now(timezone.utc)
            await session.commit()


@router.post("/run", response_model=EvalRunSummary)
async def start_eval_run(
    request: EvalRunRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    db_suite = await session.get(EvalSuiteDB, request.suite_id)
    if not db_suite:
        raise HTTPException(status_code=404, detail="Suite not found")

    db_dataset = await session.get(DatasetDB, request.dataset_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    db_run = EvalRunDB(suite_id=request.suite_id, dataset_id=request.dataset_id)
    session.add(db_run)
    await session.commit()
    await session.refresh(db_run)

    suite_config = yaml.safe_load(db_suite.config_yaml)
    entries_data = json.loads(db_dataset.entries_json)

    background_tasks.add_task(_execute_eval_run, db_run.id, suite_config, entries_data)

    return EvalRunSummary(
        id=db_run.id,
        suite_name=db_suite.name,
        dataset_name=db_dataset.name,
        status="pending",
        created_at=db_run.created_at,
    )


@router.get("", response_model=list[EvalRunSummary])
async def list_runs(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(EvalRunDB, EvalSuiteDB.name, DatasetDB.name)
        .join(EvalSuiteDB)
        .join(DatasetDB)
        .order_by(EvalRunDB.created_at.desc())
    )
    rows = result.all()
    return [
        EvalRunSummary(
            id=run.id,
            suite_name=suite_name,
            dataset_name=dataset_name,
            status=run.status,
            overall_score=run.overall_score,
            created_at=run.created_at,
        )
        for run, suite_name, dataset_name in rows
    ]


@router.get("/{run_id}", response_model=EvalRunResponse)
async def get_run(run_id: str, session: AsyncSession = Depends(get_session)):
    db_run = await session.get(EvalRunDB, run_id)
    if not db_run:
        raise HTTPException(status_code=404, detail="Run not found")

    response = EvalRunResponse(
        id=db_run.id,
        suite_id=db_run.suite_id,
        dataset_id=db_run.dataset_id,
        status=db_run.status,
        overall_score=db_run.overall_score,
        error_message=db_run.error_message,
        created_at=db_run.created_at,
        completed_at=db_run.completed_at,
    )

    if db_run.results_json:
        results = json.loads(db_run.results_json)
        response.entry_results = results.get("entry_results")
        response.stats = results.get("stats")
        response.dimension_breakdown = results.get("dimension_breakdown")

    return response
