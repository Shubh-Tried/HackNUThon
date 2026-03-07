"""
Supabase client helper using httpx + PostgREST.

Thin wrapper around the Supabase REST API.  Avoids the heavy `supabase` pip
package (which requires Visual C++ Build Tools on Windows).

Tables supported:
  - plants
  - inverters
  - inverter_latest_data
  - inverter_metrics
  - string_metrics

Environment variables (loaded from backend/.env):
  - SUPABASE_URL   e.g. https://abc123.supabase.co
  - SUPABASE_KEY   anon or service-role key
"""

import os
import time
import threading
import logging
from dotenv import load_dotenv
import httpx

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
load_dotenv(_env_path)

SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY must be set in backend/.env. "
        "Copy .env.example to .env and fill in your credentials."
    )

REST_URL = f"{SUPABASE_URL}/rest/v1"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

_client = httpx.Client(base_url=REST_URL, headers=HEADERS, timeout=15.0)

# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def fetch_all(table: str, params: dict | None = None) -> list[dict]:
    """SELECT * from a Supabase table.  Optional PostgREST query params."""
    resp = _client.get(f"/{table}", params=params or {})
    resp.raise_for_status()
    return resp.json()


def fetch_one(table: str, column: str, value) -> dict | None:
    """SELECT * … WHERE column = value  → first row or None."""
    params = {column: f"eq.{value}", "limit": "1"}
    resp = _client.get(f"/{table}", params=params)
    resp.raise_for_status()
    rows = resp.json()
    return rows[0] if rows else None


def upsert(table: str, rows: list[dict]) -> list[dict]:
    """INSERT … ON CONFLICT UPDATE (upsert) rows into a table."""
    headers = {**HEADERS, "Prefer": "resolution=merge-duplicates,return=representation"}
    resp = _client.post(f"/{table}", json=rows, headers=headers)
    resp.raise_for_status()
SIMULATION_TIMESTAMPS = []
SIMULATION_INDEX = 0

def init_simulation():
    global SIMULATION_TIMESTAMPS, SIMULATION_INDEX
    rows = fetch_all("inverter_latest_data", {"select": "timestamp", "order": "timestamp.asc", "limit": "10000"})
    unique = sorted(list(set(r["timestamp"] for r in rows if r.get("timestamp"))))
    SIMULATION_TIMESTAMPS = unique
    SIMULATION_INDEX = 0

def advance_simulation():
    global SIMULATION_TIMESTAMPS, SIMULATION_INDEX
    if SIMULATION_TIMESTAMPS and SIMULATION_INDEX < len(SIMULATION_TIMESTAMPS) - 1:
        SIMULATION_INDEX += 1

def delete_old_records(table: str, days: int = 7) -> None:
    """DELETE records older than `days` relative to simulation time."""
    from datetime import datetime, timedelta
    global SIMULATION_TIMESTAMPS, SIMULATION_INDEX
    if not SIMULATION_TIMESTAMPS: return
    
    current_time_str = SIMULATION_TIMESTAMPS[SIMULATION_INDEX].replace('Z', '+00:00')
    try:
        current_time = datetime.fromisoformat(current_time_str).replace(tzinfo=None)
    except:
        current_time = datetime.utcnow()
        
    cutoff = current_time - timedelta(days=days)
    cutoff_iso = cutoff.isoformat()
    
    # Using PostgREST lt (less than) operator
    params = {"timestamp": f"lt.{cutoff_iso}"}
    try:
        resp = _client.delete(f"/{table}", params=params)
        resp.raise_for_status()
        log.info(f"Deleted records older than {days} days relative to sim time from {table}")
    except Exception as exc:
        log.error(f"Failed to delete old records from {table}: {exc}")


# ---------------------------------------------------------------------------
# Domain-specific helpers  (real schema)
# ---------------------------------------------------------------------------

def fetch_plants() -> list[dict]:
    """All rows from the `plants` table."""
    return fetch_all("plants", {"order": "plant_id.asc"})


def fetch_inverters() -> list[dict]:
    """All inverter registrations (joined with nothing — raw table)."""
    return fetch_all("inverters", {"order": "inverter_id.asc"})


