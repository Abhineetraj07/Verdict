import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.database import DatasetDB, get_session
from backend.app.models.schemas import DatasetCreate, DatasetResponse

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


@router.post("", response_model=DatasetResponse)
async def create_dataset(
    dataset: DatasetCreate,
    session: AsyncSession = Depends(get_session),
):
    entries_json = json.dumps([e.model_dump() for e in dataset.entries])
    db_dataset = DatasetDB(
        name=dataset.name,
        entries_json=entries_json,
        entry_count=len(dataset.entries),
    )
    session.add(db_dataset)
    await session.commit()
    await session.refresh(db_dataset)
    return DatasetResponse(
        id=db_dataset.id,
        name=db_dataset.name,
        entry_count=db_dataset.entry_count,
        created_at=db_dataset.created_at,
    )


@router.get("", response_model=list[DatasetResponse])
async def list_datasets(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(DatasetDB).order_by(DatasetDB.created_at.desc()))
    datasets = result.scalars().all()
    return [
        DatasetResponse(
            id=d.id, name=d.name, entry_count=d.entry_count, created_at=d.created_at
        )
        for d in datasets
    ]


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str, session: AsyncSession = Depends(get_session)):
    db_dataset = await session.get(DatasetDB, dataset_id)
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetResponse(
        id=db_dataset.id,
        name=db_dataset.name,
        entry_count=db_dataset.entry_count,
        created_at=db_dataset.created_at,
    )
