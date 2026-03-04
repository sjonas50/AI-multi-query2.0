"""Query execution with SSE streaming, cancellation, retry, and cleanup."""

import asyncio
import json
import time
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sse_starlette.sse import EventSourceResponse

from backend.auth import get_current_user
from backend.config import CONFIGURED_PROVIDERS, ANALYZE_RESPONSES
from backend.models.schemas import QueryRequest
from backend.services.query_service import QueryService
from backend.services import conversation_service

router = APIRouter(prefix="/api/queries", tags=["queries"])

# In-memory store for active query sessions
_query_queues: dict[str, asyncio.Queue] = {}
_query_results: dict[str, dict] = {}
_query_tasks: dict[str, asyncio.Task] = {}
_query_timestamps: dict[str, float] = {}
_cancelled: set[str] = set()

# Cleanup completed queries after 30 minutes
_RESULT_TTL_SECONDS = 1800
_cleanup_task: Optional[asyncio.Task] = None


async def _periodic_cleanup():
    """Remove expired query results every 5 minutes."""
    while True:
        await asyncio.sleep(300)
        now = time.time()
        expired = [
            qid for qid, ts in _query_timestamps.items()
            if now - ts > _RESULT_TTL_SECONDS
        ]
        for qid in expired:
            _query_results.pop(qid, None)
            _query_queues.pop(qid, None)
            _query_tasks.pop(qid, None)
            _query_timestamps.pop(qid, None)
            _cancelled.discard(qid)


def _ensure_cleanup_running():
    global _cleanup_task
    if _cleanup_task is None or _cleanup_task.done():
        _cleanup_task = asyncio.create_task(_periodic_cleanup())


# Max retries for transient failures
_MAX_RETRIES = 2
_RETRY_BACKOFF = [1, 3]  # seconds


def _is_retryable(error: str) -> bool:
    """Check if an error is transient and worth retrying."""
    retryable_patterns = [
        "timeout", "timed out", "rate limit", "429", "500", "502", "503",
        "504", "overloaded", "capacity", "connection", "reset",
    ]
    error_lower = error.lower()
    return any(p in error_lower for p in retryable_patterns)


@router.post("")
async def submit_query(request: QueryRequest, _user=Depends(get_current_user)):
    """Submit a new query. Returns a query_id for SSE streaming."""
    _ensure_cleanup_running()
    conversation_service.cleanup_expired()

    query_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    _query_queues[query_id] = queue
    _query_timestamps[query_id] = time.time()

    providers = request.providers or CONFIGURED_PROVIDERS
    providers = [p for p in providers if p in CONFIGURED_PROVIDERS]

    if not providers:
        raise HTTPException(status_code=400, detail="No configured providers selected")

    # Conversation management: reuse or create
    conv_id = request.conversation_id
    if not conv_id:
        conv_id = conversation_service.create_conversation()

    task = asyncio.create_task(
        _execute_query(query_id, request.query, providers, request, queue, conv_id)
    )
    _query_tasks[query_id] = task

    return {"query_id": query_id, "providers": providers, "conversation_id": conv_id}


@router.delete("/{query_id}")
async def cancel_query(query_id: str, _user=Depends(get_current_user)):
    """Cancel a running query."""
    task = _query_tasks.get(query_id)
    if not task:
        raise HTTPException(status_code=404, detail="Query not found")
    if task.done():
        return {"status": "already_complete"}

    _cancelled.add(query_id)
    task.cancel()

    # Push a cancelled event so the SSE stream closes cleanly
    queue = _query_queues.get(query_id)
    if queue:
        await queue.put({"event": "cancelled", "data": {"query_id": query_id}})

    return {"status": "cancelled"}


