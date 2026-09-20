"""
Task 9 - Retrieval pipeline hoan chinh.

Luong xu ly:
    1. Chay semantic_search va lexical_search.
    2. Fuse hai danh sach bang RRF dung mot lan.
    3. Lay best cosine score goc tu dense results.
    4. Neu score duoi threshold, thu PageIndex fallback.
    5. Neu fallback loi, tra hybrid results thay vi crash.

Khong so sanh threshold voi RRF score vi hai thang do khac nhau.
"""

import os
from dotenv import load_dotenv
load_dotenv()

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


# Doc tu .env; fallback 0.3 neu chua thiet lap
_threshold_str = os.getenv("SCORE_THRESHOLD", "").strip()
SCORE_THRESHOLD: float = float(_threshold_str) if _threshold_str else 0.3
DEFAULT_TOP_K = 5


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """Tra ve hybrid hoac pageindex SearchResult.

    Fallback logic:
        - Lay best cosine score tu dense results (KHONG dung RRF score).
        - Neu score < threshold, thu pageindex_search.
        - Neu pageindex loi hoac tra rong, van tra hybrid.
    """
    # 1. Dual retrieval
    dense = semantic_search(query, top_k=top_k * 2)
    sparse = lexical_search(query, top_k=top_k * 2)

    # 2. Fuse mot lan bang RRF
    if use_reranking and (dense or sparse):
        lists_to_fuse = [lst for lst in [dense, sparse] if lst]
        hybrid = rerank_rrf(lists_to_fuse, top_k=top_k)
    else:
        hybrid = dense[:top_k]

    # 3. Fallback: dung cosine score goc tu dense, KHONG dung RRF score
    best_dense_score = dense[0]["score"] if dense else 0.0
    if best_dense_score < score_threshold:
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                return fallback
        except Exception:
            pass  # Fallback loi: tra hybrid, khong crash

    return hybrid[:top_k]


if __name__ == "__main__":
    import sys
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    query = "What are the IELTS Writing Task 2 band descriptors for coherence?"
    print(f"Query: {query!r}")
    print(f"Threshold: {SCORE_THRESHOLD}")
    results = retrieve(query, top_k=3)
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] [{r['score']:.4f}] {r['retrieval_method']}")
        print(f"     {r['id']}")
        print(f"     {r['content'][:150]}...")
