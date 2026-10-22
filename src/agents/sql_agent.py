import sys

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from config.llm import langfuse, langfuse_handler, llm
from src.state import State
from src.tools.db_tools import TOOLS, query_df

MAX_STEPS = 10
MAX_HISTORY = 5

SYSTEM_PROMPT = """
You are a data agent working on a SQLite database (Northwind).
Your only job is to fetch the data the user's question asks for.
Use list_tables and describe_table to explore the schema, then use run_sql to get the data.
If a query returns an error, fix it and retry. When you have the data, stop calling tools.
Your LAST run_sql query must return the complete answer by itself, in one query.
Do not split the answer into multiple queries or compute anything outside SQL.

Data notes:
- Dialect is SQLite. Use strftime()/date() for dates; YEAR()/MONTH() do not exist.
- Orders.OrderDate, RequiredDate, ShippedDate are TEXT with mixed formats. Wrap with date() when comparing.
- Assume today's date is 2023-10-28 for relative time expressions ("this year", "last month").
- Revenue = UnitPrice * Quantity * (1 - Discount), computed from "Order Details".
- Questions may be in other languages; translate terms to the English values stored in the database
(e.g. 'Almanya' -> 'Germany').
"""

agent = create_agent(
    model=llm,
    tools=TOOLS,
    system_prompt=SYSTEM_PROMPT,
    middleware=[ModelCallLimitMiddleware(run_limit=MAX_STEPS)],
    name="sql_agent",
)

def last_successful_sql(messages) -> str | None:
    results = {m.tool_call_id: m.content for m in messages if isinstance(m, ToolMessage)}
    last_sql = None
    for m in messages:
        if not isinstance(m, AIMessage):
            continue
        for call in m.tool_calls:
            if call["name"] == "run_sql" and not results.get(call["id"], "Error").startswith("Error"):
                last_sql = call["args"]["query"]
    return last_sql


def print_steps(messages) -> None:
    results = {m.tool_call_id: m.content for m in messages if isinstance(m, ToolMessage)}
    step = 0
    for m in messages:
        if isinstance(m, AIMessage) and m.tool_calls:
            step += 1
            for call in m.tool_calls:
                result = results.get(call["id"], "")
                print(f"[{step}] 🔧 {call['name']}({call['args']})")
                print(f"     ↳ {result[:200]}{'...' if len(result) > 200 else ''}")


def build_messages(state: State) -> list[dict]:
    messages = []
    for turn in state.get("history", [])[-MAX_HISTORY:]:
        messages.append({"role": "user", "content": turn["question"]})
        messages.append({"role": "assistant", "content": f"Final SQL:\n{turn['sql']}"})
    messages.append({"role": "user", "content": state["question"]})
    return messages


def run_sql_agent(state: State, config: RunnableConfig | None = None, verbose: bool = False) -> dict:
    input_messages = build_messages(state)
    result = agent.invoke({"messages": input_messages}, config=config)
    messages = result["messages"][len(input_messages):]

    if verbose:
        print_steps(messages)

    sql = last_successful_sql(messages)
    return {
        "sql": sql,
        "data": query_df(sql) if sql else None,
        "llm_calls": sum(isinstance(m, AIMessage) for m in messages),
        "history": [{"question": state["question"], "sql": sql}] if sql else [],
    }


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "2023 yılında en çok ciro yapan 5 ürün hangisi?"
    print(f"❓ {question}\n")
    out = run_sql_agent({"question": question}, config={"callbacks": [langfuse_handler()]}, verbose=True)
    print(f"\n📊 SQL: {out['sql']}\n📋 Data:\n{out['data']}\n📞 LLM calls: {out['llm_calls']}")
    langfuse.flush()