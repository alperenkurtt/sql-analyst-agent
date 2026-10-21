import sys
from typing import Literal

import pandas as pd
import plotly.express as px
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from config.llm import langfuse, langfuse_handler, llm
from src.state import State

CHART_TYPES = ("bar", "line", "pie", "scatter")

SYSTEM_PROMPT = """
You are a chart agent. You receive a question and a description of the data that answers it.
Decide whether a chart would help and, if so, which one.
- bar: compare categories. line: values over time. pie: parts of a whole (at most 8 slices).
- scatter: relation between two numeric columns.
- x and y must be exact column names from the data. y must be a numeric measure, not an ID.
- color is optional: a column that splits the data into series (e.g. a year column when comparing periods).
- Write the title in the language of the question.
- If a chart would not help, set type to null.
"""

class ChartSpec(BaseModel):
    """How to draw the chart. type is null when a chart would not help."""
    type: Literal["bar", "line", "pie", "scatter"] | None = Field(description="Chart type, or null for no chart.")
    x: str | None = Field(description="Exact column name for the x axis (pie: slice labels).")
    y: str | None = Field(description="Exact numeric column name for the y axis (pie: slice sizes).")
    color: str | None = Field(description="Column that splits the data into series, or null.")
    title: str | None = Field(description="Chart title in the language of the question.")


prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Question: {question}\n\nData:\n{data}"),
])

chain = (prompt | llm.with_structured_output(ChartSpec)).with_config(run_name="chart_agent")


def describe_data(df: pd.DataFrame) -> str:
    return (
        f"{len(df)} rows.\nColumn types:\n{df.dtypes.to_string()}\n\n"
        f"First rows:\n{df.head(5).to_string(index=False)}"
    )


def is_valid(spec: dict, df: pd.DataFrame) -> bool:
    if spec.get("type") not in CHART_TYPES:
        return False
    if spec.get("x") not in df.columns or spec.get("y") not in df.columns:
        return False
    if spec.get("color") not in (None, *df.columns):
        return False
    return pd.api.types.is_numeric_dtype(df[spec["y"]])


def needs_chart(state: State) -> bool:
    df = state.get("data")
    return df is not None and len(df) >= 2 and not df.select_dtypes("number").empty


def run_chart_agent(state: State, config: RunnableConfig | None = None) -> dict:
    df = state["data"]
    spec = chain.invoke(
        {"question": state["question"], "data": describe_data(df)},
        config=config,
    ).model_dump()
    return {"chart": spec if is_valid(spec, df) else None, "llm_calls": 1}


def build_figure(spec: dict, df: pd.DataFrame):
    """Tariften plotly figürü üretir. Streamlit'te st.plotly_chart(fig) ile gösterilecek."""
    if spec["type"] == "pie":
        return px.pie(df, names=spec["x"], values=spec["y"], title=spec.get("title"))
    draw = {"bar": px.bar, "line": px.line, "scatter": px.scatter}[spec["type"]]
    return draw(df, x=spec["x"], y=spec["y"], color=spec.get("color"), title=spec.get("title"))


if __name__ == "__main__":
      from src.agents.sql_agent import run_sql_agent

      question = " ".join(sys.argv[1:]) or "2023 yılında kategorilere göre ciro nedir?"
      print(f"❓ {question}\n")
      config = {"callbacks": [langfuse_handler()]}
      state = {"question": question}
      state |= run_sql_agent(state, config=config)
      if needs_chart(state):
          state |= run_chart_agent(state, config=config)
      print(f"📋 Data:\n{state['data']}\n📈 Chart: {state.get('chart')}")
      langfuse.flush()
      if state.get("chart"):
          build_figure(state["chart"], state["data"]).show()