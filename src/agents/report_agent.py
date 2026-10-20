from langdetect import DetectorFactory, LangDetectException, detect

from config.llm import chat
from config.settings import settings
from src.state import State

DetectorFactory.seed = 0
LANG_NAMES = {"tr": "Turkish", "en": "English"}

MAX_ROWS = 50
FLOAT_FORMAT = lambda x: f"{x:,.2f}"  # 1.88e+07 yerine 18,823,200.00 → LLM büyüklüğü yanlış okumasın

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

def data_to_text(state: State) -> str:
    """Küçük tablo → tamamı. Büyük tablo → ilk MAX_ROWS satır + toplam satır sayısı + describe()."""
    df = state.data
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

def run_report_agent(state: State) -> State:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Question: {state.question}\n\n"
            f"Data:\n{data_to_text(state)}\n\n"
            f"All monetary values are in {settings.CURRENCY}.\n"
            f"Answer in {detect_language(state.question)}."
        )},
    ]
    response = chat(
        state,
        messages=messages,
        temperature=0,
    )
    state.report = response.choices[0].message.content
    return state