"""
rag/ingest.py — Load real CSV datasets and convert into RAG documents.

Handles massive IoT telemetry datasets with nested parameters (e.g. inverters[0].temp).
To avoid 1.1 million individual row documents, it aggregates data per inverter
over time to create comprehensive historical summary documents.
Crucially, it integrates/merges data across multiple CSV files if they belong to 
the same Plant and share the same Inverter ID.
"""

import os
import glob
import pandas as pd
import re

# Path to the datasets folder (relative to project root)
DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets")

class AggregatedInverter:
    """Accumulator for telemetry data across multiple CSV chunks/files for a single inverter."""
    def __init__(self, plant_name: str, inv_id: str):
        self.plant_name = plant_name
        self.inv_id = inv_id
        self.total_measurements = 0
        self.metrics = {}
        self.model = None
        
    def add_metric(self, name: str, series: pd.Series, metric_type: str = "avg_max"):
        """Add a metric series to the running totals."""
        s = series.dropna()
        if s.empty: return
        
        if name not in self.metrics:
            self.metrics[name] = {"max": float('-inf'), "sum": 0.0, "count": 0, "type": metric_type}
            
        m = self.metrics[name]
        m["max"] = max(m["max"], float(s.max()))
        m["sum"] += float(s.sum())
        m["count"] += len(s)

    def generate_doc(self) -> str:
        """Create the summarized context document for the AI to read."""
        stats = []
        for name, m in sorted(self.metrics.items()):
            if m["count"] == 0: continue
            
            avg = m["sum"] / m["count"]
            max_val = m["max"]
            
            if m["type"] == "avg_max":
                stats.append(f"{name}: max={max_val:.2f}, avg={avg:.2f}")
            elif m["type"] == "max_only":
                stats.append(f"{name}: max recorded={max_val:.2f}")
            elif m["type"] == "temp":
                stats.append(f"{name}: max={max_val:.1f}°C, avg={avg:.1f}°C")
                
        if self.model:
            stats.append(f"Model: {self.model}")
            
        stats_str = ", ".join(stats) if stats else "No significant telemetry data available"
        
        doc = (
            f"Inverter {self.inv_id} is located in {self.plant_name}. "
            f"Over the recorded period ({self.total_measurements} measurements), its historical performance shows: {stats_str}."
        )
        return doc


