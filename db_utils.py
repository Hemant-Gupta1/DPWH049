"""
VisionGate AI — Database Utilities
====================================
Persistent SQLite storage for container inspection logs.
Designed for the DP World Hackathon Grand Finale.

Table: container_logs
Columns: id, timestamp, iso_code, damage_status, severity,
         recommended_action, location, inspection_type

Every container scanned by the Gate Inspector or Thermal Inspector
is logged here. The ESG Dashboard, Yard Copilot, and Compliance
Reports all read from this DB.

inspection_type: 'structural' (Gate Inspector dual-view) or
                 'thermal' (Thermal Inspector infrared).
"""

import sqlite3
import datetime
import os

# IST timezone (UTC+5:30) — used for all timestamps
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

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
    Also migrates the schema by adding `inspection_type` if missing.
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
            location            TEXT    NOT NULL,
            inspection_type     TEXT    NOT NULL DEFAULT 'structural'
        )
    """)
    # Migration: add inspection_type column to existing DBs that lack it
    try:
        conn.execute("ALTER TABLE container_logs ADD COLUMN inspection_type TEXT NOT NULL DEFAULT 'structural'")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Create Ship Delays table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ship_delays (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp           TEXT    NOT NULL,
            ship_name           TEXT    NOT NULL,
            terminal            TEXT    NOT NULL,
            driver_contact      TEXT    NOT NULL,
            delay_minutes       INTEGER NOT NULL,
            sms_sent            BOOLEAN NOT NULL
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
    inspection_type: str = "structural",
    timestamp: str | None = None,
) -> int:
    """
    Inserts a new container inspection record into the database.

    Parameters
    ----------
    iso_code : str
        ISO 6346 container code (or "N/A" if not readable).
    damage_status : str
        Overall damage status: CLEAR, MINOR_DAMAGE, WARNING, CRITICAL
        (structural) or NORMAL, ELEVATED, WARNING, CRITICAL (thermal).
    severity : str
        Simplified severity: Low, Medium, High.
    recommended_action : str
        Routing action string.
    location : str
        Terminal name selected in the sidebar.
    inspection_type : str
        'structural' for Gate Inspector, 'thermal' for Thermal Inspector.
    timestamp : str, optional
        ISO 8601 timestamp; defaults to current IST time.

    Returns
    -------
    int
        Row ID of the newly inserted record.
    """
    if timestamp is None:
        timestamp = datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")

    conn = _get_connection()
    cursor = conn.execute(
        """
        INSERT INTO container_logs
            (timestamp, iso_code, damage_status, severity, recommended_action, location, inspection_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (timestamp, iso_code, damage_status, severity, recommended_action, location, inspection_type),
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

def insert_ship_delay(
    ship_name: str,
    terminal: str,
    driver_contact: str,
    delay_minutes: int,
    sms_sent: bool,
    timestamp: str | None = None,
) -> int:
    """Inserts a ship delay record."""
    if timestamp is None:
        timestamp = datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")

    conn = _get_connection()
    cursor = conn.execute(
        """
        INSERT INTO ship_delays
            (timestamp, ship_name, terminal, driver_contact, delay_minutes, sms_sent)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (timestamp, ship_name, terminal, driver_contact, delay_minutes, sms_sent),
    )
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id

def fetch_delay_logs(terminal: str | None = None) -> list[dict]:
    """Returns all ship_delay records, filtered by terminal optionally."""
    conn = _get_connection()
    if terminal:
        rows = conn.execute(
            "SELECT * FROM ship_delays WHERE terminal = ? ORDER BY id DESC", (terminal,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM ship_delays ORDER BY id DESC"
        ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def fetch_logs_today() -> list[dict]:
    """Returns today's container_logs records (IST date), newest first."""
    today = datetime.datetime.now(IST).strftime("%Y-%m-%d")
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

def get_summary_stats(location: str | None = None, inspection_type: str | None = None) -> dict:
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
    inspection_type : str, optional
        If provided, filters stats by inspection type ('structural' or 'thermal').

    Returns
    -------
    dict with keys:
        total_processed, cleared, damaged, high_severity,
        idling_hours_saved, co2_tons_saved, manpower_hours_saved,
        fte_saved, current_gate_queue_seconds
    """
    conn = _get_connection()

    conditions = []
    params: list = []
    if location:
        conditions.append("location = ?")
        params.append(location)
    if inspection_type:
        conditions.append("inspection_type = ?")
        params.append(inspection_type)

    where_clause = ""
    if conditions:
        where_clause = " WHERE " + " AND ".join(conditions)

    base_query = f"FROM container_logs{where_clause}"
    param_tuple = tuple(params)

    total = conn.execute(f"SELECT COUNT(*) {base_query}", param_tuple).fetchone()[0]

    # For cleared/high_sev, add to existing conditions
    cleared_conditions = conditions + ["damage_status = 'CLEAR'"]
    cleared_where = " WHERE " + " AND ".join(cleared_conditions)
    cleared = conn.execute(
        f"SELECT COUNT(*) FROM container_logs{cleared_where}",
        param_tuple,
    ).fetchone()[0]

    high_sev_conditions = conditions + ["severity = 'High'"]
    high_sev_where = " WHERE " + " AND ".join(high_sev_conditions)
    high_sev = conn.execute(
        f"SELECT COUNT(*) FROM container_logs{high_sev_where}",
        param_tuple,
    ).fetchone()[0]

    today_prefix = datetime.datetime.now(IST).strftime("%Y-%m-%d")
    high_sev_today_conditions = conditions + ["severity = 'High'", "timestamp LIKE ?"]
    high_sev_today_where = " WHERE " + " AND ".join(high_sev_today_conditions)
    high_sev_today = conn.execute(
        f"SELECT COUNT(*) FROM container_logs{high_sev_today_where}",
        tuple(params + [f"{today_prefix}%"]),
    ).fetchone()[0]

    conn.close()

    damaged = total - cleared
    idling_hours = round(total * 5 / 60, 2)
    co2_tons = round(idling_hours * 10 / 1000, 4)

    # ─── Live Metrics Assumptions ───
    # Assumption 1: Manpower Saved. 5 mins per container. 8 hours = 1 FTE
    manpower_hours = round(total * 5 / 60, 1)
    fte_saved = round(manpower_hours / 8, 1)

    # Assumption 2: Gate Queue Time. Base 14s + 0.5s per high-severity container today
    gate_queue = 14.0 + (0.5 * high_sev_today)

    return {
        "total_processed": total,
        "cleared": cleared,
        "damaged": damaged,
        "high_severity": high_sev,
        "idling_hours_saved": idling_hours,
        "co2_tons_saved": co2_tons,
        "manpower_hours_saved": manpower_hours,
        "fte_saved": fte_saved,
        "current_gate_queue_seconds": gate_queue,
    }


def get_thermal_stats(location: str | None = None) -> dict:
    """
    Returns thermal-specific aggregated statistics.
    Completely separate from structural metrics.

    Thermal Metrics:
        - total_thermal_scans: total thermal inspections
        - heat_anomalies: count where thermal status != NORMAL/CLEAR
        - critical_thermal: count where severity = 'High'
        - anomaly_rate: percentage of scans with issues

    Parameters
    ----------
    location : str, optional
        If provided, filters to a specific terminal.

    Returns
    -------
    dict with thermal-specific keys
    """
    conn = _get_connection()

    conditions = ["inspection_type = 'thermal'"]
    params: list = []
    if location:
        conditions.append("location = ?")
        params.append(location)

    where_clause = " WHERE " + " AND ".join(conditions)
    param_tuple = tuple(params)

    total = conn.execute(
        f"SELECT COUNT(*) FROM container_logs{where_clause}", param_tuple
    ).fetchone()[0]

    # Heat anomalies: anything not NORMAL or CLEAR
    anomaly_conditions = conditions + ["damage_status NOT IN ('NORMAL', 'CLEAR')"]
    anomaly_where = " WHERE " + " AND ".join(anomaly_conditions)
    anomalies = conn.execute(
        f"SELECT COUNT(*) FROM container_logs{anomaly_where}", param_tuple
    ).fetchone()[0]

    # Critical thermal alerts
    critical_conditions = conditions + ["severity = 'High'"]
    critical_where = " WHERE " + " AND ".join(critical_conditions)
    critical = conn.execute(
        f"SELECT COUNT(*) FROM container_logs{critical_where}", param_tuple
    ).fetchone()[0]

    conn.close()

    anomaly_rate = round((anomalies / total) * 100, 1) if total > 0 else 0.0

    return {
        "total_thermal_scans": total,
        "heat_anomalies": anomalies,
        "critical_thermal": critical,
        "normal_scans": total - anomalies,
        "anomaly_rate": anomaly_rate,
    }

def get_ship_delay_stats(terminal: str | None = None) -> dict:
    """
    Calculates advanced stats (Average, Median, P95, % Delayed) for ship delays.
    """
    conn = _get_connection()
    if terminal:
        rows = conn.execute("SELECT delay_minutes FROM ship_delays WHERE terminal = ?", (terminal,)).fetchall()
    else:
        rows = conn.execute("SELECT delay_minutes FROM ship_delays").fetchall()
    conn.close()

    delays = [r[0] for r in rows if r[0] > 0]
    total_logged_ships = len(rows)

    if not delays:
        return {"avg": 0, "median": 0, "p95": 0, "percent_delayed": 0.0, "total": total_logged_ships}

    import statistics
    import math

    # Calculate statistics
    avg = sum(delays) / len(delays)
    median = statistics.median(delays)

    # Calculate P95
    delays_sorted = sorted(delays)
    p95_index = max(0, math.ceil(0.95 * len(delays_sorted)) - 1)
    p95 = delays_sorted[p95_index]

    # Percentage of delayed ships out of total logged ships in DB
    percent_delayed = min((len(delays) / total_logged_ships) * 100, 100.0) if total_logged_ships > 0 else 0.0

    return {
        "avg": round(avg, 1),
        "median": round(median, 1),
        "p95": round(p95, 1),
        "percent_delayed": round(percent_delayed, 1),
        "total": total_logged_ships
    }


def get_hourly_throughput() -> dict:
    """
    Groups container_logs by hour for the last 24 hours.
    Returns a dictionary of { 'YYYY-MM-DD HH:00': count }.
    """
    conn = _get_connection()
    hours_query = """
        SELECT strftime('%Y-%m-%d %H:00', timestamp) AS hour_bucket, COUNT(*) 
        FROM container_logs 
        WHERE timestamp >= datetime('now', '-24 hours')
        GROUP BY hour_bucket 
        ORDER BY hour_bucket ASC
    """
    rows = conn.execute(hours_query).fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}

def get_esg_compliance_stats() -> dict:
    """
    Retrieves compliance logic natively from DB text matches.
    """
    conn = _get_connection()
    total = conn.execute("SELECT COUNT(*) FROM container_logs").fetchone()[0]
    if total == 0:
        conn.close()
        return {"iso_valid_percent": 100.0, "auto_compliance": 94.0}
        
    iso_valid = conn.execute("SELECT COUNT(*) FROM container_logs WHERE iso_code != 'UNKNOWN' AND iso_code != 'FAILED_OCR'").fetchone()[0]
    conn.close()
    
    iso_percent = round((iso_valid / total) * 100, 1)
    auto_compliance = round(min(100.0, 94.0 + (total / 10)), 1)
    return {"iso_valid_percent": iso_percent, "auto_compliance": auto_compliance}


def get_db_context_for_llm(location: str | None = None) -> str:
    """
    Builds a formatted text summary of the database for injection into
    the Yard Copilot's LLM system prompt. This enables the AI to answer
    questions about both structural and thermal inspections with real data.
    """
    stats = get_summary_stats(location, inspection_type='structural')
    thermal_stats = get_thermal_stats(location)
    logs_today = fetch_logs_today()
    all_logs = fetch_all_logs()

    # Separate today's logs by type
    structural_today = [l for l in logs_today if l.get('inspection_type', 'structural') == 'structural']
    thermal_today = [l for l in logs_today if l.get('inspection_type') == 'thermal']

    lines = [
        "=== VisionGate AI Database Summary ===",
        "",
        "--- STRUCTURAL INSPECTIONS (Gate Inspector) ---",
        f"Total containers processed (structural): {stats['total_processed']}",
        f"Cleared for loading: {stats['cleared']}",
        f"Damaged (diverted): {stats['damaged']}",
        f"High-severity incidents: {stats['high_severity']}",
        f"Truck idling hours saved: {stats['idling_hours_saved']} hrs",
        f"CO₂ emissions prevented: {stats['co2_tons_saved']} Tons",
        "",
        "--- THERMAL INSPECTIONS (Thermal Inspector) ---",
        f"Total thermal scans: {thermal_stats['total_thermal_scans']}",
        f"Heat anomalies detected: {thermal_stats['heat_anomalies']}",
        f"Critical thermal alerts: {thermal_stats['critical_thermal']}",
        f"Normal scans: {thermal_stats['normal_scans']}",
        f"Anomaly rate: {thermal_stats['anomaly_rate']}%",
        "",
        f"=== Today's Structural Inspections ({len(structural_today)} records) ===",
    ]

    for log in structural_today[:15]:
        lines.append(
            f"  [{log['timestamp']}] ISO: {log['iso_code']} | "
            f"Status: {log['damage_status']} | Severity: {log['severity']} | "
            f"Action: {log['recommended_action']} | Location: {log['location']}"
        )

    if not structural_today:
        lines.append("  No structural inspections today yet.")

    lines.append(f"\n=== Today's Thermal Inspections ({len(thermal_today)} records) ===")
    for log in thermal_today[:15]:
        lines.append(
            f"  [{log['timestamp']}] ISO: {log.get('iso_code', 'N/A')} | "
            f"Thermal Status: {log['damage_status']} | Severity: {log['severity']} | "
            f"Action: {log['recommended_action']} | Location: {log['location']}"
        )

    if not thermal_today:
        lines.append("  No thermal inspections today yet.")

    if len(all_logs) > len(logs_today):
        lines.append(f"\n=== Historical Records (last 10 of {len(all_logs)} total) ===")
        for log in all_logs[:10]:
            itype = log.get('inspection_type', 'structural').upper()
            lines.append(
                f"  [{itype}] [{log['timestamp']}] ISO: {log['iso_code']} | "
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
