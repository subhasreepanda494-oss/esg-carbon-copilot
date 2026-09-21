import sqlite3
from pathlib import Path

DB_FILE = Path("backend/esg_audit.db")


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
            emissions_kg_co2e REAL,
            formula TEXT,
            status TEXT,
            source_file TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

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
            emissions_kg_co2e,
            formula,
            status,
            source_file
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        record["activity"],
        record["scope"],
        record["quantity"],
        record["unit"],
        record["factor"],
        record["factor_source"],
        record["factor_year"],
        record["emissions_kg_co2e"],
        record["formula"],
        record["status"],
        record.get("source_file", "Manual Calculation")
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