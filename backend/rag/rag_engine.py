"""
rag/rag_engine.py — RAG-powered question answering engine.

Loads inverter datasets at import time (once), builds the retriever index,
and provides rag_answer() to answer questions using retrieved context + Groq (LLaMA).
"""

import os
from dotenv import load_dotenv

from rag.ingest import load_documents
from rag.retriever import Retriever


# ---------------------------------------------------------------------------
# Initialise at import time (once, at server startup)
# ---------------------------------------------------------------------------
load_dotenv()

print("[RAG engine] Loading documents from datasets...")
_documents = load_documents()

print("[RAG engine] Building retriever index...")
_retriever = Retriever()
_retriever.build_index(_documents)

print(f"[RAG engine] Ready — {len(_documents)} documents indexed.")


# ---------------------------------------------------------------------------
# Groq model setup
# ---------------------------------------------------------------------------
_client = None

try:
    from groq import Groq

    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        _client = Groq(api_key=api_key)
        print("[RAG engine] Groq client configured. Using llama-3.3-70b-versatile.")
    else:
        print("[RAG engine] WARNING: GROQ_API_KEY not set.")
except Exception as e:
    print(f"[RAG engine] WARNING: Failed to configure Groq: {e}")


# Find the overall summary document (starts with "DATASET SUMMARY:")
_summary_doc = None
for doc in _documents:
    if doc.startswith("DATASET SUMMARY:"):
        _summary_doc = doc
        break


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def rag_answer(question: str) -> str:
    """
    Answer a question using RAG: retrieve relevant documents then
    send them as context to Groq.

    Args:
        question: The user's question about inverter data.

    Returns:
        Answer string from Groq, grounded in the retrieved context.
    """
    if not _documents:
        return "No inverter data available. Please add CSV files to the datasets/ folder."

    # Step 1: Retrieve relevant documents
    context_docs = _retriever.search(question, k=10)

    if not context_docs:
        # Fallback: provide a sample of all documents so Groq has some context
        context_docs = _documents[:10]

    # Always include the overall summary so Groq knows totals/counts
    if _summary_doc and _summary_doc not in context_docs:
        context_docs.insert(0, _summary_doc)

    context_text = "\n".join(f"- {doc}" for doc in context_docs)

    # Step 2: Build messages for Groq's Chat API
    system_prompt = (
        "You are a solar energy expert AI assistant. Answer the user's question using ONLY the inverter data provided below.\n\n"
        "INVERTER DATA (retrieved from datasets):\n"
        f"{context_text}\n\n"
        "RULES:\n"
        "- Answer using ONLY the provided data above.\n"
        "- Do NOT hallucinate or invent data that is not in the context.\n"
        "- If the answer cannot be determined from the provided data, say 'Insufficient data to answer this question.'\n"
        "- Be concise but thorough. Reference specific inverter IDs and values.\n"
        "- If the question asks about risk or problems, explain the likely causes based on the metrics.\n"
        "- For questions about totals, counts, or 'how many', use the DATASET SUMMARY information which contains the accurate totals."
    )

    # Step 3: Call Groq
    if _client is None:
        return "GROQ_API_KEY is not configured. Cannot generate answer."

    try:
        response = _client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            temperature=0.1,  # Low temperature for factual RAG answers
            top_p=0.9,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI response temporarily unavailable. Error: {str(e)}"

