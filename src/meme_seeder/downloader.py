from pathlib import Path

import httpx
from rich.console import Console
from rich.progress import track

from .schema import EnrichedTemplate

console = Console()

_REPO_ROOT = Path(__file__).parents[2]
ENRICHED_DIR = _REPO_ROOT / "data" / "enriched"
IMAGES_DIR = _REPO_ROOT / "data" / "images"


def _ext(url: str) -> str:
    suffix = Path(url.split("?")[0]).suffix
    return suffix if suffix else ".jpg"


def download_images(force: bool = False) -> list[Path]:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    enriched_files = sorted(ENRICHED_DIR.glob("*.json"))
    if not enriched_files:
        console.print("[yellow]No enriched templates found in data/enriched/ — run the pipeline first.[/]")
        return []

    templates = []
    for f in enriched_files:
        try:
            templates.append(EnrichedTemplate.model_validate_json(f.read_text()))
        except Exception as e:
            console.print(f"  [red]Skipping {f.name}:[/] {e}")

    downloaded: list[Path] = []
    skipped = 0

    for t in track(templates, description="  Downloading..."):
        dest = IMAGES_DIR / f"{t.id}{_ext(t.image_url)}"
        if dest.exists() and not force:
            skipped += 1
            downloaded.append(dest)
            continue
        try:
            response = httpx.get(t.image_url, timeout=30, follow_redirects=True)
            response.raise_for_status()
            dest.write_bytes(response.content)
            downloaded.append(dest)
        except Exception as e:
            console.print(f"  [red]✗ {t.name}:[/] {e}")

    console.print(f"  [green]✓[/] {len(downloaded) - skipped} downloaded, {skipped} already cached")
    return downloaded


def copy_images(dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    images = list(IMAGES_DIR.glob("*"))
    if not images:
        console.print("[yellow]No images in data/images/ — run download-images first.[/]")
        return
    for src in images:
        (dest_dir / src.name).write_bytes(src.read_bytes())
    console.print(f"  [green]✓[/] Copied {len(images)} images to {dest_dir}")
