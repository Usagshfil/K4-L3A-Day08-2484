"""
Task 7 - Reciprocal Rank Fusion (RRF).

RRF gop nhieu bang xep hang ma khong cong truc tiep cosine score voi BM25
score. Cong thuc: RRF(d) = sum(1 / (k + rank)), rank bat dau tu 1.

Luu y: RRF score chi phan anh thu hang, khong dung de quyet dinh fallback.
"""


def rerank_rrf(
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    k: int = 60,
) -> list[dict]:
    """Fuse nhieu ranked lists va tra hybrid SearchResult.

    Args:
        ranked_lists: Danh sach cac ranked results tu dense va BM25.
        top_k: So ket qua tra ve.
        k: Hang so RRF (60 la gia tri chuan).

    Returns:
        Danh sach SearchResult da fuse, sort theo RRF score giam dan.
    """
    rrf_scores: dict[str, float] = {}
    item_store: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            item_id = item["id"]
            rrf_scores[item_id] = rrf_scores.get(item_id, 0.0) + 1.0 / (k + rank)
            # Luu item moi nhat (uu tien dense item de giu cosine score trong metadata)
            if item_id not in item_store:
                item_store[item_id] = item

    # Sort theo RRF score giam dan
    ranked_ids = sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)

    results = []
    for item_id in ranked_ids[:top_k]:
        result = item_store[item_id].copy()
        result["score"] = rrf_scores[item_id]
        result["retrieval_method"] = "hybrid"
        results.append(result)

    return results


if __name__ == "__main__":
    # Demo nhanh
    list1 = [
        {"id": "a", "content": "A", "score": 0.9, "metadata": {}, "retrieval_method": "dense"},
        {"id": "b", "content": "B", "score": 0.7, "metadata": {}, "retrieval_method": "dense"},
    ]
    list2 = [
        {"id": "b", "content": "B", "score": 5.0, "metadata": {}, "retrieval_method": "bm25"},
        {"id": "c", "content": "C", "score": 3.0, "metadata": {}, "retrieval_method": "bm25"},
    ]
    fused = rerank_rrf([list1, list2], top_k=3)
    for r in fused:
        print(f"  [{r['score']:.4f}] {r['id']} ({r['retrieval_method']})")
