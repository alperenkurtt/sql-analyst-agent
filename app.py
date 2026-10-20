import html

import streamlit as st

from src.agents.chart_agent import build_figure, run_chart_agent
from src.agents.report_agent import run_report_agent
from src.agents.sql_agent import run_sql_agent
from src.state import State

st.set_page_config(page_title="Veri Asistanı")

PLACEHOLDER = "Verine bir soru sor..."

# Her soru-cevap çifti burada: {"question": str, "state": State | None}
if "messages" not in st.session_state:
    st.session_state.messages = []


def run_pipeline(question: str) -> State:
    # Küçük, kapalı bir status: sadece etiket değişiyor, dikkat çekmiyor
    with st.status("SQL agent veriyi getiriyor...", expanded=False) as status:
        state = run_sql_agent(State(question=question), verbose=False)
        status.update(label="Raporcu cevabı yazıyor...")
        state = run_report_agent(state)
        status.update(label="Grafikçi grafiği seçiyor...")
        state = run_chart_agent(state)
    return state


def render_answer(state: State) -> None:
    st.markdown(state.report)
    if state.chart:
        st.plotly_chart(build_figure(state.chart, state.data), use_container_width=True)
    with st.expander("📋 Veri"):
        st.dataframe(state.data, use_container_width=True)
    with st.expander("🧾 SQL"):
        st.code(state.sql or "-", language="sql")


if not st.session_state.messages:
    # İlk açılış: soru çubuğu ekranın ortasında
    st.markdown("<div style='height: 30vh'></div>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center'>Ne öğrenmek istersin?</h2>", unsafe_allow_html=True)
    with st.container():  # container içindeki chat_input alta yapışmaz, olduğu yerde durur
        question = st.chat_input(PLACEHOLDER)
else:
    for msg in st.session_state.messages:
        # chat_message yerine sade balon: avatar yok, cevap tam genişlikte
        st.markdown(
            "<div style='display: flex; justify-content: flex-end; margin: 1rem 0'>"
            "<div style='background: rgba(128, 128, 128, 0.15); padding: 0.6rem 1rem; "
            f"border-radius: 1rem; max-width: 80%'>{html.escape(msg['question'])}</div></div>",
            unsafe_allow_html=True,
        )
        if msg["state"] is None:  # yeni soru: şimdi çalıştır ve sakla
            status_slot = st.empty()
            with status_slot.container():
                msg["state"] = run_pipeline(msg["question"])
            status_slot.empty()
        render_answer(msg["state"])
    question = st.chat_input(PLACEHOLDER)  # sayfa gövdesinde → en alta sabitlenir

if question:
    st.session_state.messages.append({"question": question, "state": None})
    st.rerun()  # düzeni (orta → alt) değiştirmek için baştan çiz