def fetch_latest_data() -> list[dict]:
    """Most recent snapshot of every inverter up to current simulation time."""
    global SIMULATION_TIMESTAMPS, SIMULATION_INDEX
    if not SIMULATION_TIMESTAMPS:
        init_simulation()
        
    if not SIMULATION_TIMESTAMPS:
        return []
        
    cutoff_time = SIMULATION_TIMESTAMPS[SIMULATION_INDEX]
    rows = fetch_all("inverter_latest_data", {
        "timestamp": f"lte.{cutoff_time}",
        "order": "timestamp.desc",
        "limit": "15000"
    })
    
    from ml.predict import predict_inverter
    unique = {}
    for r in rows:
        code = r.get("inverter_code")
        if code and code not in unique:
            # Inline the ML prediction calculation exactly as requested
            try:
                res = predict_inverter({
                    "inverter_id": r.get("id"),
                    "power": r.get("power", 0),
                    "pv_power": r.get("pv_power", 0),
                    "temperature": r.get("temperature", 0),
                    "frequency": r.get("frequency", 50.0),
                    "voltage_ab": r.get("voltage_ab", 230),
                    "voltage_bc": r.get("voltage_bc", 230),
                    "voltage_ca": r.get("voltage_ca", 230),
                    "power_factor": r.get("power_factor", 1.0),
                    "op_state": r.get("op_state", 1),
                })
                r["risk_score"] = res["risk_score"]
                r["status"] = res["status"]
            except:
                r["risk_score"] = 0.5
                r["status"] = "Unknown"
            unique[code] = r

    # Ensure all baseline inverters are present
    all_invs = fetch_all("inverters")
    for inv in all_invs:
        code = inv.get("inverter_code")
        if code and code not in unique:
            blank = {
                "id": inv.get("inverter_id", 0),
                "inverter_code": code,
                "plant_id": inv.get("plant_id", 1),
                "timestamp": cutoff_time,
                "power": 0.0,
                "pv_power": 0.0,
                "temperature": 25.0,
                "frequency": 50.0,
                "voltage_ab": 230.0,
                "voltage_bc": 230.0,
                "voltage_ca": 230.0,
                "power_factor": 1.0,
                "op_state": 0,
                "kwh_today": 0.0,
                "kwh_total": 0.0
            }
            try:
                res = predict_inverter(blank)
                blank["risk_score"] = res["risk_score"]
                blank["status"] = res["status"]
            except:
                blank["risk_score"] = 0.5
                blank["status"] = "Unknown"
            unique[code] = blank
            
    return sorted(unique.values(), key=lambda x: x.get("inverter_code", ""))


def fetch_metrics(inverter_code: str, limit: int = 100) -> list[dict]:
    """Recent time-series rows from `inverter_latest_data` for one inverter."""
    params = {
        "inverter_code": f"eq.{inverter_code}",
        "order": "timestamp.desc",
        "limit": str(limit),
    }
    global SIMULATION_TIMESTAMPS, SIMULATION_INDEX
    if SIMULATION_TIMESTAMPS:
        cutoff = SIMULATION_TIMESTAMPS[SIMULATION_INDEX]
        params["timestamp"] = f"lte.{cutoff}"
        
    return fetch_all("inverter_latest_data", params)


def fetch_string_metrics(inverter_id: int, limit: int = 50) -> list[dict]:
    """Recent string-level current readings for one inverter."""
    params = {
        "inverter_id": f"eq.{inverter_id}",
        "order": "timestamp.desc",
        "limit": str(limit),
    }
    global SIMULATION_TIMESTAMPS, SIMULATION_INDEX
    if SIMULATION_TIMESTAMPS:
        cutoff = SIMULATION_TIMESTAMPS[SIMULATION_INDEX]
        params["timestamp"] = f"lte.{cutoff}"
        
    return fetch_all("string_metrics", params)


# ---------------------------------------------------------------------------
# In-memory cache  (refreshed every 5 minutes by background thread)
# ---------------------------------------------------------------------------
_cache: dict = {
    "latest_data": [],
    "plants": [],
    "inverters": [],
    "last_refresh": 0.0,
}
_cache_lock = threading.Lock()

REFRESH_INTERVAL = 300  # seconds (5 minutes)

# Callbacks invoked after every successful cache refresh
_refresh_callbacks: list = []


def on_cache_refresh(callback):
    """Register a callback to be called after each successful cache refresh.

    Use this to keep downstream indices (e.g. the RAG engine) in sync
    with the latest Supabase data automatically.
    """
    _refresh_callbacks.append(callback)


def _refresh_cache():
    """Pull fresh data from Supabase and store in the module cache."""
    try:
        latest = fetch_latest_data()
        plants = fetch_plants()
        inverters = fetch_inverters()
        with _cache_lock:
            _cache["latest_data"] = latest
            _cache["plants"] = plants
            _cache["inverters"] = inverters
            _cache["last_refresh"] = time.time()
        log.info("Cache refreshed — %d latest rows, %d plants, %d inverters",
                 len(latest), len(plants), len(inverters))

        # Notify registered listeners (e.g. RAG engine)
        for cb in _refresh_callbacks:
            try:
                cb()
            except Exception as cb_exc:
                log.error("Refresh callback %s failed: %s", cb.__name__, cb_exc)

    except Exception as exc:
        log.error("Cache refresh failed: %s", exc)


def _background_loop():
    """Daemon thread that refreshes the cache every REFRESH_INTERVAL seconds."""
    from ml.predict import run_batch_predictions_and_log
    while True:
        advance_simulation()
        _refresh_cache()
        
        # ML Training / Prediction Logging
        with _cache_lock:
            latest = list(_cache["latest_data"])
        if latest:
            run_batch_predictions_and_log(latest)
            
        # Delete old data relative to simulation time
        delete_old_records("inverter_latest_data", days=7)
        
        time.sleep(REFRESH_INTERVAL)


# Start the daemon on import
_thread = threading.Thread(target=_background_loop, daemon=True, name="supabase-cache")
_thread.start()


def get_cached_latest() -> list[dict]:
    """Return the cached latest-data snapshot (fast, no network call)."""
    with _cache_lock:
        return list(_cache["latest_data"])


def get_cached_plants() -> list[dict]:
    with _cache_lock:
        return list(_cache["plants"])


def get_cached_inverters() -> list[dict]:
    with _cache_lock:
        return list(_cache["inverters"])


def get_cache_age() -> float:
    """Seconds since last successful refresh."""
    with _cache_lock:
        if _cache["last_refresh"] == 0:
            return float("inf")
        return time.time() - _cache["last_refresh"]