async def _execute_query(
    query_id: str,
    query: str,
    providers: list[str],
    request: QueryRequest,
    queue: asyncio.Queue,
    conv_id: str = "",
):
    """Run providers in parallel with retry, push results to queue."""
    service = QueryService()
    loop = asyncio.get_event_loop()
    all_results = []

    # Build conversation context for follow-ups
    context_messages = None
    if conv_id:
        conv = conversation_service.get_conversation(conv_id)
        if conv and conv.turns:
            context_messages = conversation_service.build_messages_for_openai(conv_id, query)

    async def run_one(provider: str):
        if query_id in _cancelled:
            return

        display_name = service.get_provider_display_name(provider)
        await queue.put({"event": "provider_start", "data": {"provider": display_name}})

        # Streaming callbacks — fire from executor thread, push to async queue
        def on_token(text: str):
            if query_id not in _cancelled:
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    {"event": "provider_token", "data": {"provider": display_name, "text": text}},
                )

        def on_thinking(text: str):
            if query_id not in _cancelled:
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    {"event": "provider_thinking", "data": {"provider": display_name, "text": text}},
                )

        def on_status(message: str):
            if query_id not in _cancelled:
                loop.call_soon_threadsafe(
                    queue.put_nowait,
                    {"event": "provider_status", "data": {"provider": display_name, "message": message}},
                )

        last_error = None
        for attempt in range(_MAX_RETRIES + 1):
            if query_id in _cancelled:
                return

            try:
                start_time = time.time()
                result = await loop.run_in_executor(
                    None, service.stream_provider, provider, query,
                    request.request_sources, request.web_search, request.deep_research,
                    on_token, on_thinking, context_messages, on_status,
                )
                elapsed = round(time.time() - start_time, 2)
                result["response_time"] = elapsed
                result["response_length"] = len(str(result.get("response", "")))

                if result.get("error") and attempt < _MAX_RETRIES and _is_retryable(result["error"]):
                    last_error = result["error"]
                    await queue.put({
                        "event": "provider_retry",
                        "data": {"provider": display_name, "attempt": attempt + 1, "error": last_error},
                    })
                    await asyncio.sleep(_RETRY_BACKOFF[attempt])
                    continue

                all_results.append(result)
                await queue.put({
                    "event": "provider_complete",
                    "data": {"provider": display_name, "result": result},
                })

                # Run analysis if requested
                if request.analyze and result.get("success") and result.get("provider") != "Google Search":
                    await _run_analysis(queue, loop, result, query, display_name)

                return

            except asyncio.CancelledError:
                return
            except Exception as e:
                last_error = str(e)
                if attempt < _MAX_RETRIES and _is_retryable(last_error):
                    await queue.put({
                        "event": "provider_retry",
                        "data": {"provider": display_name, "attempt": attempt + 1, "error": last_error},
                    })
                    await asyncio.sleep(_RETRY_BACKOFF[attempt])
                    continue

                all_results.append({"provider": display_name, "error": last_error})
                await queue.put({"event": "provider_error", "data": {"provider": display_name, "error": last_error}})
                return

    try:
        tasks = [run_one(p) for p in providers]
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass

    if query_id in _cancelled:
        _cancelled.discard(query_id)
        return

    filename = service.save_results(query, all_results) if all_results else None

    # Save conversation turn for follow-ups
    if conv_id and all_results:
        responses = {}
        for r in all_results:
            if r.get("success") and isinstance(r.get("response"), str):
                responses[r["provider"]] = r["response"]
        if responses:
            conversation_service.add_turn(conv_id, query, responses)

    _query_results[query_id] = {
        "query": query,
        "results": all_results,
        "filename": filename,
    }
    _query_timestamps[query_id] = time.time()

    await queue.put({"event": "all_complete", "data": {"query_id": query_id, "filename": filename, "conversation_id": conv_id}})


async def _run_analysis(queue, loop, result, query, display_name):
    """Run AISEO analysis on a provider result."""
    await queue.put({"event": "analysis_start", "data": {"provider": display_name}})
    try:
        from backend.services.analysis_service import get_analyzer
        analyzer = get_analyzer()
        if analyzer and analyzer.analyze_enabled:
            analysis = await loop.run_in_executor(
                None, analyzer.analyze_with_ai, result["response"], query, result["provider"]
            )
            if analysis:
                result["analysis"] = analysis
                analyzer.save_to_csv(analysis)
                await queue.put(
                    {"event": "analysis_complete", "data": {"provider": display_name, "analysis": analysis}}
                )
    except Exception as e:
        await queue.put(
            {"event": "analysis_error", "data": {"provider": display_name, "error": str(e)}}
        )


@router.get("/{query_id}/stream")
async def stream_results(query_id: str, _user=Depends(get_current_user)):
    """SSE endpoint — streams provider results as they complete."""
    queue = _query_queues.get(query_id)
    if not queue:
        # Check if results already exist (reconnection case)
        if query_id in _query_results:
            async def replay_results():
                data = _query_results[query_id]
                for r in data.get("results", []):
                    yield {
                        "event": "provider_complete",
                        "data": json.dumps({"provider": r.get("provider"), "result": r}, default=str),
                    }
                yield {
                    "event": "all_complete",
                    "data": json.dumps({"query_id": query_id, "filename": data.get("filename")}, default=str),
                }
            return EventSourceResponse(replay_results())
        raise HTTPException(status_code=404, detail="Query not found or already completed")

    async def event_generator():
        try:
            while True:
                msg = await asyncio.wait_for(queue.get(), timeout=300)
                yield {"event": msg["event"], "data": json.dumps(msg["data"], default=str)}
                if msg["event"] in ("all_complete", "cancelled"):
                    break
        except asyncio.TimeoutError:
            yield {"event": "timeout", "data": json.dumps({"error": "Query timed out"})}
        finally:
            _query_queues.pop(query_id, None)

    return EventSourceResponse(event_generator())


@router.get("/{query_id}/suggestions")
async def get_suggestions(query_id: str, _user=Depends(get_current_user)):
    """Generate follow-up question suggestions for a completed query."""
    data = _query_results.get(query_id)
    if not data:
        raise HTTPException(status_code=404, detail="Query not found")

    responses = {}
    for r in data.get("results", []):
        if r.get("success") and isinstance(r.get("response"), str):
            responses[r["provider"]] = str(r["response"])[:2000]

    if len(responses) < 1:
        return {"questions": []}

    from backend.services.suggestions_service import generate_suggestions
    loop = asyncio.get_event_loop()
    questions = await loop.run_in_executor(None, generate_suggestions, data["query"], responses)
    return {"questions": questions}


@router.get("/{query_id}")
async def get_query_results(query_id: str, _user=Depends(get_current_user)):
    """Get final results for a completed query."""
    result = _query_results.get(query_id)
    if not result:
        raise HTTPException(status_code=404, detail="Query not found")
    return result
