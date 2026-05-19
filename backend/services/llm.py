import json
import os
from typing import Dict, List, Optional

import openai

_openai_client: Optional[openai.OpenAI] = None


def _openai() -> openai.OpenAI:
    global _openai_client
    if _openai_client is None:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Copy backend/.env.example to backend/.env and add your key."
            )
        _openai_client = openai.OpenAI(api_key=key)
    return _openai_client


def answer_question(question: str, chunks: List[Dict]) -> str:
    context = ""
    for chunk in chunks:
        context += f"[Page {chunk['page']}]\n{chunk['text']}\n\n"

    prompt = f"""You are a research assistant answering questions about a research paper or technical document.

The context below is a set of non-contiguous excerpts retrieved by search. They may be partial sentences, figure captions, or references. That is normal.

Rules:
- Ground your answer in these excerpts. Do not invent facts that are clearly absent from them.
- When the question asks for a summary, the paper's purpose, or "what it is about", synthesize themes from whatever substantive phrases appear (problem, method, dataset, contributions, evaluation). References and section titles still count as evidence of topic.
- Give a helpful, good-faith answer whenever any excerpt plausibly relates to the question. It is OK if the answer is high-level or brief.
- Only say the excerpts do not address the question if nothing in them is even loosely related.
- Always cite page numbers inline like (Page 5) after the information they support.

Context:
{context}

Question: {question}

Answer:"""

    response = _openai().chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=900,
    )
    return response.choices[0].message.content or ""


def generate_summary_map(pages: List[Dict]) -> List[Dict]:
    sections = []
    group_size = 5

    for i in range(0, len(pages), group_size):
        group = pages[i : i + group_size]
        start_page = group[0]["page_num"]
        end_page = group[-1]["page_num"]
        combined_text = "\n".join([p["text"] for p in group])[:3000]

        prompt = f"""Analyze this section of a research document (pages {start_page}–{end_page}).
Return ONLY valid JSON, no markdown, no explanation:
{{
  "theme": "main topic in 3-5 words",
  "summary": "one clear sentence summarising the key point",
  "key_terms": ["term1", "term2", "term3"],
  "pages": "{start_page}-{end_page}"
}}

Document section:
{combined_text}"""

        response = _openai().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200,
        )

        raw = (response.choices[0].message.content or "").strip()
        try:
            section = json.loads(raw)
            sections.append(section)
        except json.JSONDecodeError:
            sections.append(
                {
                    "theme": f"Pages {start_page}–{end_page}",
                    "summary": "Could not generate summary for this section.",
                    "key_terms": [],
                    "pages": f"{start_page}-{end_page}",
                }
            )

    return sections
