"""Cross-provider comparison service using Claude Opus 4.6."""

import json
import re
from datetime import datetime

from backend.config import API_KEYS, HAS_ANTHROPIC

_COMPARISON_MODEL = "claude-opus-4-6"

_SYSTEM_PROMPT = (
    "You are an expert AI response analyst. You compare responses from multiple AI providers "
    "to the same query, identifying key differences, strengths, gaps, agreements, and disagreements. "
    "Focus especially on where providers diverge — conflicting facts, different recommendations, "
    "and unique insights only one provider mentions. You always return valid JSON."
)

_MAX_RESPONSE_CHARS = 6000


def _build_prompt(query: str, responses: dict[str, str]) -> str:
    providers = list(responses.keys())
    provider_list = ", ".join(providers)

    sections = ""
    for provider, text in responses.items():
        truncated = text[:_MAX_RESPONSE_CHARS]
        if len(text) > _MAX_RESPONSE_CHARS:
            truncated += "\n... [truncated]"
        sections += f"\n\n### {provider}\n{truncated}"

    # Build the providers JSON fragment for the schema example
    prov_example = ", ".join(f'"{p}": "agrees|disagrees|not_mentioned|partially"' for p in providers)
    detail_example = ", ".join(f'"{p}": "brief excerpt..."' for p in providers)
    ranking_example = ",\n    ".join(
        f'"{p}": {{"completeness": 8, "accuracy_signals": 7, "sourcing": 9, "unique_value": "one sentence"}}'
        for p in providers
    )

    return f"""Compare the following AI responses to the same query. Providers: {provider_list}.

## Original Query
{query}

## Provider Responses
{sections}

## Your Task

Analyze and compare these responses, with a strong focus on **key differences** between the providers. Return a JSON object with EXACTLY these keys:

{{
  "summary": "A 3-5 paragraph markdown narrative comparing the responses. Structure it as: (1) **Key Differences** — where providers disagree or give conflicting information (this should be the main focus). (2) **Agreement** — what all providers agree on. (3) **Unique Insights** — valuable information only one provider mentions. (4) **Verdict** — which response is most useful and why. Use provider names explicitly, be specific with examples from the text, and use markdown formatting.",

  "claims": [
    {{
      "claim": "A specific fact, claim, recommendation, or topic from any response",
      "category": "fact|recommendation|entity|statistic|opinion|caveat",
      "providers": {{ {prov_example} }},
      "details": {{ {detail_example} }}
    }}
  ],

  "provider_rankings": {{
    {ranking_example}
  }}
}}

RULES:
- Extract 10-25 claims representing the most significant facts, recommendations, and topics.
- PRIORITIZE claims where providers disagree or give different information — these are the most valuable.
- Every provider MUST appear in every claim's "providers" and "details" dicts.
- Every provider MUST have an entry in "provider_rankings".
- Use "not_mentioned" and empty string for providers that don't address a claim.
- The summary should lead with differences and be specific — quote or paraphrase actual content, don't just say "Provider X was more detailed"."""


def _parse_json(text: str) -> dict:
    """Parse JSON from the model response, handling markdown code blocks."""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]

    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fix trailing commas
        fixed = re.sub(r",\s*}", "}", text)
        fixed = re.sub(r",\s*]", "]", fixed)
        return json.loads(fixed)


def generate_comparison(query: str, responses: dict[str, str]) -> dict:
    """Send all provider responses to Claude Opus 4.6 and return structured comparison."""
    import anthropic
    import httpx

    client = anthropic.Anthropic(
        api_key=API_KEYS["anthropic"],
        timeout=httpx.Timeout(120.0, connect=10.0),
    )
    prompt = _build_prompt(query, responses)

    response = client.messages.create(
        model=_COMPARISON_MODEL,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=8000,
        temperature=0.3,
    )

    # Extract text from content blocks
    text = ""
    for block in response.content:
        if hasattr(block, "text") and block.text:
            text += block.text

    result = _parse_json(text)
    result["generated_at"] = datetime.now().isoformat()
    result["model_used"] = _COMPARISON_MODEL
    return result
