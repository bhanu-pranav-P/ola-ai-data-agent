"""ETL Analyst agent — a ReAct agent with plain Python tools.

Unlike the SQL Analyst (a fixed graph), ETL work is unpredictable: profile
this file, clean that column, load it there. So this agent uses the ReAct
pattern — the LLM reasons, picks a tool, looks at the result, and decides
the next step until the task is done.
"""

import os

import pandas as pd
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from config import settings
from db_utils import get_engine

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@tool
def profile_csv(file_path: str) -> str:
    """Profile a CSV file: row/column counts, column names, null counts and dtypes."""
    df = pd.read_csv(file_path)
    lines = [
        f"Rows: {len(df)}, Columns: {len(df.columns)}",
        f"Columns: {list(df.columns)}",
        "Nulls per column:",
    ]
    for col in df.columns:
        lines.append(f"  {col}: {int(df[col].isna().sum())} nulls, dtype {df[col].dtype}")
    dupes = int(df.duplicated().sum())
    lines.append(f"Fully duplicated rows: {dupes}")
    return "\n".join(lines)


@tool
def clean_csv(file_path: str) -> str:
    """Basic cleaning: drop fully duplicated rows, trim whitespace in text columns,
    drop rows that are entirely empty. Saves to data/cleaned/<name>_cleaned.csv
    and returns the new path plus what changed."""
    df = pd.read_csv(file_path)
    before = len(df)
    df = df.drop_duplicates().dropna(how="all")
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()
    out_dir = os.path.join(BASE_DIR, "data", "cleaned")
    os.makedirs(out_dir, exist_ok=True)
    name = os.path.splitext(os.path.basename(file_path))[0]
    out_path = os.path.join(out_dir, f"{name}_cleaned.csv")
    df.to_csv(out_path, index=False)
    return f"Cleaned file saved to {out_path}. Rows before: {before}, after: {len(df)}."


@tool
def load_csv_to_postgres(file_path: str, table_name: str) -> str:
    """Load a CSV file into a new Postgres table (replaces the table if it exists)."""
    df = pd.read_csv(file_path)
    df.to_sql(table_name, get_engine(), if_exists="replace", index=False)
    return f"Loaded {len(df)} rows into table '{table_name}'."


@tool
def summarise_table(table_name: str) -> str:
    """Give a quick summary of a table in Postgres: row count and basic stats
    for numeric columns."""
    df = pd.read_sql_table(table_name, get_engine())
    lines = [f"Table '{table_name}': {len(df)} rows, {len(df.columns)} columns."]
    numeric = df.describe().T
    for col, row in numeric.iterrows():
        lines.append(f"  {col}: min {row['min']:.2f}, max {row['max']:.2f}, mean {row['mean']:.2f}")
    return "\n".join(lines)


TOOLS = [profile_csv, clean_csv, load_csv_to_postgres, summarise_table]

SYSTEM_PROMPT = """You are an ETL analyst. You have tools to profile, clean and load CSV
data into PostgreSQL. Work step by step: profile a file before loading it, and
report clearly what you did, including row counts before and after."""


def ask_etl_agent(task: str) -> str:
    llm = ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0)
    agent = create_react_agent(llm, TOOLS, prompt=SYSTEM_PROMPT)
    result = agent.invoke({"messages": [("user", task)]})
    return result["messages"][-1].content
