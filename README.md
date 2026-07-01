# meme-seeder

Scraper and LLM enricher for seeding the [you-get-a-meme](https://github.com/charlie-curtis/you-get-a-meme) template database.

The quality of meme search and caption generation in you-get-a-meme depends entirely on the richness of template metadata. This repo provides the pipeline to fetch, enrich, and curate that metadata at scale.

## Pipeline

```
Imgflip API          →  template names, image URLs, box counts (top N memes)
       ↓
Know Your Meme       →  cultural context: origin, how it's used in the wild
       ↓
LLM enrichment       →  description, caption_pattern, box_labels, tags
       ↓
data/output/templates.txt + data/images/
```

Intermediate results are cached in `data/raw/` and `data/enriched/`, so re-runs only process new or changed templates.

## Full workflow

```bash
# 1. Install
pip install -e .

# 2. Scrape + enrich (Claude CLI backend — must be logged in)
meme-seeder run --backend claude --limit 50

# 3. Download template images from Imgflip
meme-seeder download-images

# 4. Copy templates.txt and images into you-get-a-meme
meme-seeder install

# 5. Rebuild embeddings in you-get-a-meme
cd ../you-get-a-meme && .venv/bin/python -m you_get_a_meme.embeddings
```

## Commands

### `meme-seeder run`

Scrape Imgflip + Know Your Meme, enrich with LLM, write `data/output/templates.txt`.

| Flag | Default | Description |
|------|---------|-------------|
| `--limit N` | 50 | Max templates to fetch from Imgflip |
| `--backend` | `ollama` | LLM backend: `ollama` or `claude` |
| `--model` | `llama3.2:3b` | Model override |
| `--ollama-url` | `http://127.0.0.1:11434` | Ollama base URL |
| `--skip-kym` | off | Skip Know Your Meme scraping (faster) |
| `--force-reenrich` | off | Re-enrich even if cached |

### `meme-seeder download-images`

Downloads each template image from Imgflip into `data/images/`. Reads from the existing `data/enriched/` cache — no re-enrichment needed.

| Flag | Default | Description |
|------|---------|-------------|
| `--force` | off | Re-download even if already cached |

### `meme-seeder install`

Copies `data/output/templates.txt` and `data/images/` into the you-get-a-meme repo.

| Flag | Default | Description |
|------|---------|-------------|
| `--dest PATH` | `../you-get-a-meme` | Path to you-get-a-meme repo |

## Template schema

```ini
[template-id]
name = Template Name
description = Semantic description — what situation does this meme fit?
caption_pattern = Instructions for filling each text box, in order
box_labels = label for box 1, label for box 2
tags = keyword1, keyword2, keyword3
box_count = 2
image_url = https://i.imgflip.com/...
```

`description` and `tags` feed the embedding model for semantic search. `caption_pattern` and `box_labels` guide the caption-generation LLM. `image_url` is the Imgflip source used by `download-images`.

## Prompts

`prompts/enrich_template.md` — the main enrichment prompt. Uses placeholders `{{name}}`, `{{box_count}}`, `{{context_block}}`. Edit this to improve output quality.

`prompts/validate_template.md` — scores existing templates on description quality, caption pattern clarity, box label accuracy, and tag coverage. Useful for auditing after a run.

## Data layout

```
data/
  raw/                        # gitignored — scraped source data
    imgflip.json
    kym_{id}.json
  enriched/                   # gitignored — LLM output cache (one file per template)
    {id}.json
  images/                     # gitignored — downloaded template images
    {id}.jpg / {id}.png
  output/
    templates.txt             # committed — the deliverable
```
