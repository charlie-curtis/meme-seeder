import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import httpx
from pydantic import BaseModel

from .schema import EnrichedFields, EnrichedTemplate, RawTemplate

PROMPT_PATH = Path(__file__).parents[2] / "prompts" / "enrich_template.md"


class EnricherConfig(BaseModel):
    backend: Literal["ollama", "claude"] = "ollama"
    model: str = "llama3.2:3b"
    ollama_url: str = "http://127.0.0.1:11434"
    timeout_seconds: int = 60


def _build_prompt(raw: RawTemplate) -> str:
    template = PROMPT_PATH.read_text()

    context_block = ""
    if raw.kym:
        context_block = f"**Know Your Meme description:**\n{raw.kym.about}"
        if raw.kym.origin:
            context_block += f"\n\n**Origin:**\n{raw.kym.origin}"
        if raw.kym.spread:
            context_block += f"\n\n**Spread/usage:**\n{raw.kym.spread}"

    return (
        template.replace("{{name}}", raw.imgflip.name)
        .replace("{{box_count}}", str(raw.imgflip.box_count))
        .replace("{{context_block}}", context_block)
    )


def _parse_response(text: str) -> EnrichedFields:
    # Strip markdown code fences if present
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)
    else:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)

    data = json.loads(text)
    return EnrichedFields(**data)


def _call_ollama(prompt: str, config: EnricherConfig) -> str:
    response = httpx.post(
        f"{config.ollama_url}/api/chat",
        json={
            "model": config.model,
            "messages": [{"role": "user", "content": prompt}],
            "format": "json",
            "stream": False,
        },
        timeout=config.timeout_seconds,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def _call_claude(prompt: str, config: EnricherConfig) -> str:
    args = ["claude", "-p", prompt]
    if config.model:
        args += ["--model", config.model]
    result = subprocess.run(args, capture_output=True, text=True, timeout=config.timeout_seconds)
    if result.returncode != 0:
        raise RuntimeError(f"claude -p failed: {result.stderr.strip()}")
    return result.stdout


def enrich(raw: RawTemplate, config: EnricherConfig) -> EnrichedTemplate:
    prompt = _build_prompt(raw)

    if config.backend == "ollama":
        text = _call_ollama(prompt, config)
    else:
        text = _call_claude(prompt, config)

    fields = _parse_response(text)

    # Validate box_labels length matches box_count
    if len(fields.box_labels) != raw.imgflip.box_count:
        fields.box_labels = _fix_box_labels(fields.box_labels, raw.imgflip.box_count)

    return EnrichedTemplate(
        id=raw.imgflip.id,
        name=raw.imgflip.name,
        description=fields.description,
        caption_pattern=fields.caption_pattern,
        box_labels=fields.box_labels,
        tags=fields.tags,
        box_count=raw.imgflip.box_count,
        image_url=raw.imgflip.url,
        enriched_at=datetime.now(timezone.utc),
        enrichment_model=f"{config.backend}/{config.model}",
    )


def _fix_box_labels(labels: list[str], expected: int) -> list[str]:
    """Pad or truncate box_labels to match expected box count."""
    if len(labels) < expected:
        labels = labels + [f"box {i + 1}" for i in range(len(labels), expected)]
    return labels[:expected]
