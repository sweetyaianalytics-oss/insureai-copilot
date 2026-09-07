"""Load the local CSV files into a SQLite database."""

import csv
from pathlib import Path
import sqlite3


def quote_identifier(name):
    """Safely quote a table or column name for SQLite."""
    return '"' + name.replace('"', '""') + '"'


def setup_database():
    # Resolve paths from this script, regardless of the working directory.
    data_dir = Path(__file__).resolve().parent.parent / "data"
    csv_data = {}

    # Read and validate every CSV before changing any database tables.
    for table_name in ("members", "policies", "claims"):
        with (data_dir / f"{table_name}.csv").open(
            newline="", encoding="utf-8-sig"
        ) as csv_file:
            reader = csv.reader(csv_file)
            columns = next(reader, [])
            if not columns or any(not column.strip() for column in columns):
                raise ValueError(f"{table_name}.csv needs nonempty column names.")
            if len({column.lower() for column in columns}) != len(columns):
                raise ValueError(f"{table_name}.csv has duplicate column names.")
            rows = list(reader)
            if any(len(row) != len(columns) for row in rows):
                raise ValueError(f"{table_name}.csv has a row with missing or extra columns.")
            csv_data[table_name] = (columns, rows)

    connection = sqlite3.connect(data_dir / "insureai.db")
    try:
        # One explicit transaction makes table replacement safe: any error
        # rolls back all changes and preserves previously loaded tables.
        with connection:
            connection.execute("BEGIN")
            for table_name, (columns, rows) in csv_data.items():
                table = quote_identifier(table_name)
                # TEXT preserves the original CSV values, including codes.
                column_definitions = ", ".join(
                    f"{quote_identifier(column)} TEXT" for column in columns
                )
                connection.execute(f"DROP TABLE IF EXISTS {table}")
                connection.execute(f"CREATE TABLE {table} ({column_definitions})")

                # Placeholders insert values safely without building SQL from data.
                placeholders = ", ".join("?" for _ in columns)
                connection.executemany(
                    f"INSERT INTO {table} VALUES ({placeholders})", rows
                )

        for table_name in csv_data:
            count = connection.execute(
                f"SELECT COUNT(*) FROM {quote_identifier(table_name)}"
            ).fetchone()[0]
            print(f"{table_name}: {count} rows loaded")

        # Test that the requested claim can be retrieved with SQL.
        claim = connection.execute(
            "SELECT * FROM claims WHERE claim_id = ?", ("C003",)
        ).fetchone()
        print(f"Claim C003: {claim}")
    finally:
        connection.close()


if __name__ == "__main__":
    setup_database()
