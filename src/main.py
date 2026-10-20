import sys

from src.agents.report_agent import run_report_agent
from src.agents.sql_agent import run_sql_agent
from src.agents.chart_agent import run_chart_agent
from src.state import State


def run_pipeline(question: str, verbose: bool = False) -> State:
    state = State(question=question)
    state = run_sql_agent(state, verbose=verbose)      # 1) SQL agent
    state = run_report_agent(state)                    # 2) Report agent
    state = run_chart_agent(state)                     # 3) Chart agent
    return state


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "2023 yılında en çok ciro yapan 5 ürün hangisi?"
    print(f"Question: {question}\n")
    state = run_pipeline(question)
    print(f"SQL: {state.sql}")
    print(f"DATA: {state.data}")
    print(f"REPORT:\n{state.report}")
    print(f"CHART: {state.chart}")
    print(f"LLM calls: {state.llm_calls}")
    print(f"Input tokens: {state.prompt_tokens}")
    print(f"Output tokens: {state.completion_tokens}")
    print(f"Cost: {state.cost_usd}")
    print(f"Latency: {state.llm_seconds}")
