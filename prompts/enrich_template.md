You are an expert in internet meme culture and semantic information retrieval. Your task is to generate structured metadata for a meme template that will power a local meme-finder application.

## Template Information

**Name:** {{name}}
**Text boxes:** {{box_count}}

{{context_block}}

---

## Your Task

Generate metadata for this template. The metadata serves two purposes:

1. **Semantic search** — When a user describes a real-life situation (e.g., "my manager keeps scheduling unnecessary meetings"), the `description` field must help a cosine-similarity search surface this template. Write for retrieval, not for humans.

2. **Caption generation** — The `caption_pattern` and `box_labels` fields guide an LLM to fill each text box correctly. Be explicit about order and what each slot means.

## Output

Return a JSON object with exactly these six fields:

```json
{
  "description": "...",
  "caption_pattern": "...",
  "box_labels": ["...", "..."],
  "tags": ["...", "..."],
  "tone": "...",
  "notes": "..."
}
```

---

## Field Guidelines

### `description`
One to two sentences. Describe the **emotional or social situation** this meme captures — not its visual appearance.

Ask yourself: "When someone is living through this moment and wants a meme, what are they feeling or experiencing?"

Rules:
- Situational, not visual. Never describe what the image looks like.
- Use active language. Start with a verb or scenario.
- Include the emotional register: sarcasm, pride, exhaustion, disbelief, etc.
- Concrete enough to match natural language. Someone typing "my boss said X but did Y" should match a hypocrisy meme.

**Bad:** "A meme featuring Drake where he rejects one option and approves another."
**Good:** "Dismissing a conventional or expected option in favor of something more honest, lazy, clever, or self-aware. Used when you want to highlight a clear personal preference — especially when the chosen alternative feels more relatable than the 'proper' answer."

---

### `caption_pattern`
Explicit instructions for filling each text box, in order. Name each box. Describe what kind of content fits.

Rules:
- Reference boxes by position AND purpose: "Top panel (rejected):", "Center figure (the distracted person):"
- Describe the relationship between boxes, not just each in isolation
- Mention if there's a polarity (approved vs rejected, then vs now, expectation vs reality)
- One sentence per box

**Bad:** "Top and bottom text."
**Good:** "Top panel (rejected): The thing being dismissed — usually the conventional, expected, or 'correct' approach. Bottom panel (approved): The preferred alternative — often funnier, lazier, or more honest than what you 'should' choose."

---

### `box_labels`
Short labels (1–4 words each) for each box, in the exact order they appear in the meme image. These appear in the UI and are passed directly to the caption-generation LLM.

**IMPORTANT — verify the box count yourself.** The box count provided above comes from Imgflip and is sometimes wrong. Common failure: the template image has text baked in (e.g. "0 DAYS WITHOUT" with the 0 already printed, "Marked safe from ___" with the frame pre-filled) but Imgflip still counts it as a fillable box. Only list boxes the user actually fills. The final box count will be `len(box_labels)` — your label list is the source of truth.

Examples:
- `["rejected option", "approved option"]`
- `["boyfriend", "girlfriend", "distraction"]`
- `["expectation", "reality"]`
- `["them", "me", "what i said", "what i meant"]`

---

### `tags`
5–10 lowercase keywords. Include a mix of:
- **Emotions:** frustration, pride, relief, anxiety, jealousy
- **Situations:** comparison, preference, irony, betrayal, decision, escalation
- **Cultural shorthand:** upgrade, side-eye, big brain, cope, skill issue
- **Synonyms:** multiple ways a user might describe the same scenario

Good tag coverage means "choosing between" and "indecision" and "impossible choice" all hit the same template.

---

### `tone`
One word for the meme's dominant register: `humorous`, `ironic`, `sarcastic`, `absurdist`, `sincere`, `self-deprecating`, or `passive-aggressive`.

Memes are primarily used to be funny — but the *kind* of funny matters for caption generation. "This Is Fine" is ironic cope; "Disaster Girl" is smug dark humor; "Epic Handshake" can be used sincerely. If a meme has both a sincere and an ironic usage, pick the one that dominates in the wild today (ironic usually wins).

---

### `notes`
One to three sentences of caption-writer guidance that doesn't fit the other fields:
- Text baked into the image (things the user must NOT re-supply)
- Panels that intentionally stay blank (e.g. Anakin's silent smile panel IS the punchline — adding text breaks it)
- Common misuse to avoid
- Whether a box is almost always a fixed phrase (e.g. box 2 of "Always Has Been" is nearly always just "Always has been.")

---

Return only the JSON object. No preamble or explanation outside the JSON.
