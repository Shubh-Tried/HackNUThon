"""
In-memory data store with realistic solar inverter telemetry data.
All values based on real-world inverter operating ranges:
- DC voltage: 300-800V (string voltage for commercial inverters)
- AC voltage: 220-240V (grid-tied output)  
- Current: 5-40A per string
- Temperature: 25-75°C (operating range)
- Efficiency: 93-98.5% (typical for commercial inverters)
"""

from datetime import datetime, timedelta
from app.models.inverter import (
    InverterMetadata, TelemetryData, InverterRecord,
    InverterStatus, RiskCategory, AlertRecord, AlertSeverity,
    TimeSeriesPoint
)
import math


def _generate_inverters():
    """Generate realistic inverter fleet data for a solar plant."""
    inverters = []
    
    configs = [
        # Block A - Healthy inverters
        {"id": "INV-101", "block": "A", "location": "Block A - Row 1", "cap": 50.0, "status": InverterStatus.ACTIVE,
         "risk": 0.08, "risk_cat": RiskCategory.NO_RISK,
         "tel": {"dc_voltage": 620.5, "ac_voltage": 236.2, "current": 28.4, "power_output": 42150.0,
                 "temperature": 42.3, "efficiency": 97.2, "daily_generation": 285.6, "inverter_runtime": 18720.0, "alarm_frequency": 0}},
        {"id": "INV-102", "block": "A", "location": "Block A - Row 2", "cap": 50.0, "status": InverterStatus.ACTIVE,
         "risk": 0.05, "risk_cat": RiskCategory.NO_RISK,
         "tel": {"dc_voltage": 615.8, "ac_voltage": 235.9, "current": 27.9, "power_output": 41800.0,
                 "temperature": 40.1, "efficiency": 97.5, "daily_generation": 280.2, "inverter_runtime": 18720.0, "alarm_frequency": 0}},
        {"id": "INV-103", "block": "A", "location": "Block A - Row 3", "cap": 50.0, "status": InverterStatus.ACTIVE,
         "risk": 0.12, "risk_cat": RiskCategory.NO_RISK,
         "tel": {"dc_voltage": 608.2, "ac_voltage": 234.8, "current": 26.8, "power_output": 40200.0,
                 "temperature": 44.7, "efficiency": 96.8, "daily_generation": 272.4, "inverter_runtime": 17550.0, "alarm_frequency": 1}},
        
        # Block B - Mixed health
        {"id": "INV-201", "block": "B", "location": "Block B - Row 1", "cap": 50.0, "status": InverterStatus.WARNING,
         "risk": 0.62, "risk_cat": RiskCategory.DEGRADATION_RISK,
         "tel": {"dc_voltage": 548.3, "ac_voltage": 232.1, "current": 22.4, "power_output": 33600.0,
                 "temperature": 58.9, "efficiency": 93.2, "daily_generation": 198.5, "inverter_runtime": 22100.0, "alarm_frequency": 5}},
        {"id": "INV-202", "block": "B", "location": "Block B - Row 2", "cap": 50.0, "status": InverterStatus.ACTIVE,
         "risk": 0.15, "risk_cat": RiskCategory.NO_RISK,
         "tel": {"dc_voltage": 612.0, "ac_voltage": 235.5, "current": 27.2, "power_output": 40900.0,
                 "temperature": 41.5, "efficiency": 97.0, "daily_generation": 275.0, "inverter_runtime": 16800.0, "alarm_frequency": 0}},
        {"id": "INV-203", "block": "B", "location": "Block B - Row 3", "cap": 50.0, "status": InverterStatus.CRITICAL,
         "risk": 0.89, "risk_cat": RiskCategory.SHUTDOWN_RISK,
         "tel": {"dc_voltage": 485.2, "ac_voltage": 228.4, "current": 18.1, "power_output": 27150.0,
                 "temperature": 72.4, "efficiency": 88.5, "daily_generation": 145.2, "inverter_runtime": 25400.0, "alarm_frequency": 12}},
        {"id": "INV-204", "block": "B", "location": "Block B - Row 4", "cap": 50.0, "status": InverterStatus.WARNING,
         "risk": 0.74, "risk_cat": RiskCategory.SHUTDOWN_RISK,
         "tel": {"dc_voltage": 520.1, "ac_voltage": 230.5, "current": 20.5, "power_output": 30750.0,
                 "temperature": 65.8, "efficiency": 91.2, "daily_generation": 172.3, "inverter_runtime": 24200.0, "alarm_frequency": 8}},
        
        # Block C - Mostly healthy
        {"id": "INV-301", "block": "C", "location": "Block C - Row 1", "cap": 60.0, "status": InverterStatus.ACTIVE,
         "risk": 0.06, "risk_cat": RiskCategory.NO_RISK,
         "tel": {"dc_voltage": 635.4, "ac_voltage": 237.1, "current": 32.5, "power_output": 52200.0,
                 "temperature": 39.8, "efficiency": 97.8, "daily_generation": 348.0, "inverter_runtime": 15200.0, "alarm_frequency": 0}},
        {"id": "INV-302", "block": "C", "location": "Block C - Row 2", "cap": 60.0, "status": InverterStatus.ACTIVE,
         "risk": 0.11, "risk_cat": RiskCategory.NO_RISK,
         "tel": {"dc_voltage": 628.7, "ac_voltage": 236.5, "current": 31.8, "power_output": 51000.0,
                 "temperature": 43.2, "efficiency": 97.1, "daily_generation": 340.5, "inverter_runtime": 15200.0, "alarm_frequency": 0}},
        {"id": "INV-303", "block": "C", "location": "Block C - Row 3", "cap": 60.0, "status": InverterStatus.WARNING,
         "risk": 0.48, "risk_cat": RiskCategory.DEGRADATION_RISK,
         "tel": {"dc_voltage": 572.3, "ac_voltage": 233.2, "current": 25.1, "power_output": 38600.0,
                 "temperature": 54.6, "efficiency": 94.5, "daily_generation": 245.8, "inverter_runtime": 21800.0, "alarm_frequency": 3}},
        
        # Block D
        {"id": "INV-401", "block": "D", "location": "Block D - Row 1", "cap": 50.0, "status": InverterStatus.ACTIVE,
         "risk": 0.09, "risk_cat": RiskCategory.NO_RISK,
         "tel": {"dc_voltage": 618.9, "ac_voltage": 236.0, "current": 28.1, "power_output": 42000.0,
                 "temperature": 41.0, "efficiency": 97.3, "daily_generation": 282.0, "inverter_runtime": 19000.0, "alarm_frequency": 0}},
        {"id": "INV-402", "block": "D", "location": "Block D - Row 2", "cap": 50.0, "status": InverterStatus.OFFLINE,
         "risk": 0.95, "risk_cat": RiskCategory.SHUTDOWN_RISK,
         "tel": {"dc_voltage": 0.0, "ac_voltage": 0.0, "current": 0.0, "power_output": 0.0,
                 "temperature": 28.5, "efficiency": 0.0, "daily_generation": 0.0, "inverter_runtime": 26100.0, "alarm_frequency": 18}},
    ]
    
    now = datetime.utcnow()
    for cfg in configs:
        rec = InverterRecord(
            metadata=InverterMetadata(
                inverter_id=cfg["id"],
                location=cfg["location"],
                block=cfg["block"],
                capacity_kw=cfg["cap"],
                installation_date=(now - timedelta(days=int(cfg["tel"]["inverter_runtime"] / 12))).strftime("%Y-%m-%d"),
                manufacturer="SMA Solar" if cfg["block"] in ("A", "C") else "Huawei",
                model="Sunny Tripower 50" if cfg["cap"] == 50 else "SUN2000-60KTL"
            ),
            telemetry=TelemetryData(**cfg["tel"]),
            status=cfg["status"],
            risk_score=cfg["risk"],
            risk_category=cfg["risk_cat"],
            last_update=now.strftime("%Y-%m-%dT%H:%M:%SZ")
        )
        inverters.append(rec)
    
    return inverters


