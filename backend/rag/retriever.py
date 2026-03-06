"""
rag/retriever.py — TF-IDF based document retriever using scikit-learn.

Uses TF-IDF vectorization + cosine similarity for semantic search
over inverter telemetry documents. Lightweight alternative to
sentence-transformers + FAISS that works on all platforms.
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class Retriever:
    """
    TF-IDF-based document retriever.

    Builds a TF-IDF index over a list of text documents and supports
    top-k similarity search using cosine similarity.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),   # Unigrams + bigrams for better matching
            max_features=5000,
        )
        self.doc_embeddings = None
        self.documents = []

    def build_index(self, documents: list[str]) -> None:
        """
        Build the TF-IDF index from a list of documents.

        Args:
            documents: List of text strings to index.
        """
        if not documents:
            print("[RAG retriever] WARNING: No documents to index.")
            return

        self.documents = documents
        self.doc_embeddings = self.vectorizer.fit_transform(documents)
        print(f"[RAG retriever] Indexed {len(documents)} documents "
              f"(vocabulary size: {len(self.vectorizer.vocabulary_)})")

    def search(self, query: str, k: int = 3) -> list[str]:
        """
        Search for the top-k most relevant documents to the query.

        Args:
            query: The search query string.
            k: Number of top results to return.

        Returns:
            List of the top-k most relevant document strings.
        """
        if self.doc_embeddings is None or not self.documents:
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.doc_embeddings).flatten()

        # Get top-k indices sorted by similarity (descending)
        top_k_indices = np.argsort(similarities)[::-1][:k]

        results = []
        for idx in top_k_indices:
            if similarities[idx] > 0:  # Only include if there's some relevance
                results.append(self.documents[idx])

        return results