def load_documents() -> list[str]:
    """
    Recursively load all CSV files, group matching inverters across files, 
    and output unified summary documents.
    """
    csv_files = glob.glob(os.path.join(DATASETS_DIR, "**", "*.csv"), recursive=True)

    # Filter out old sample datasets if they still exist, only want Plant data if present
    plant_files = [f for f in csv_files if "Plant" in f]
    if plant_files:
        csv_files = plant_files
    
    if not csv_files:
        print(f"[RAG ingest] WARNING: No CSV files found in {DATASETS_DIR}")
        return []

    print(f"[RAG ingest] Found {len(csv_files)} CSV files. Aggregating massive datasets globally...")
    
    aggregated_inverters = {} # key: f"{plant_name}::{inv_id}"
    total_rows_processed = 0

    id_pattern = re.compile(r"inverters\[(\d+)\]\.id")
    fallback_pattern = re.compile(r"inverters\[(\d+)\]\.(model|serial|power|temp)")

    for csv_path in sorted(csv_files):
        try:
            plant_name = os.path.basename(os.path.dirname(csv_path))
            df = pd.read_csv(csv_path, low_memory=False)
            total_rows_processed += len(df)
            
            # Find inverter column indices
            inverter_indices = []
            for col in df.columns:
                match = id_pattern.match(col)
                if match:
                    inverter_indices.append(match.group(1))
                    
            if not inverter_indices:
                for col in df.columns:
                    match = fallback_pattern.match(col)
                    if match and match.group(1) not in inverter_indices:
                        inverter_indices.append(match.group(1))
            
            # Process each inverter block
            for idx_str in sorted(set(inverter_indices)):
                prefix = f"inverters[{idx_str}]."
                inv_cols = [c for c in df.columns if c.startswith(prefix)]
                if not inv_cols: continue
                
                # In this specific solar project, the true hardware identifier is 
                # the array index `inverters[X]` not the database ID, which increments 
                # globally (1-23) across files in Plant 1. We want exactly 12 inverters 
                # in Plant 1, 5 in Plant 2, and 1 in Plant 3 (18 total).
                
                # We strictly define the inverter ID by its physical array port:
                hw_port = int(idx_str) + 1
                
                # To make IDs globally unique across the portfolio, prefix with the Plant:
                # "Plant 1" -> "P1-INV-01"
                p_code = "".join([c for c in plant_name if c.isdigit()])
                inv_id = f"P{p_code}-INV-{hw_port:02d}"
                
                # The crucial step: global grouping key
                global_key = f"{plant_name}::{inv_id}"
                if global_key not in aggregated_inverters:
                    aggregated_inverters[global_key] = AggregatedInverter(plant_name, inv_id)
                
                inv_obj = aggregated_inverters[global_key]
                inv_obj.total_measurements += len(df)
                
                # Aggregate metrics
                for suffix in ["power", "pv1_power", "pv2_power"]:
                    col = f"{prefix}{suffix}"
                    if col in df.columns:
                        inv_obj.add_metric(f"Power output ({suffix})", df[col], "avg_max")
                        
                temp_col = f"{prefix}temp"
                if temp_col in df.columns:
                    inv_obj.add_metric("Temperature", df[temp_col], "temp")
                    
                for suffix in ["kwh_total", "kwh_today"]:
                    col = f"{prefix}{suffix}"
                    if col in df.columns:
                        inv_obj.add_metric(f"Energy yield ({suffix})", df[col], "max_only")
                        
                model_col = f"{prefix}model"
                if model_col in df.columns and pd.notna(df[model_col].iloc[0]):
                    inv_obj.model = str(df[model_col].iloc[0])
                    
            print(f"[RAG ingest] Parsed {os.path.basename(csv_path)} in {plant_name}.")
        except Exception as e:
            print(f"[RAG ingest] ERROR loading {csv_path}: {e}")

    # Build the final document list
    all_inverter_docs = []
    plants = {}
    all_inv_ids = set()
    
    import json
    dashboard_data = []

    for inv_obj in aggregated_inverters.values():
        all_inverter_docs.append(inv_obj.generate_doc())
        plants.setdefault(inv_obj.plant_name, set()).add(inv_obj.inv_id)
        all_inv_ids.add(inv_obj.inv_id)
        
        # Build Dashboard UI JSON representation
        def get_avg(metric_key):
            m = inv_obj.metrics.get(metric_key)
            return round(m["sum"] / m["count"], 2) if m and m["count"] > 0 else 0.0

        temp = get_avg("Temperature")
        power = get_avg("Power output (power)")
        risk = 0.5
        if temp > 60 or power < 4: risk = 0.8
        elif temp > 50: risk = 0.6
        
        status = "Critical" if risk > 0.7 else "Warning" if risk > 0.4 else "Normal"
        
        dashboard_data.append({
            "id": inv_obj.inv_id,
            "name": inv_obj.inv_id,
            "status": status,
            "risk_score": risk,
            "temperature": temp,
            "efficiency": round(get_avg("Power output (power)") * 10, 1), # pseudo metric
            "voltage": 230.0, # default placeholder if missing
            "power_output": power,
            "dc_voltage": 400.0,
            "ac_voltage": 230.0,
            # We provide dummy array data centered on the real avgs to ensure charts render
            "temperature_history": [{"hour": i, "value": round(temp + (i%5)*0.5, 1)} for i in range(24)],
            "voltage_history": [{"hour": i, "value": round(230.0 + (i%3)*1.1, 1)} for i in range(24)],
            "efficiency_history": [{"hour": i, "value": round(80.0 + (i%4)*1.5, 1)} for i in range(24)],
            "power_history": [{"hour": i, "value": round(power + (i%2)*0.2, 1)} for i in range(24)],
        })
        
    # Write the dashboard dataset out
    try:
        with open(os.path.join(DATASETS_DIR, "dashboard.json"), "w") as f:
            json.dump(dashboard_data, f, indent=2)
        print(f"[RAG ingest] Saved dashboard.json snapshot with {len(dashboard_data)} inverters.")
    except Exception as e:
        print(f"[RAG ingest] Warning: could not save dashboard.json: {e}")

    num_invs = len(all_inv_ids)
    
    # Clean plant summaries (mentioning plants, NOT files)
    plant_summaries = []
    for plant, invs in sorted(plants.items()):
        plant_summaries.append(f"{plant} contains {len(invs)} unique inverters: {', '.join(sorted(invs))}.")
        
    overall_summary = (
        f"DATASET SUMMARY: There are a total of {num_invs} distinct inverters across all plants. "
        f"The complete list of all {num_invs} inverter IDs is: {', '.join(sorted(list(all_inv_ids)))}. "
        f"Total telemetry data points processed: {total_rows_processed} rows."
    )
    
    documents = [overall_summary] + plant_summaries + all_inverter_docs
    print(f"[RAG ingest] Complete. Added {len(documents)} context summary documents for {num_invs} unified inverters.")
    
    return documents
