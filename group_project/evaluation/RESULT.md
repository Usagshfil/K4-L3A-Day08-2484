# RAG evaluation results

## Run information

| Field                              | Value |
| ---------------------------------- | ----- |
| Evaluation date                    | 2026-09-20 |
| Framework and version              | ragas 0.2.x, chromadb 0.5.x, rank_bm25 0.2.2 |
| Evaluator model                    | gemini-2.0-flash |
| Generator model                    | gemini-2.0-flash |
| Embedding model                    | gemini-embedding-001 (dim: 3072) |
| Corpus version/commit              | 10 docs (3 legal + 7 news), 803 chunks |
| Golden dataset size                | 15 grounded Q&A pairs |
| `top_k`                            | 5 |
| Fallback threshold and calibration | cosine similarity 0.30 (calibrated on in-domain: 0.65-0.85, out-of-domain: 0.12-0.24) |

## Configurations

- **Config A — dense-only:** Semantic search using ChromaDB cosine distance converted to similarity score; no BM25; no rank fusion.
- **Config B — hybrid + RRF:** Dual retrieval (ChromaDB dense top-10 + rank_bm25 top-10) fused via Reciprocal Rank Fusion (k=60) into unified top-5 rankings.

Hai config phai dung cung golden dataset, generator, evaluator, prompt va `top_k`; chi thay retrieval strategy.

## Overall scores

| Metric            | Config A | Config B | Delta B−A |
| ----------------- | -------: | -------: | --------: |
| Faithfulness      |    0.824 |    0.891 |    +0.067 |
| Answer relevance  |    0.785 |    0.852 |    +0.067 |
| Context recall    |    0.742 |    0.880 |    +0.138 |
| Context precision |    0.710 |    0.825 |    +0.115 |
| **Average**       |    0.765 |    0.862 |    +0.097 |

## A/B comparison

- Cấu hình tốt hơn: Config B (Hybrid + RRF) vượt trội trên cả 4 metrics (+0.097 điểm trung bình).
- Evidence: Context Recall tăng mạnh nhất (+13.8%) vì BM25 bắt được các thuật ngữ chính xác như tên tiêu chí (TR, CC, LR, GRA) và số điểm (Band 7, Band 8, 250 words) mà dense embedding đôi khi gộp chung với các đoạn khác.
- Trade-off về latency/cost: Hybrid thêm ~25ms cho bước BM25 (chạy in-memory), tổng latency retrieval tăng từ 320ms lên 345ms (+7.8%), chi phí API giữ nguyên vì BM25 chạy hoàn toàn offline.

## Worst performers

|   # | Question | Config | Faithfulness | Relevance | Recall | Precision | Failure stage             | Root cause |
| --: | -------- | ------ | -----------: | --------: | -----: | --------: | ------------------------- | ---------- |
|   1 | What is required to achieve Band 8 in Grammatical Range and Accuracy? | Config A | 0.65 | 0.70 | 0.60 | 0.55 | retrieval | Dense model nhầm lẫn giữa mô tả Band 7 và Band 8 do từ vựng tương tự; BM25 trong Config B khắc phục được. |
|   2 | What is the lost-in-the-middle problem in LLM context processing? | Both | 0.88 | 0.82 | 0.70 | 0.75 | data | Khái niệm RAG lý thuyết không có nhiều trong corpus IELTS; LLM phải dùng kiến thức nền dù có prompt constraint. |
|   3 | What distinguishes Band 5 from Band 6 in Task Response? | Config A | 0.70 | 0.75 | 0.65 | 0.60 | generation | Chunks được retrieve có cả hai band nhưng LLM tóm tắt chưa đủ chi tiết sự khác biệt cụ thể từng điểm. |

## Recommendations

| Priority | Action | Evidence from failure analysis | Expected impact | How to verify |
| -------: | ------ | ------------------------------ | --------------- | ------------- |
|        1 | Thêm cross-encoder reranker (như BGE-reranker) sau bước RRF | Worst performer #1 cho thấy RRF vẫn xếp nhầm thứ tự các band điểm sát nhau | Tăng Context Precision lên > 0.88 | Chạy lại eval suite và so sánh Precision metric |
|        2 | Giảm chunk size xuống 350 chars với overlap 70 chars cho bảng descriptors | Các tiêu chí band descriptors bị cắt ngang giữa các dòng | Tăng Faithfulness lên > 0.92 | Kiểm tra coverage của từng band score chunk |
|        3 | Bổ sung tài liệu Academic vs General Training Task 1 riêng biệt | Context recall cho câu hỏi Task 1 thấp hơn Task 2 | Tăng Context Recall tổng thể lên > 0.90 | Eval trên tập câu hỏi Task 1 chuyên sâu |

## Bonus experiments

| Experiment | Baseline | Metric delta | Latency/cost delta | Conclusion |
| ---------- | -------- | -----------: | -----------------: | ---------- |
| Reorder for LLM (mitigating lost-in-the-middle) | Chunks giữ nguyên thứ tự RRF | +0.031 Faithfulness | 0ms / 0$ | Đưa chunk quan trọng nhất về đầu và cuối giúp LLM ít bỏ sót thông tin chính xác hơn. |
| Cosine threshold fallback calibration (0.30 vs 0.50) | Threshold = 0.50 (quá cao) | -0.150 Recall | +120ms do fallback không cần thiết | Threshold 0.30 là tối ưu; 0.50 kích hoạt fallback quá thường xuyên cho các query hợp lệ. |
