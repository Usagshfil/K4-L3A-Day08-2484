"""
Task 1 - Thu thap tai lieu chinh sach/quy dinh.

Chu de: IELTS Writing - Band Descriptors & Scoring Criteria

Huong dan:
    1. Script se tu dong tai 3 PDF tu ielts.org.
    2. Neu bi block, hay tai thu cong va dat vao data/landing/legal/.
    3. Dat ten khong dau, the hien dung noi dung.
"""

import sys
from pathlib import Path

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DATA_DIR = Path(__file__).parent.parent / "data" / "landing" / "legal"


def setup_directory() -> None:
    """Tao thu muc luu tai lieu goc."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Ready: {DATA_DIR}")


def download_documents() -> None:
    """Tai it nhat 3 PDF/DOCX tu nguon cong khai.

    Chu de: IELTS Writing - Band Descriptors & Scoring Criteria

    Neu download tu dong bi block:
        1. Truy cap cac URL ben duoi va tai PDF ve may.
        2. Dat file vao thu muc: data/landing/legal/
        3. Dat ten file theo format: ielts_<noi_dung>.pdf
    """
    import requests

    SOURCES = {
        "ielts-writing-band-descriptors.pdf": (
            "https://ielts.org/cdn/Guides/ielts-writing-band-descriptors.pdf"
        ),
        "writingbanddescriptorstask1and2.pdf": (
            "https://assets.ctfassets.net/unrdeg6se4ke/19SJoSvnUYjrHgVhWvuMnC/42f1b0cb0d7709646a1392d8418646d0/writingbanddescriptorstask1and2.pdf"
        ),
        "Band-7-8-and-9-Task-1-VIP-Student-Samples-1.pdf": (
            "https://www.ieltsadvantage.com/wp-content/uploads/2025/08/Band-7-8-and-9-Task-1-VIP-Student-Samples-1.pdf"
        ),
        # General Training Writing band descriptors (alternative URL)
        "ielts-writing-key-assessment-criteria.pdf": (
            "https://ielts.org/cdn/Guides/ielts-writing-key-assessment-criteria.pdf"
        ),
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    success_count = 0
    for filename, url in SOURCES.items():
        dest = DATA_DIR / filename
        if dest.exists():
            print(f"  [EXISTS] {filename}")
            success_count += 1
            continue
        try:
            print(f"  [DOWNLOAD] {filename}")
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            dest.write_bytes(resp.content)
            print(f"  [OK] Saved {len(resp.content):,} bytes")
            success_count += 1
        except Exception as e:
            print(f"  [FAIL] {url}")
            print(f"         Reason: {e}")
            print(f"         -> Hay tai thu cong vao: {DATA_DIR / filename}")

    print(f"\nResult: {success_count}/{len(SOURCES)} files downloaded.")
    if success_count < 3:
        print("[WARN] Chua du 3 tai lieu. Hay tai thu cong vao data/landing/legal/")
        print("   Nguon goi y:")
        print("   - https://www.ielts.org/for-test-takers/test-information/scoring")
        print("   - https://www.britishcouncil.vn/thi/ielts/ielts-ban-can-biet")
        print("   - https://ieltsliz.com/ielts-writing-task-2-band-scores-and-assessment/")


if __name__ == "__main__":
    setup_directory()
    download_documents()
