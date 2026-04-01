# Verdict — Federated Prompt Evaluation Framework

An open-source LLM evaluation framework where multiple AI judges independently score outputs across configurable dimensions, aggregate results using 5 strategies, and present findings in an interactive dashboard.

Built with **FastAPI**, **LangGraph**, **Google Gemini**, **React**, and **Recharts**.

## Why Verdict?

Evaluating LLM outputs manually doesn't scale. Verdict automates it by:

- **Multi-dimensional scoring** — Each judge evaluates a specific quality (accuracy, tone, safety, etc.) with its own rubric
- **Parallel judge execution** — Judges run concurrently per entry using `asyncio.gather`
- **Configurable aggregation** — 5 methods to combine scores based on your use case
- **Interactive dashboard** — Radar charts, heatmaps, score distributions, and drill-down reasoning
- **Side-by-side comparison** — Compare runs to track if your prompts are improving

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Dashboard                    │
│  (Radar Charts, Heatmaps, Score Distributions)      │
└──────────────────────┬──────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────┐
│                  FastAPI Backend                      │
│  ┌─────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │  Suites │  │ Datasets │  │   Evaluations      │  │
│  │  CRUD   │  │  CRUD    │  │   (Background)     │  │
│  └─────────┘  └──────────┘  └────────┬───────────┘  │
│                                      │               │
│  ┌───────────────────────────────────▼────────────┐  │
│  │          LangGraph Orchestrator                │  │
│  │  ┌──────────┐    ┌───────────┐    ┌────────┐  │  │
│  │  │ Evaluate │───>│ Aggregate │───>│  END   │  │  │
│  │  │ (judges) │    │ (scores)  │    │        │  │  │
│  │  └──────────┘    └───────────┘    └────────┘  │  │
│  └───────────────────────────────────────────────┘  │
│                       │                              │
│  ┌────────────────────▼───────────────────────────┐  │
│  │           Gemini Provider                      │  │
│  │  (Rate limiting, Retry, Structured JSON)       │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │  SQLite + SQLAlchemy (async)                   │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

## Features

### Evaluation Engine
- **LangGraph StateGraph** orchestration with typed state and annotated reducers
- **Parallel judge execution** within each entry via `asyncio.gather`
- **Sequential entry processing** with calculated delays to respect Gemini's 15 RPM free tier
- **Exponential backoff retry** (5 attempts, 8-120s wait) using `tenacity`
- **Rate limiting** via `asyncio.Semaphore`

### 5 Aggregation Methods

| Method | When to use |
|---|---|
| **Weighted Average** | Default — all dimensions matter with different importance |
| **Min Score** | Conservative — any failed dimension = overall fail |
| **Majority Vote** | Binary pass/fail decisions with configurable threshold |
| **Median** | Robust to outlier judges giving extreme scores |
| **Hybrid** | Critical dimension gating + weighted average (e.g., safety < 3 = instant FAIL) |

### Dashboard Visualizations
- **Radar chart** — Dimension scores at a glance
- **Bar chart** — Per-entry score distribution
- **Heatmap** — Entries x Dimensions score matrix
- **Entry drill-down** — Expand to see judge reasoning
- **Run comparison** — Overlaid radar + per-entry deltas

### CLI
```bash
python -m cli.verdict_cli run --suite suite.yaml --dataset data.json --output results.json
python -m cli.verdict_cli init  # Generate example files
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- [Google Gemini API key](https://aistudio.google.com/apikey) (free tier works)

### Setup

```bash
# Clone
git clone https://github.com/yourusername/verdict.git
cd verdict

# Backend
conda create -n verdict python=3.11 -y
conda activate verdict
pip install -r backend/requirements.txt

# Environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Frontend
cd frontend
npm install
cd ..
```

### Run

```bash
# Terminal 1 — Backend
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Open **http://localhost:5173** — the dashboard is ready.

### Docker

```bash
docker compose up --build
```

Backend at `:8000`, frontend at `:5173`.

### Run Tests

