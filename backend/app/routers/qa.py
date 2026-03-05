"""Natural Language Q&A router."""

from fastapi import APIRouter
from app.schemas.requests import QARequest
from app.genai.qa_engine import answer_question

router = APIRouter(tags=["Q&A"])


@router.post("/qa")
async def qa(request: QARequest):
    """
    Answer a natural language question about inverter performance.
    Grounded in actual inverter data with hallucination guardrails.
    """
    result = await answer_question(request.question)
    return result
