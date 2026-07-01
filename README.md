# meme-seeder

Scraper and LLM enricher for seeding the [you-get-a-meme](../you-get-a-meme) template database.

The quality of meme search and caption generation in you-get-a-meme depends entirely on the richness of template metadata. This repo provides the pipeline to fetch, enrich, and curate that metadata at scale.

## Pipeline

```
Imgflip API          →  template names, image URLs, box counts (top N memes)
       ↓
Know Your Meme       →  cultural context: origin, how it's used in the wild
       ↓
LLM enrichment       →  description, caption_pattern, box_labels, tags
       ↓
data/output/templates.txt   (INI format, drop-in for you-get-a-meme)
```

Intermediate results are cached in `data/raw/` and `data/enriched/`, so re-runs only process new or changed templates.

## Quickstart

```bash
pip install -e .

# Full pipeline with Ollama (must be running locally)
meme-seeder run --limit 50

# Full pipeline with Claude CLI — requires `claude` to be installed and logged in
meme-seeder run --backend claude --limit 50

# Skip KYM scraping (faster, fewer LLM context tokens)
meme-seeder run --skip-kym --limit 100

# Force re-enrichment of already-cached templates
meme-seeder run --force-reenrich --backend claude
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--limit N` | 50 | Max templates to fetch from Imgflip |
| `--backend` | `ollama` | LLM backend: `ollama` or `claude` |
| `--model` | `llama3.2:3b` / `claude-sonnet-4-6` | Model override |
| `--ollama-url` | `http://127.0.0.1:11434` | Ollama base URL |
| `--skip-kym` | off | Skip Know Your Meme scraping |
| `--force-reenrich` | off | Re-enrich even if cached |

## Template Schema

```ini
[template-id]
name = Template Name
description = Semantic description — what situation does this meme fit?
caption_pattern = Instructions for filling each text box, in order
box_labels = label for box 1, label for box 2
tags = keyword1, keyword2, keyword3
box_count = 2
```

The `description` and `tags` fields feed the embedding model for semantic search. The `caption_pattern` and `box_labels` feed the caption-generation LLM.

## Prompts

`prompts/enrich_template.md` — the main enrichment prompt. Edit this to improve output quality. It uses three placeholders: `{{name}}`, `{{box_count}}`, `{{context_block}}`.

`prompts/validate_template.md` — scores existing templates on description quality, caption pattern clarity, box label accuracy, and tag coverage. Useful for auditing the output after a run.

## Data Layout

```
data/
  raw/
    imgflip.json          # Full response from Imgflip API
    kym_{id}.json         # Cached KYM pages per template
  enriched/
    {id}.json             # LLM-enriched template (one file per template)
  output/
    templates.txt         # Final output — committed, copy to you-get-a-meme
```

`data/raw/` and `data/enriched/` are gitignored. `data/output/templates.txt` is committed and is the deliverable.

## Copying to you-get-a-meme

```bash
cp data/output/templates.txt ../you-get-a-meme/data/templates.txt
cd ../you-get-a-meme
you-get-a-meme-build-embeddings  # Rebuild embedding cache
```
