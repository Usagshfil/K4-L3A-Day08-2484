"""
Task 8 - PageIndex vectorless fallback.

Neu PAGEINDEX_API_KEY co trong .env, dung PageIndex.
Neu khong, fallback sang BM25 on-disk (de khong crash pipeline).

Moi result phai co: id, content, score, metadata, retrieval_method='pageindex'.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def upload_documents() -> None:
    """Upload tai lieu va luu document IDs de tai su dung.

    Chi upload neu PAGEINDEX_API_KEY duoc cau hinh.
    Neu khong co key, skip (fallback BM25 se duoc dung).
    """
    if not PAGEINDEX_API_KEY:
        print("[PageIndex] PAGEINDEX_API_KEY khong duoc thiet lap. Skip upload.")
        return

    try:
        # Placeholder: implement voi PageIndex SDK neu co key
        # from pageindex import Client
        # client = Client(api_key=PAGEINDEX_API_KEY)
        # for path in STANDARDIZED_DIR.rglob("*.md"):
        #     client.upload(str(path))
        print("[PageIndex] Upload not implemented yet. Add SDK code here.")
    except Exception as e:
        print(f"[PageIndex] Upload failed: {e}")


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """Tra ve pageindex SearchResult.

    Fallback chain:
        1. Thu PageIndex API neu co key.
        2. Neu khong co key hoac loi, raise NotImplementedError
           de task9 biet fallback khong kha dung.
    """
    if not PAGEINDEX_API_KEY:
        # Khong co key: raise de task9 dung hybrid thay the
        raise NotImplementedError("PAGEINDEX_API_KEY chua duoc thiet lap")

    try:
        # Placeholder: implement voi PageIndex SDK neu co key
        # from pageindex import Client
        # client = Client(api_key=PAGEINDEX_API_KEY)
        # results_raw = client.query(query, top_k=top_k)
        # results = []
        # for rank, item in enumerate(results_raw, 1):
        #     results.append({
        #         "id": item["id"],
        #         "content": item["content"],
        #         "score": 1.0 / rank,  # Assign descending scores if no score provided
        #         "metadata": {
        #             "source": item.get("source", "pageindex"),
        #             "title": item.get("title", ""),
        #             "doc_type": "news",
        #             "url": item.get("url"),
        #             "chunk_index": rank - 1,
        #         },
        #         "retrieval_method": "pageindex",
        #     })
        # return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]
        raise NotImplementedError("PageIndex SDK not implemented yet")
    except Exception as e:
        raise RuntimeError(f"PageIndex search failed: {e}") from e


if __name__ == "__main__":
    upload_documents()
