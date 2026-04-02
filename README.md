<h1 align="center">⚖️ Verdict — Federated LLM Evaluation Framework</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/LangGraph-Orchestration-2CA5E0?style=for-the-badge" />
  <img src="https://img.shields.io/badge/React-Dashboard-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/Google_Gemini-LLM-4285F4?style=for-the-badge&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  <img src="https://img.shields.io/badge/Tests-46_passing-brightgreen?style=for-the-badge&logo=pytest&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />
</p>

<p align="center">
  <img src="https://github.com/Abhineetraj07/Verdict/actions/workflows/ci.yml/badge.svg" alt="CI" />
  <img src="https://img.shields.io/github/last-commit/Abhineetraj07/Verdict?style=flat-square&color=blue" alt="Last Commit" />
  <img src="https://img.shields.io/github/stars/Abhineetraj07/Verdict?style=flat-square&color=yellow" alt="Stars" />
</p>

<p align="center">
  An open-source framework where <b>multiple AI judges independently score LLM outputs</b> across configurable dimensions, aggregate results using 5 strategies, and surface findings in an interactive analytics dashboard.
</p>

---

## 🤔 Why Verdict?

Evaluating LLM outputs manually doesn't scale. Verdict automates it by:

- 🧑‍⚖️ **Multi-judge panel** — each judge owns one quality dimension (accuracy, tone, safety…) with its own rubric
- ⚡ **Parallel execution** — judges run concurrently per entry via `asyncio.gather`
- 🎛️ **5 aggregation strategies** — from simple weighted average to hybrid critical-dimension gating
- 📊 **Rich dashboard** — radar charts, heatmaps, score distributions, per-entry drill-down
- 🔀 **Run comparison** — compare two evaluation runs side-by-side to track prompt improvements

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React Dashboard                    │
│  (Radar Charts · Heatmaps · Score Distributions)    │
└──────────────────────┬──────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────┐
│                  FastAPI Backend                      │
│  ┌─────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │  Suites │  │ Datasets │  │   Evaluations      │  │
│  │  CRUD   │  │  CRUD    │  │  (Background task) │  │
│  └─────────┘  └──────────┘  └────────┬───────────┘  │
│                                      │               │
│  ┌───────────────────────────────────▼────────────┐  │
│  │          LangGraph Orchestrator                │  │
│  │  ┌──────────┐    ┌───────────┐    ┌────────┐  │  │
│  │  │ Evaluate │───▶│ Aggregate │───▶│  END   │  │  │
│  │  │ (judges) │    │ (scores)  │    └────────┘  │  │
│  │  └──────────┘    └───────────┘                │  │
│  └───────────────────────────────────────────────┘  │
│                       │                              │
│  ┌────────────────────▼───────────────────────────┐  │
│  │   Gemini Provider (rate limit · retry · JSON)  │  │
│  └────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │  SQLite + SQLAlchemy async (4 tables)          │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

---

## ✨ Features

### 🧑‍⚖️ Evaluation Engine
- **LangGraph StateGraph** orchestration with typed state and annotated reducers
- **Parallel judge execution** within each entry via `asyncio.gather`
- **Sequential entry processing** with calculated delays — respects Gemini's 15 RPM free tier
- **Exponential backoff retry** (5 attempts, 8–120s) via `tenacity`
- **Rate limiting** via `asyncio.Semaphore`

### 🎛️ 5 Aggregation Methods

| Method | Best For |
|--------|----------|
| **Weighted Average** | Default — all dimensions matter with different importance |
| **Min Score** | Conservative — any failed dimension = overall fail |
| **Majority Vote** | Binary pass/fail with configurable threshold |
| **Median** | Robust to outlier judges giving extreme scores |
| **Hybrid** | Critical dimension gating + weighted average (e.g. `safety < 3` = instant FAIL) |

### 📊 Dashboard Visualizations
- **Radar chart** — dimension scores at a glance
- **Bar chart** — per-entry score distribution
- **Heatmap** — Entries × Dimensions score matrix
- **Entry drill-down** — expand to see full judge reasoning
- **Run comparison** — overlaid radar + per-entry deltas

