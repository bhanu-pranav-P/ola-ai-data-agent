"""Small helpers around the Postgres connection.

The most important function here is `is_safe_select` — the SQL agent is only
allowed to run read-only queries, and this is the gate that enforces it.
"""

import re

from sqlalchemy import create_engine, text

from config import settings

_engine = None

# anything that changes data or structure is banned for the SQL agent
# TODO: the keyword check is regex-based and could probably be fooled by a
# clever query. For a portfolio project it's fine, but a real deployment
# should also run with a read-only DB user.
BANNED_KEYWORDS = [
    "insert", "update", "delete", "drop", "alter", "truncate",
    "create", "grant", "revoke", "copy", "vacuum", "analyze",
]


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url)
    return _engine


def is_safe_select(sql: str) -> tuple[bool, str]:
    """Return (True, "") if the SQL is a single read-only SELECT, else (False, reason)."""
    cleaned = sql.strip().rstrip(";")
    if not cleaned:
        return False, "empty query"
    if ";" in cleaned:
        return False, "multiple statements are not allowed"
    lowered = cleaned.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        return False, "only SELECT queries are allowed"
    for keyword in BANNED_KEYWORDS:
        if re.search(rf"\b{keyword}\b", lowered):
            return False, f"keyword '{keyword}' is not allowed"
    return True, ""


def get_schema_info() -> str:
    """Describe every table and column so the LLM writes grounded SQL."""
    query = text(
        """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
        """
    )
    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(query).fetchall()

    tables: dict[str, list[str]] = {}
    for table_name, column_name, data_type in rows:
        tables.setdefault(table_name, []).append(f"{column_name} ({data_type})")

    lines = []
    for table_name, columns in tables.items():
        lines.append(f"Table {table_name}: " + ", ".join(columns))
    return "\n".join(lines)


def run_query(sql: str) -> list[dict]:
    """Run a read-only query and return rows as dicts. Raises ValueError on unsafe SQL."""
    safe, reason = is_safe_select(sql)
    if not safe:
        raise ValueError(f"Unsafe SQL rejected: {reason}")
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        return [dict(row) for row in result.mappings().fetchall()]
