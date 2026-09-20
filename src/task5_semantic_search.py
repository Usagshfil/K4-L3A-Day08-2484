"""
Task 5 - Semantic search.

Embed query bang chinh ham cua Task 4, query ChromaDB va doi cosine distance
thanh similarity. Output phai theo SearchResult, sort giam dan va khong qua top_k.
"""

from .task4_chunking_indexing import embed_texts, get_collection


def semantic_search(query: str, top_k: int = 10) -> list[dict]:
    """Tra ve dense SearchResult theo score giam dan."""
    query_vector = embed_texts([query])[0]
    collection = get_collection()

    try:
        response = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
    except Exception:
        # ChromaDB raises if n_results > collection size; retry with count
        try:
            count = collection.count()
            n_results = min(top_k, count) if count > 0 else 1
            response = collection.query(
                query_embeddings=[query_vector],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            return []

    results = []
    for item_id, content, metadata, distance in zip(
        response["ids"][0],
        response["documents"][0],
        response["metadatas"][0],
        response["distances"][0],
    ):
        # ChromaDB cosine distance: 0 = identical, 2 = opposite
        # similarity = 1 - distance (khi dung cosine space)
        results.append({
            "id": item_id,
            "content": content,
            "score": float(max(0.0, 1.0 - distance)),
            "metadata": metadata,
            "retrieval_method": "dense",
        })

    return sorted(results, key=lambda item: item["score"], reverse=True)[:top_k]


if __name__ == "__main__":
    query = "IELTS Writing Task 2 band descriptors"
    print(f"Query: {query!r}")
    for result in semantic_search(query, top_k=3):
        print(f"  [{result['score']:.3f}] {result['id']}")
        print(f"         {result['content'][:100]}...")
