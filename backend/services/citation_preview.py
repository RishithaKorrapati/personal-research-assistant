"""
Build human-readable citation previews for UI (and exports).

PDF text is often fused (missing spaces) or mid-line truncated; raw chunks look bad
in the chat. We normalize heuristically and optionally ask gpt-4o-mini for one-line
labels grounded in each excerpt.
"""

import json
import os
import re
from typing import Dict, List, Optional

from .llm import _openai

_MAX_CHARS_HEURISTIC = 240
_MAX_INPUT_LLM = 900


def _heuristic_preview(raw: str, max_chars: int = _MAX_CHARS_HEURISTIC) -> str:
    t = raw.replace("\n", " ").strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"([a-z])([A-Z])", r"\1 \2", t)
    t = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", t)
    t = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", t)
    t = re.sub(r"([\w,])([\[\(])", r"\1 \2", t)
    t = re.sub(r"\s+", " ", t).strip()
    if len(t) <= max_chars:
        return t
    cut = t[:max_chars]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut + "…"


def _llm_preview_labels(texts: List[str]) -> Optional[List[str]]:
    if not texts:
        return []
    use = os.getenv("CITATION_PREVIEW_USE_LLM", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    if not use:
        return None

    blocks = []
    for i, t in enumerate(texts, start=1):
        snippet = t[:_MAX_INPUT_LLM].replace("\n", " ")
        blocks.append(f"{i}. {snippet}")

    prompt = f"""You are cleaning up PDF-extracted text for a research Q&A app.
Each numbered item below is a noisy excerpt (missing spaces, line breaks, or cut mid-sentence).

For EVERY item, write ONE short, readable English sentence (max 30 words) that tells a human what that passage is about or what topic it touches. Paraphrase; do not copy garbled tokens. If it is mostly references or bibliography, say something like "Bibliography and related work on …" using any clear keywords.

Return ONLY valid JSON with this exact shape:
{{"previews": ["sentence for item 1", "sentence for item 2", ...]}}

There must be exactly {len(texts)} strings in "previews", in order.

---
{chr(10).join(blocks)}
"""

    response = _openai().chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=400,
    )
    raw = (response.choices[0].message.content or "").strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        data = json.loads(raw)
        previews = data.get("previews", [])
    except json.JSONDecodeError:
        return None
    if not isinstance(previews, list) or len(previews) != len(texts):
        return None
    out = []
    for p in previews:
        if not isinstance(p, str):
            return None
        s = " ".join(p.split())
        if len(s) > 320:
            s = s[:317] + "…"
        out.append(s)
    return out


def attach_citation_previews(chunks: List[Dict]) -> None:
    """Mutates each chunk dict with key ``preview`` (readable excerpt)."""
    texts = [c["text"] for c in chunks]
    for c in chunks:
        c["preview"] = _heuristic_preview(c["text"])

    polished = _llm_preview_labels(texts)
    if polished:
        for c, p in zip(chunks, polished, strict=True):
            if p:
                c["preview"] = p
