"""
Task 4 - Chunking, embedding va indexing.

Chu de: IELTS Writing - Band Descriptors & Scoring Criteria

Huong dan:
    1. Doc toan bo Markdown trong data/standardized/.
    2. Chia van ban bang RecursiveCharacterTextSplitter.
    3. Embed chunks bang Gemini embedding-001.
    4. Upsert vao ChromaDB voi cosine distance.

Moi document/chunk phai theo docs/MODULE_CONTRACTS.md.
"""

import os
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"

# Tham so chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
CHUNKING_METHOD = "recursive"

# Embedding: su dung Gemini gemini-embedding-001 theo .env
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "gemini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIM = 3072  # gemini-embedding-001 = 3072 dims

COLLECTION_NAME = "rag_documents"


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed texts dung provider duoc cau hinh trong .env.

    Task 5 va cac task sau phai dung ham nay de dam bao chung embedding space.
    """
    provider = EMBEDDING_PROVIDER.lower()

    if provider == "gemini":
        import time
        from google import genai
        from google.genai import types

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY khong duoc thiet lap trong .env")
        client = genai.Client(api_key=api_key)

        embeddings = []
        BATCH_SIZE = 50  # Giam batch size de tranh rate limit
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            # Retry voi exponential backoff khi gap rate limit
            for attempt in range(5):
                try:
                    result = client.models.embed_content(
                        model=EMBEDDING_MODEL,
                        contents=batch,
                        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
                    )
                    for emb in result.embeddings:
                        embeddings.append(emb.values)
                    break  # Thanh cong, thoat retry loop
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                        wait_sec = 65 * (attempt + 1)  # 65s, 130s, ...
                        print(f"    [RATE LIMIT] Doi {wait_sec}s truoc khi retry (lan {attempt + 1}/5)...")
                        time.sleep(wait_sec)
                    else:
                        raise  # Loi khac: raise ngay
            else:
                raise RuntimeError(f"Failed after 5 retries for batch {i//BATCH_SIZE + 1}")

            # Them delay nho giua cac batches
            if i + BATCH_SIZE < len(texts):
                time.sleep(1)
        return embeddings

    elif provider == "openai":
        import openai
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.embeddings.create(
            input=texts, model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
        )
        return [item.embedding for item in response.data]

    elif provider == "sentence_transformers":
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3"))
        return model.encode(texts, normalize_embeddings=True).tolist()

    else:
        raise ValueError(f"Khong ho tro EMBEDDING_PROVIDER={provider!r}")


def get_collection():
    """Mo hoac tao Chroma collection dung cosine distance."""
    import chromadb

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def load_documents() -> list[dict]:
    """Doc Markdown va tra ve danh sach Document theo contract."""
    documents = []
    for path in STANDARDIZED_DIR.rglob("*.md"):
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        doc_type = "legal" if "legal" in path.parts else "news"

        # Lay URL tu dong header trong news files
        url = None
        for line in content.splitlines():
            if line.startswith("**Source:**"):
                url = line.replace("**Source:**", "").strip()
                break

        doc_id = path.relative_to(STANDARDIZED_DIR).as_posix()
        documents.append({
            "id": doc_id,
            "content": content,
            "metadata": {
                "source": path.name,
                "title": path.stem.replace("_", " ").replace("-", " "),
                "doc_type": doc_type,
                "url": url,
            },
        })

    print(f"  Loaded {len(documents)} documents from {STANDARDIZED_DIR}")
    return documents


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Chia Document thanh chunks co id va chunk_index."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for document in documents:
        texts = splitter.split_text(document["content"])
        for index, text in enumerate(texts):
            text = text.strip()
            if not text:
                continue
            chunks.append({
                "id": f"{document['id']}::chunk-{index}",
                "content": text,
                "metadata": {
                    **document["metadata"],
                    "chunk_index": index,
                },
            })

    print(f"  Created {len(chunks)} chunks (avg {len(chunks)//max(len(documents),1)} per doc)")
    return chunks


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """Them embedding vao tung chunk."""
    BATCH_SIZE = 50  # de an toan voi rate limit
    texts = [chunk["content"] for chunk in chunks]

    all_vectors = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        print(f"  Embedding batch {i//BATCH_SIZE + 1}/{(len(texts)-1)//BATCH_SIZE + 1} ({len(batch)} chunks)...")
        vectors = embed_texts(batch)
        all_vectors.extend(vectors)

    for chunk, vector in zip(chunks, all_vectors):
        chunk["embedding"] = vector

    print(f"  Embedded {len(chunks)} chunks, dim={len(all_vectors[0]) if all_vectors else 0}")
    return chunks


def index_to_vectorstore(chunks: list[dict]) -> None:
    """Upsert chunks vao ChromaDB."""
    collection = get_collection()
    existing_count = collection.count()

    # Batch upsert
    BATCH_SIZE = 100
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        collection.upsert(
            ids=[c["id"] for c in batch],
            documents=[c["content"] for c in batch],
            embeddings=[c["embedding"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )
    new_count = collection.count()
    print(f"  ChromaDB: {existing_count} -> {new_count} documents (upserted {len(chunks)})")


def run_pipeline() -> None:
    """Chay load, chunk, embed va index chi cho cac chunks chua co trong ChromaDB."""
    print("=== Task 4: Chunking & Indexing ===")

    print("\n[1/4] Loading documents...")
    documents = load_documents()

    print("\n[2/4] Chunking documents...")
    chunks = chunk_documents(documents)

    collection = get_collection()
    existing_ids = set()
    if collection.count() > 0:
        existing_data = collection.get(include=[])
        existing_ids = set(existing_data.get("ids", []))

    new_chunks = [c for c in chunks if c["id"] not in existing_ids]
    print(f"  Existing in ChromaDB: {len(existing_ids)} chunks")
    print(f"  New chunks to embed:  {len(new_chunks)} chunks")

    if not new_chunks:
        print("\n[DONE] Tat ca chunks da co trong ChromaDB. Khong can embed lai!")
        return

    print("\n[3/4] Embedding new chunks...")
    embedded_chunks = embed_chunks(new_chunks)

    print("\n[4/4] Indexing to ChromaDB...")
    index_to_vectorstore(embedded_chunks)

    print(f"\n[DONE] Indexed {len(embedded_chunks)} new chunks. Total in ChromaDB: {collection.count()}")
    print(f"       ChromaDB stored at: {CHROMA_DIR}")


if __name__ == "__main__":
    run_pipeline()
