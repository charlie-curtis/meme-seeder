import argparse
import os
import sys

from rich.console import Console

from .enricher import EnricherConfig
from .pipeline import run_pipeline

console = Console()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="meme-seeder",
        description="Seed meme template databases by scraping and LLM enrichment",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the full scrape → enrich → write pipeline")
    run_parser.add_argument(
        "--limit", type=int, default=50,
        help="Max templates to fetch from Imgflip (default: 50)"
    )
    run_parser.add_argument(
        "--skip-kym", action="store_true",
        help="Skip Know Your Meme scraping (faster, less context for enrichment)"
    )
    run_parser.add_argument(
        "--force-reenrich", action="store_true",
        help="Re-enrich templates even if a cached enrichment exists"
    )
    run_parser.add_argument(
        "--backend", choices=["ollama", "claude"], default="ollama",
        help="LLM backend for enrichment (default: ollama)"
    )
    run_parser.add_argument(
        "--model",
        help="Model name (default: llama3.2:3b for ollama, claude-sonnet-4-6 for claude)"
    )
    run_parser.add_argument(
        "--ollama-url", default="http://127.0.0.1:11434",
        help="Ollama base URL (default: http://127.0.0.1:11434)"
    )

    args = parser.parse_args()

    if args.command == "run":
        model = args.model
        if model is None:
            model = "claude-sonnet-4-6" if args.backend == "claude" else "llama3.2:3b"

        claude_api_key = os.environ.get("ANTHROPIC_API_KEY") if args.backend == "claude" else None
        if args.backend == "claude" and not claude_api_key:
            console.print("[red]Error:[/] ANTHROPIC_API_KEY environment variable is required for --backend claude")
            sys.exit(1)

        config = EnricherConfig(
            backend=args.backend,
            model=model,
            ollama_url=args.ollama_url,
            claude_api_key=claude_api_key,
        )

        run_pipeline(
            limit=args.limit,
            skip_kym=args.skip_kym,
            force_reenrich=args.force_reenrich,
            enrich_config=config,
        )


if __name__ == "__main__":
    main()
