import sqlite3
from contextlib import closing

import pandas as pd
from langchain.tools import tool

from config.settings import settings

EXCLUDED_TABLES = ("sqlite_sequence", "CustomerCustomerDemo", "CustomerDemographics")
DB_PATH = settings.DATABASE_PATH
MAX_ROWS = 50
MAX_CELL_CHARS = 100


def _quote(name: str) -> str:
    """Wrap table names containing spaces in double quotes (e.g. "Order Details")."""
    return f'"{name}"' if " " in name else name


def _connect():
    """Open a read-only connection so the agent can never modify the database."""
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


def _table_names() -> list[str]:
    """Return the names of all user tables in the database."""
    placeholders = ",".join("?" * len(EXCLUDED_TABLES))
    with closing(_connect()) as conn:
        rows = conn.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' "
            f"AND name NOT IN ({placeholders}) ORDER BY name",
            EXCLUDED_TABLES,
        ).fetchall()
    return [r[0] for r in rows]


def query_df(query: str) -> pd.DataFrame:
    """Run a read-only SELECT query and return a DataFrame. Raises on error (for code, not for the LLM)."""
    if not query.strip().upper().startswith(("SELECT", "WITH")):
        raise ValueError("only SELECT queries are allowed.")
    with closing(_connect()) as conn:
        return pd.read_sql_query(query, conn)


# --- Tools (the LLM sees the docstrings below as tool descriptions) ---

@tool
def list_tables() -> str:
    """List all tables in the SQLite database.

    Call this first when you don't know the schema yet,
    then use describe_table on the tables relevant to the question.
    """
    return ", ".join(_quote(t) for t in _table_names())


@tool(parse_docstring=True)
def describe_table(table_name: str) -> str:
    """Show the columns, types, primary keys and foreign keys of a table.

    Use the foreign keys to figure out how to JOIN tables.
    Call this for every table you plan to use before writing SQL.

    Args:
        table_name: Exact table name as returned by list_tables, e.g. Orders or Order Details.
    """
    table_name = table_name.strip('"')
    tables = _table_names()
    if table_name not in tables:
        return f"Error: table '{table_name}' does not exist. Available tables: {', '.join(tables)}"

    with closing(_connect()) as conn:
        # (cid, name, type, notnull, dflt_value, pk)
        columns = conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
        # (id, seq, table, from, to, on_update, on_delete, match)
        fks = conn.execute(f'PRAGMA foreign_key_list("{table_name}")').fetchall()

    lines = [f"Table: {_quote(table_name)}", "Columns:"]
    for col in columns:
        pk = " PRIMARY KEY" if col[5] else ""
        lines.append(f"  - {col[1]} ({col[2]}){pk}")

    if fks:
        lines.append("Foreign keys:")
        for fk in fks:
            lines.append(f"  - {fk[3]} -> {_quote(fk[2])}.{fk[4]}")

    return "\n".join(lines)


@tool(parse_docstring=True)
def run_sql(query: str) -> str:
    """Execute a read-only SQL query (SQLite dialect) and return the result as text.

    Only SELECT/WITH queries are allowed. At most 50 rows are returned,
    so aggregate or use LIMIT instead of fetching raw rows.
    If the result starts with 'Error:', fix the query and try again.

    Args:
        query: A single SQLite SELECT statement. Quote table names with spaces: "Order Details".
    """
    try:
        df = query_df(query)
    except Exception as e:
        # Returned to the LLM so it can fix its own query
        return f"Error: {e}"

    if df.empty:
        return "Query returned 0 rows."
    total_rows = len(df)
    # Binary columns (e.g. Categories.Picture) would flood the LLM context
    df = df.head(MAX_ROWS).map(
        lambda v: "<binary>" if isinstance(v, bytes)
        else v[:MAX_CELL_CHARS] + "..." if isinstance(v, str) and len(v) > MAX_CELL_CHARS
        else v
    )
    text = df.to_string(index=False)
    if total_rows > MAX_ROWS:
        text += f"\n... ({total_rows} rows total, showing first {MAX_ROWS})"
    return text


TOOLS = [list_tables, describe_table, run_sql]