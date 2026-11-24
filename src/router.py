"""Router agent — reads a request and decides which specialist handles it.

Uses the LLM with structured output when an API key is available, and falls
back to simple keyword rules otherwise (handy for tests and demos).
"""

from langchain_openai import ChatOpenAI

from config import settings
from models import RouteDecision

ETL_KEYWORDS = ["load", "clean", "profile", "csv", "file", "import", "etl", "upload"]
SQL_KEYWORDS = [
    "how many", "total", "average", "top", "highest", "lowest", "revenue",
    "show me", "which", "count", "sum", "per city", "per driver",
]


def _keyword_route(question: str) -> RouteDecision:
    q = question.lower()
    if any(word in q for word in ETL_KEYWORDS):
        return RouteDecision(agent="etl_analyst", reason="request mentions file/ETL work")
    if any(word in q for word in SQL_KEYWORDS):
        return RouteDecision(agent="sql_analyst", reason="request looks like a data question")
    return RouteDecision(agent="general", reason="no clear signal, treating as general")


def route(question: str) -> RouteDecision:
    if not settings.openai_api_key:
        return _keyword_route(question)

    llm = ChatOpenAI(
        model=settings.openai_model, api_key=settings.openai_api_key, temperature=0
    ).with_structured_output(RouteDecision)

    prompt = f"""Classify this user request for a data agent.

- sql_analyst: a question that should be answered by querying the bookings database
  (counts, totals, rankings, revenue, trends).
- etl_analyst: a request to profile, clean, load or move data files.
- general: anything else.

Request: {question}"""
    try:
        return llm.invoke(prompt)
    except Exception:
        return _keyword_route(question)
