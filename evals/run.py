import argparse
import time

import pandas as pd

from evals.cases import CASES
from src.agents.sql_agent import run_sql_agent
from src.tools.db_tools import query_df
from src.state import State
from config.llm import langfuse, langfuse_handler


def results_match(pred_df, gold_df):
    """Same row count, and every gold column appears (order-insensitive) among the predicted columns."""
    if len(pred_df) != len(gold_df):
        return False

    def norm(col):
        vals = (None if pd.isna(v) else round(v, 2) if isinstance(v, float) else v for v in col)
        return sorted(vals, key=str)

    pred_cols = [norm(pred_df.iloc[:, i]) for i in range(pred_df.shape[1])]
    return all(norm(gold_df.iloc[:, i]) in pred_cols for i in range(gold_df.shape[1]))


def is_correct(sql, gold_df):
    if not sql:
        return False
    try:
        return results_match(query_df(sql), gold_df)
    except Exception:
        return False


def evaluate(solver, cases):
    """solver: any function question -> {"sql": ..., "llm_calls": ...}.
    Stage 1 agent, Stage 2 analyst+critic... all get measured by this same function."""
    rows = []
    for i, tc in enumerate(cases, 1):
        gold_df = query_df(tc["gold_sql"])

        start = time.perf_counter()
        try:
            out = solver(tc["question"])
        except Exception as e:  # one crashing question shouldn't kill the whole run
            out = {"sql": None, "llm_calls": 0}
        seconds = time.perf_counter() - start

        ok = is_correct(out.get("sql"), gold_df)
        print(f"{'✅' if ok else '❌'} #{i:<3} {seconds:5.1f}s  {tc['question']}")
        rows.append({
            "id": i, "question": tc["question"], "correct": ok,
            "seconds": seconds, "llm_calls": out.get("llm_calls", 0),
            "sql": out.get("sql"),
        })
    return pd.DataFrame(rows)


def summarize(df, label):
    print(f"\n===== {label} =====")
    print(f"Accuracy : {df['correct'].mean():.0%}  ({df['correct'].sum()}/{len(df)})")
    print(f"LLM calls: {df['llm_calls'].mean():.1f} avg / question")
    print(f"Time     : {df['seconds'].mean():.1f}s avg / question")
    print(f"Failed   : {df.loc[~df['correct'], 'id'].tolist()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="only the first N questions (quick test)")
    args = parser.parse_args()

    cases = CASES[: args.limit]
    df = evaluate(
        lambda q: run_sql_agent(
            {"question": q},
            config={
                "callbacks": [langfuse_handler()],
                "metadata": {"langfuse_user_id": "eval", "langfuse_tags": ["eval"]},
            },
        ),
        cases,
    )
    summarize(df, "Stage 1: single agent")
    langfuse.flush()