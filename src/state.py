from dataclasses import dataclass

import pandas as pd

@dataclass
class State:
    question: str
    sql: str | None = None
    data: pd.DataFrame | None = None
    report: str | None = None
    chart: dict | None = None
    llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    llm_seconds: float = 0.0
