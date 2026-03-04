"""Generate follow-up question suggestions using a fast LLM call."""

import json

from backend.config import API_KEYS, HAS_OPENAI

_MAX_RESPONSE_LEN = 2000


def generate_suggestions(query: str, responses: dict[str, str]) -> list[str]:
    """Generate 3-4 follow-up questions based on the query and provider responses."""
    if not HAS_OPENAI or not API_KEYS.get("openai"):
        return []

    try:
        from openai import OpenAI
        client = OpenAI(api_key=API_KEYS["openai"])

        # Build context from responses (truncated)
        response_summaries = []
        for provider, text in responses.items():
            truncated = text[:_MAX_RESPONSE_LEN]
            if len(text) > _MAX_RESPONSE_LEN:
                truncated += "..."
            response_summaries.append(f"[{provider}]: {truncated}")

        prompt = f"""Given this query and the AI responses below, suggest 3-4 natural follow-up questions the user might want to ask next. Questions should explore different angles, dig deeper, or clarify interesting points from the responses.

Query: {query}

Responses:
{chr(10).join(response_summaries)}

Return a JSON array of question strings only. Example: ["What are the main advantages?", "How does this compare to X?"]"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.8,
            response_format={"type": "json_object"},
            timeout=10,
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)

        # Handle both {"questions": [...]} and direct [...] formats
        if isinstance(data, list):
            return data[:4]
        if isinstance(data, dict):
            for key in ("questions", "follow_up_questions", "suggestions"):
                if key in data and isinstance(data[key], list):
                    return data[key][:4]

        return []
    except Exception:
        return []
