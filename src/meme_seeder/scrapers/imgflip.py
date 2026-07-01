import re

import httpx

from ..schema import ImgflipRaw

IMGFLIP_API = "https://api.imgflip.com/get_memes"


def slug_from_name(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)
    return slug


def fetch_templates(limit: int = 100) -> list[ImgflipRaw]:
    response = httpx.get(IMGFLIP_API, timeout=30)
    response.raise_for_status()
    data = response.json()

    if not data.get("success"):
        raise RuntimeError(f"Imgflip API error: {data}")

    memes = data["data"]["memes"][:limit]
    return [
        ImgflipRaw(
            id=slug_from_name(m["name"]),
            name=m["name"],
            url=m["url"],
            width=m["width"],
            height=m["height"],
            box_count=m["box_count"],
            rank=i + 1,
        )
        for i, m in enumerate(memes)
    ]
