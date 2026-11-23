"""Pydantic models shared by the agents.

The SQL agent passes its working state through a LangGraph graph, and the
judge returns a structured verdict instead of free text — that's what makes
the retry loop reliable.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class SQLAgentState(BaseModel):
    """Everything the SQL Analyst graph carries from node to node."""

    question: str
    schema_info: str = ""
    generated_sql: str = ""
    query_result: list[dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    judge_feedback: str = ""
    retry_count: int = 0
    final_answer: str = ""


class JudgeVerdict(BaseModel):
    """Structured output of the LLM-as-a-Judge step."""

    is_correct: bool
    score: int = Field(ge=0, le=10, description="How well the result answers the question")
    feedback: str = Field(description="What is wrong, if anything, in one or two lines")


class RouteDecision(BaseModel):
    """Structured output of the Router agent."""

    agent: str = Field(description="One of: sql_analyst, etl_analyst, general")
    reason: str = Field(description="Short reason for the routing decision")
