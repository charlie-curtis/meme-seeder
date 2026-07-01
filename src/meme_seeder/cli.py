import argparse
from pathlib import Path

from rich.console import Console

from .enricher import EnricherConfig
from .pipeline import run_pipeline

console = Console()

YOU_GET_A_MEME = Path(__file__).parents[3] / "you-get-a-meme"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="meme-seeder",
        description="Seed meme template databases by scraping and LLM enrichment",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run
    run_parser = subparsers.add_parser("run", help="Run the full scrape → enrich → write pipeline")
    run_parser.add_argument("--limit", type=int, default=50)
    run_parser.add_argument("--skip-kym", action="store_true")
    run_parser.add_argument("--force-reenrich", action="store_true")
    run_parser.add_argument("--backend", choices=["ollama", "claude"], default="ollama")
    run_parser.add_argument("--model")
    run_parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")

    # download-images
    dl_parser = subparsers.add_parser("download-images", help="Download template images from Imgflip")
    dl_parser.add_argument("--force", action="store_true", help="Re-download even if already cached")

    # install
    install_parser = subparsers.add_parser(
        "install",
        help="Copy templates.txt and images into you-get-a-meme",
    )
    install_parser.add_argument(
        "--dest",
        type=Path,
        default=YOU_GET_A_MEME,
        help=f"Path to you-get-a-meme repo (default: {YOU_GET_A_MEME})",
    )

    args = parser.parse_args()

    if args.command == "run":
        model = args.model or ("" if args.backend == "claude" else "llama3.2:3b")
        config = EnricherConfig(
            backend=args.backend,
            model=model,
            ollama_url=args.ollama_url,
        )
        run_pipeline(
            limit=args.limit,
            skip_kym=args.skip_kym,
            force_reenrich=args.force_reenrich,
            enrich_config=config,
        )

    elif args.command == "download-images":
        from .downloader import download_images
        console.print("[bold blue]Downloading images...[/]")
        paths = download_images(force=args.force)
        console.print(f"  [green]✓[/] {len(paths)} images in data/images/")

    elif args.command == "install":
        from pathlib import Path as P
        from .downloader import copy_images
        dest = P(args.dest)
        if not dest.exists():
            console.print(f"[red]Destination not found:[/] {dest}")
            return

        # Copy templates.txt
        src_txt = P(__file__).parents[2] / "data" / "output" / "templates.txt"
        dest_txt = dest / "data" / "templates.txt"
        dest_txt.write_text(src_txt.read_text())
        console.print(f"  [green]✓[/] Copied templates.txt → {dest_txt}")

        # Copy images
        copy_images(dest / "data" / "images")


if __name__ == "__main__":
    main()
