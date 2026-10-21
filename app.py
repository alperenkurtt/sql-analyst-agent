import html

import streamlit as st

from src.agents.chart_agent import build_figure
from src.graph import graph, pipeline_config
from src.state import State

st.set_page_config(page_title="Data Assistant")

PLACEHOLDER = "Ask a question about your data..."

if "messages" not in st.session_state:
    st.session_state.messages = []


def run_pipeline(question: str) -> State:
    with st.status("Fetching the data...", expanded=False) as status:
        for mode, chunk in graph.stream(
            {"question": question},
            config=pipeline_config(),
            stream_mode=["updates", "values"],
        ):
            if mode == "updates" and "sql" in chunk:
                status.update(label="Writing the answer and choosing a chart...")
            elif mode == "values":
                state = chunk
    return state


def render_answer(state: State) -> None:
    st.markdown(state.get("report"))
    if state.get("chart"):
        st.plotly_chart(build_figure(state["chart"], state["data"]), use_container_width=True)
    with st.expander("Data"):
        st.dataframe(state.get("data"), use_container_width=True)
    with st.expander("SQL"):
        st.code(state.get("sql") or "-", language="sql")


if not st.session_state.messages:
    with st.container():
        st.markdown("<div style='height: 30vh'></div>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center'>What would you like to know?</h2>", unsafe_allow_html=True)
        question = st.chat_input(PLACEHOLDER)
else:
    question = st.chat_input(PLACEHOLDER)

    for msg in st.session_state.messages:
        st.markdown(
            "<div style='display: flex; justify-content: flex-end; margin: 1rem 0'>"
            "<div style='background: rgba(128, 128, 128, 0.15); padding: 0.6rem 1rem; "
            f"border-radius: 1rem; max-width: 80%'>{html.escape(msg['question'])}</div></div>",
            unsafe_allow_html=True,
        )
        if msg["state"] is None:
            status_slot = st.empty()
            with status_slot.container():
                msg["state"] = run_pipeline(msg["question"])
            status_slot.empty()
        render_answer(msg["state"])

if question:
    st.session_state.messages.append({"question": question, "state": None})
    st.rerun()