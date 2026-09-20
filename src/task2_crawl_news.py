"""
Task 2 - Crawl bai viet/thong bao ve IELTS Writing.

Chu de: IELTS Writing - huong dan, tieu chi cham diem, bai mau (EN + VI).

Cai browser truoc khi chay:
    python -m playwright install chromium
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "news"

# 7 bai cong khai ve IELTS Writing (EN + VI) - da kiem tra HTTP 200
ARTICLE_URLS = [
    # Wikipedia - luon accessible, noi dung IELTS tong quat
    "https://en.wikipedia.org/wiki/IELTS",
    # IELTS.org chinh thuc - dinh dang bai thi
    "https://www.ielts.org/about-the-test/test-format",
    # IELTS Advantage - writing resources
    "https://www.ieltsadvantage.com/writing/",
    # IDP Vietnam - writing band descriptors (tieng Anh)
    "https://ielts.idp.com/vietnam/prepare/article-ielts-writing-band-descriptors",
    # IDP Vietnam - writing task 2 guide
    "https://ielts.idp.com/vietnam/prepare/article-ielts-writing-task-2",
    # IDP Vietnam - writing tips
    "https://ielts.idp.com/vietnam/prepare/article-ielts-writing-tips",
    # IDP Vietnam - results & scoring
    "https://ielts.idp.com/vietnam/results",
]


async def crawl_with_playwright(url: str) -> dict:
    """Crawl URL dung Crawl4AI (Playwright-based)."""
    from crawl4ai import AsyncWebCrawler
    async with AsyncWebCrawler(verbose=False) as crawler:
        result = await crawler.arun(url=url)
        title = (result.metadata or {}).get("title", "") or url.split("/")[-1]
        return {
            "url": url,
            "title": title,
            "date_crawled": datetime.now().isoformat(),
            "content_markdown": result.markdown or "",
        }


def crawl_with_requests(url: str) -> dict:
    """Fallback: Crawl URL dung requests + markitdown (khong can browser)."""
    import requests
    from markitdown import MarkItDown

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()

    # Extract title from HTML
    import re
    title_match = re.search(r"<title>(.*?)</title>", resp.text, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else url.split("/")[-1]
    title = re.sub(r"\s+", " ", title)

    # Convert HTML to Markdown using markitdown
    converter = MarkItDown()
    # Save HTML temporarily and convert
    tmp = Path(__file__).parent.parent / "data" / "landing" / "news" / "_tmp_crawl.html"
    tmp.write_bytes(resp.content)
    result = converter.convert(str(tmp))
    tmp.unlink(missing_ok=True)

    return {
        "url": url,
        "title": title,
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": result.text_content or resp.text[:5000],
    }


async def crawl_article(url: str) -> dict:
    """Crawl mot URL - thu Playwright truoc, fallback sang requests."""
    try:
        return await crawl_with_playwright(url)
    except Exception as playwright_err:
        print(f"    [Playwright failed: {type(playwright_err).__name__}] -> Trying requests fallback...")
        return crawl_with_requests(url)


async def crawl_all() -> None:
    """Crawl tat ca URL va luu moi bai thanh mot file JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    success = 0
    for index, url in enumerate(ARTICLE_URLS, 1):
        output = DATA_DIR / f"article_{index:02d}.json"
        if output.exists():
            print(f"  [SKIP] {output.name} (already exists)")
            success += 1
            continue
        try:
            print(f"  [{index}/{len(ARTICLE_URLS)}] Crawling: {url}")
            article = await crawl_article(url)
            output.write_text(
                json.dumps(article, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            chars = len(article["content_markdown"])
            print(f"    [OK] {chars:,} chars -> {output.name}")
            success += 1
        except Exception as error:
            print(f"    [FAIL] {url}")
            print(f"           {error}")

    print(f"\nResult: {success}/{len(ARTICLE_URLS)} articles crawled.")
    if success < 5:
        print("[WARN] Chua du 5 bai. Kiem tra ket noi va chay lai.")


if __name__ == "__main__":
    asyncio.run(crawl_all())
