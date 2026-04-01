# Understanding Verdict — Complete Code Guide

This document explains every part of the Verdict project from scratch.
If you're new to FastAPI, SQLAlchemy, LangGraph, or async Python — this is for you.

---

## Table of Contents

1. [What is Verdict?](#1-what-is-verdict)
2. [How Prompt Evaluation Works](#2-how-prompt-evaluation-works)
3. [Project Structure](#3-project-structure)
4. [The Complete Data Flow](#4-the-complete-data-flow)
5. [File-by-File Explanation](#5-file-by-file-explanation)
   - [config.py — Settings](#51-configpy--settings)
   - [schemas.py — Data Shapes](#52-schemaspy--data-shapes)
   - [database.py — Storage](#53-databasepy--storage)
   - [base.py — Abstract Provider](#54-basepy--abstract-provider)
   - [gemini.py — Gemini API](#55-geminipy--gemini-api)
   - [judges.py — Judge Logic](#56-judgespy--judge-logic)
   - [aggregator.py — Scoring Math](#57-aggregatorpy--scoring-math)
   - [orchestrator.py — LangGraph Workflow](#58-orchestratorpy--langgraph-workflow)
   - [main.py — FastAPI Server](#59-mainpy--fastapi-server)
   - [API Routes](#510-api-routes)
   - [verdict_cli.py — CLI Tool](#511-verdict_clipy--cli-tool)
6. [Key Concepts Explained](#6-key-concepts-explained)
7. [Live Test Walkthrough](#7-live-test-walkthrough)

---

## 1. What is Verdict?

Verdict is an LLM evaluation framework. In simple terms:

**Problem:** You built a chatbot. How do you know if its responses are good?
You can't manually read thousands of responses. And "good" means different
things — accurate? helpful? safe? polite?

**Solution:** Use another LLM (Gemini) as a "judge" to automatically score
your chatbot's responses across multiple dimensions (accuracy, helpfulness, tone, etc.)

**What makes Verdict special:**
- Multiple judges evaluate different aspects (not just one score)
- 5 different ways to combine scores (weighted average, min-score, etc.)
- LangGraph orchestrates everything (parallel execution, batching)
- Full-stack: CLI + REST API + (upcoming) React dashboard

---

## 2. How Prompt Evaluation Works

### The Naive Way (Manual)
```
You: *reads chatbot response* "Hmm, this seems okay... I'd give it a 4/5"
Problem: Slow, subjective, not scalable
```

### The LLM-as-a-Judge Way (What Verdict Does)
```
Step 1: You have a chatbot response to evaluate
  Input:  "How do I reset my password?"
  Output: "Just google it lol"

Step 2: Verdict sends this to Gemini with instructions:
  "You are an accuracy evaluator. Score this 1-5. 
   Respond as JSON: {score: X, reasoning: '...'}"

Step 3: Gemini responds:
  {score: 1, reasoning: "Response provides no actual information"}

Step 4: Repeat with different judges:
  Accuracy judge:    score=1 (completely wrong)
  Helpfulness judge: score=1 (not helpful at all)  
  Tone judge:        score=1 (rude and dismissive)

Step 5: Combine scores:
  Weighted average: (1×0.4 + 1×0.3 + 1×0.3) / 1.0 = 1.0
  → This response is terrible.
```

### Multi-Dimensional Evaluation
One number isn't enough. A response can be:
- Accurate but rude
- Helpful but contains made-up facts
- Polite but completely wrong

So Verdict uses MULTIPLE judges, each focused on ONE dimension:

```
                    ┌─ Accuracy Judge  → "Is this factually correct?"
Input + Output ─────┼─ Helpfulness Judge → "Does this help the user?"
                    └─ Tone Judge → "Is this professional?"
                                          │
                                    Aggregate Scores
                                          │
                                    Final Score: 3.8/5
```

---

## 3. Project Structure

```
verdict/
├── .env                    ← Your secret API key (never committed to git)
├── .env.example            ← Template showing what .env should look like
├── .gitignore              ← Tells git which files to ignore
│
├── backend/                ← All Python server code
│   ├── requirements.txt    ← Python packages needed (pip install -r)
│   └── app/
│       ├── main.py              ← Server entry point (starts FastAPI)
│       ├── config.py            ← Reads settings from .env
│       │
│       ├── models/              ← DATA LAYER
│       │   ├── schemas.py       ← Pydantic models (data validation)
│       │   └── database.py      ← SQLAlchemy models (data storage)
│       │
│       ├── engine/              ← CORE LOGIC (the brain)
│       │   ├── judges.py        ← Builds prompts, runs judges
│       │   ├── aggregator.py    ← Combines scores (5 methods)
│       │   └── orchestrator.py  ← LangGraph workflow (runs everything)
│       │
│       ├── providers/           ← LLM INTEGRATIONS
│       │   ├── base.py          ← Abstract interface
│       │   └── gemini.py        ← Google Gemini implementation
│       │
│       └── api/routes/          ← REST API ENDPOINTS
│           ├── suites.py        ← Create/list eval suite configs
│           ├── datasets.py      ← Upload/list test datasets
│           ├── evaluations.py   ← Trigger + monitor eval runs
│           └── results.py       ← Compare runs side-by-side
│
├── cli/
│   └── verdict_cli.py      ← Command-line interface
│
└── examples/
    ├── suites/              ← Example YAML eval configs
    └── datasets/            ← Example test datasets
```

### What Each Folder Does:
- **models/** = "What does data look like?" (shapes + storage)
- **engine/** = "What happens to data?" (processing + scoring)
- **providers/** = "How do we talk to LLMs?" (API integrations)
- **api/routes/** = "How do users interact with the system?" (HTTP endpoints)
- **cli/** = "How do users run this from terminal?" (command line)

---

## 4. The Complete Data Flow

### Flow 1: Using the CLI
```
Terminal command:
  python -m cli.verdict_cli run --suite suite.yaml --dataset data.json

Step 1: verdict_cli.py reads the YAML and JSON files from disk
Step 2: Validates them using Pydantic schemas (schemas.py)
Step 3: Creates a GeminiProvider (gemini.py)
Step 4: Calls run_evaluation() (orchestrator.py)
Step 5: LangGraph runs the evaluation:
        For each entry (sequentially):
          For each judge (in parallel):
            judges.py builds the prompt
            gemini.py sends it to Gemini API
            gemini.py parses the JSON response
            judges.py returns the score
          aggregator.py combines judge scores into one entry score
        aggregator.py computes overall statistics
Step 6: verdict_cli.py prints pretty tables using rich library
Step 7: (Optional) Saves results to JSON file
```

### Flow 2: Using the API
```
HTTP request:
  POST /api/evaluations/run  {"suite_id": "abc", "dataset_id": "xyz"}

Step 1: evaluations.py receives the request
Step 2: Looks up suite config and dataset from SQLite database
Step 3: Creates an EvalRun record with status="pending"
Step 4: Returns immediately to the user (HTTP 200)
Step 5: IN THE BACKGROUND: kicks off _execute_eval_run()
Step 6: Same as CLI Steps 4-5 (LangGraph orchestrator runs)
Step 7: Saves results to SQLite database
Step 8: Sets status="completed" with overall_score

User polls: GET /api/evaluations/{run_id}
  → Returns status + results when done
```

### Diagram of Internal Data Flow
```
┌──────────┐     ┌──────────┐     ┌───────────────┐
│  YAML    │────→│ Pydantic │────→│  LangGraph    │
│  Suite   │     │ Validate │     │  Orchestrator │
└──────────┘     └──────────┘     └───────┬───────┘
                                          │
┌──────────┐     ┌──────────┐             │
│  JSON    │────→│ Pydantic │────→────────┘
│  Dataset │     │ Validate │     
└──────────┘     └──────────┘     
                                          │
                            ┌─────────────┤
                            │   For each entry:
                            │
                    ┌───────▼────────┐
                    │  judges.py     │
                    │  Build prompt: │
                    │  "Evaluate     │
                    │   this on      │
                    │   accuracy..." │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │  gemini.py     │
                    │  API call to   │
                    │  Gemini:       │
                    │  → Send prompt │
                    │  ← Get JSON   │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │ aggregator.py  │
                    │ Combine scores │
                    │ → Entry score  │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │   Results:     │
                    │  CLI tables    │
                    │  or SQLite DB  │
                    └────────────────┘
```

---

## 5. File-by-File Explanation

### 5.1 config.py — Settings

**Purpose:** Load configuration from the .env file so the rest of the app can use it.

```python
from pydantic_settings import BaseSettings
```
- `pydantic_settings` is a library that reads environment variables
- It automatically maps .env file entries to Python variables

```python
class Settings(BaseSettings):
    gemini_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./verdict.db"
    gemini_model: str = "gemini-2.5-flash"
    max_retries: int = 3
    rate_limit_rpm: int = 15
```
- Each line declares a setting with a type and default value
- `gemini_api_key: str = ""` means:
  - Look for `GEMINI_API_KEY` in .env (auto-converted from snake_case to UPPER_SNAKE_CASE)
  - If not found, default to empty string ""
- `database_url`: Where SQLite stores data
  - `sqlite` = database type
  - `aiosqlite` = async driver (non-blocking)
  - `///./verdict.db` = file path (current directory, file named verdict.db)
- `rate_limit_rpm = 15`: Gemini free tier allows 15 requests per minute

```python
    model_config = {"env_file": ".env"}
```
- Tells pydantic: "read the .env file from the project root"
- Your .env has: `GEMINI_API_KEY=AIzaSy...`
- Pydantic reads it and sets `settings.gemini_api_key = "AIzaSy..."`

```python
settings = Settings()
```
- Creates ONE global instance that all files import
- Instead of `os.getenv("GEMINI_API_KEY")` scattered everywhere,
  every file just does: `from backend.app.config import settings`
- Single source of truth for all configuration

---

### 5.2 schemas.py — Data Shapes

**Purpose:** Define what every piece of data looks like using Pydantic models.

**What is Pydantic?**
Pydantic is a data validation library. When you create a Pydantic model,
it automatically:
- Checks that required fields are present
- Checks that types are correct (str is str, int is int)
- Converts types when possible (string "5" → integer 5)
- Rejects invalid data with clear error messages

**Think of schemas as "contracts"**: if data doesn't match the shape, it's rejected.

#### Group 1: Configuration (what user defines before running)

```python
class JudgeConfig(BaseModel):
    name: str                  # "accuracy_judge"
    dimension: str             # "accuracy"
    rubric: str                # "Score 1-5: 5=perfect, 4=mostly accurate..."
    weight: float = 1.0       # How important this judge is (0.4 = 40%)
    scoring_scale: int = 5    # Max score (5 means judges score 1-5)
```
- This defines what ONE judge looks like in the YAML config
- `weight: float = 1.0` means: if not specified, default to 1.0
- `Field(default=5, description="...")` adds documentation that shows up in Swagger UI

```python
class AggregationConfig(BaseModel):
    method: str = "weighted_average"    # Which scoring method to use
    pass_threshold: int = 3             # For majority_vote: >= 3 means "pass"
    critical_dimensions: list[str] = [] # For hybrid: must-pass dimensions
    critical_threshold: int = 3         # For hybrid: min score for critical dims
```
- Controls HOW multiple judge scores combine into one final score
- `default_factory=list` means: if not specified, default to empty list []
  (We use `default_factory` instead of `default=[]` because mutable defaults
   are shared between instances in Python — a common gotcha)

```python
class EvalSuiteCreate(BaseModel):
    name: str                          # "Customer Support Bot Eval"
    description: str = ""              # Optional description
    judges: list[JudgeConfig]          # List of judge configurations
    aggregation: AggregationConfig     # How to combine scores
```
- The COMPLETE evaluation config
- This maps directly to the YAML file you write
- `list[JudgeConfig]` means: a list where each item must be a valid JudgeConfig

```python
class EvalSuiteResponse(BaseModel):
    id: str                # "a1b2c3d4-..." (UUID, added by server)
    name: str
    description: str
    judges: list[JudgeConfig]
    aggregation: AggregationConfig
    created_at: datetime   # When it was created (added by server)
```
- Same as EvalSuiteCreate but WITH id and created_at
- **Why two classes?**
  - `Create` = what the user SENDS (no id yet, server generates it)
  - `Response` = what the server RETURNS (includes id + timestamp)
  - This is a common REST API pattern

#### Group 2: Data (what gets evaluated)

```python
class DatasetEntry(BaseModel):
    input: str                         # "How do I reset my password?"
    output: str                        # "Just google it lol"
    expected_output: Optional[str]     # Optional correct answer for reference
```
- One test case. The atomic unit of evaluation.
- `Optional[str] = None` means this field can be a string OR null/missing

```python
class DatasetCreate(BaseModel):
    name: str                          # "Customer Support Sample"
    entries: list[DatasetEntry]        # List of test cases
```

#### Group 3: Results (what comes out after evaluation)

```python
class JudgeScore(BaseModel):
    judge_name: str    # "accuracy_judge"
    dimension: str     # "accuracy"
    score: float       # 4.0
    reasoning: str     # "Mostly accurate but oversimplified..."
```
- ONE judge's verdict on ONE entry

```python
class EntryResult(BaseModel):
    entry_index: int                   # 0 (first entry)
    input: str                         # The question
    output: str                        # The response that was evaluated
    judge_scores: list[JudgeScore]     # All judges' verdicts
    aggregated_score: float            # Combined final score (e.g., 3.8)
```
- ALL judges' verdicts on ONE entry, plus the combined score

```python
class RunStats(BaseModel):
    mean: float      # Average score across all entries
    median: float    # Middle score
    std: float       # Standard deviation (how spread out scores are)
    min: float       # Worst entry score
    max: float       # Best entry score
    q25: float       # 25th percentile
    q75: float       # 75th percentile
```
- Statistics across ALL entries in a run
- Answers: "How did the chatbot do overall?"

```python
class EvalRunResponse(BaseModel):
    id: str
    suite_id: str
    dataset_id: str
    status: str                        # "pending" → "running" → "completed"
    overall_score: Optional[float]     # null until completed
    entry_results: Optional[list]      # null until completed
    stats: Optional[RunStats]          # null until completed
    dimension_breakdown: Optional[list] # null until completed
    error_message: Optional[str]       # null unless failed
    created_at: datetime
    completed_at: Optional[datetime]   # null until completed
```
- Everything about a completed evaluation run
- Optional fields are null while the evaluation is still running

---

### 5.3 database.py — Storage

**Purpose:** Define SQLite tables and how to interact with the database.

**What is SQLAlchemy?**
SQLAlchemy is an ORM (Object-Relational Mapper). It lets you:
- Define database tables as Python classes
- Query the database using Python (not raw SQL)
- Automatically create tables from your class definitions

**What is async?**
Normally, when your code talks to a database, it WAITS (blocks) until
the database responds. With async, while waiting for the database,
the server can handle OTHER requests. This makes the server faster
when handling many users.

#### Setup
```python
engine = create_async_engine(settings.database_url, echo=False)
```
- Creates a connection to the SQLite database
- `async` = non-blocking (server can multitask while waiting for DB)
- `echo=False` = don't print SQL queries to console (set True for debugging)

```python
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```
- A "session" = one conversation with the database
- Think of it like opening a text document: open → read/write → close
- `expire_on_commit=False` = after saving data, keep it accessible in Python
  (without this, accessing a saved object would need ANOTHER database query)

#### Tables

```python
class EvalSuiteDB(Base):
    __tablename__ = "eval_suites"  # Actual table name in SQLite
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    config_yaml = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    runs = relationship("EvalRunDB", back_populates="suite")
```
- Each `Column()` = one column in the database table
- `primary_key=True` = unique identifier for each row
- `default=generate_uuid` = auto-generate a UUID like "a1b2c3d4-..."
- `nullable=False` = this field MUST have a value (can't be null)
- `config_yaml` = stores the ENTIRE YAML config as a text string
  (simpler than creating separate tables for judges, aggregation, etc.)

**What is `relationship()`?**
```python
runs = relationship("EvalRunDB", back_populates="suite")
```
- This is NOT a database column. It's a Python convenience.
- It lets you do: `suite.runs` → get all evaluation runs for this suite
- `back_populates="suite"` means: on the EvalRunDB side, `run.suite` points back
- SQLAlchemy automatically does the SQL JOIN for you

**What is `ForeignKey()`?**
```python
class EvalRunDB(Base):
    suite_id = Column(String, ForeignKey("eval_suites.id"), nullable=False)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
```
- `ForeignKey("eval_suites.id")` = this value MUST match an existing suite's id
- It LINKS two tables together
- An eval run belongs to ONE suite and ONE dataset

```
Table relationships:

  eval_suites ──┐
                ├──→ eval_runs ──→ judge_results  
  datasets ─────┘

  One suite + one dataset = one eval run
  One eval run has many judge results (one per judge × entry)
  5 entries × 3 judges = 15 rows in judge_results
```

#### Functions

```python
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```
- Called when the server starts (from main.py)
- `Base.metadata.create_all` = "create all tables IF they don't exist yet"
- If tables already exist, it does nothing (safe to call repeatedly)

```python
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
```
- This is a FastAPI "dependency" (explained in the API routes section)
- `yield` makes it a generator:
  1. Before yield: create and open a database session
  2. yield session: the API route uses it
  3. After yield: automatically close the session
- This ensures sessions are always properly closed, even if errors occur

---

### 5.4 base.py — Abstract Provider

**Purpose:** Define an interface that ALL LLM providers must follow.

```python
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        ...
```

**What is ABC (Abstract Base Class)?**
- `ABC` means: you CANNOT create `LLMProvider()` directly
- You MUST create a subclass that implements all @abstractmethod methods
- If you forget to implement `generate()`, Python throws an error

**Why bother?**
Right now we only have GeminiProvider. But later we might add:
- OpenAIProvider (GPT-4)
- OllamaProvider (local models)
- GroqProvider (fast inference)

They all share the same interface: `generate(system_prompt, user_prompt) → str`

The rest of the code (judges.py) doesn't care WHICH provider it uses.
You could swap Gemini for GPT-4 by just changing one line.

```
This is the "Strategy Pattern" from software design:

         judges.py
            │ calls
      LLMProvider.generate()    ← abstract interface
       /        |        \
  Gemini    OpenAI    Ollama   ← concrete implementations
```

---

### 5.5 gemini.py — Gemini API Integration

**Purpose:** Send prompts to Google's Gemini API and get responses back.

#### Constructor
```python
def __init__(self, model_name=None, api_key=None):
    self._api_key = api_key or settings.gemini_api_key
    self._model_name = model_name or settings.gemini_model
    genai.configure(api_key=self._api_key)
    self._model = genai.GenerativeModel(self._model_name)
    self._semaphore = asyncio.Semaphore(settings.rate_limit_rpm)
```

Line by line:
- `api_key or settings.gemini_api_key` → use custom key if provided, else use .env key
  - `or` in Python: if left side is None/empty/""/0, use right side
- `genai.configure()` → set the API key globally for Google's SDK
- `GenerativeModel("gemini-2.5-flash")` → create a model instance
- `asyncio.Semaphore(15)` → **RATE LIMITER**

**What is a Semaphore?**
Think of a nightclub with a maximum capacity of 15 people:
- When someone enters: capacity goes from 15 → 14
- When someone leaves: capacity goes from 14 → 15
- When capacity = 0: new people WAIT outside until someone leaves

In our code:
- Each Gemini API call "enters" the semaphore
- Only 15 calls can be "inside" (running) at once
- The 16th call waits until one finishes
- This prevents us from exceeding Gemini's rate limit

#### The generate() method
```python
@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=8, max=120),
)
async def generate(self, system_prompt, user_prompt):
    async with self._semaphore:
        response = await self._model.generate_content_async(
            contents=[{"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )
        return response.text
```

**@retry decorator (from tenacity library):**
If `generate()` throws an error, AUTOMATICALLY retry with increasing delays:
```
Attempt 1 fails → wait 8 seconds  → try again
Attempt 2 fails → wait 16 seconds → try again
Attempt 3 fails → wait 32 seconds → try again
Attempt 4 fails → wait 64 seconds → try again
Attempt 5 fails → give up, raise the error
```
Why? Gemini sometimes returns:
- 429 (rate limit exceeded) — waiting helps
- 500 (server error) — usually temporary
These are "transient" errors — retrying usually works.

**async with self._semaphore:**
- "Wait for permission to make an API call"
- When this block finishes, the semaphore releases a slot

**generate_content_async:**
- The async version of Gemini's API. Doesn't block the thread while waiting.
- `contents` = the conversation (we combine system + user prompt into one message
  because Gemini's API doesn't have a separate "system" field like OpenAI)

**generation_config:**
- `response_mime_type="application/json"` → CRUCIAL
  - Tells Gemini: "respond ONLY in JSON format"
  - Without this: Gemini might say "Sure! Here's my score: 4 out of 5..."
  - With this: Gemini returns `{"score": 4, "reasoning": "..."}`
- `temperature=0.0` → Makes output deterministic (no randomness)
  - Same input = same output every time
  - Important for reproducible evaluations

#### The generate_judge_score() method
```python
async def generate_judge_score(self, system_prompt, user_prompt):
    raw = await self.generate(system_prompt, user_prompt)
    parsed = json.loads(raw)
    return {
        "score": float(parsed["score"]),
        "reasoning": str(parsed.get("reasoning", "")),
    }
```
- Calls `generate()` to get raw text from Gemini
- `json.loads(raw)` parses the JSON string into a Python dictionary
  - Input: `'{"score": 4, "reasoning": "Mostly accurate"}'` (string)
  - Output: `{"score": 4, "reasoning": "Mostly accurate"}` (dict)
- Extracts score and reasoning
- If parsing fails (malformed JSON), raises ValueError → triggers retry

---

### 5.6 judges.py — Judge Logic

**Purpose:** Build the prompts that tell Gemini HOW to evaluate, and parse the results.

#### Prompt Templates
```python
JUDGE_SYSTEM_PROMPT_TEMPLATE = """You are an expert LLM output evaluator.
Your task is to evaluate a response on the dimension of "{dimension}".

## Rubric
{rubric}

## Instructions
- Score the response on a scale of 1 to {scale}.
- Provide a brief reasoning for your score.
- Respond ONLY with valid JSON in this exact format:
{{"score": <number>, "reasoning": "<your reasoning>"}}
"""
```

**What are {placeholders}?**
Python's `.format()` replaces `{dimension}` with the actual value.

After formatting with dimension="accuracy", rubric="Score 1-5...", scale=5:
```
You are an expert LLM output evaluator.
Your task is to evaluate a response on the dimension of "accuracy".

## Rubric
Score the response on factual accuracy (1-5):
5: Completely accurate, all claims verifiable
4: Mostly accurate, minor imprecisions
...

## Instructions
- Score the response on a scale of 1 to 5.
- Respond ONLY with valid JSON in this exact format:
{"score": <number>, "reasoning": "<your reasoning>"}
```

**Why {{ and }} instead of { and }?**
In Python's .format(), `{` means "insert variable here".
To get a literal `{` in the output, you write `{{`.
So `{{"score"}}` becomes `{"score"}` after formatting.

#### build_judge_prompts()
```python
def build_judge_prompts(judge, entry):
    system_prompt = JUDGE_SYSTEM_PROMPT_TEMPLATE.format(
        dimension=judge.dimension,
        rubric=judge.rubric,
        scale=judge.scoring_scale,
    )
    
    expected_section = ""
    if entry.expected_output:
        expected_section = f"\n## Expected Output\n{entry.expected_output}\n"
    
    user_prompt = JUDGE_USER_PROMPT_TEMPLATE.format(
        input=entry.input,
        output=entry.output,
        expected_section=expected_section,
    )
    
    return system_prompt, user_prompt
```
- Takes a JudgeConfig + DatasetEntry → returns two strings (system + user prompts)
- If the entry has an expected_output (reference answer), includes it so the
  judge can compare the actual output against the expected one
- Returns a tuple: `(system_prompt, user_prompt)`

#### run_judge()
```python
async def run_judge(provider, judge, entry):
    system_prompt, user_prompt = build_judge_prompts(judge, entry)
    
    try:
        result = await provider.generate_judge_score(system_prompt, user_prompt)
        score = max(1, min(result["score"], judge.scoring_scale))
        
        return JudgeScore(
            judge_name=judge.name,
            dimension=judge.dimension,
            score=score,
            reasoning=result["reasoning"],
        )
    except Exception as e:
        return JudgeScore(
            judge_name=judge.name,
            dimension=judge.dimension,
            score=0.0,
            reasoning=f"Judge evaluation failed: {e}",
        )
```

**Score clamping:** `max(1, min(result["score"], judge.scoring_scale))`
- If Gemini returns score=7 on a 1-5 scale → min(7, 5) = 5 → max(1, 5) = 5
- If Gemini returns score=0 → min(0, 5) = 0 → max(1, 0) = 1
- If Gemini returns score=-1 → min(-1, 5) = -1 → max(1, -1) = 1
- Ensures scores are ALWAYS within 1 to scoring_scale

**Graceful failure:** The try/except block
- If ANYTHING goes wrong (network error, bad JSON, rate limit), 
  return score=0 with error message instead of crashing
- Other judges and entries continue running
- This is why we saw score=0 in failed tests — the judges didn't crash,
  they just reported "I couldn't evaluate this"

---

### 5.7 aggregator.py — Scoring Math

**Purpose:** Combine multiple judge scores into one final score.

#### Method 1: Weighted Average
```python
def weighted_average(scores, weights):
    total_weight = sum(weights.get(s.judge_name, 1.0) for s in scores)
    weighted_sum = sum(s.score * weights.get(s.judge_name, 1.0) for s in scores)
    return weighted_sum / total_weight
```
Example with our live test:
```
Entry #0 ("How do I reset my password?"):
  accuracy=5 (weight=0.4), helpfulness=5 (weight=0.3), tone=4 (weight=0.3)
  
  total_weight = 0.4 + 0.3 + 0.3 = 1.0
  weighted_sum = (5×0.4) + (5×0.3) + (4×0.3) = 2.0 + 1.5 + 1.2 = 4.7
  result = 4.7 / 1.0 = 4.7 ✓ (matches our live test!)
```
When to use: Default. Good when all dimensions matter but some more than others.

#### Method 2: Min Score
```python
def min_score(scores):
    return min(s.score for s in scores)
```
Example: accuracy=5, helpfulness=5, tone=2 → min = 2
- Conservative: "you're only as good as your worst dimension"
- When to use: Safety-critical apps where ANY failure matters

#### Method 3: Majority Vote
```python
def majority_vote(scores, threshold=3):
    votes = [1 if s.score >= threshold else 0 for s in scores]
    counter = Counter(votes)
    majority = counter.most_common(1)[0][0]
    return float(majority)
```
Example: accuracy=4(pass), helpfulness=2(fail), tone=4(pass)
- votes = [1, 0, 1] → Counter({1: 2, 0: 1}) → majority = 1 (PASS)
- When to use: Binary decisions — "good enough to ship?"

#### Method 4: Median
```python
def median_score(scores):
    return statistics.median(s.score for s in scores)
```
Example: accuracy=1, helpfulness=4, tone=5 → sorted=[1,4,5] → median=4
- Ignores extreme outliers
- When to use: When some judges might give unreliable extreme scores

#### Method 5: Hybrid (what our example suite uses!)
```python
def hybrid(scores, weights, critical_dimensions, critical_threshold=3):
    for s in scores:
        if s.dimension in critical_dimensions and s.score < critical_threshold:
            return 0.0  # INSTANT FAIL
    return weighted_average(scores, weights)
```
This is the most sophisticated method:
1. First check "hard gates" — critical dimensions MUST pass
2. If any critical dimension fails → score is 0 (FAIL), no matter what
3. If all critical dimensions pass → compute weighted average normally

Example from our live test (critical_dimensions=["tone"], critical_threshold=2):
```
Entry #1 ("Just google it lol"):
  accuracy=1, helpfulness=1, tone=1
  
  Check critical dimensions:
    tone (1) < critical_threshold (2) → INSTANT FAIL → return 0.0
  
  Result: 0.0 ← tone was too bad, doesn't matter what other scores are

Entry #0 ("To reset your password, go to..."):
  accuracy=5, helpfulness=5, tone=4
  
  Check critical dimensions:
    tone (4) >= critical_threshold (2) → PASS, continue
  
  Fall through to weighted_average:
    (5×0.4 + 5×0.3 + 4×0.3) / 1.0 = 4.7
```

#### The router function
```python
def aggregate_scores(scores, config, weights):
    match config.method:
        case "weighted_average": return weighted_average(scores, weights)
        case "min_score":        return min_score(scores)
        case "majority_vote":    return majority_vote(scores, threshold=config.pass_threshold)
        case "median":           return median_score(scores)
        case "hybrid":           return hybrid(scores, weights, ...)
        case _:                  return weighted_average(scores, weights)
```
- `match/case` is Python's switch statement (like switch/case in Java/C++)
- Reads `config.method` and calls the right function
- `case _` is the default (if method doesn't match any known name)

#### Statistics functions
```python
def compute_run_stats(entry_scores):
```
Input from our live test: [4.70, 0.00, 3.40, 5.00, 1.70]
```
sorted:  [0.00, 1.70, 3.40, 4.70, 5.00]
mean:    2.96  (sum / count)
median:  3.40  (middle value)
std:     2.11  (spread of values)
min:     0.00  (worst entry)
max:     5.00  (best entry)
q25:     1.70  (25th percentile)
q75:     4.70  (75th percentile)
```
All match our live test output.

```python
def compute_dimension_breakdown(all_scores):
```
Groups ALL scores by dimension across ALL entries:
```
accuracy scores:    [5, 1, 1, 5, 2] → mean=2.80, min=1, max=5
helpfulness scores: [5, 1, 5, 5, 1] → mean=3.40, min=1, max=5
tone scores:        [4, 1, 5, 5, 2] → mean=3.40, min=1, max=5
```

---

### 5.8 orchestrator.py — LangGraph Workflow

**Purpose:** Coordinate the entire evaluation process using LangGraph.

**What is LangGraph?**
LangGraph is a framework for building workflows as graphs.
A graph has:
- **Nodes** = steps (functions that do work)
- **Edges** = connections (which step comes after which)
- **State** = shared memory that flows through the graph

Our graph:
```
START → [evaluate all entries] → [aggregate scores] → END
```

#### State Definition
```python
class EvalState(TypedDict):
    suite: EvalSuiteCreate
    entries: list[DatasetEntry]
    provider: GeminiProvider
    entry_results: Annotated[list[EntryResult], _merge_entry_results]
    overall_score: float
    status: str
    error: str
```
- This is the "shared whiteboard" that flows through the graph
- Each node reads from it and writes to it
- Think of it like passing a notebook between team members

**What is `Annotated[..., _merge_entry_results]`?**
This is a LangGraph "reducer". Normally, when a node returns
`{"entry_results": [new_stuff]}`, LangGraph REPLACES the old value.
With a reducer, it MERGES (appends) instead:
```python
def _merge_entry_results(existing, new):
    return existing + new  # append new results to existing list
```
This is important because we process entries one at a time and want to
ACCUMULATE all results, not lose previous ones.

#### evaluate_entry() — Process one entry
```python
async def evaluate_entry(entry_index, entry, judges, provider, aggregation):
    # Run all judges IN PARALLEL for this one entry
    tasks = [run_judge(provider, judge, entry) for judge in judges]
    judge_scores = await asyncio.gather(*tasks)
    
    # Combine judge scores into one entry score
    weights = {j.name: j.weight for j in judges}
    agg_score = aggregate_scores(judge_scores, aggregation, weights)
    
    return EntryResult(...)
```

**What is asyncio.gather()?**
It runs multiple async functions SIMULTANEOUSLY (in parallel).

Without gather (sequential):
```
judge1 starts → waits 2s → done
                               judge2 starts → waits 2s → done  
                                                              judge3 starts → waits 2s → done
Total: 6 seconds
```

With gather (parallel):
```
judge1 starts → waits 2s → done
judge2 starts → waits 2s → done     (all three run at the same time!)
judge3 starts → waits 2s → done
Total: ~2 seconds (3x faster)
```

`*tasks` unpacks the list: `gather(task1, task2, task3)` instead of `gather([task1, task2, task3])`

#### run_evaluation_node() — The main evaluation loop
```python
async def run_evaluation_node(state):
    num_judges = len(suite.judges)
    
    # Calculate delay between entries to respect rate limits
    delay_between_entries = max(1, (num_judges * 60) // 15 + 2)
    
    for i, entry in enumerate(entries):
        result = await evaluate_entry(i, entry, ...)
        all_results.append(result)
        
        if i < len(entries) - 1:  # Don't sleep after the last entry
            await asyncio.sleep(delay_between_entries)
```

**Rate limit math:**
```
Gemini free tier: 15 requests per minute (RPM)
Each entry uses 3 judges = 3 API calls

delay = (3 × 60) ÷ 15 + 2 = 12 + 2 = 14 seconds between entries

Timeline for 5 entries:
  Entry 0: 3 parallel judge calls (takes ~2s)
  Wait 14 seconds
  Entry 1: 3 parallel judge calls (takes ~2s)
  Wait 14 seconds
  Entry 2: 3 parallel judge calls (takes ~2s)
  Wait 14 seconds
  Entry 3: 3 parallel judge calls (takes ~2s)
  Wait 14 seconds
  Entry 4: 3 parallel judge calls (takes ~2s)
  No wait (last entry)
  
  Total: ~66 seconds for 5 entries with 3 judges
```

#### build_eval_graph() — Define the workflow
```python
def build_eval_graph():
    graph = StateGraph(EvalState)            # Create graph with our state type
    
    graph.add_node("evaluate", run_evaluation_node)  # Register node 1
    graph.add_node("aggregate", aggregate_node)       # Register node 2
    
    graph.set_entry_point("evaluate")        # Start here
    graph.add_edge("evaluate", "aggregate")  # After evaluate → aggregate
    graph.add_edge("aggregate", END)         # After aggregate → done
    
    return graph.compile()                   # Lock the graph, make it runnable
```

Visualization:
```
[START] → [evaluate] → [aggregate] → [END]
```

Why LangGraph for something this simple?
- Right now it's 2 nodes in a line — could just be two function calls
- But later we can add: retry nodes, human review, conditional branching
- LangGraph gives us: state management, checkpointing, error recovery
- It's also a portfolio showpiece — shows you know production frameworks

#### run_evaluation() — The public API
```python
async def run_evaluation(suite, entries, provider=None):
    if provider is None:
        provider = GeminiProvider()
    
    graph = build_eval_graph()
    
    initial_state = {
        "suite": suite,
        "entries": entries,
        "provider": provider,
        "entry_results": [],
        "overall_score": 0.0,
        "status": "running",
        "error": "",
    }
    
    result = await graph.ainvoke(initial_state)
    
    return {
        "entry_results": result["entry_results"],
        "overall_score": result["overall_score"],
        "stats": compute_run_stats(...),
        "dimension_breakdown": compute_dimension_breakdown(...),
    }
```
- This is what the CLI and API routes call
- Sets up initial state → runs the graph → returns final results

---

### 5.9 main.py — FastAPI Server

**Purpose:** Create and configure the web server.

```python
@asynccontextmanager
async def lifespan(app):
    await init_db()   # Runs at SERVER STARTUP: create database tables
    yield              # Server runs and handles requests here
                       # (After yield: shutdown code would go here)
```
- `lifespan` controls what happens when the server starts and stops
- `init_db()` creates all SQLite tables on startup

```python
app = FastAPI(
    title="Verdict",
    description="...",
    version="0.1.0",
    lifespan=lifespan,
)
```
- Creates the FastAPI application
- title/description/version show up in the Swagger docs (localhost:8000/docs)

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```
**What is CORS?**
When your React frontend (localhost:5173) tries to call your backend
(localhost:8000), the browser BLOCKS the request by default.
This is a security feature called "Cross-Origin Resource Sharing".
Adding CORS middleware tells the browser: "it's okay, allow these requests."
- `allow_origins=["*"]` = allow requests from ANY domain
- In production, you'd restrict this to your frontend's domain only

```python
app.include_router(suites.router)
app.include_router(datasets.router)
app.include_router(evaluations.router)
app.include_router(results.router)
```
- Registers all API endpoints from the route files
- Each router adds its endpoints (POST /api/suites, GET /api/suites, etc.)

---

### 5.10 API Routes

All route files follow the same pattern. Here's suites.py as the example:

```python
router = APIRouter(prefix="/api/suites", tags=["suites"])
```
- All routes in this file start with `/api/suites`
- `tags=["suites"]` groups them together in the Swagger UI

#### CREATE: POST /api/suites
```python
@router.post("", response_model=EvalSuiteResponse)
async def create_suite(
    suite: EvalSuiteCreate,                    # Request body (auto-validated)
    session: AsyncSession = Depends(get_session),  # Database session
):
    config_yaml = yaml.dump(suite.model_dump())    # Convert to YAML string
    db_suite = EvalSuiteDB(name=suite.name, ...)   # Create DB object
    session.add(db_suite)                          # Stage for insert
    await session.commit()                         # Write to disk
    await session.refresh(db_suite)                # Reload (get generated id)
    return suite_db_to_response(db_suite)          # Convert to API response
```

**What is `Depends(get_session)`?**
This is FastAPI's "Dependency Injection":
- FastAPI sees `Depends(get_session)` and automatically calls `get_session()`
- You get a ready-to-use database session as a parameter
- When the route finishes, FastAPI automatically closes the session
- You never have to manage sessions manually

**What is `response_model`?**
- Tells FastAPI: "the response MUST match EvalSuiteResponse"
- FastAPI validates the response and shows it in Swagger docs
- If your code returns wrong data, FastAPI catches it

#### LIST: GET /api/suites
```python
@router.get("", response_model=list[EvalSuiteResponse])
async def list_suites(session=Depends(get_session)):
    result = await session.execute(
        select(EvalSuiteDB).order_by(EvalSuiteDB.created_at.desc())
    )
    suites = result.scalars().all()
    return [suite_db_to_response(s) for s in suites]
```
- `select(EvalSuiteDB)` = SQL: `SELECT * FROM eval_suites`
- `.order_by(...desc())` = `ORDER BY created_at DESC` (newest first)
- `.scalars().all()` = convert query result to list of Python objects
- List comprehension converts each DB object to API response

#### evaluations.py — The interesting one
```python
@router.post("/run")
async def start_eval_run(request, background_tasks, session):
    # 1. Look up suite and dataset from database
    # 2. Create an EvalRun record with status="pending"
    # 3. Kick off evaluation IN THE BACKGROUND
    background_tasks.add_task(_execute_eval_run, run_id, suite_config, entries)
    # 4. Return immediately (don't wait for evaluation to finish)
    return EvalRunSummary(status="pending", ...)
```

**What is BackgroundTasks?**
- Normally, an API endpoint finishes when the function returns
- `background_tasks.add_task()` says: "run this function AFTER responding"
- The HTTP response returns immediately (user isn't waiting)
- The evaluation runs in the background
- User polls `GET /api/evaluations/{id}` to check if it's done

---

### 5.11 verdict_cli.py — CLI Tool

**Purpose:** Run evaluations from the terminal without starting a server.

```python
app = typer.Typer(name="verdict")
console = Console()  # Rich library for pretty output
```
- Typer = CLI framework (like argparse but with type hints)
- Console = Rich library's console for colored output and tables

```python
@app.command()
def run(
    suite: str = typer.Option(..., "--suite", "-s"),
    dataset: str = typer.Option(..., "--dataset", "-d"),
    output: str = typer.Option(None, "--output", "-o"),
):
```
- `@app.command()` makes this a CLI command
- `typer.Option(...)` = REQUIRED argument (... means no default)
- `typer.Option(None, ...)` = OPTIONAL argument (default None)
- User types: `python -m cli.verdict_cli run --suite file.yaml --dataset file.json`

```python
with console.status("[bold green]Running evaluation..."):
    result = asyncio.run(_run_eval(eval_suite, entries))
```
- `console.status()` shows a spinning animation while waiting
- `asyncio.run()` bridges sync CLI code with async engine code
  - The CLI is synchronous (`def run`, not `async def run`)
  - But the engine is async. `asyncio.run()` handles the conversion.

The `_print_results()` function uses Rich's `Table` class to create
the formatted tables you saw in the live test output.

---

## 6. Key Concepts Explained

### What is async/await?
Normal (synchronous) code waits for each operation to finish:
```python
data1 = get_from_database()      # Waits 100ms
data2 = call_gemini_api()        # Waits 2000ms
data3 = get_from_database()      # Waits 100ms
# Total: 2200ms
```

Async code can do OTHER work while waiting:
```python
data1 = await get_from_database()   # Starts, while waiting...
data2 = await call_gemini_api()     # ...this can start too
# Total: ~2000ms (operations overlap)
```

### What is Pydantic?
A library that validates data. Instead of:
```python
# Manual validation (tedious, error-prone)
if "name" not in data:
    raise Error("name required")
if not isinstance(data["name"], str):
    raise Error("name must be string")
```

You write:
```python
class MyModel(BaseModel):
    name: str           # Required string
    age: int = 0        # Optional int, default 0

data = MyModel(name="Alice", age=25)  # Validates automatically
data = MyModel(name=123)              # Error! name must be str
data = MyModel()                      # Error! name is required
```

### What is SQLAlchemy ORM?
Instead of writing raw SQL:
```sql
INSERT INTO eval_suites (id, name) VALUES ('abc', 'My Suite');
SELECT * FROM eval_suites WHERE id = 'abc';
```

You write Python:
```python
suite = EvalSuiteDB(name="My Suite")  # Python object
session.add(suite)                     # Stage for insert
await session.commit()                 # Write to DB

suite = await session.get(EvalSuiteDB, "abc")  # Fetch by ID
print(suite.name)  # "My Suite"
```

### What is FastAPI?
A web framework that creates REST APIs. It automatically:
- Validates request data using Pydantic models
- Generates interactive API docs (Swagger UI at /docs)
- Handles async operations efficiently
- Serializes Python objects to JSON responses

### What is LangGraph?
A framework for building AI workflows as graphs.
- **Nodes** = functions that process data
- **Edges** = connections between nodes
- **State** = shared data that flows through the graph
- You can add conditional branches, loops, parallel execution

---

## 7. Live Test Walkthrough

When we ran:
```bash
python -m cli.verdict_cli run --suite customer_support.yaml --dataset customer_support_sample.json
```

Here's EXACTLY what happened:

### Step 1: CLI reads files
- YAML → EvalSuiteCreate with 3 judges (accuracy, helpfulness, tone)
- JSON → 5 DatasetEntry objects

### Step 2: Orchestrator starts
- Creates LangGraph: [evaluate] → [aggregate] → END
- Enters the evaluate node

### Step 3: Entry #0 processed
```
Input:  "How do I reset my password?"
Output: "To reset your password, go to the login page..."

Judge 1 (accuracy):
  Prompt: "Evaluate this response on accuracy. Score 1-5."
  Gemini returns: {"score": 5, "reasoning": "Completely accurate steps"}

Judge 2 (helpfulness):
  Prompt: "Evaluate this response on helpfulness. Score 1-5."
  Gemini returns: {"score": 5, "reasoning": "Provides clear, actionable steps"}

Judge 3 (tone):
  Prompt: "Evaluate this response on tone. Score 1-5."
  Gemini returns: {"score": 4, "reasoning": "Professional but could be warmer"}

Aggregation (hybrid):
  Check critical: tone(4) >= threshold(2) → PASS
  Weighted average: (5×0.4 + 5×0.3 + 4×0.3) = 4.70
```

### Step 4: Wait 14 seconds (rate limit)

### Step 5: Entry #1 processed
```
Input:  "My order hasn't arrived. It's been 2 weeks."
Output: "Just google it lol"

Judge 1 (accuracy):  {"score": 1, "reasoning": "No factual content"}
Judge 2 (helpfulness): {"score": 1, "reasoning": "Completely unhelpful"}
Judge 3 (tone):      {"score": 1, "reasoning": "Rude and dismissive"}

Aggregation (hybrid):
  Check critical: tone(1) < threshold(2) → INSTANT FAIL → 0.00
```

### Steps 6-8: Entries #2, #3, #4 processed similarly

### Step 9: Aggregate node runs
```
Entry scores: [4.70, 0.00, 3.40, 5.00, 1.70]
Overall mean: 2.96
```

### Step 10: CLI prints the tables
The rich library formats everything into the neat tables you saw.

---

## Summary

```
config.py     → "Where is my API key?" 
schemas.py    → "What does data look like?"
database.py   → "How is data stored?"
gemini.py     → "How do I talk to Gemini?"
judges.py     → "What should I ask Gemini?"
aggregator.py → "How do I combine scores?"
orchestrator.py → "In what order do I do everything?"
main.py       → "Start the server"
routes/*.py   → "Handle HTTP requests"
verdict_cli.py → "Handle terminal commands"
```

The whole system in one sentence:
**Verdict reads a YAML config (judges + rubrics) and a JSON dataset
(input/output pairs), sends each output to Gemini for scoring across
multiple dimensions, combines the scores using a configurable method,
and presents the results as tables or via a REST API.**
