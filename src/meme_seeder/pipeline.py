import json
from pathlib import Path

from rich.console import Console
from rich.progress import track

from .enricher import EnricherConfig, enrich
from .schema import EnrichedTemplate, KYMRaw, RawTemplate
from .scrapers.imgflip import fetch_templates
from .scrapers.knowyourmeme import fetch_kym
from .writer import write_templates

console = Console()

_REPO_ROOT = Path(__file__).parents[2]
RAW_DIR = _REPO_ROOT / "data" / "raw"
ENRICHED_DIR = _REPO_ROOT / "data" / "enriched"
OUTPUT_PATH = _REPO_ROOT / "data" / "output" / "templates.txt"


def _load_enriched(template_id: str) -> EnrichedTemplate | None:
    path = ENRICHED_DIR / f"{template_id}.json"
    if path.exists():
        try:
            return EnrichedTemplate.model_validate_json(path.read_text())
        except Exception:
            return None
    return None


def _save_enriched(template: EnrichedTemplate) -> None:
    ENRICHED_DIR.mkdir(parents=True, exist_ok=True)
    (ENRICHED_DIR / f"{template.id}.json").write_text(template.model_dump_json(indent=2))


def _load_kym_cache(template_id: str) -> KYMRaw | None:
    path = RAW_DIR / f"kym_{template_id}.json"
    if path.exists():
        try:
            return KYMRaw.model_validate_json(path.read_text())
        except Exception:
            return None
    return None


def run_pipeline(
    limit: int = 50,
    skip_kym: bool = False,
    force_reenrich: bool = False,
    enrich_config: EnricherConfig | None = None,
    output_path: Path = OUTPUT_PATH,
) -> None:
    if enrich_config is None:
        enrich_config = EnricherConfig()

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Imgflip
    console.print("[bold blue]Step 1:[/] Fetching templates from Imgflip API...")
    imgflip_templates = fetch_templates(limit=limit)
    console.print(f"  [green]✓[/] {len(imgflip_templates)} templates fetched")
    (RAW_DIR / "imgflip.json").write_text(
        json.dumps([t.model_dump() for t in imgflip_templates], indent=2)
    )

    # Step 2: Know Your Meme
    raw_templates: list[RawTemplate] = []
    if skip_kym:
        console.print("[bold blue]Step 2:[/] Skipping KYM (--skip-kym)")
        raw_templates = [RawTemplate(imgflip=t) for t in imgflip_templates]
    else:
        console.print("[bold blue]Step 2:[/] Fetching context from Know Your Meme...")
        for t in track(imgflip_templates, description="  KYM..."):
            kym = _load_kym_cache(t.id)
            if kym is None:
                kym = fetch_kym(t.name)
                if kym:
                    (RAW_DIR / f"kym_{t.id}.json").write_text(kym.model_dump_json(indent=2))
            raw_templates.append(RawTemplate(imgflip=t, kym=kym))

        found = sum(1 for r in raw_templates if r.kym is not None)
        console.print(f"  [green]✓[/] KYM data found for {found}/{len(raw_templates)} templates")

    # Step 3: LLM enrichment
    backend_label = f"{enrich_config.backend}/{enrich_config.model}"
    console.print(f"[bold blue]Step 3:[/] Enriching with LLM ({backend_label})...")
    enriched: list[EnrichedTemplate] = []

    for raw in track(raw_templates, description="  Enriching..."):
        if not force_reenrich:
            cached = _load_enriched(raw.imgflip.id)
            if cached:
                enriched.append(cached)
                continue
        try:
            result = enrich(raw, enrich_config)
            _save_enriched(result)
            enriched.append(result)
        except Exception as e:
            console.print(f"  [red]✗ {raw.imgflip.name}:[/] {e}")

    console.print(f"  [green]✓[/] {len(enriched)} templates enriched")

    # Step 4: Write output
    console.print("[bold blue]Step 4:[/] Writing templates.txt...")
    write_templates(enriched, output_path)
    console.print(f"  [green]✓[/] Written to {output_path}")
