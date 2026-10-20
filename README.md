# SQL Analyst Agent (v1)

Ask a question about your data in plain language. Get back the answer, a chart, and the SQL that produced it.

This project is a small multi-agent system that works on the Northwind sample database. It understands questions in English and Turkish.

```
Question: "Show total revenue by year."

  -> SQL agent     explores the database and writes the query
  -> Report agent  turns the result into a short written answer
  -> Chart agent   picks a chart type that fits the data
```

**v1 is written from scratch.** It uses no agent framework. The agent loop, the tool calling and the cost tracking are all plain Python on top of the OpenAI SDK. The goal was to understand how an agent actually works before using a framework. v2 will rebuild the same system with LangChain and add observability with Langfuse.

---

## How it works

The pipeline has three agents. They run one after another and share a single `State` object, which holds the question, the SQL, the data, the report, the chart, and the token and cost counters.

### 1. SQL agent (`src/agents/sql_agent.py`)

This is the core of the project. It is a tool-calling loop with three tools:

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

The loop stops after at most 10 steps.

### 2. Report agent (`src/agents/report_agent.py`)

Gets the question and the result table and writes a short answer for a business user. It answers in the same language as the question. Large tables are not sent in full. The agent gets the first 50 rows, the total row count and summary statistics.

### 3. Chart agent (`src/agents/chart_agent.py`)

Decides whether a chart would help and returns a small JSON spec, for example `{"type": "bar", "x": "Year", "y": "Revenue"}`. The spec is checked before it is used: the column names must exist and `y` must be numeric. If the data has only one row, or has no numeric columns, the agent does not call the model at all.

### Shared LLM wrapper (`config/llm.py`)

Every model call goes through one `chat()` function. It counts LLM calls, tokens, cost and latency for each question. These numbers are the starting point for the observability work in v2.

---

## Accuracy: from 72% to 98%

The SQL agent is measured with an evaluation set of 43 questions (`evals/cases.py`). Each question has a hand-written "gold" SQL query. The questions range from simple counts to joins, date handling, percentages and "top N per group" queries.

**How a question is scored.** The agent's SQL and the gold SQL are both run. The answer is correct if both results have the same number of rows and every gold column appears among the agent's columns. Column order, row order and small float differences are ignored. Results are compared, not SQL text, because the same answer can be written in many different ways.

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

After these changes the agent reached **91%** (42/43) on the same set.

The main lesson: **most of the gain came from measuring first and then fixing specific failures**, not from a bigger model. Without the eval set, every change would have been a guess.

Run the evaluation yourself:

```bash
python -m evals.run            # all 43 questions
python -m evals.run --limit 5  # quick check with the first 5
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

### 3. Add your API key

The project uses [OpenRouter](https://openrouter.ai), so you can switch between models with one setting. Copy the example file and add your key:

```bash
cp .env.example .env
```

```
OPENROUTER_API_KEY=your-key-here
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

The command line version also prints the number of LLM calls, the tokens used, the cost and the latency.

---

## Project structure

```
.
├── app.py                  Streamlit chat interface
├── config/
│   ├── settings.py         Settings loaded from .env
│   └── llm.py              Single entry point for all LLM calls (tracks tokens, cost, time)
├── src/
│   ├── main.py             Runs the full pipeline from the command line
│   ├── state.py            Shared state passed between agents
│   ├── agents/
│   │   ├── sql_agent.py    Tool-calling loop that writes the SQL
│   │   ├── report_agent.py Turns the result into a written answer
│   │   └── chart_agent.py  Chooses and validates a chart
│   └── tools/
│       └── db_tools.py     Database tools and their schemas
├── evals/
│   ├── cases.py            43 questions with gold SQL
│   └── run.py              Runs and scores the evaluation
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

- **v1 (this version):** from-scratch agents, custom tool loop, eval set, Streamlit UI
- **v2:** rebuild the agents with LangChain, and add tracing and cost monitoring with Langfuse
