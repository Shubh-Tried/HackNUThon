"""
Pydantic models for solar inverter telemetry, metadata, alerts, and predictions.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class RiskCategory(str, Enum):
    NO_RISK = "no_risk"
    DEGRADATION_RISK = "degradation_risk"
    SHUTDOWN_RISK = "shutdown_risk"


class InverterStatus(str, Enum):
    ACTIVE = "active"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TelemetryData(BaseModel):
    dc_voltage: float = Field(..., ge=0, le=1500, description="DC input voltage in volts")
    ac_voltage: float = Field(..., ge=0, le=500, description="AC output voltage in volts")
    current: float = Field(..., ge=0, le=100, description="Output current in amps")
    power_output: float = Field(..., ge=0, le=100000, description="Power output in watts")
    temperature: float = Field(..., ge=-20, le=100, description="Inverter temperature in celsius")
    efficiency: float = Field(..., ge=0, le=100, description="Inverter efficiency percentage")
    daily_generation: float = Field(..., ge=0, description="Daily energy generation in kWh")
    inverter_runtime: float = Field(..., ge=0, description="Runtime in hours")
    alarm_frequency: int = Field(..., ge=0, description="Number of alarms in last 24h")


class InverterMetadata(BaseModel):
    inverter_id: str
    location: str
    block: str
    capacity_kw: float
    installation_date: str
    manufacturer: str
    model: str


class InverterRecord(BaseModel):
    metadata: InverterMetadata
    telemetry: TelemetryData
    status: InverterStatus
    risk_score: float = Field(0.0, ge=0, le=1)
    risk_category: RiskCategory = RiskCategory.NO_RISK
    last_update: str


class AlertRecord(BaseModel):
    alert_id: str
    inverter_id: str
    alert_type: str
    severity: AlertSeverity
    timestamp: str
    message: str


class FeatureContribution(BaseModel):
    feature: str
    importance: float
    direction: str  # "positive" or "negative" impact on risk


class PredictionResult(BaseModel):
    inverter_id: Optional[str] = None
    risk_score: float
    risk_category: RiskCategory
    top_feature_contributions: List[FeatureContribution]
    genai_summary: str


class DashboardSummary(BaseModel):
    total_inverters: int
    active_inverters: int
    inverters_at_risk: int
    average_efficiency: float
    total_power_output: float
    total_daily_generation: float
    total_capacity_kw: float
    capacity_utilization: float
    risk_distribution: dict


class TimeSeriesPoint(BaseModel):
    timestamp: str
    value: float
