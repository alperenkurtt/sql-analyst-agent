import operator
from typing import Annotated, TypedDict

import pandas as pd

class State(TypedDict, total=False):
    question: str
    sql: str | None
    data: pd.DataFrame | None
    report: str | None
    chart: dict | None
    llm_calls: Annotated[int, operator.add]
    history: Annotated[list[dict], operator.add]