def _generate_alerts(inverters):
    """Generate alerts for at-risk inverters."""
    alerts = []
    now = datetime.utcnow()
    
    alert_configs = [
        {"inv": "INV-203", "type": "OVERTEMPERATURE", "sev": AlertSeverity.CRITICAL,
         "msg": "Inverter temperature 72.4°C exceeds critical threshold of 70°C. Immediate cooling system inspection required."},
        {"inv": "INV-203", "type": "EFFICIENCY_DROP", "sev": AlertSeverity.HIGH,
         "msg": "Efficiency dropped to 88.5%, below minimum threshold of 92%. DC string inspection recommended."},
        {"inv": "INV-203", "type": "HIGH_ALARM_RATE", "sev": AlertSeverity.HIGH,
         "msg": "12 alarms in last 24 hours. Pattern indicates potential IGBT module degradation."},
        {"inv": "INV-204", "type": "OVERTEMPERATURE", "sev": AlertSeverity.HIGH,
         "msg": "Inverter temperature 65.8°C approaching critical threshold. Cooling fan performance check advised."},
        {"inv": "INV-204", "type": "POWER_CURTAILMENT", "sev": AlertSeverity.MEDIUM,
         "msg": "Power output 30.75kW is 38.5% below rated capacity. DC voltage drop detected on strings 3-4."},
        {"inv": "INV-204", "type": "HIGH_ALARM_RATE", "sev": AlertSeverity.MEDIUM,
         "msg": "8 alarms in last 24 hours. Intermittent grid synchronization failures detected."},
        {"inv": "INV-201", "type": "EFFICIENCY_DROP", "sev": AlertSeverity.MEDIUM,
         "msg": "Efficiency at 93.2%, trending downward over past 5 days. Dust accumulation or panel soiling suspected."},
        {"inv": "INV-201", "type": "DC_VOLTAGE_LOW", "sev": AlertSeverity.MEDIUM,
         "msg": "DC input voltage 548.3V is 11.5% below nominal. Check string connections and panel condition."},
        {"inv": "INV-303", "type": "EFFICIENCY_DROP", "sev": AlertSeverity.LOW,
         "msg": "Efficiency at 94.5%, 2.8% below baseline. Minor degradation trend observed over 14 days."},
        {"inv": "INV-402", "type": "SHUTDOWN", "sev": AlertSeverity.CRITICAL,
         "msg": "Inverter offline. Communication lost. Last known state: ground fault detected on DC side."},
        {"inv": "INV-402", "type": "COMMUNICATION_LOSS", "sev": AlertSeverity.CRITICAL,
         "msg": "No telemetry data received for 6 hours. Physical inspection and restart procedure required."},
    ]
    
    for i, cfg in enumerate(alert_configs):
        alert = AlertRecord(
            alert_id=f"ALT-{1001 + i}",
            inverter_id=cfg["inv"],
            alert_type=cfg["type"],
            severity=cfg["sev"],
            timestamp=(now - timedelta(minutes=i * 35 + 10)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            message=cfg["msg"]
        )
        alerts.append(alert)
    
    return alerts


def _generate_time_series(inverter_id: str, telemetry: TelemetryData):
    """Generate 7-day time series data for charts, based on current telemetry readings."""
    now = datetime.utcnow()
    series = {
        "dc_voltage": [],
        "ac_voltage": [],
        "power_output": [],
        "temperature": [],
        "efficiency": []
    }
    
    base_values = {
        "dc_voltage": telemetry.dc_voltage,
        "ac_voltage": telemetry.ac_voltage,
        "power_output": telemetry.power_output,
        "temperature": telemetry.temperature,
        "efficiency": telemetry.efficiency,
    }
    
    for i in range(168):  # 7 days * 24 hours
        ts = (now - timedelta(hours=167 - i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        hour_of_day = (now - timedelta(hours=167 - i)).hour
        
        # Solar generation curve: peaks at midday, zero at night
        solar_factor = max(0, math.sin(math.pi * (hour_of_day - 6) / 12)) if 6 <= hour_of_day <= 18 else 0
        
        # Gradual degradation trend for at-risk inverters
        day_index = i / 24
        degradation = 1.0 - (day_index * 0.005) if base_values["efficiency"] < 94 else 1.0
        
        for key, base in base_values.items():
            if key == "temperature":
                # Temperature follows ambient + load heating
                val = 25 + (base - 25) * solar_factor * degradation + (day_index * 0.3 if degradation < 1 else 0)
            elif key in ("dc_voltage", "ac_voltage"):
                val = base * (0.3 + 0.7 * solar_factor) * degradation if solar_factor > 0 else 0
            elif key == "power_output":
                val = base * solar_factor * degradation
            elif key == "efficiency":
                val = base * degradation if solar_factor > 0 else 0
            else:
                val = base * solar_factor
            
            series[key].append(TimeSeriesPoint(timestamp=ts, value=round(val, 2)))
    
    return series


# Initialize the data store
_inverters = _generate_inverters()
_alerts = _generate_alerts(_inverters)


class InverterStore:
    """In-memory data store for inverter data."""
    
    @staticmethod
    def get_all_inverters():
        return _inverters
    
    @staticmethod
    def get_inverter(inverter_id: str):
        for inv in _inverters:
            if inv.metadata.inverter_id == inverter_id:
                return inv
        return None
    
    @staticmethod
    def get_inverter_metrics(inverter_id: str):
        inv = InverterStore.get_inverter(inverter_id)
        if inv is None:
            return None
        return _generate_time_series(inverter_id, inv.telemetry)
    
    @staticmethod
    def get_alerts(inverter_id: str = None):
        if inverter_id:
            return [a for a in _alerts if a.inverter_id == inverter_id]
        return _alerts
    
    @staticmethod
    def get_plant_metrics():
        """
        Aggregate per-inverter time-series into plant-wide hourly metrics.
        - Power: sum of all inverter power outputs
        - Efficiency: weighted average (by power) across active inverters
        - Temperature: average across all inverters
        All values computed from actual inverter telemetry data.
        """
        # Get metrics for every inverter
        all_series = {}
        for inv in _inverters:
            series = _generate_time_series(inv.metadata.inverter_id, inv.telemetry)
            all_series[inv.metadata.inverter_id] = series
        
        num_hours = 168  # 7 days
        plant_power = []
        plant_efficiency = []
        plant_temperature = []
        
        for h in range(num_hours):
            ts = None
            total_power = 0
            weighted_eff_sum = 0
            total_weight = 0
            temp_sum = 0
            temp_count = 0
            
            for inv_id, series in all_series.items():
                pw = series["power_output"][h].value
                ef = series["efficiency"][h].value
                tp = series["temperature"][h].value
                ts = series["power_output"][h].timestamp
                
                total_power += pw
                if pw > 0 and ef > 0:
                    weighted_eff_sum += ef * pw
                    total_weight += pw
                if tp > 0:
                    temp_sum += tp
                    temp_count += 1
            
            avg_eff = round(weighted_eff_sum / total_weight, 1) if total_weight > 0 else 0
            avg_temp = round(temp_sum / max(1, temp_count), 1)
            
            plant_power.append({"timestamp": ts, "value": round(total_power / 1000, 1)})  # kW
            plant_efficiency.append({"timestamp": ts, "value": avg_eff})
            plant_temperature.append({"timestamp": ts, "value": avg_temp})
        
        return {
            "power_kw": plant_power,
            "efficiency": plant_efficiency,
            "temperature": plant_temperature,
        }
    
    @staticmethod
    def get_dashboard_summary():
        from app.models.inverter import DashboardSummary
        total = len(_inverters)
        active = sum(1 for i in _inverters if i.status == InverterStatus.ACTIVE)
        at_risk = sum(1 for i in _inverters if i.risk_category != RiskCategory.NO_RISK)
        
        # Compute average efficiency ONLY from inverters that are producing (eff > 0)
        producing = [i for i in _inverters if i.telemetry.efficiency > 0]
        avg_eff = sum(i.telemetry.efficiency for i in producing) / max(1, len(producing))
        
        # Sum actual power output and daily generation from all inverters
        total_power = sum(i.telemetry.power_output for i in _inverters)
        total_daily_gen = sum(i.telemetry.daily_generation for i in _inverters)
        
        # Total installed capacity from metadata
        total_capacity = sum(i.metadata.capacity_kw for i in _inverters)
        
        # Capacity utilization = actual output / rated capacity * 100
        capacity_util = (total_power / 1000 / total_capacity * 100) if total_capacity > 0 else 0
        
        risk_dist = {
            "no_risk": sum(1 for i in _inverters if i.risk_category == RiskCategory.NO_RISK),
            "degradation_risk": sum(1 for i in _inverters if i.risk_category == RiskCategory.DEGRADATION_RISK),
            "shutdown_risk": sum(1 for i in _inverters if i.risk_category == RiskCategory.SHUTDOWN_RISK),
        }
        
        return DashboardSummary(
            total_inverters=total,
            active_inverters=active,
            inverters_at_risk=at_risk,
            average_efficiency=round(avg_eff, 1),
            total_power_output=total_power,
            total_daily_generation=round(total_daily_gen, 1),
            total_capacity_kw=total_capacity,
            capacity_utilization=round(capacity_util, 1),
            risk_distribution=risk_dist
        )