### 🖥️ CLI
```bash
python -m cli.verdict_cli run --suite suite.yaml --dataset data.json --output results.json
python -m cli.verdict_cli init   # Generate example files
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- [Google Gemini API key](https://aistudio.google.com/apikey) (free tier works)

### Installation

```bash
git clone https://github.com/Abhineetraj07/Verdict.git
cd Verdict

# Backend
conda create -n verdict python=3.11 -y
conda activate verdict
pip install -r backend/requirements.txt

# Environment
cp .env.example .env
# Add your GEMINI_API_KEY to .env

# Frontend
cd frontend && npm install && cd ..
```

### Run

```bash
# Terminal 1 — Backend
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Open **http://localhost:5173** — dashboard ready.

### Docker (one command)

```bash
docker compose up --build
```

Backend at `:8000` · Frontend at `:5173`

### Tests

```bash
pytest tests/ -v   # 46 tests across aggregator, schemas, judges, API
```

---

## 📖 Usage

### 1. Define a Judge Suite (YAML)

```yaml
name: "Customer Support Bot Eval"
judges:
  - name: "accuracy_judge"
    dimension: "accuracy"
    rubric: "Score factual accuracy 1-5. Deduct for wrong info or hallucinations."
    weight: 0.4
    scoring_scale: 5
  - name: "tone_judge"
    dimension: "tone"
    rubric: "Score professional tone 1-5. Rude or dismissive responses score 1."
    weight: 0.3
    scoring_scale: 5
aggregation:
  method: "hybrid"
  critical_dimensions: ["tone"]
  critical_threshold: 2
```

### 2. Create a Dataset (JSON)

```json
{
  "name": "Support Samples",
  "entries": [
    { "input": "How do I reset my password?", "output": "Go to login, click Forgot Password..." },
    { "input": "My order is late",            "output": "Just google it lol" }
  ]
}
```

### 3. Run & Analyse

Select suite + dataset in the dashboard → click **Run Evaluation** → drill down into per-entry reasoning → compare against previous runs.

---

## 📁 Project Structure

```
Verdict/
├── backend/
│   └── app/
│       ├── main.py              # FastAPI app — lifespan, CORS, routers
│       ├── config.py            # Pydantic settings from .env
│       ├── models/
│       │   ├── schemas.py       # 13 Pydantic models
│       │   └── database.py      # SQLAlchemy async ORM (4 tables)
│       ├── api/routes/          # suites, datasets, evaluations, results
│       ├── engine/
│       │   ├── orchestrator.py  # LangGraph StateGraph
│       │   ├── judges.py        # Parallel judge execution
│       │   └── aggregator.py    # 5 aggregation strategies
│       └── providers/
│           └── gemini.py        # Rate limiting + retry
├── frontend/src/                # React · TypeScript · Vite · TailwindCSS
├── cli/verdict_cli.py           # Typer CLI with Rich output
├── tests/                       # 46 tests
├── examples/                    # 4 ready-to-use suite + dataset pairs
├── docker-compose.yml
└── Dockerfile
```

---

## 🔌 API Reference

```
POST   /api/suites              Create evaluation suite
GET    /api/suites              List all suites
POST   /api/datasets            Create dataset
POST   /api/evaluations/run     Trigger evaluation run (background)
GET    /api/evaluations/{id}    Get run results
GET    /api/compare?run_ids=a,b Compare runs side-by-side
GET    /health                  Health check
```

Full interactive docs at **http://localhost:8000/docs**

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI · Python 3.11 · SQLAlchemy async · Pydantic v2 |
| **LLM** | Google Gemini (free tier) |
| **Orchestration** | LangGraph (StateGraph) |
| **Frontend** | React · TypeScript · Vite · TailwindCSS · Recharts |
| **Testing** | pytest · pytest-asyncio · httpx (46 tests) |
| **Deployment** | Docker + Nginx |

---

## 👨‍💻 Author

**Abhineet Raj** · CS @ SRM Institute of Science & Technology  
🌐 [Portfolio](https://aabhineet07-portfolio.netlify.app/) · 🐙 [GitHub](https://github.com/Abhineetraj07)

---

## 📄 License

MIT License
