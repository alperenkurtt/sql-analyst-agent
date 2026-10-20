import json
import sys

import pandas as pd
import plotly.express as px

from config.llm import chat
from src.state import State

CHART_TYPES = ("bar", "line", "pie", "scatter")

SYSTEM_PROMPT = """
You are a chart agent. You receive a question and a description of the data that answers it.
Decide whether a chart would help and, if so, which one.
- bar: compare categories. line: values over time. pie: parts of a whole (at most 8 slices).
    scatter: relation between two numeric columns.
- x and y must be exact column names from the data. y must be a numeric measure, not an ID.
- color is optional: a column that splits the data into series (e.g. a year column when comparing periods).
- Write the title in the language of the question.
- If a chart would not help, reply {"type": null}.

Reply in JSON: {"type": "bar|line|pie|scatter", "x": "...", "y": "...", "color": null, "title": "..."}
"""

def describe_data(df: pd.DataFrame) -> str:
    """LLM'e tablonun tamamını değil, kolon tiplerini ve ilk 5 satırı veriyoruz."""
    return (
        f"{len(df)} rows.\nColumn types:\n{df.dtypes.to_string()}\n\n"
        f"First rows:\n{df.head(5).to_string(index=False)}"
    )

def is_valid(spec: dict, df: pd.DataFrame) -> bool:
    """LLM'in cevabına körü körüne güvenme: tip ve kolonlar gerçekten var mı?"""
    if spec.get("type") not in CHART_TYPES:
        return False
    if spec.get("x") not in df.columns or spec.get("y") not in df.columns:
        return False
    if spec.get("color") not in (None, *df.columns):
        return False
    return pd.api.types.is_numeric_dtype(df[spec["y"]])

def run_chart_agent(state: State) -> State:
    df = state.data
    # Tek satır ya da sayısal kolon yoksa grafiğe gerek yok, LLM çağrısı da harcama
    if df is None or len(df) < 2 or df.select_dtypes("number").empty:
        return state

    response = chat(
        state,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Question: {state.question}\n\nData:\n{describe_data(df)}"},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    spec = json.loads(response.choices[0].message.content)
    if is_valid(spec, df):
        state.chart = spec
    return state

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
    state = run_chart_agent(run_sql_agent(State(question=question), verbose=False))
    print(f"📋 Data:\n{state.data}\n📈 Chart: {state.chart}\n📞 LLM calls: {state.llm_calls}")
    if state.chart:
        build_figure(state.chart, state.data).show()  # tarayıcıda açar