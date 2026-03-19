from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import datasets, evaluations, results, suites
from backend.app.models.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Verdict",
    description="Federated Prompt Evaluation Framework — Multi-judge LLM output evaluation",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(suites.router)
app.include_router(datasets.router)
app.include_router(evaluations.router)
app.include_router(results.router)


@app.get("/")
async def root():
    return {
        "name": "Verdict",
        "version": "0.1.0",
        "description": "Federated Prompt Evaluation Framework",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
