import hmac
import html
import uuid
import streamlit as st

from config.settings import settings
from src.agents.chart_agent import build_figure
from src.graph import graph, pipeline_config, turn_input
from src.state import State

st.set_page_config(page_title="Data Assistant")

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
        background: rgba(128, 128, 128, 0.15);
        border-color: rgba(128, 128, 128, 0.3);
        color: inherit;
    }
    [data-testid="stSidebar"] [data-testid="stBaseButton-primary"]:hover {
        background: rgba(128, 128, 128, 0.25);
        border-color: rgba(128, 128, 128, 0.4);
        color: inherit;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

def check_access() -> None:
    """Ask for the demo access code once per session; stop rendering until it is correct."""
    if not settings.DEMO_ACCESS_CODE or st.session_state.get("authorized"):
        return
    st.markdown("<div style='height: 25vh'></div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center'>Demo access</h2>", unsafe_allow_html=True)
    code = st.text_input("Access code", type="password")
    if code:
        if hmac.compare_digest(code, settings.DEMO_ACCESS_CODE):
            st.session_state.authorized = True
            st.rerun()
        st.error("Wrong access code.")
    st.stop()

check_access()

PLACEHOLDER = "Ask a question about your data..."

if "chats" not in st.session_state:
    st.session_state.chats = {}

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

st.session_state.messages = st.session_state.chats.setdefault(st.session_state.session_id, [])
questions_left = settings.MAX_QUESTIONS_PER_SESSION - sum(len(m) for m in st.session_state.chats.values())
limit_reached = questions_left <= 0

with st.sidebar:
    st.caption(f"Demo: {max(questions_left, 0)} questions left")
    if st.button("New chat", use_container_width=True):
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.caption("Chats")
    for chat_id, msgs in reversed(st.session_state.chats.items()):
        if not msgs:
            continue
        is_current = chat_id == st.session_state.session_id
        if st.button(
            msgs[0]["question"][:40],
            key=chat_id,
            use_container_width=True,
            type="primary" if is_current else "secondary",
        ):
            st.session_state.session_id = chat_id
            st.rerun()

def run_pipeline(question: str) -> State:
    with st.status("Fetching the data...", expanded=False) as status:
        for mode, chunk in graph.stream(
            turn_input(question),
            config=pipeline_config(
                user_id="streamlit-anonymous",
                session_id=st.session_state.session_id,
                tags=["streamlit"],
            ),
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
        question = st.chat_input(PLACEHOLDER, disabled=limit_reached)
else:
    question = st.chat_input(PLACEHOLDER, disabled=limit_reached)
    if limit_reached:
        st.info("Demo limit reached. Thanks for trying it out!")

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