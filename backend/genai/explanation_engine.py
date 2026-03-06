import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Groq model setup
# ---------------------------------------------------------------------------
_client = None

try:
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        _client = Groq(api_key=api_key)
        print("[Explanation engine] Groq client configured. Using llama-3.3-70b-versatile.")
    else:
        print("[Explanation engine] WARNING: GROQ_API_KEY not set.")
except Exception as e:
    print(f"[Explanation engine] WARNING: Failed to configure Groq: {e}")


def generate_maintenance_ticket(data):

    if _client is None:
        return "Error: GROQ_API_KEY not set. Cannot generate explanation."

    features = "\n".join([f"- {f}" for f in data["top_features"]])

    system_prompt = (
        "You are an AI assistant helping operators in a solar power plant. "
        "Your job is to analyze risk factors and output a formal maintenance ticket."
    )

    prompt = f"""
Inverter ID: {data['inverter_id']}
Risk Score: {data['risk_score']}
Status: {data['status']}

Top contributing factors:
{features}

Tasks:
1. Explain why the inverter is at risk.
2. Identify the most likely issue.
3. Generate a maintenance ticket.

Rules:
- Use only the provided information.
- Do not invent measurements or values.

Return the result in exactly this format:

Maintenance Ticket
Inverter ID:
Priority:
Issue:
Explanation:
Recommended Action:
"""

    try:
        response = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            top_p=0.9,
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Error generating maintenance ticket: {str(e)}"