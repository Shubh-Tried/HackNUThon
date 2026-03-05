"""Alerts router."""

from fastapi import APIRouter, Query
from typing import Optional
from app.database.store import InverterStore

router = APIRouter(tags=["Alerts"])


@router.get("/alerts")
async def get_alerts(
    inverter_id: Optional[str] = Query(None, description="Filter by inverter ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
):
    """Get active alerts, optionally filtered by inverter or severity."""
    alerts = InverterStore.get_alerts(
        inverter_id=inverter_id.upper() if inverter_id else None
    )
    
    if severity:
        alerts = [a for a in alerts if a.severity.value == severity.lower()]
    
    return {
        "alerts": [a.model_dump() for a in alerts],
        "total": len(alerts)
    }
