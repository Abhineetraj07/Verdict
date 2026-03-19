import json

import yaml
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.database import EvalSuiteDB, get_session
from backend.app.models.schemas import EvalSuiteCreate, EvalSuiteResponse

router = APIRouter(prefix="/api/suites", tags=["suites"])


def suite_db_to_response(db_suite: EvalSuiteDB) -> EvalSuiteResponse:
    config = yaml.safe_load(db_suite.config_yaml)
    suite = EvalSuiteCreate(**config)
    return EvalSuiteResponse(
        id=db_suite.id,
        name=suite.name,
        description=suite.description,
        judges=suite.judges,
        aggregation=suite.aggregation,
        created_at=db_suite.created_at,
    )


@router.post("", response_model=EvalSuiteResponse)
async def create_suite(
    suite: EvalSuiteCreate,
    session: AsyncSession = Depends(get_session),
):
    config_yaml = yaml.dump(suite.model_dump(), default_flow_style=False)
    db_suite = EvalSuiteDB(
        name=suite.name,
        description=suite.description,
        config_yaml=config_yaml,
    )
    session.add(db_suite)
    await session.commit()
    await session.refresh(db_suite)
    return suite_db_to_response(db_suite)


@router.get("", response_model=list[EvalSuiteResponse])
async def list_suites(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(EvalSuiteDB).order_by(EvalSuiteDB.created_at.desc()))
    suites = result.scalars().all()
    return [suite_db_to_response(s) for s in suites]


@router.get("/{suite_id}", response_model=EvalSuiteResponse)
async def get_suite(suite_id: str, session: AsyncSession = Depends(get_session)):
    db_suite = await session.get(EvalSuiteDB, suite_id)
    if not db_suite:
        raise HTTPException(status_code=404, detail="Suite not found")
    return suite_db_to_response(db_suite)
