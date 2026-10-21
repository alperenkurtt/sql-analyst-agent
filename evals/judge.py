from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from config.llm import llm

SYSTEM_PROMPT = """
You evaluate answers written by a data assistant. You receive the user's question,
the data the assistant was given, and the assistant's report.
Check:
1. Faithfulness: every number, name and fact in the report appears in the data. Nothing invented.
2. Relevance: the report directly answers the question.
3. Language: the report is written in the language of the question.
Score 1-5:
5 = faithful, answers the question, correct language.
3 = answers the question but has a minor issue (vague, slightly off, missing a key number).
1 = invents or misstates data, or does not answer the question.
"""


class Verdict(BaseModel):
    reasoning: str = Field(description="Short check of each criterion, written before the score.")
    score: int = Field(ge=1, le=5, description="Overall score from 1 to 5.")


prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Question: {question}\n\nData:\n{data}\n\nReport:\n{report}"),
])

judge = (prompt | llm.with_structured_output(Verdict)).with_config(run_name="report_judge")