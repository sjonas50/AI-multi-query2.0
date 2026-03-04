"""In-memory conversation state for multi-turn follow-up queries."""

import time
import uuid
from dataclasses import dataclass, field

_TTL_SECONDS = 7200  # 2 hours

@dataclass
class ConversationTurn:
    query: str
    responses: dict[str, str]  # provider_name → response_text


@dataclass
class ConversationState:
    id: str
    turns: list[ConversationTurn] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


_conversations: dict[str, ConversationState] = {}


def create_conversation() -> str:
    """Create a new conversation and return its ID."""
    conv_id = str(uuid.uuid4())
    _conversations[conv_id] = ConversationState(id=conv_id)
    return conv_id


def add_turn(conv_id: str, query: str, responses: dict[str, str]) -> None:
    """Append a Q&A round to an existing conversation."""
    conv = _conversations.get(conv_id)
    if not conv:
        return
    conv.turns.append(ConversationTurn(query=query, responses=responses))
    conv.updated_at = time.time()


def get_conversation(conv_id: str) -> ConversationState | None:
    return _conversations.get(conv_id)


def build_messages_for_openai(conv_id: str, new_query: str) -> list[dict]:
    """Build OpenAI-style messages array with conversation history."""
    conv = _conversations.get(conv_id)
    if not conv or not conv.turns:
        return [{"role": "user", "content": new_query}]

    messages = []
    for turn in conv.turns[-5:]:  # Last 5 turns to stay within context limits
        messages.append({"role": "user", "content": turn.query})
        # Use the first available response as the assistant reply
        if turn.responses:
            first_response = next(iter(turn.responses.values()))
            # Truncate long responses to keep context manageable
            if len(first_response) > 3000:
                first_response = first_response[:3000] + "\n\n[Response truncated for context...]"
            messages.append({"role": "assistant", "content": first_response})
    messages.append({"role": "user", "content": new_query})
    return messages


def build_context_prefix(conv_id: str, new_query: str) -> str:
    """Build a text prefix with conversation context for providers that don't support messages."""
    conv = _conversations.get(conv_id)
    if not conv or not conv.turns:
        return new_query

    parts = ["Previous conversation:\n"]
    for turn in conv.turns[-3:]:  # Last 3 turns
        parts.append(f"User: {turn.query}")
        if turn.responses:
            first_response = next(iter(turn.responses.values()))
            if len(first_response) > 2000:
                first_response = first_response[:2000] + "..."
            parts.append(f"Assistant: {first_response}")
        parts.append("")

    parts.append(f"Now answer this follow-up question:\n{new_query}")
    return "\n".join(parts)


def cleanup_expired() -> None:
    """Remove conversations older than TTL."""
    now = time.time()
    expired = [cid for cid, c in _conversations.items() if now - c.updated_at > _TTL_SECONDS]
    for cid in expired:
        del _conversations[cid]
