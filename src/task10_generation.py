"""
Task 10 - Generation co citation.

Huong dan:
    1. Retrieve top-k chunks.
    2. Reorder de giam lost-in-the-middle.
    3. Format context kem title va source.
    4. Goi provider duoc chon trong .env (Gemini / OpenAI / Anthropic).
    5. Tra answer, sources va retrieval_source.

Neu context khong du hoac provider loi, tra safe refusal; khong bia thong tin.
"""

import os
import sys

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

load_dotenv()

TOP_K = 5
TEMPERATURE = 0.3

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-3.6-flash")

SYSTEM_PROMPT = """You are a helpful IELTS expert assistant. Answer the user's question using the provided context documents.
- Base your answer on the facts mentioned in the context.
- Cite your sources inline using [Document N] format (e.g. "...as outlined in [Document 1]").
- If the context truly does not mention anything related to the question, state: "I cannot verify this information from the available sources."
- Be concise, accurate, and helpful."""


def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """Dua chunks quan trong ve dau va cuoi context (giam lost-in-the-middle).

    Chunks quan trong nhat (index 0, 2, 4...) o dau.
    Chunks thu yeu hon (index 1, 3, 5...) o cuoi (dao nguoc).
    """
    if len(chunks) <= 2:
        return list(chunks)
    front = chunks[::2]   # Even indices: 0, 2, 4, ...
    back = chunks[1::2]   # Odd indices: 1, 3, 5, ...
    return front + back[::-1]


def format_context(chunks: list[dict]) -> str:
    """Tao context co title va source label de LLM tao citation."""
    parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk["metadata"]
        title = metadata.get("title", "Unknown")
        source = metadata.get("source", "Unknown")
        url = metadata.get("url", "")
        source_str = f"{source}" + (f" ({url})" if url else "")
        parts.append(
            f"[Document {index} | Title: {title} | Source: {source_str}]\n"
            f"{chunk['content']}"
        )
    return "\n\n---\n\n".join(parts)


def call_llm(system_prompt: str, user_message: str) -> str:
    """Goi Gemini, OpenAI hoac Anthropic theo cau hinh .env."""
    provider = LLM_PROVIDER.lower()

    if provider == "gemini":
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY khong duoc thiet lap")
        client = genai.Client(api_key=api_key)
        model = LLM_MODEL or "gemini-2.0-flash"

        response = client.models.generate_content(
            model=model,
            contents=[
                {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_message}"}]}
            ],
        )
        return response.text

    elif provider == "openai":
        import openai

        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        model = LLM_MODEL or "gpt-4o-mini"
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=TEMPERATURE,
        )
        return response.choices[0].message.content

    elif provider == "anthropic":
        import anthropic

        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        model = LLM_MODEL or "claude-3-haiku-20240307"
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    else:
        raise ValueError(f"LLM_PROVIDER khong ho tro: {provider!r}")


def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """Tra ve GenerationResult voi answer, sources va retrieval_source."""
    # 1. Retrieve chunks
    chunks = retrieve(query, top_k=top_k)

    # 2. Safe refusal neu khong co context
    if not chunks:
        return {
            "answer": "I cannot verify this information from the available sources.",
            "sources": [],
            "retrieval_source": "none",
        }

    # 3. Reorder chunks de giam lost-in-the-middle
    reordered = reorder_for_llm(chunks)

    # 4. Format context
    context = format_context(reordered)
    user_message = f"Context:\n{context}\n\nQuestion: {query}"

    # 5. Goi LLM
    try:
        answer = call_llm(SYSTEM_PROMPT, user_message)
    except Exception as e:
        answer = f"I cannot verify this information from the available sources. (Error: {e})"

    # 6. Lay retrieval_source tu chunk dau tien
    retrieval_source = chunks[0].get("retrieval_method", "hybrid")
    # Map retrieval_method -> retrieval_source
    if retrieval_source in ("dense", "bm25", "hybrid"):
        retrieval_source = "hybrid"
    elif retrieval_source == "pageindex":
        retrieval_source = "pageindex"
    else:
        retrieval_source = "none"

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": retrieval_source,
    }


if __name__ == "__main__":
    test_queries = [
        "What are the IELTS Writing Task 2 band descriptors for coherence and cohesion?",
        "What is the scoring criteria for IELTS Writing Task 1?",
        "How to get band 8 in IELTS Writing?",
    ]
    for q in test_queries[:1]:  # Chi chay 1 query de test
        print(f"\nQuery: {q!r}")
        result = generate_with_citation(q, top_k=3)
        print(f"\nAnswer: {result['answer'][:300]}...")
        print(f"\nSources ({len(result['sources'])}):")
        for src in result["sources"]:
            print(f"  - {src['id']} [{src['score']:.3f}]")
        print(f"\nRetrieval source: {result['retrieval_source']}")
