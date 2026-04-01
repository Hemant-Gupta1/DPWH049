"""
VisionGate AI — Database Utilities
====================================
Persistent SQLite storage for container inspection logs.
Designed for the DP World Hackathon Grand Finale.

Table: container_logs
Columns: id, timestamp, iso_code, damage_status, severity,
         recommended_action, location

Every container scanned by the Gate Inspector is logged here.
The ESG Dashboard and Yard Copilot both read from this DB.
"""

import sqlite3
import datetime
import os

# ─── Database path (co-located with the app) ─────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "visiongate.db")


def _get_connection() -> sqlite3.Connection:
    """Returns a new SQLite connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── Schema Initialisation ───────────────────────────────────────────────────

def init_db() -> None:
    """
    Creates the container_logs table if it doesn't already exist.
    Called once on app startup — idempotent.
    """
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS container_logs (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp           TEXT    NOT NULL,
            iso_code            TEXT,
            damage_status       TEXT    NOT NULL,
            severity            TEXT    NOT NULL,
            recommended_action  TEXT    NOT NULL,
            location            TEXT    NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# ─── Write Operations ────────────────────────────────────────────────────────

def insert_log(
    iso_code: str,
    damage_status: str,
    severity: str,
    recommended_action: str,
    location: str,
    timestamp: str | None = None,
) -> int:
    """
    Inserts a new container inspection record into the database.

    Parameters
    ----------
    iso_code : str
        ISO 6346 container code (or "N/A" if not readable).
    damage_status : str
        Overall damage status: CLEAR, MINOR_DAMAGE, WARNING, CRITICAL.
    severity : str
        Simplified severity: Low, Medium, High.
    recommended_action : str
        Routing action: VESSEL_LOAD, INSPECTION_HOLD, MAINTENANCE_YARD, QUARANTINE.
    location : str
        Terminal name selected in the sidebar.
    timestamp : str, optional
        ISO 8601 timestamp; defaults to current UTC time.

    Returns
    -------
    int
        Row ID of the newly inserted record.
    """
    if timestamp is None:
        timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    conn = _get_connection()
    cursor = conn.execute(
        """
        INSERT INTO container_logs
            (timestamp, iso_code, damage_status, severity, recommended_action, location)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (timestamp, iso_code, damage_status, severity, recommended_action, location),
    )
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


# ─── Read Operations ────────────────────────────────────────────────────────

def fetch_all_logs() -> list[dict]:
    """Returns all container_logs records as a list of dicts, newest first."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM container_logs ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_logs_today() -> list[dict]:
    """Returns today's container_logs records (UTC date), newest first."""
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM container_logs WHERE timestamp LIKE ? ORDER BY id DESC",
        (f"{today}%",),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_logs_by_location(location: str) -> list[dict]:
    """Returns records filtered by terminal location, newest first."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM container_logs WHERE location = ? ORDER BY id DESC",
        (location,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ─── Aggregation & Analytics ────────────────────────────────────────────────

def get_summary_stats(location: str | None = None) -> dict:
    """
    Returns aggregated statistics from the container_logs table.
    Used by the ESG Dashboard for dynamic metric calculation.

    ESG Logic:
        - Each container scanned saves 5 minutes of truck idling.
        - 1 hour of idling ≈ 10 kg CO₂.
        - idling_hours = total_processed × 5 / 60
        - co2_tons = idling_hours × 10 / 1000

    Parameters
    ----------
    location : str, optional
        If provided, filters stats to a specific terminal.

    Returns
    -------
    dict with keys:
        total_processed, cleared, damaged, high_severity,
        idling_hours_saved, co2_tons_saved
    """
    conn = _get_connection()

    base_query = "FROM container_logs"
    params: tuple = ()
    if location:
        base_query += " WHERE location = ?"
        params = (location,)

    total = conn.execute(f"SELECT COUNT(*) {base_query}", params).fetchone()[0]
    cleared = conn.execute(
        f"SELECT COUNT(*) {base_query}{' AND' if location else ' WHERE'} damage_status = 'CLEAR'",
        params,
    ).fetchone()[0]
    high_sev = conn.execute(
        f"SELECT COUNT(*) {base_query}{' AND' if location else ' WHERE'} severity = 'High'",
        params,
    ).fetchone()[0]
    conn.close()

    damaged = total - cleared
    idling_hours = round(total * 5 / 60, 2)
    co2_tons = round(idling_hours * 10 / 1000, 4)

    return {
        "total_processed": total,
        "cleared": cleared,
        "damaged": damaged,
        "high_severity": high_sev,
        "idling_hours_saved": idling_hours,
        "co2_tons_saved": co2_tons,
    }


def get_db_context_for_llm(location: str | None = None) -> str:
    """
    Builds a formatted text summary of the database for injection into
    the Yard Copilot's LLM system prompt. This enables the AI to answer
    questions like "summarise damaged containers today" with real data.
    """
    stats = get_summary_stats(location)
    logs_today = fetch_logs_today()
    all_logs = fetch_all_logs()

    lines = [
        "=== VisionGate AI Database Summary ===",
        f"Total containers ever processed: {stats['total_processed']}",
        f"Cleared for loading: {stats['cleared']}",
        f"Damaged (diverted): {stats['damaged']}",
        f"High-severity incidents: {stats['high_severity']}",
        f"Truck idling hours saved: {stats['idling_hours_saved']} hrs",
        f"CO₂ emissions prevented: {stats['co2_tons_saved']} Tons",
        "",
        f"=== Today's Inspections ({len(logs_today)} records) ===",
    ]

    for log in logs_today[:20]:  # Cap at 20 to avoid token bloat
        lines.append(
            f"  [{log['timestamp']}] ISO: {log['iso_code']} | "
            f"Status: {log['damage_status']} | Severity: {log['severity']} | "
            f"Action: {log['recommended_action']} | Location: {log['location']}"
        )

    if not logs_today:
        lines.append("  No inspections today yet.")

    if len(all_logs) > len(logs_today):
        lines.append(f"\n=== Historical Records (last 10 of {len(all_logs)} total) ===")
        for log in all_logs[:10]:
            lines.append(
                f"  [{log['timestamp']}] ISO: {log['iso_code']} | "
                f"Status: {log['damage_status']} | Severity: {log['severity']} | "
                f"Action: {log['recommended_action']} | Location: {log['location']}"
            )

    return "\n".join(lines)


# ─── Severity Mapping (Rich Gemini → Simplified DB Schema) ──────────────────

def map_severity(detections: list) -> str:
    """
    Maps the rich Gemini detection severities to the simplified DB schema.

    Rules:
        critical / severe → High
        moderate          → Medium
        minor             → Low
        No detections     → Low
    """
    if not detections:
        return "Low"

    severity_rank = {"critical": 3, "severe": 3, "moderate": 2, "minor": 1}
    worst = 0
    for det in detections:
        sev = det.get("severity", "minor").lower()
        worst = max(worst, severity_rank.get(sev, 1))

    return {3: "High", 2: "Medium", 1: "Low"}.get(worst, "Low")
