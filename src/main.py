import sys

from config.llm import langfuse
from src.graph import graph, pipeline_config

if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "2023 yılında en çok ciro yapan 5 ürün hangisi?"
    print(f"Question: {question}\n")
    state = graph.invoke({"question": question}, config=pipeline_config())
    print(f"SQL: {state.get('sql')}")
    print(f"DATA:\n{state.get('data')}")
    print(f"REPORT:\n{state.get('report')}")
    print(f"CHART: {state.get('chart')}")
    print(f"LLM calls: {state['llm_calls']}")
    langfuse.flush()