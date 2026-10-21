import argparse

from langfuse import Evaluation

from config.llm import langfuse
from config.settings import settings
from evals.run import is_correct
from evals.upload_dataset import DATASET_NAME
from evals.judge import judge
from src.agents.report_agent import data_to_text
from src.graph import graph, pipeline_config
from src.graph import pipeline_config
from src.tools.db_tools import query_df


def task(*, item, **kwargs):
    state = graph.invoke(
        {"question": item.input["question"]},
        config=pipeline_config(user_id="eval", tags=["eval"]),
    )
    return {
        "sql": state.get("sql"),
        "report": state.get("report"),
        "data": data_to_text(state),
        "llm_calls": state.get("llm_calls", 0),
    }

def correctness(*, output, expected_output, **kwargs):
    gold_df = query_df(expected_output["gold_sql"])
    ok = is_correct(output["sql"], gold_df)
    return Evaluation(name="correct", value=1.0 if ok else 0.0)


def llm_calls(*, output, **kwargs):
    return Evaluation(name="llm_calls", value=output["llm_calls"])

def report_quality(*, input, output, **kwargs):
    verdict = judge.invoke({
        "question": input["question"],
        "data": output["data"],
        "report": output["report"],
    })
    return Evaluation(name="report_quality", value=verdict.score, comment=verdict.reasoning)


def accuracy(*, item_results, **kwargs):
    scores = [e.value for r in item_results for e in r.evaluations if e.name == "correct"]
    return Evaluation(name="accuracy", value=sum(scores) / len(scores))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default="sql-agent", help="experiment name (what you're testing)")
    args = parser.parse_args()

    dataset = langfuse.get_dataset(DATASET_NAME)
    result = dataset.run_experiment(
        name=args.name,
        description="SQL agent on Northwind, result-set match vs gold SQL",
        task=task,
        evaluators=[correctness, llm_calls, report_quality],
        run_evaluators=[accuracy],
        max_concurrency=5,
        metadata={"model": settings.MODEL_NAME},
    )
    print(result.format())
    langfuse.flush()