"""
rag/rag_engine.py — RAG-powered question answering engine.

Loads inverter data from Supabase, builds a TF-IDF retriever index, and
auto-refreshes every time the Supabase cache updates (every 5 minutes).

Provides rag_answer() to answer questions using retrieved context + Groq (LLaMA).
"""

import os
import threading
import logging
from dotenv import load_dotenv

from rag.ingest import load_documents
from rag.retriever import Retriever

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# RAG Engine — auto-refreshing
# ---------------------------------------------------------------------------

class RAGEngine:
    """Holds the document index and retriever, supports live refresh."""

    def __init__(self):
        self._documents: list[str] = []
        self._retriever = Retriever()
        self._summary_doc: str | None = None
        self._lock = threading.Lock()

    def refresh(self):
        """Reload documents from Supabase and rebuild the TF-IDF index."""
        try:
            docs = load_documents()
            retriever = Retriever()
            retriever.build_index(docs)

            summary = next(
                (d for d in docs if d.startswith("DATASET SUMMARY:")), None
            )

            with self._lock:
                self._documents = docs
                self._retriever = retriever
                self._summary_doc = summary

            log.info("RAG index refreshed — %d documents indexed.", len(docs))
            print(f"[RAG engine] RAG index refreshed — {len(docs)} documents indexed.")
        except Exception as exc:
            log.error("RAG refresh failed: %s", exc)
            print(f"[RAG engine] WARNING: RAG refresh failed: {exc}")

    @property
    def documents(self) -> list[str]:
        with self._lock:
            return list(self._documents)

    @property
    def summary_doc(self) -> str | None:
        with self._lock:
            return self._summary_doc

    def search(self, query: str, k: int = 10) -> list[str]:
        with self._lock:
            return self._retriever.search(query, k=k)


# ---------------------------------------------------------------------------
# Initialise at import time (once, at server startup)
# ---------------------------------------------------------------------------
load_dotenv()

print("[RAG engine] Loading documents from Supabase...")
_engine = RAGEngine()
_engine.refresh()

# Register for automatic refresh when Supabase cache updates
from database.supabase_client import on_cache_refresh
on_cache_refresh(_engine.refresh)

print(f"[RAG engine] Ready — {len(_engine.documents)} documents indexed. "
      f"Auto-refresh enabled (synced with Supabase cache).")


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
    documents = _engine.documents

    if not documents:
        return "No inverter data available. Please check the Supabase connection."

    # Step 1: Retrieve relevant documents
    context_docs = _engine.search(question, k=10)

    if not context_docs:
        # Fallback: provide a sample of all documents so Groq has some context
        context_docs = documents[:10]

    # Always include the overall summary so Groq knows totals/counts
    summary = _engine.summary_doc
    if summary and summary not in context_docs:
        context_docs.insert(0, summary)

    context_text = "\n".join(f"- {doc}" for doc in context_docs)

    # Step 2: Build messages for Groq's Chat API
    system_prompt = (
        "You are a solar energy expert AI assistant. Answer the user's question using ONLY the inverter data provided below.\n\n"
        "INVERTER DATA (live from Supabase database):\n"
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
