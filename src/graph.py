from langgraph.graph import END, START, StateGraph

from config.llm import langfuse_handler
from src.agents.chart_agent import needs_chart, run_chart_agent
from src.agents.report_agent import run_report_agent
from src.agents.sql_agent import run_sql_agent
from src.state import State
from config.settings import settings
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.types import Overwrite
import uuid


def route_chart(state: State) -> str:
    return "chart" if needs_chart(state) else END


builder = StateGraph(State)
builder.add_node("sql", run_sql_agent)
builder.add_node("report", run_report_agent)
builder.add_node("chart", run_chart_agent)

builder.add_edge(START, "sql")
builder.add_edge("sql", "report")
builder.add_conditional_edges("sql", route_chart, ["chart", END])
builder.add_edge("report", END)
builder.add_edge("chart", END)

graph = builder.compile(checkpointer=InMemorySaver(serde=JsonPlusSerializer(pickle_fallback=True)))

APP_NAME = "sql_analyst"

def turn_input(question: str) -> dict:
    return {"question": question, "chart": None, "llm_calls": Overwrite(0)}

def pipeline_config(user_id: str, session_id: str | None = None, tags: list[str] | None = None) -> dict:
    metadata = {
        "app_name": APP_NAME,
        "model": settings.MODEL_NAME,
        "langfuse_user_id": user_id,
        "langfuse_tags": [APP_NAME, *(tags or [])],
    }
    if session_id:
        metadata["langfuse_session_id"] = session_id
    return {
        "callbacks": [langfuse_handler()],
        "run_name": APP_NAME,
        "metadata": metadata,
        "configurable": {"thread_id": session_id or str(uuid.uuid4())},
    }