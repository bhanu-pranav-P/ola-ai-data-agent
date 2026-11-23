"""Create the tables and load the sample CSVs into Postgres.

Run after `docker compose up -d`:
    python db/seed.py
"""

import os
import sys

import pandas as pd
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from config import settings  # noqa: E402

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> None:
    engine = create_engine(settings.database_url)

    schema_path = os.path.join(BASE_DIR, "db", "schema.sql")
    with engine.begin() as conn:
        conn.execute(text(open(schema_path).read()))
    print("Tables created.")

    # load order matters: bookings references customers and drivers
    for table in ["customers", "drivers", "bookings"]:
        csv_path = os.path.join(BASE_DIR, "data", f"{table}.csv")
        df = pd.read_csv(csv_path)
        df.to_sql(table, engine, if_exists="append", index=False)
        print(f"Loaded {len(df)} rows into {table}")

    print("Done. Database is ready:", settings.database_url.rsplit("@", 1)[-1])


if __name__ == "__main__":
    main()
