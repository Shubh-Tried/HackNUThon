"""
Request and response schemas for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from app.models.inverter import TelemetryData


class PredictRequest(BaseModel):
    inverter_id: Optional[str] = None
    telemetry: TelemetryData


class QARequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, description="Natural language question about inverter performance")


class QAResponse(BaseModel):
    question: str
    answer: str
    referenced_inverters: List[str]
    confidence: float


class ErrorResponse(BaseModel):
    detail: str
    status_code: int
