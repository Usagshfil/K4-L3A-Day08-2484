"""
IELTS Writing RAG Chatbot - Streamlit UI

Hien thi: answer, citation, retrieval method, score, sources.
"""

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="IELTS Writing RAG Chatbot",
    page_icon="📝",
    layout="wide",
)

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📝 IELTS Writing RAG")
    st.caption("Chatbot tra loi cac cau hoi ve IELTS Writing dua tren Band Descriptors chinh thuc.")
    st.divider()

    top_k = st.slider("So chunks (top-k)", 3, 10, 5)
    use_reranking = st.checkbox("Dung Hybrid RRF", value=True)
    show_sources = st.checkbox("Hien thi nguon tham khao", value=True)
    show_scores = st.checkbox("Hien thi retrieval score", value=False)

    st.divider()
    if st.button("Xoa lich su chat"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("**Cau hoi goi y:**")
    example_queries = [
        "IELTS Writing Task 2 band descriptors for coherence?",
        "How is Task 1 Academic writing scored?",
        "What does Band 7 mean in IELTS Writing?",
        "Criteria for Lexical Resource in IELTS Writing?",
        "What is Grammatical Range and Accuracy?",
    ]
    for eq in example_queries:
        if st.button(eq, key=f"eg_{eq[:20]}"):
            st.session_state.pending_query = eq

# ─── Main chat area ────────────────────────────────────────────────────────────
st.title("📝 IELTS Writing RAG Chatbot")
st.caption(
    "Chatbot tra loi ve IELTS Writing Band Descriptors & Scoring Criteria. "
    "Du lieu tu IELTS.org, IDP Vietnam, Wikipedia."
)

# Init session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and show_sources and message.get("sources"):
            with st.expander(f"📚 {len(message['sources'])} nguon tham khao", expanded=False):
                for i, src in enumerate(message["sources"], 1):
                    meta = src.get("metadata", {})
                    score_str = f" | Score: {src['score']:.3f}" if show_scores else ""
                    method_str = src.get("retrieval_method", "unknown")
                    url = meta.get("url", "")
                    title = meta.get("title", meta.get("source", "Unknown"))
                    st.markdown(
                        f"**[{i}] {title}** | `{method_str}`{score_str}"
                        + (f"\n\n🔗 {url}" if url else "")
                    )
                    st.caption(src["content"][:300] + "...")
                    if i < len(message["sources"]):
                        st.divider()

# Handle pending query from sidebar examples
query = st.chat_input("Nhap cau hoi ve IELTS Writing...")
if not query and "pending_query" in st.session_state:
    query = st.session_state.pop("pending_query")

if query:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Dang tim kiem va tao cau tra loi..."):
            try:
                from src.task10_generation import generate_with_citation

                result = generate_with_citation(query, top_k=top_k)
                answer = result["answer"]
                sources = result["sources"]
                retrieval_source = result.get("retrieval_source", "hybrid")

            except Exception as e:
                answer = f"Loi: {e}"
                sources = []
                retrieval_source = "none"

        # Display answer
        st.markdown(answer)

        # Retrieval method badge
        method_colors = {
            "hybrid": "🟢 Hybrid (Dense + BM25 + RRF)",
            "pageindex": "🔵 PageIndex",
            "none": "🔴 No retrieval",
        }
        st.caption(method_colors.get(retrieval_source, f"🟡 {retrieval_source}"))

        # Sources expander
        if show_sources and sources:
            with st.expander(f"📚 {len(sources)} nguon tham khao", expanded=False):
                for i, src in enumerate(sources, 1):
                    meta = src.get("metadata", {})
                    score_str = f" | Score: {src['score']:.3f}" if show_scores else ""
                    method_str = src.get("retrieval_method", "unknown")
                    url = meta.get("url", "")
                    title = meta.get("title", meta.get("source", "Unknown"))
                    st.markdown(
                        f"**[{i}] {title}** | `{method_str}`{score_str}"
                        + (f"\n\n🔗 {url}" if url else "")
                    )
                    st.caption(src["content"][:300] + "...")
                    if i < len(sources):
                        st.divider()

    # Save to session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "sources": sources,
        "retrieval_source": retrieval_source,
    })
