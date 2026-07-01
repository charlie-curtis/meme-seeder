import re
import time
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup

from ..schema import KYMRaw

KYM_BASE = "https://knowyourmeme.com/memes"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def name_to_slug(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)
    return slug


def _extract_section(soup: BeautifulSoup, section_id: str) -> str | None:
    section = soup.find("section", {"id": section_id})
    if not section:
        return None
    body = section.find(class_="bodycopy")
    if not body:
        return None
    for tag in body.find_all(["script", "style", "figure"]):
        tag.decompose()
    return body.get_text(separator=" ", strip=True)


def fetch_kym(name: str, delay_seconds: float = 2.5) -> KYMRaw | None:
    """Fetch meme context from Know Your Meme. Returns None if not found or on error."""
    slug = name_to_slug(name)
    url = f"{KYM_BASE}/{slug}"

    time.sleep(delay_seconds)

    try:
        response = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        if response.status_code == 404:
            return None
        response.raise_for_status()
    except httpx.HTTPError:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    about = _extract_section(soup, "about")
    if not about:
        return None

    return KYMRaw(
        slug=slug,
        name=name,
        url=str(response.url),
        about=about[:2000],
        origin=(_extract_section(soup, "origin") or "")[:800],
        spread=(_extract_section(soup, "spread") or "")[:800],
        fetched_at=datetime.now(timezone.utc),
    )
