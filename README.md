# SQL Analyst Agent (v2)

Ask a question about your data in plain language. Get back the answer, a chart, and the SQL that produced it.

This project is a small multi-agent system that works on the Northwind sample database. It understands questions in English and Turkish.

```
Question: "Show total revenue by year."

  -> SQL agent     explores the database and writes the query
  -> Report agent  turns the result into a short written answer   (runs in parallel)
  -> Chart agent   picks a chart type that fits the data          (runs in parallel)
```

The project was built in two versions, on purpose:

- **v1 was written from scratch.** No agent framework: the agent loop, tool calling and cost tracking were plain Python on top of the OpenAI SDK. The goal was to understand how an agent actually works before using a framework.
- **v2 (this version) rebuilds the same system with LangChain and LangGraph**, and adds observability and evaluation with [Langfuse](https://langfuse.com): every run is traced, and the system is measured with Langfuse datasets, experiments and an LLM-as-judge.

---

## How it works

The pipeline is a LangGraph `StateGraph` (`src/graph.py`). The agents are nodes and share a single `State` object, which holds the question, the SQL, the data, the report, the chart and the number of LLM calls.

```
START -> sql -> report -------------> END
            \-> chart (if needed) --> END
```

After the SQL agent, the report agent and the chart agent run **in parallel**. The chart branch is conditional: if the data has only one row or no numeric columns, the chart node is skipped and no model call is made.

### 1. SQL agent (`src/agents/sql_agent.py`)

This is the core of the project. It is built with LangChain's `create_agent` and has three tools:

| Tool | What it does |
|---|---|
| `list_tables` | Lists the tables in the database |
| `describe_table` | Shows a table's columns, types, primary keys and foreign keys |
| `run_sql` | Runs a read-only `SELECT` query and returns the rows as text |

The loop works like this:

1. The model gets the question and the list of tools.
2. It calls tools to explore the schema, then writes a query.
3. If the query fails, the error message goes back to the model and it tries again.
4. When the model stops calling tools, the last successful query is the answer.

A `ModelCallLimitMiddleware` stops the loop after at most 10 model calls.

### 2. Report agent (`src/agents/report_agent.py`)

Gets the question and the result table and writes a short answer for a business user. It answers in the same language as the question. Large tables are not sent in full. The agent gets the first 50 rows, the total row count and summary statistics.

### 3. Chart agent (`src/agents/chart_agent.py`)

Decides whether a chart would help and returns a small spec through structured output, for example `{"type": "bar", "x": "Year", "y": "Revenue"}`. The spec is checked before it is used: the column names must exist and `y` must be numeric.

---

## Observability with Langfuse

Every pipeline run is sent to Langfuse through LangChain's `CallbackHandler` (`config/llm.py`). One question becomes one trace, with every agent, tool call, SQL attempt, token count, cost and latency inside it.

Each trace also carries metadata (`pipeline_config()` in `src/graph.py`):

| Field | Value | Used for |
|---|---|---|
| `user_id` | `cli`, `streamlit-anonymous`, `eval` | Cost and traces per user |
| `session_id` | One id per Streamlit browser session | Groups the questions of one conversation |
| `tags` | `sql_analyst` + `cli` / `streamlit` / `eval` | Filtering, e.g. hiding eval runs |
| `metadata` | `app_name`, `model` | Comparing traces across models |

---

## Evaluation

### The eval set

The system is measured with 43 questions (`evals/cases.py`). Each question has a hand-written "gold" SQL query. The questions range from simple counts to joins, date handling, percentages and "top N per group" queries.

**How SQL is scored.** The agent's SQL and the gold SQL are both run. The answer is correct if both results have the same number of rows and every gold column appears among the agent's columns. Column order, row order and small float differences are ignored. Results are compared, not SQL text, because the same answer can be written in many different ways.

### v1: from 72% to 98%

The first version answered **72%** of the questions correctly. Reading the failures one by one showed that most of them were not about reasoning. They came from a few repeated problems, and each one had a direct fix:

| Problem | Fix |
|---|---|
| The model wrote MySQL-style functions like `YEAR()`, which do not exist in SQLite | The prompt states the dialect is SQLite and that dates use `strftime()` and `date()` |
| Order dates are stored as text in mixed formats, so date comparisons failed silently | The prompt says to wrap date columns with `date()` before comparing |
| "Revenue" was calculated in different ways | The prompt defines it once: `UnitPrice * Quantity * (1 - Discount)` from `"Order Details"` |
| Relative dates like "this year" had no fixed reference | The prompt fixes "today" to the last date in the dataset |
| Turkish questions used Turkish values (`Almanya`) that are not in the data | The prompt tells the model to translate values to the English ones stored in the database |
| The model split one answer across several queries, or did math in its head | The last query must return the full answer by itself |
| A failed query ended the run | Errors are returned to the model as text, so it can fix its own query |
| Binary image columns and long text filled up the context | Results are capped at 50 rows, long text is cut short, and binary values become `<binary>` |
| The model guessed at table names and joins | Tool descriptions tell it to list tables first, describe every table it plans to use, and use foreign keys to join |

After these changes the agent reached **98%** (42/43) on the same set.

The main lesson: **most of the gain came from measuring first and then fixing specific failures**, not from a bigger model. Without the eval set, every change would have been a guess.

### v2: Langfuse datasets, experiments and LLM-as-judge

In v2 the eval set lives in Langfuse as a **dataset** (`northwind-text-to-sql`), uploaded by `evals/upload_dataset.py`. Each item stores the question as input and the gold SQL as expected output.

`evals/experiment.py` runs the full pipeline on every item as a Langfuse **experiment**. Each run is linked to the dataset, so runs can be compared side by side in the Langfuse UI (for example after changing the model or a prompt). Each item gets these scores:

| Score | How it is measured |
|---|---|
| `correct` | Result-set match against the gold SQL (same check as above) |
| `llm_calls` | Number of LLM calls the pipeline made |
| `report_quality` | **LLM-as-judge**, 1 to 5 (see below) |
| `accuracy` | Run-level average of `correct` |

**LLM-as-judge (`evals/judge.py`).** SQL can be checked with a rule, but the written report cannot. So a second model grades each report. It gets the question, the data the report agent saw and the report, and checks three things:

1. **Faithfulness:** every number and name in the report appears in the data. Nothing is invented.
2. **Relevance:** the report actually answers the question.
3. **Language:** the report is in the language of the question.

The judge writes its reasoning first and the score after it, which makes scores more consistent. The reasoning is stored as a comment next to the score in Langfuse, so every low score can be explained.

### Results

| Run | Items | SQL accuracy | Report quality | LLM calls / question |
|---|---|---|---|---|
| `sql-agent` (SQL agent only) | 43 | **100%** (43/43) | – | 4.1 |
| `full-pipeline-judge` (full pipeline + judge) | 42 of 43 | **97.6%** (41/42) | **4.50 / 5 (90%)** | 5.7 |

Run the evaluation yourself:

```bash
python -m evals.upload_dataset                    # once: upload the questions to Langfuse
python -m evals.experiment --name my-experiment   # run an experiment, scores go to Langfuse
python -m evals.run --limit 5                     # quick local check, no dataset needed
```

---

## Getting started

### 1. Clone and install

```bash
git clone https://github.com/<alperenkurtt>/sql-analyst-agent.git
cd sql-analyst-agent

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Download the database

The database is not included in this repository. Download the SQLite version of Northwind from [jpwhite3/northwind-SQLite3](https://github.com/jpwhite3/northwind-SQLite3) and put it in the `data/` folder:

```bash
mkdir data
curl -L -o data/northwind.db https://github.com/jpwhite3/northwind-SQLite3/raw/main/dist/northwind.db
```

The file is about 24 MB. The final path must be `data/northwind.db`.

### 3. Add your API keys

The project uses [OpenRouter](https://openrouter.ai), so you can switch between models with one setting, and [Langfuse](https://cloud.langfuse.com) for tracing (the free tier is enough). Copy the example file and add your keys:

```bash
cp .env.example .env
```

```
OPENROUTER_API_KEY=your-key-here
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

The default model is `openai/gpt-4o-mini`. To use another model, add `MODEL_NAME=...` to `.env`.

### 4. Run it

**Web app (Streamlit):**

```bash
streamlit run app.py
```

**Command line:**

```bash
python -m src.main "Show total revenue by year."
```

Tokens, cost, latency and every agent step are visible in the run's trace in Langfuse.

---

## Project structure

```
.
├── app.py                  Streamlit chat interface
├── config/
│   ├── settings.py         Settings loaded from .env
│   └── llm.py              Shared LLM client and Langfuse client/handler
├── src/
│   ├── main.py             Runs the full pipeline from the command line
│   ├── graph.py            LangGraph pipeline and trace config (user, session, tags)
│   ├── state.py            Shared state passed between agents
│   ├── agents/
│   │   ├── sql_agent.py    Tool-calling agent that writes the SQL
│   │   ├── report_agent.py Turns the result into a written answer
│   │   └── chart_agent.py  Chooses and validates a chart
│   └── tools/
│       └── db_tools.py     Database tools for the SQL agent
├── evals/
│   ├── cases.py            43 questions with gold SQL
│   ├── run.py              Local eval runner and the result-set check
│   ├── upload_dataset.py   Uploads the questions to a Langfuse dataset
│   ├── experiment.py       Runs a Langfuse experiment with all scores
│   └── judge.py            LLM-as-judge for report quality
└── data/
    └── northwind.db        (download separately, see above)
```

---

## Safety

The agent can only read the database. This is enforced in two places:

- The connection is opened in SQLite read-only mode (`mode=ro`), so writes fail at the database level.
- `run_sql` rejects any query that does not start with `SELECT` or `WITH`.

---

## Roadmap

- **v1:** from-scratch agents, custom tool loop, eval set, Streamlit UI
- **v2 (this version):** LangChain + LangGraph rebuild, Langfuse tracing, datasets, experiments and LLM-as-judge
- **Next:** harder eval questions, conversation memory with a LangGraph checkpointer, deploy with FastAPI and Docker, RAG over a business glossary
