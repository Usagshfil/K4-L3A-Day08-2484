"""
Task 3 — Chuẩn hóa dữ liệu sang Markdown.

Hướng dẫn:
    1. Dùng MarkItDown để convert PDF/DOCX.
    2. Đọc JSON và giữ metadata ở đầu file Markdown.
    3. Giữ cấu trúc thư mục legal/ và news/.
    4. Không tạo file rỗng hoặc file trùng khi chạy lại.
"""

import json
from pathlib import Path


LANDING_DIR = Path(__file__).parent.parent / "data" / "landing"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "standardized"


def convert_legal_docs() -> None:
    """Convert PDF/DOCX → standardized/legal/*.md dùng MarkItDown."""
    from markitdown import MarkItDown

    legal_dir = LANDING_DIR / "legal"
    output_dir = OUTPUT_DIR / "legal"
    output_dir.mkdir(parents=True, exist_ok=True)

    converter = MarkItDown()
    count = 0
    for path in legal_dir.iterdir():
        if path.suffix.lower() not in {".pdf", ".doc", ".docx"}:
            continue
        dest = output_dir / f"{path.stem}.md"
        if dest.exists():
            print(f"Skip (exists): {dest.name}")
            count += 1
            continue
        try:
            print(f"Converting: {path.name}")
            result = converter.convert(str(path))
            text = result.text_content.strip()
            if not text:
                print(f"  ⚠ Empty result for {path.name}, skipping.")
                continue
            dest.write_text(text, encoding="utf-8")
            print(f"  ✓ Saved: {dest.name} ({len(text):,} chars)")
            count += 1
        except Exception as e:
            print(f"  ✗ Failed: {path.name} — {e}")

    print(f"\nLegal docs: {count} converted.")


def convert_news_articles() -> None:
    """Convert JSON → standardized/news/*.md với header metadata."""
    news_dir = LANDING_DIR / "news"
    output_dir = OUTPUT_DIR / "news"
    output_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for path in news_dir.glob("*.json"):
        dest = output_dir / f"{path.stem}.md"
        if dest.exists():
            print(f"Skip (exists): {dest.name}")
            count += 1
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            content = data.get("content_markdown", "").strip()
            if not content:
                print(f"  ⚠ Empty content in {path.name}, skipping.")
                continue
            header = (
                f"# {data.get('title', 'Untitled')}\n\n"
                f"**Source:** {data.get('url', '')}\n\n"
                f"**Crawled:** {data.get('date_crawled', '')}\n\n"
                f"---\n\n"
            )
            dest.write_text(header + content, encoding="utf-8")
            print(f"  ✓ Saved: {dest.name} ({len(content):,} chars)")
            count += 1
        except Exception as e:
            print(f"  ✗ Failed: {path.name} — {e}")

    print(f"\nNews articles: {count} converted.")


def convert_all() -> None:
    """Convert toàn bộ dữ liệu landing."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=== Converting legal docs ===")
    convert_legal_docs()
    print("\n=== Converting news articles ===")
    convert_news_articles()
    print(f"\nDone. Standardized Markdown saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    convert_all()
