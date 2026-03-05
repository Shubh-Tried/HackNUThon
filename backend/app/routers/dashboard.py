"""Dashboard summary router."""

from fastapi import APIRouter
from app.database.store import InverterStore

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard-summary")
async def get_dashboard_summary():
    """Get aggregated plant dashboard statistics."""
    summary = InverterStore.get_dashboard_summary()
    
    # Add power output trend (hourly for last 24h)
    inverters = InverterStore.get_all_inverters()
    active_inverters = [i for i in inverters if i.telemetry.power_output > 0]
    
    # Per-block efficiency comparison (computed from actual telemetry)
    block_efficiency = {}
    for inv in inverters:
        block = inv.metadata.block
        if block not in block_efficiency:
            block_efficiency[block] = {"efficiencies": [], "powers": []}
        if inv.telemetry.efficiency > 0:
            block_efficiency[block]["efficiencies"].append(inv.telemetry.efficiency)
            block_efficiency[block]["powers"].append(inv.telemetry.power_output)
    
    block_comparison = []
    for block, data in sorted(block_efficiency.items()):
        avg_eff = sum(data["efficiencies"]) / max(1, len(data["efficiencies"]))
        total_pwr = sum(data["powers"]) / 1000  # kW
        block_comparison.append({
            "block": f"Block {block}",
            "efficiency": round(avg_eff, 1),
            "power_kw": round(total_pwr, 1),
            "inverter_count": len(data["efficiencies"])
        })
    
    return {
        "summary": summary.model_dump(),
        "inverter_count_by_block": _count_by_block(inverters),
        "block_comparison": block_comparison,
        "risk_inverters": [
            {
                "inverter_id": i.metadata.inverter_id,
                "location": i.metadata.location,
                "risk_score": i.risk_score,
                "risk_category": i.risk_category.value,
                "status": i.status.value
            }
            for i in inverters if i.risk_category.value != "no_risk"
        ]
    }


@router.get("/plant-metrics")
async def get_plant_metrics():
    """Get 7-day aggregated plant-wide time-series for charts.
    All values are computed from individual inverter telemetry data.
    """
    return InverterStore.get_plant_metrics()


def _count_by_block(inverters):
    blocks = {}
    for inv in inverters:
        block = inv.metadata.block
        if block not in blocks:
            blocks[block] = {"total": 0, "active": 0, "at_risk": 0}
        blocks[block]["total"] += 1
        if inv.status.value == "active":
            blocks[block]["active"] += 1
        if inv.risk_category.value != "no_risk":
            blocks[block]["at_risk"] += 1
    return blocks

