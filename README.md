# Ola AI Data Agent

An end-to-end **agentic AI project for the data domain**. You ask questions in plain
English, and a small team of AI agents figures out what to do with them:

- *"Which city had the highest revenue last month?"* → the **SQL Analyst** writes and
  runs SQL against a PostgreSQL database of ride bookings.
- *"Load this new bookings CSV into the warehouse and tell me if the data looks clean"*
  → the **ETL Analyst** picks up its tools and does the data work.
- A **Router Agent** reads every request first and sends it to the right specialist.

The SQL Analyst doesn't just fire off one query and hope for the best — an
**LLM-as-a-Judge** step reviews the SQL and the result, and if the answer looks wrong
the agent rewrites the query and tries again (up to 2 retries).

Built with **LangChain, LangGraph, Pydantic, PostgreSQL and Python**.

## Why I built this

Data teams spend half their day answering two kinds of requests: "can you pull this
number?" and "can you load/clean this data?". This project explores how far a
multi-agent setup can go in handling both — with a router, specialised sub-agents,
structured state (Pydantic), and a self-checking loop instead of blind one-shot answers.

The sample data is modelled on a ride-hailing company (Ola-style): bookings,
customers and drivers for a few Indian cities.

## Architecture

```
                        ┌─────────────────┐
            question ──►│  Router Agent   │  classifies intent
                        └───────┬─────────┘
                   ┌────────────┴────────────┐
                   ▼                         ▼
        ┌────────────────────┐    ┌────────────────────┐
        │   SQL Analyst      │    │    ETL Analyst     │
        │   (LangGraph)      │    │    (ReAct agent)   │
        │                    │    │                    │
        │  generate SQL      │    │  tools:            │
        │       ↓            │    │   - profile a CSV  │
        │  run query         │    │   - clean a CSV    │
        │       ↓            │    │   - load to DB     │
        │  LLM judge ──┐     │    │   - table summary  │
        │       ↑      │fail │    └─────────┬──────────┘
        │       └──────┘     │              │
        │  format answer     │              │
        └─────────┬──────────┘              │
                  └────────────┬────────────┘
                               ▼
                      PostgreSQL (Docker)
```

## Project structure

```
.
├── data/                  # sample CSVs (bookings, customers, drivers)
├── db/
│   ├── schema.sql         # table definitions
│   └── seed.py            # creates tables and loads the CSVs
├── src/
│   ├── config.py          # settings (.env based)
│   ├── models.py          # Pydantic state + result models
│   ├── db_utils.py        # DB connection, schema info, read-only SQL guard
│   ├── sql_agent.py       # SQL Analyst — LangGraph graph with judge loop
│   ├── etl_agent.py       # ETL Analyst — ReAct agent + tools
│   ├── router.py          # intent classification
│   └── main.py            # orchestration graph + CLI
├── examples/
│   └── sample_questions.md
└── tests/
    └── test_sql_guard.py
```

## Getting started

**1. Clone and set up a virtual environment**

```bash
git clone <your-repo-url>
cd ola-ai-data-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**2. Add your API key**

```bash
cp .env.example .env
# edit .env and put your OPENAI_API_KEY in it
```

**3. Start Postgres and load the sample data**

```bash
docker compose up -d
python db/seed.py
```

**4. Ask questions**

```bash
python src/main.py
```

```
You: Which city generated the most revenue?
You: Show me the top 5 drivers by total trips
You: Profile the file data/bookings.csv and load it into a table called bookings_raw
```

More examples in [examples/sample_questions.md](examples/sample_questions.md).

## How the SQL Analyst works

1. **Schema first** – the agent fetches the live table/column list from Postgres, so
   the generated SQL is grounded in the real schema, not guessed.
2. **Generate** – an LLM writes one read-only `SELECT` query.
3. **Guard** – before anything runs, the query passes a safety check
   (`db_utils.is_safe_select`) that rejects writes, DDL and multi-statements.
4. **Execute** – the query runs; results come back as rows.
5. **Judge** – a second LLM call scores whether the result actually answers the
   question. If not, its feedback goes back to step 2 for a rewrite (max 2 retries).
6. **Answer** – the final answer is written in plain English with the SQL shown.

## Things I want to add next

- [ ] Streamlit chat UI on top of the CLI
- [ ] Query result caching for repeated questions
- [ ] Support for a local model (Ollama) so it runs without an API key
- [ ] More ETL tools — deduplication and basic data-quality checks

## Notes

- The SQL agent is deliberately **read-only**. Don't point it at a production
  database you care about — use a reporting replica.
- Sample data is fictional and generated for learning purposes.
