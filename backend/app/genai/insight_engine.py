"""
GenAI Insight Engine for generating natural language risk explanations.
Uses OpenAI API with fallback to template-based generation for demo mode.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Feature display names for human-readable explanations
FEATURE_DISPLAY = {
    "dc_voltage": "DC input voltage",
    "ac_voltage": "AC output voltage",
    "current": "output current",
    "power_output": "power output",
    "temperature": "operating temperature",
    "efficiency": "conversion efficiency",
    "daily_generation": "daily energy generation",
    "inverter_runtime": "total runtime hours",
    "alarm_frequency": "alarm frequency",
    "dc_voltage_deviation": "DC voltage deviation from nominal",
    "efficiency_gap": "efficiency gap from baseline",
    "temp_excess": "temperature excess above threshold",
    "capacity_utilization": "capacity utilization ratio",
    "alarm_rate_normalized": "normalized alarm rate",
    "aging_factor": "equipment aging factor",
}


async def generate_insight(
    inverter_id: str,
    risk_score: float,
    risk_category: str,
    feature_contributions: list,
    telemetry: dict
) -> str:
    """
    Generate a natural language insight about inverter risk.
    Uses OpenAI if API key is available, otherwise uses template-based generation.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        return await _generate_with_llm(
            api_key, inverter_id, risk_score, risk_category,
            feature_contributions, telemetry
        )
    else:
        return _generate_template_insight(
            inverter_id, risk_score, risk_category,
            feature_contributions, telemetry
        )


async def _generate_with_llm(
    api_key: str,
    inverter_id: str,
    risk_score: float,
    risk_category: str,
    feature_contributions: list,
    telemetry: dict
) -> str:
    """Generate insight using OpenAI API."""
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=api_key)
        
        top_features = "\n".join([
            f"- {FEATURE_DISPLAY.get(f['feature'], f['feature'])}: importance={f['importance']:.4f}, direction={f['direction']}"
            for f in feature_contributions[:5]
        ])
        
        telemetry_summary = "\n".join([f"- {k}: {v}" for k, v in telemetry.items()])
        
        prompt = f"""You are a solar power plant operations advisor. Analyze the following inverter risk assessment and provide a concise operational insight.

Inverter: {inverter_id}
Risk Score: {risk_score:.2f} (0=safe, 1=critical)
Risk Category: {risk_category}

Top Contributing Factors:
{top_features}

Current Telemetry:
{telemetry_summary}

Provide a 3-part response:
1. RISK SUMMARY: One paragraph stating the risk level and timeframe (7-10 days)
2. ROOT CAUSES: Bullet points of likely causes based on the data
3. RECOMMENDED ACTIONS: Specific operational steps the maintenance team should take

Keep the response grounded in the actual data provided. Do not invent metrics not shown above."""
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        return _generate_template_insight(
            inverter_id, risk_score, risk_category,
            feature_contributions, telemetry
        )


def _generate_template_insight(
    inverter_id: str,
    risk_score: float,
    risk_category: str,
    feature_contributions: list,
    telemetry: dict
) -> str:
    """Generate a structured insight using templates when LLM is unavailable."""
    
    # Risk summary based on category
    if risk_category == "shutdown_risk":
        summary = f"Inverter {inverter_id} shows elevated shutdown risk (score: {risk_score:.2f}) within the next 7-10 days. Immediate attention is required to prevent unplanned downtime."
    elif risk_category == "degradation_risk":
        summary = f"Inverter {inverter_id} is experiencing performance degradation (risk score: {risk_score:.2f}). Output is trending below expected levels and may worsen within 7-10 days if not addressed."
    else:
        summary = f"Inverter {inverter_id} is operating within normal parameters (risk score: {risk_score:.2f}). No significant issues detected for the next 7-10 days."
    
    # Root causes from feature contributions
    causes = []
    for fc in feature_contributions[:3]:
        feature_name = FEATURE_DISPLAY.get(fc["feature"], fc["feature"])
        if fc["direction"] == "increasing_risk":
            causes.append(f"• {feature_name} is a significant risk factor (importance: {fc['importance']:.3f})")
    
    # Telemetry-specific causes
    temp = telemetry.get("temperature", 0)
    eff = telemetry.get("efficiency", 100)
    alarms = telemetry.get("alarm_frequency", 0)
    dc_v = telemetry.get("dc_voltage", 620)
    
    if temp > 65:
        causes.append(f"• Operating temperature of {temp}°C is critically high, indicating potential cooling system failure or environmental stress")
    elif temp > 55:
        causes.append(f"• Operating temperature of {temp}°C is above optimal range, suggesting thermal management issues")
    
    if eff < 90:
        causes.append(f"• Efficiency of {eff}% is significantly below the 97% baseline, indicating possible IGBT degradation or DC string issues")
    elif eff < 95:
        causes.append(f"• Efficiency of {eff}% is below expected baseline of 97%, suggesting gradual component wear or soiling")
    
    if alarms > 8:
        causes.append(f"• High alarm frequency ({alarms} in 24h) indicates recurring system faults requiring investigation")
    
    if dc_v < 500 and dc_v > 0:
        causes.append(f"• DC voltage of {dc_v}V is well below nominal 620V, possible string disconnection or panel degradation")
    
    # Recommendations
    recommendations = []
    if risk_category == "shutdown_risk":
        recommendations = [
            "• Schedule immediate physical inspection of the inverter and its cooling system",
            "• Check DC string connections and panel condition for voltage drops",
            "• Review alarm logs for recurring fault patterns",
            "• Prepare backup inverter or load redistribution plan",
            "• Consider preventive shutdown for controlled maintenance if risk continues to increase"
        ]
    elif risk_category == "degradation_risk":
        recommendations = [
            "• Schedule maintenance inspection within the next 3-5 days",
            "• Clean panels and check for dust accumulation or soiling",
            "• Inspect DC cable connections and junction boxes",
            "• Monitor temperature trends and verify cooling fan operation",
            "• Compare performance with adjacent inverters to isolate the issue"
        ]
    else:
        recommendations = [
            "• Continue standard monitoring schedule",
            "• No immediate maintenance action required"
        ]
    
    # Build final report
    report = f"**Risk Summary**\n{summary}\n\n"
    
    if causes:
        report += "**Possible Root Causes**\n" + "\n".join(causes) + "\n\n"
    
    report += "**Recommended Actions**\n" + "\n".join(recommendations)
    
    return report
