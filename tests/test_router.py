"""Router tests — these use the keyword fallback, so no API key needed."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from router import _keyword_route  # noqa: E402


def test_data_question_goes_to_sql_agent():
    decision = _keyword_route("Which city has the highest total revenue?")
    assert decision.agent == "sql_analyst"


def test_file_task_goes_to_etl_agent():
    decision = _keyword_route("Profile the CSV file and load it into the database")
    assert decision.agent == "etl_analyst"


def test_smalltalk_is_general():
    decision = _keyword_route("Hello, what can you do?")
    assert decision.agent == "general"
