"""Data Agent — orchestration entry point.

    Router ──► SQL Analyst (LangGraph, with judge loop)
           └──► ETL Analyst (ReAct agent)
           └──► plain LLM reply for everything else

Run it:
    python src/main.py
"""

from typing import Optional

from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel

from config import settings
from etl_agent import ask_etl_agent
from models import RouteDecision
from router import route
from sql_agent import ask_sql_agent


class OrchestratorState(BaseModel):
    question: str
    decision: Optional[RouteDecision] = None
    answer: str = ""


def router_node(state: OrchestratorState) -> dict:
    decision = route(state.question)
    print(f"[router] -> {decision.agent} ({decision.reason})")
    return {"decision": decision}


def sql_node(state: OrchestratorState) -> dict:
    return {"answer": ask_sql_agent(state.question)}


def etl_node(state: OrchestratorState) -> dict:
    return {"answer": ask_etl_agent(state.question)}


def general_node(state: OrchestratorState) -> dict:
    llm = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0)
    reply = llm.invoke(
        "You are a data assistant. The user said: " + state.question +
        "\nReply helpfully in one or two lines. If they seem to be asking about data, "
        "suggest they ask a question about bookings, or give you a file task."
    )
    return {"answer": reply.content}


def pick_agent(state: OrchestratorState) -> str:
    return state.decision.agent if state.decision else "general"


def build_data_agent():
    graph = StateGraph(OrchestratorState)
    graph.add_node("router", router_node)
    graph.add_node("sql_analyst", sql_node)
    graph.add_node("etl_analyst", etl_node)
    graph.add_node("general", general_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        pick_agent,
        {"sql_analyst": "sql_analyst", "etl_analyst": "etl_analyst", "general": "general"},
    )
    graph.add_edge("sql_analyst", END)
    graph.add_edge("etl_analyst", END)
    graph.add_edge("general", END)
    return graph.compile()


def main() -> None:
    if not settings.openai_api_key:
        print("Warning: OPENAI_API_KEY is not set — routing will use keyword fallback "
              "and the agents will not be able to call the model.\n")
    agent = build_data_agent()
    print("Ola AI Data Agent. Ask a data question, or give an ETL task. Ctrl+C to exit.\n")
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if not question:
            continue
        result = agent.invoke(OrchestratorState(question=question))
        print(f"\nAgent: {result['answer']}\n")


if __name__ == "__main__":
    main()
