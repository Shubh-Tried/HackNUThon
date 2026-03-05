"""
Natural Language Q&A Engine with RAG-style grounding in actual inverter data.
Includes hallucination guardrails to prevent fabricated responses.
"""

import os
import logging
from typing import List
from app.database.store import InverterStore

logger = logging.getLogger(__name__)

# Known inverter IDs and blocks for guardrails
VALID_BLOCKS = {"A", "B", "C", "D"}


def _build_context() -> str:
    """Build a grounded context string from actual inverter data for RAG."""
    inverters = InverterStore.get_all_inverters()
    context_parts = []
    
    for inv in inverters:
        m = inv.metadata
        t = inv.telemetry
        context_parts.append(
            f"Inverter {m.inverter_id} | Location: {m.location} | Block: {m.block} | "
            f"Status: {inv.status.value} | Risk: {inv.risk_category.value} (score: {inv.risk_score:.2f}) | "
            f"Power: {t.power_output/1000:.1f}kW | Temp: {t.temperature}°C | "
            f"Efficiency: {t.efficiency}% | Alarms(24h): {t.alarm_frequency}"
        )
    
    return "\n".join(context_parts)


def _get_referenced_inverters(question: str) -> List[str]:
    """Extract inverter IDs mentioned in the question."""
    inverters = InverterStore.get_all_inverters()
    valid_ids = {inv.metadata.inverter_id for inv in inverters}
    
    referenced = []
    for inv_id in valid_ids:
        if inv_id.lower() in question.lower() or inv_id.replace("-", "").lower() in question.lower():
            referenced.append(inv_id)
    
    return referenced


def _validate_response(response: str, question: str) -> str:
    """
    Hallucination guardrail: verify that any inverter IDs mentioned in the
    response actually exist in the data store.
    """
    inverters = InverterStore.get_all_inverters()
    valid_ids = {inv.metadata.inverter_id for inv in inverters}
    
    # Check for fabricated inverter IDs in the response
    import re
    mentioned_ids = re.findall(r'INV-\d+', response)
    invalid_ids = [mid for mid in mentioned_ids if mid not in valid_ids]
    
    if invalid_ids:
        disclaimer = (
            f"\n\n⚠️ Note: The following inverter IDs mentioned are not in our "
            f"current dataset and have been flagged: {', '.join(invalid_ids)}. "
            f"Please verify with the actual plant registry."
        )
        response += disclaimer
    
    return response


async def answer_question(question: str) -> dict:
    """
    Answer a natural language question about inverter performance.
    Uses RAG approach: retrieves actual data, then generates answer.
    """
    context = _build_context()
    referenced = _get_referenced_inverters(question)
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if api_key:
        answer = await _answer_with_llm(api_key, question, context)
    else:
        answer = _answer_with_rules(question, context)
    
    # Apply hallucination guardrail
    answer = _validate_response(answer, question)
    
    # Determine confidence based on whether we found specific data
    confidence = 0.9 if referenced else 0.75
    
    # If using template-based, slightly lower confidence
    if not api_key:
        confidence -= 0.1
    
    return {
        "question": question,
        "answer": answer,
        "referenced_inverters": referenced,
        "confidence": round(confidence, 2)
    }


async def _answer_with_llm(api_key: str, question: str, context: str) -> str:
    """Answer using LLM with RAG context."""
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=api_key)
        
        prompt = f"""You are a solar plant operations assistant. Answer the operator's question using ONLY the provided inverter data. 
Do not invent data or reference inverters not listed. If the question cannot be answered from the data, say so.

CURRENT INVERTER DATA:
{context}

OPERATOR QUESTION: {question}

Provide a clear, concise, data-grounded answer. Reference specific inverter IDs and metrics from the data above."""
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.2
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        logger.error(f"LLM Q&A failed: {e}")
        return _answer_with_rules(question, context)


