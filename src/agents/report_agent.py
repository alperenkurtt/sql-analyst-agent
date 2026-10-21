from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langdetect import DetectorFactory, LangDetectException, detect
from langchain_core.runnables import RunnableConfig

from config.llm import llm
from config.settings import settings
from src.state import State

DetectorFactory.seed = 0
LANG_NAMES = {"tr": "Turkish", "en": "English"}

MAX_ROWS = 50
FLOAT_FORMAT = lambda x: f"{x:,.2f}"

SYSTEM_PROMPT = """
You are a report agent. You receive a user's question and the data that answers it.
Write a short, clear answer to the question using ONLY the given data.
- The user already sees the full data table. Never copy it row by row; summarize it instead.
- If only part of the data is shown, start by stating the total number of rows and use the
  summary statistics for overall figures. Do not claim things about the rows you cannot see.
- Do not invent numbers, names, trends, units or currencies that are not in the data.
- If the data is empty, say that no matching records were found.
- Do not mention SQL, tables or columns; write for a business user.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", (
        "Question: {question}\n\n"
        "Data:\n{data}\n\n"
        "All monetary values are in {currency}.\n"
        "Answer in {language}."
    )),
])

chain = (prompt | llm | StrOutputParser()).with_config(run_name="report_agent")


def data_to_text(state: State) -> str:
    df = state.get("data")
    if df is None or df.empty:
        return "No data (0 rows)."

    if len(df) <= MAX_ROWS:
        return df.to_string(index=False, float_format=FLOAT_FORMAT)

    return (
        f"{df.head(MAX_ROWS).to_string(index=False, float_format=FLOAT_FORMAT)}\n"
        f"... ({len(df)} rows total, showing first {MAX_ROWS})\n\n"
        f"Summary statistics of all rows:\n{df.describe().to_string(float_format=FLOAT_FORMAT)}"
    )


def detect_language(text: str) -> str:
    try:
        return LANG_NAMES.get(detect(text), "English")
    except LangDetectException:
        return "English"


def run_report_agent(state: State, config: RunnableConfig | None = None) -> dict:
    report = chain.invoke(
        {
            "question": state["question"],
            "data": data_to_text(state),
            "currency": settings.CURRENCY,
            "language": detect_language(state["question"]),
        },
        config=config,
    )
    return {"report": report, "llm_calls": 1}