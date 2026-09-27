import sqlite3
from pathlib import Path

DB_FILE = Path("backend/esg_audit.db")

AUDIT_METADATA_COLUMNS = {
    "factor_version": "TEXT",
    "source_url": "TEXT",
    "source_row_id": "TEXT",
    "category": "TEXT"
}


def init_db():
    conn = sqlite3.connect(DB_FILE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity TEXT,
            scope TEXT,
            quantity REAL,
            unit TEXT,
            factor REAL,
            factor_source TEXT,
            factor_year TEXT,
            factor_version TEXT,
            source_url TEXT,
            source_row_id TEXT,
            emissions_kg_co2e REAL,
            formula TEXT,
            status TEXT,
            source_file TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            category TEXT DEFAULT 'Environmental'
        )
    """)

    existing_columns = {
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(audit_log)"
        ).fetchall()
    }

    for column, definition in AUDIT_METADATA_COLUMNS.items():
        if column not in existing_columns:
            conn.execute(
                f"ALTER TABLE audit_log ADD COLUMN {column} {definition}"
            )
            if column == 'category':
                conn.execute("UPDATE audit_log SET category = 'Environmental' WHERE category IS NULL")

    conn.commit()
    conn.close()


def save_audit(record):

    conn = sqlite3.connect(DB_FILE)

    conn.execute("""
        INSERT INTO audit_log (
            activity,
            scope,
            quantity,
            unit,
            factor,
            factor_source,
            factor_year,
            factor_version,
            source_url,
            source_row_id,
            emissions_kg_co2e,
            formula,
            status,
            source_file,
            category
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record["activity"],
        record.get("scope", "N/A"),
        record.get("quantity", 0),
        record.get("unit", "N/A"),
        record.get("factor"),
        record.get("factor_source"),
        record.get("factor_year"),
        record.get("factor_version"),
        record.get("source_url"),
        record.get("source_row_id"),
        record.get("emissions_kg_co2e", 0),
        record.get("formula"),
        record.get("status"),
        record.get("source_file", "Manual Calculation"),
        record.get("category", "Environmental")
    ))

    conn.commit()
    conn.close()


def get_audit_logs():

    conn = sqlite3.connect(DB_FILE)

    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT *
        FROM audit_log
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return [dict(row) for row in rows]
