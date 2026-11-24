"""SQL Analyst agent — a LangGraph graph with a self-checking loop.

Flow:
    get_schema -> generate_sql -> execute_sql -> judge
                      ^                          |
                      └──── rewrite (if judge ───┘
                            rejects, max 2)
    judge approves -> format_answer -> END

The judge is the interesting part: a second LLM call that only checks
"did this result actually answer the question?" and returns a structured
verdict (see models.JudgeVerdict). Without it, text-to-SQL demos happily
return wrong-but-plausible numbers.
"""

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

import db_utils
from config import settings
from models import JudgeVerdict, SQLAgentState

llm = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0)
judge_llm = llm.with_structured_output(JudgeVerdict)


def get_schema(state: SQLAgentState) -> dict:
    return {"schema_info": db_utils.get_schema_info()}


def generate_sql(state: SQLAgentState) -> dict:
    retry_note = ""
    if state.judge_feedback:
        retry_note = (
            f"\nYour previous query was:\n{state.generated_sql}\n"
            f"The judge rejected the result: {state.judge_feedback}\n"
            "Write a corrected query."
        )
    if state.error:
        retry_note += f"\nThe previous query failed with this error: {state.error}\nFix it."

    prompt = f"""You are a PostgreSQL expert. Write ONE read-only SQL query that answers the question.

Database schema:
{state.schema_info}

Question: {state.question}
{retry_note}

Rules:
- Output ONLY the SQL query, no explanation, no markdown fences.
- Use only tables and columns from the schema above.
- Add a LIMIT when the question doesn't ask for an aggregate."""

    sql = llm.invoke(prompt).content.strip().strip("`").replace("sql\n", "", 1).strip()
    # print("Generated SQL:", sql)  # uncomment when a question gives a weird answer
    return {"generated_sql": sql, "error": None}


def execute_sql(state: SQLAgentState) -> dict:
    try:
        rows = db_utils.run_query(state.generated_sql)
        return {"query_result": rows[: settings.max_rows_to_show]}
    except Exception as exc:  # send the error back so the next attempt can fix it
        return {"query_result": [], "error": str(exc)}


def judge(state: SQLAgentState) -> dict:
    if state.error:
        # nothing to judge — an execution error always goes back for a rewrite
        return {"judge_feedback": f"Query failed: {state.error}", "retry_count": state.retry_count + 1}

    prompt = f"""You are a strict reviewer of SQL results.

Question: {state.question}
SQL used: {state.generated_sql}
Result rows: {state.query_result}

Does this result actually answer the question? Be strict about wrong columns,
wrong filters and empty results that should not be empty."""
    verdict: JudgeVerdict = judge_llm.invoke(prompt)
    return {
        "judge_feedback": "" if verdict.is_correct else verdict.feedback,
        "retry_count": state.retry_count if verdict.is_correct else state.retry_count + 1,
    }


def should_retry(state: SQLAgentState) -> str:
    needs_retry = bool(state.judge_feedback) or bool(state.error)
    if needs_retry and state.retry_count <= settings.max_sql_retries:
        return "generate_sql"
    return "format_answer"


def format_answer(state: SQLAgentState) -> dict:
    if state.error and not state.query_result:
        return {
            "final_answer": (
                f"I couldn't get a working query for that question. "
                f"Last error: {state.error}\nLast SQL tried: {state.generated_sql}"
            )
        }
    prompt = f"""Answer the question in plain English using the query result.
Keep it short and state the actual numbers.

Question: {state.question}
SQL used: {state.generated_sql}
Result: {state.query_result}"""
    answer = llm.invoke(prompt).content.strip()
    return {"final_answer": f"{answer}\n\n(SQL used: {state.generated_sql})"}


def build_sql_agent():
    graph = StateGraph(SQLAgentState)
    graph.add_node("get_schema", get_schema)
    graph.add_node("generate_sql", generate_sql)
    graph.add_node("execute_sql", execute_sql)
    graph.add_node("judge", judge)
    graph.add_node("format_answer", format_answer)

    graph.set_entry_point("get_schema")
    graph.add_edge("get_schema", "generate_sql")
    graph.add_edge("generate_sql", "execute_sql")
    graph.add_edge("execute_sql", "judge")
    graph.add_conditional_edges("judge", should_retry, {"generate_sql": "generate_sql", "format_answer": "format_answer"})
    graph.add_edge("format_answer", END)
    return graph.compile()


def ask_sql_agent(question: str) -> str:
    agent = build_sql_agent()
    result = agent.invoke(SQLAgentState(question=question))
    return result["final_answer"]
