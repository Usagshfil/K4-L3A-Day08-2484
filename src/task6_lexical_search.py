"""
Task 6 - Lexical search bang BM25.

Dung cung corpus chunks voi Task 5. BM25 phu hop voi tu khoa chinh xac, ma tai
lieu va ten rieng. Output phai theo SearchResult va sort score giam dan.

CORPUS la global variable de test co the monkeypatch.
"""

import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


# Global CORPUS: co the duoc monkeypatch trong tests
CORPUS: list[dict] = []


def _load_corpus_from_chroma() -> list[dict]:
    """Load corpus chunks tu ChromaDB."""
    try:
        from .task4_chunking_indexing import get_collection

        collection = get_collection()
        count = collection.count()
        if count == 0:
            return []

        result = collection.get(
            include=["documents", "metadatas"],
            limit=count,
        )
        corpus = []
        for item_id, content, metadata in zip(
            result["ids"], result["documents"], result["metadatas"]
        ):
            corpus.append({
                "id": item_id,
                "content": content,
                "metadata": metadata,
            })
        return corpus
    except Exception:
        return []


def build_bm25_index(corpus: list[dict]):
    """Tao BM25 index tu cung corpus chunks cua Task 4."""
    from rank_bm25 import BM25Okapi

    tokenized = [item["content"].lower().split() for item in corpus]
    return BM25Okapi(tokenized)


def lexical_search(query: str, top_k: int = 10) -> list[dict]:
    """Tra ve BM25 SearchResult theo score giam dan.

    Su dung CORPUS global (de test monkeypatch duoc).
    Neu CORPUS rong, load tu ChromaDB.
    """
    import numpy as np

    # Lay CORPUS tu module globals de monkeypatch co hieu luc
    corpus = globals().get("CORPUS") or _load_corpus_from_chroma()
    if not corpus:
        return []

    bm25 = build_bm25_index(corpus)
    scores = bm25.get_scores(query.lower().split())
    indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for index in indices:
        item = corpus[int(index)]
        results.append({
            "id": item["id"],
            "content": item["content"],
            "score": float(scores[index]),
            "metadata": item["metadata"],
            "retrieval_method": "bm25",
        })

    # BM25 co the tra 0 voi corpus nho (IDF=0 khi tu xuat hien >= N/2 docs)
    # Fallback: dem so tu khop de duy tri thu tu hop ly
    if all(r["score"] == 0.0 for r in results):
        query_words = set(query.lower().split())
        for r in results:
            doc_words = set(r["content"].lower().split())
            r["score"] = float(len(query_words & doc_words))

    # Loai ket qua co score <= 0 sau ca hai phuong phap
    non_zero = [r for r in results if r["score"] > 0]
    final = sorted(non_zero or results, key=lambda x: x["score"], reverse=True)
    return final[:top_k]


if __name__ == "__main__":
    query = "IELTS Writing Task 2 band descriptors coherence"
    print(f"Query: {query!r}")
    for result in lexical_search(query, top_k=3):
        print(f"  [{result['score']:.3f}] {result['id']}")
        print(f"         {result['content'][:100]}...")
