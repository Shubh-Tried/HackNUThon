"""Inverter data routers."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.database.store import InverterStore

router = APIRouter(tags=["Inverters"])


@router.get("/inverters")
async def list_inverters(
    block: Optional[str] = Query(None, description="Filter by block (A, B, C, D)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    risk_category: Optional[str] = Query(None, description="Filter by risk category"),
):
    """List all inverters with optional filters."""
    inverters = InverterStore.get_all_inverters()
    
    results = []
    for inv in inverters:
        if block and inv.metadata.block != block.upper():
            continue
        if status and inv.status.value != status.lower():
            continue
        if risk_category and inv.risk_category.value != risk_category.lower():
            continue
        
        results.append({
            "inverter_id": inv.metadata.inverter_id,
            "location": inv.metadata.location,
            "block": inv.metadata.block,
            "status": inv.status.value,
            "risk_score": inv.risk_score,
            "risk_category": inv.risk_category.value,
            "temperature": inv.telemetry.temperature,
            "power_output": inv.telemetry.power_output,
            "efficiency": inv.telemetry.efficiency,
            "last_update": inv.last_update,
        })
    
    return {"inverters": results, "total": len(results)}


@router.get("/inverters/{inverter_id}")
async def get_inverter(inverter_id: str):
    """Get detailed information for a specific inverter."""
    inv = InverterStore.get_inverter(inverter_id.upper())
    if inv is None:
        raise HTTPException(status_code=404, detail=f"Inverter {inverter_id} not found")
    
    return {
        "metadata": inv.metadata.model_dump(),
        "telemetry": inv.telemetry.model_dump(),
        "status": inv.status.value,
        "risk_score": inv.risk_score,
        "risk_category": inv.risk_category.value,
        "last_update": inv.last_update,
    }


@router.get("/inverters/{inverter_id}/metrics")
async def get_inverter_metrics(inverter_id: str):
    """Get time-series metrics for an inverter (7-day history)."""
    metrics = InverterStore.get_inverter_metrics(inverter_id.upper())
    if metrics is None:
        raise HTTPException(status_code=404, detail=f"Inverter {inverter_id} not found")
    
    # Convert TimeSeriesPoint objects to dicts
    return {
        key: [{"timestamp": p.timestamp, "value": p.value} for p in points]
        for key, points in metrics.items()
    }
