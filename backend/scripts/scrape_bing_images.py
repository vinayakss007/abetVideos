"""Scrape event-related images using Bing Image Search (no API key needed).
Usage: python3 scripts/scrape_bing_images.py "wedding ceremony" --count 10 --output ./images
"""

import argparse
import asyncio
import hashlib
import re
import sys
from pathlib import Path

import httpx

BING_URL = "https://www.bing.com/images/search"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _extract_image_urls(html: str) -> list[str]:
    urls: set[str] = set()
    # murl values in Bing HTML (HTML-encoded JSON within script tags)
    for m in re.finditer(r'murl(?:&quot;|\").{0,2}(?:&quot;|\")([^"&]+)', html):
        u = m.group(1).replace("\\", "")
        if u.startswith("http"):
            urls.add(u)
    return list(urls)[:50]


async def search_bing(query: str, count: int = 10) -> list[str]:
    params = {"q": query, "count": min(count, 35), "setlang": "en-US"}
    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=15.0) as client:
        resp = await client.get(BING_URL, params=params)
        resp.raise_for_status()
        urls = _extract_image_urls(resp.text)
        return urls[:count]


async def download(url: str, output_dir: Path, client: httpx.AsyncClient) -> str | None:
    try:
        resp = await client.get(url, timeout=30.0, follow_redirects=True)
        resp.raise_for_status()
        ext = Path(url.split("?")[0].split("#")[0]).suffix or ".jpg"
        name = hashlib.md5(url.encode()).hexdigest()[:16] + ext
        path = output_dir / name
        path.write_bytes(resp.content)
        return str(path)
    except Exception as e:
        print(f"  Failed: {url[:70]}... {e}", file=sys.stderr)
        return None


async def scrape(query: str, count: int = 10, output_dir: str | None = None):
    out = Path(output_dir or f"./bing_images/{query.replace(' ', '_')}")
    out.mkdir(parents=True, exist_ok=True)

    print(f"Searching Bing for: {query}")
    urls = await search_bing(query, count)
    print(f"Found {len(urls)} image URLs")

    sem = asyncio.Semaphore(3)

    async def limited_dl(url: str) -> str | None:
        async with sem:
            return await download(url, out, client)

    async with httpx.AsyncClient(headers=HEADERS, timeout=30.0, follow_redirects=True) as client:
        tasks = [limited_dl(url) for url in urls]
        results = await asyncio.gather(*tasks)

    successful = [r for r in results if r]
    print(f"\nDownloaded {len(successful)}/{len(urls)} images to {out}")


def main():
    parser = argparse.ArgumentParser(description="Scrape images from Bing Image Search")
    parser.add_argument("query", help="Search query (e.g. 'wedding ceremony', 'birthday party')")
    parser.add_argument("--count", "-n", type=int, default=10, help="Number of images (default: 10)")
    parser.add_argument("--output", "-o", help="Output directory (default: ./bing_images/<query>)")
    args = parser.parse_args()
    asyncio.run(scrape(args.query, args.count, args.output))


if __name__ == "__main__":
    main()
