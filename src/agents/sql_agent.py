import json
import sys

from config.llm import chat
from src.tools.db_tools import TOOL_SCHEMAS, TOOLS, query_df
from src.state import State

MAX_STEPS = 10

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

def run_sql_agent(state: State, verbose: bool = True) -> State:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": state.question},
    ]
    last_sql = None  # son BAŞARILI run_sql sorgusu → eval bununla puanlanacak

    for step in range(1, MAX_STEPS + 1):
        # 1) LLM'e konuşmanın tamamını + tool menüsünü gönder
        response = chat(
            state,
            messages=messages,
            tools=TOOL_SCHEMAS,
            temperature=0,
        )
        msg = response.choices[0].message

        # 2) LLM'in cevabını geçmişe ekle (tool_calls dahil, yoksa API sonraki adımda hata verir)
        messages.append(msg.model_dump(exclude_none=True))

        # 3) Tool istemediyse: LLM "bitti" dedi
        if not msg.tool_calls:
            break

        # 4) İstenen her tool'u çalıştır, sonucu geri ver
        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments or "{}")  # argümanlar JSON string gelir

            if name in TOOLS:
                result = TOOLS[name](**args)
            else:
                result = f"Error: unknown tool '{name}'"

            if name == "run_sql" and not result.startswith("Error"):
                last_sql = args["query"]

            if verbose:
                print(f"[{step}] 🔧 {name}({args})")
                print(f"     ↳ {result[:200]}{'...' if len(result) > 200 else ''}")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,  # hangi isteğin cevabı olduğunu eşler
                "content": result,
            })

    # LLM'e kırpılmış metin gitti; state'e kırpılmamış DataFrame koyuyoruz
    state.sql = last_sql
    state.data = query_df(last_sql) if last_sql else None
    return state

if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "2023 yılında en çok ciro yapan 5 ürün hangisi?"
    print(f"❓ {question}\n")
    state = run_sql_agent(State(question=question))
    print(f"📊 SQL: {state.sql}\n📋 Data:\n{state.data}\n📞 LLM calls: {state.llm_calls}")