```bash
pytest tests/ -v
```

## Usage

### 1. Create a Suite
Define your judge panel — each judge has a dimension, rubric, weight, and scoring scale.

```yaml
name: "Customer Support Bot Eval"
judges:
  - name: "accuracy_judge"
    dimension: "accuracy"
    rubric: "Score on factual accuracy (1-5)..."
    weight: 0.4
    scoring_scale: 5
  - name: "tone_judge"
    dimension: "tone"
    rubric: "Score professional tone (1-5)..."
    weight: 0.3
    scoring_scale: 5
aggregation:
  method: "hybrid"
  critical_dimensions: ["tone"]
  critical_threshold: 2
```

### 2. Create a Dataset
Provide input-output pairs to evaluate.

```json
{
  "name": "Support Samples",
  "entries": [
    {"input": "How do I reset my password?", "output": "Go to login page, click Forgot Password..."},
    {"input": "My order is late", "output": "Just google it lol"}
  ]
}
```

### 3. Run Evaluation
Select suite + dataset from the Runs page and click **Run Evaluation**. The engine:
1. Processes each entry sequentially (rate limit aware)
2. Runs all judges in parallel per entry
3. Aggregates scores using your configured method
4. Saves results to the database

### 4. Analyze Results
View radar charts, heatmaps, and per-entry drill-downs. The bad response ("Just google it lol") will score low across all dimensions — and the hybrid aggregation's tone gate will flag it as a hard FAIL.

### 5. Compare Runs
Tweak your prompts, run again on the same dataset, then compare side-by-side to see what improved.

## Project Structure

```
verdict/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI app with lifespan, CORS, routers
│       ├── config.py            # Pydantic settings from .env
│       ├── models/
│       │   ├── schemas.py       # 13 Pydantic models (validation layer)
│       │   └── database.py      # SQLAlchemy async ORM (4 tables)
│       ├── api/routes/
│       │   ├── suites.py        # Suite CRUD
│       │   ├── datasets.py      # Dataset CRUD
│       │   ├── evaluations.py   # Run trigger + background execution
│       │   └── results.py       # Run comparison endpoint
│       ├── engine/
│       │   ├── orchestrator.py  # LangGraph StateGraph workflow
│       │   ├── judges.py        # Prompt building + judge execution
│       │   └── aggregator.py    # 5 aggregation strategies
│       └── providers/
│           ├── base.py          # Abstract LLM provider (Strategy pattern)
│           └── gemini.py        # Gemini with rate limiting + retry
├── frontend/src/
│   ├── api/                     # TypeScript types, axios client, React Query hooks
│   ├── components/              # Layout, StatusBadge, ScoreBar
│   └── pages/                   # Dashboard, Suites, Datasets, Runs, RunDetail, Compare
├── cli/
│   └── verdict_cli.py           # Typer CLI with Rich output
├── tests/                       # 46 tests (aggregator, schemas, judges, API)
├── examples/                    # 4 ready-to-use suite + dataset pairs
├── docker-compose.yml
└── Dockerfile
```

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.11, SQLAlchemy (async), Pydantic |
| LLM | Google Gemini (free tier) |
| Orchestration | LangGraph (StateGraph) |
| Frontend | React, TypeScript, Vite, TailwindCSS |
| Visualizations | Recharts (radar, bar, heatmap) |
| State Management | TanStack React Query |
| CLI | Typer + Rich |
| Testing | pytest + pytest-asyncio + httpx |
| Deployment | Docker + Nginx |

## API Endpoints

```
POST   /api/suites              # Create eval suite
GET    /api/suites              # List all suites
GET    /api/suites/{id}         # Get suite details

POST   /api/datasets            # Create dataset
GET    /api/datasets            # List datasets

POST   /api/evaluations/run     # Trigger evaluation run
GET    /api/evaluations         # List all runs
GET    /api/evaluations/{id}    # Get run results

GET    /api/compare?run_ids=a,b # Compare runs side-by-side
GET    /health                  # Health check
```

## License

MIT
