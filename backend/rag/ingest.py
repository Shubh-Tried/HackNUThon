"""
rag/ingest.py — Load live data from Supabase and convert into RAG documents.

Pulls real-time inverter data from the Supabase database (via supabase_client.py)
and creates text documents suitable for the TF-IDF retriever. This replaces
the old CSV-based ingestion.
"""

import logging

log = logging.getLogger(__name__)


def load_documents_from_supabase() -> list[str]:
    """
    Fetch live inverter data from Supabase and convert each record
    into a natural-language document for RAG indexing.

    Returns:
        List of text documents describing each inverter and overall summary.
    """
    from database.supabase_client import (
        get_cached_latest,
        get_cached_plants,
        get_cached_inverters,
    )

    documents = []

    # --- Fetch data ---
    latest = get_cached_latest()
    plants = get_cached_plants()
    inverters_reg = get_cached_inverters()

    if not latest:
        log.warning("No inverter data in Supabase cache. RAG will have no context.")
        return ["No inverter data available in the database."]

    # --- Build a plant lookup ---
    plant_map = {}
    for p in plants:
        pid = p.get("plant_id") or p.get("id")
        pname = p.get("name") or p.get("plant_name") or f"Plant {pid}"
        if pid is not None:
            plant_map[pid] = pname

    # --- Per-inverter documents ---
    status_counts = {"Normal": 0, "Warning": 0, "Critical": 0}
    total_power = 0.0
    total_kwh_today = 0.0

    for inv in latest:
        inv_id = inv.get("inverter_code") or inv.get("id") or "Unknown"
        plant_id = inv.get("plant_id")
        plant_name = plant_map.get(plant_id, f"Plant {plant_id}" if plant_id else "Unknown Plant")

        power = inv.get("power") or inv.get("pv_power") or 0
        pv_power = inv.get("pv_power") or 0
        temp = inv.get("temperature") or inv.get("temp") or 0
        voltage_ab = inv.get("voltage_ab") or 0
        voltage_bc = inv.get("voltage_bc") or 0
        voltage_ca = inv.get("voltage_ca") or 0
        frequency = inv.get("frequency") or 0
        power_factor = inv.get("power_factor") or 0
        kwh_today = inv.get("kwh_today") or 0
        kwh_total = inv.get("kwh_total") or 0
        op_state = inv.get("op_state")

        # Determine status
        risk_factors = []
        risk = 0.2
        if temp and float(temp) > 70:
            risk += 0.35
            risk_factors.append(f"very high temperature ({temp}°C)")
        elif temp and float(temp) > 60:
            risk += 0.2
            risk_factors.append(f"high temperature ({temp}°C)")
        elif temp and float(temp) > 50:
            risk += 0.1
            risk_factors.append(f"elevated temperature ({temp}°C)")

        if power_factor and float(power_factor) < 0.85:
            risk += 0.15
            risk_factors.append(f"low power factor ({power_factor})")

        if pv_power and float(pv_power) < 1.0:
            risk += 0.1
            risk_factors.append("low PV power output")

        if frequency and (float(frequency) < 49.5 or float(frequency) > 50.5):
            risk += 0.1
            risk_factors.append(f"frequency deviation ({frequency} Hz)")

        risk = min(1.0, risk)
        if risk > 0.7:
            status = "Critical"
        elif risk > 0.4:
            status = "Warning"
        else:
            status = "Normal"

        status_counts[status] = status_counts.get(status, 0) + 1
        total_power += float(power or 0)
        total_kwh_today += float(kwh_today or 0)

        # Operating state text
        op_text = "running" if op_state == 1 else "stopped" if op_state == 0 else "unknown state"

        # Risk factors text
        if risk_factors:
            risk_text = f"Risk factors: {', '.join(risk_factors)}."
        else:
            risk_text = "All parameters are within normal range."

        doc = (
            f"Inverter {inv_id} is located in {plant_name}. "
            f"It is currently {op_text} with status: {status} (risk score: {risk:.0%}). "
            f"Current readings: power output = {power} kW, PV power = {pv_power} kW, "
            f"temperature = {temp}°C, "
            f"voltage AB = {voltage_ab} V, voltage BC = {voltage_bc} V, voltage CA = {voltage_ca} V, "
            f"frequency = {frequency} Hz, power factor = {power_factor}, "
            f"energy today = {kwh_today} kWh, total energy = {kwh_total} kWh. "
            f"{risk_text}"
        )
        documents.append(doc)

    # --- Plant summary documents ---
    plant_inverter_counts = {}
    for inv in latest:
        pid = inv.get("plant_id")
        pname = plant_map.get(pid, f"Plant {pid}" if pid else "Unknown")
        plant_inverter_counts.setdefault(pname, 0)
        plant_inverter_counts[pname] += 1

    for pname, count in plant_inverter_counts.items():
        plant_invs = [
            inv.get("inverter_code") or inv.get("id")
            for inv in latest
            if plant_map.get(inv.get("plant_id")) == pname
        ]
        doc = f"{pname} contains {count} inverters: {', '.join(str(x) for x in plant_invs)}."
        documents.append(doc)

    # --- Overall summary document ---
    total = len(latest)
    summary = (
        f"DATASET SUMMARY: There are {total} inverters in the database. "
        f"{status_counts.get('Normal', 0)} are Normal, "
        f"{status_counts.get('Warning', 0)} are in Warning state, "
        f"{status_counts.get('Critical', 0)} are Critical. "
        f"Total power output across all inverters: {total_power:.1f} kW. "
        f"Total energy generated today: {total_kwh_today:.1f} kWh. "
        f"Plants in the system: {', '.join(plant_map.values()) if plant_map else 'None'}."
    )
    documents.insert(0, summary)

    log.info("Loaded %d RAG documents from Supabase (%d inverters).", len(documents), total)
    print(f"[RAG ingest] Loaded {len(documents)} documents from Supabase ({total} inverters).")

    return documents


# Keep backward compat — old code calls load_documents()
def load_documents() -> list[str]:
    """Backward-compatible wrapper. Now fetches from Supabase instead of CSVs."""
    return load_documents_from_supabase()
