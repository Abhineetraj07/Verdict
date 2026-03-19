import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

from backend.app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def generate_uuid() -> str:
    return str(uuid.uuid4())


class EvalSuiteDB(Base):
    __tablename__ = "eval_suites"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    config_yaml = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    runs = relationship("EvalRunDB", back_populates="suite")


class DatasetDB(Base):
    __tablename__ = "datasets"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    entries_json = Column(Text, nullable=False)
    entry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    runs = relationship("EvalRunDB", back_populates="dataset")


class EvalRunDB(Base):
    __tablename__ = "eval_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    suite_id = Column(String, ForeignKey("eval_suites.id"), nullable=False)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    overall_score = Column(Float, nullable=True)
    results_json = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    suite = relationship("EvalSuiteDB", back_populates="runs")
    dataset = relationship("DatasetDB", back_populates="runs")
    judge_results = relationship("JudgeResultDB", back_populates="run")


class JudgeResultDB(Base):
    __tablename__ = "judge_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, ForeignKey("eval_runs.id"), nullable=False)
    entry_index = Column(Integer, nullable=False)
    judge_name = Column(String, nullable=False)
    dimension = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    reasoning = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    run = relationship("EvalRunDB", back_populates="judge_results")


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