def _answer_with_rules(question: str, context: str) -> str:
    """Rule-based Q&A fallback using actual inverter data."""
    question_lower = question.lower()
    inverters = InverterStore.get_all_inverters()
    
    # "Which inverters have elevated risk"
    if any(kw in question_lower for kw in ["elevated risk", "at risk", "high risk", "risky"]):
        at_risk = [i for i in inverters if i.risk_category.value != "no_risk"]
        if at_risk:
            lines = []
            for inv in sorted(at_risk, key=lambda x: x.risk_score, reverse=True):
                lines.append(
                    f"• **{inv.metadata.inverter_id}** ({inv.metadata.location}) — "
                    f"Risk: {inv.risk_category.value} (score: {inv.risk_score:.2f}), "
                    f"Temp: {inv.telemetry.temperature}°C, Efficiency: {inv.telemetry.efficiency}%"
                )
            return "The following inverters currently have elevated risk:\n\n" + "\n".join(lines)
        return "No inverters currently show elevated risk. All systems operating normally."
    
    # "Why is INV-XXX at risk"
    if "why" in question_lower and "risk" in question_lower:
        refs = _get_referenced_inverters(question)
        if refs:
            inv = InverterStore.get_inverter(refs[0])
            if inv and inv.risk_category.value != "no_risk":
                reasons = []
                t = inv.telemetry
                if t.temperature > 60:
                    reasons.append(f"Operating temperature of {t.temperature}°C exceeds safe thresholds")
                if t.efficiency < 95:
                    reasons.append(f"Efficiency at {t.efficiency}% is below the 97% baseline")
                if t.alarm_frequency > 3:
                    reasons.append(f"High alarm frequency ({t.alarm_frequency} alarms in 24h)")
                if t.dc_voltage < 550 and t.dc_voltage > 0:
                    reasons.append(f"DC voltage at {t.dc_voltage}V is below nominal 620V")
                if t.power_output == 0:
                    reasons.append("Inverter is offline with zero power output")
                
                return (
                    f"**{inv.metadata.inverter_id}** ({inv.metadata.location}) has a "
                    f"{inv.risk_category.value} classification (score: {inv.risk_score:.2f}) "
                    f"due to:\n\n" + "\n".join(f"• {r}" for r in reasons)
                )
            elif inv:
                return f"{inv.metadata.inverter_id} is currently operating normally with no elevated risk (score: {inv.risk_score:.2f})."
        return "Please specify an inverter ID (e.g., INV-203) so I can provide specific risk details."
    
    # "Show underperforming inverters in Block X"
    if "block" in question_lower or "underperform" in question_lower:
        # Find which block
        target_block = None
        for block in VALID_BLOCKS:
            if f"block {block.lower()}" in question_lower:
                target_block = block
                break
        
        block_inverters = [
            i for i in inverters
            if (target_block is None or i.metadata.block == target_block) and i.telemetry.efficiency < 96
        ]
        
        if block_inverters:
            block_label = f"Block {target_block}" if target_block else "all blocks"
            lines = []
            for inv in block_inverters:
                lines.append(
                    f"• **{inv.metadata.inverter_id}** — Efficiency: {inv.telemetry.efficiency}%, "
                    f"Power: {inv.telemetry.power_output/1000:.1f}kW, Status: {inv.status.value}"
                )
            return f"Underperforming inverters in {block_label}:\n\n" + "\n".join(lines)
        
        block_label = f"Block {target_block}" if target_block else "the plant"
        return f"No underperforming inverters detected in {block_label}. All units operating above 96% efficiency."
    
    # "Status of INV-XXX" or general inverter question
    refs = _get_referenced_inverters(question)
    if refs:
        inv = InverterStore.get_inverter(refs[0])
        if inv:
            t = inv.telemetry
            return (
                f"**{inv.metadata.inverter_id}** — {inv.metadata.location}\n\n"
                f"• Status: {inv.status.value}\n"
                f"• Risk: {inv.risk_category.value} (score: {inv.risk_score:.2f})\n"
                f"• Power Output: {t.power_output/1000:.1f} kW\n"
                f"• Temperature: {t.temperature}°C\n"
                f"• Efficiency: {t.efficiency}%\n"
                f"• DC Voltage: {t.dc_voltage}V\n"
                f"• Alarms (24h): {t.alarm_frequency}\n"
                f"• Daily Generation: {t.daily_generation} kWh"
            )
    
    # Default summary
    summary = InverterStore.get_dashboard_summary()
    return (
        f"**Plant Overview**\n\n"
        f"• Total Inverters: {summary.total_inverters}\n"
        f"• Active: {summary.active_inverters}\n"
        f"• At Risk: {summary.inverters_at_risk}\n"
        f"• Average Efficiency: {summary.average_efficiency}%\n"
        f"• Total Power: {summary.total_power_output/1000:.1f} kW\n\n"
        f"Ask about specific inverters (e.g., 'Why is INV-203 at risk?') for detailed analysis."
    )
