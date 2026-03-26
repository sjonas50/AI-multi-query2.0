# AI Multi-Query: Multi-LLM Comparison Platform

A full-stack platform for querying, comparing, and analyzing responses from multiple LLM providers side-by-side. Includes a Next.js web frontend with real-time streaming, cross-provider comparison powered by Claude Opus, and follow-up conversations.

## Supported Providers

| Provider | Model | Web Search | Deep Research |
|----------|-------|------------|---------------|
| **OpenAI** | gpt-5.2 | Responses API | - |
| **Anthropic** | claude-sonnet-4-6 | - | - |
| **Google Gemini** | gemini-2.5-flash | Google Search tool | Interactions API |
| **Perplexity** | sonar-pro | Always on | sonar-deep-research |
| **Grok (xAI)** | grok-4 | Responses API | - |
| **Google Search** | Custom Search API | N/A | N/A |

## Quick Start

### 1. Install dependencies

```bash
# Backend
pip3 install -r requirements.txt

# Frontend
cd frontend && npm install
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run the web app

```bash
# Terminal 1: Backend (FastAPI)
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend (Next.js)
cd frontend && npm run dev
```

Open http://localhost:3000 and log in with your `AUTH_SECRET` password.

## Web App Features

### Multi-Provider Query (`/query`)
- Submit a query to all configured providers simultaneously
- Real-time token streaming as responses generate
- Provider status updates (searching the web, generating response, deep research progress)
- Web search and deep research toggles per query
- Automatic retry with exponential backoff on transient failures

### Cross-Provider Comparison
- Auto-triggered after all providers respond
- Powered by Claude Opus 4.6
- AI-generated narrative summary focused on key differences
- Claims matrix showing agreement/disagreement across providers
- Provider rankings (completeness, accuracy, sourcing)
- Pick-two diff view for side-by-side claim comparison

### Follow-Up Conversations
- Multi-turn conversations with context preserved across rounds
- Conversation history passed to all providers (messages array for Chat APIs, context prefix for web search APIs)
- Thread layout showing all turns in sequence

### Suggested Follow-Up Questions
- AI-generated follow-up suggestions after each query completes
- Clickable pills to trigger follow-up with one click
- Powered by gpt-4o-mini for fast generation

### Inline Citations & Sources
- Automatic URL extraction from provider responses
- Collapsible sources panel with favicons and numbered references
- Supports markdown links, bare URLs, and Perplexity-style markers

### Export
- Export results as JSON or CSV
- Includes cross-provider comparison data (summary, claims, rankings)

### Other Features
- Saved searches with pinning and collections
- Result history browser with search
- AISEO analysis mode (companies mentioned, authority signals, optimization insights)
- Settings page for provider configuration
- Dark mode support

## Architecture

```
AI-multi-query/
├── backend/                  # FastAPI backend
│   ├── main.py              # App entry, CORS, auth
│   ├── config.py            # Environment config
│   ├── auth.py              # JWT auth + rate limiting
│   ├── routers/
│   │   ├── queries.py       # SSE streaming, retry, cancellation
│   │   ├── providers.py     # Provider listing + health checks
│   │   ├── comparisons.py   # Cross-provider comparison endpoint
│   │   ├── results.py       # Saved results browser
│   │   ├── collections.py   # Saved searches + pinning
│   │   └── analysis.py      # AISEO analysis
│   ├── services/
│   │   ├── query_service.py       # Provider streaming + test methods
│   │   ├── comparison_service.py  # Claude Opus comparison analysis
│   │   ├── conversation_service.py # Multi-turn conversation state
│   │   ├── suggestions_service.py  # Follow-up question generation
│   │   ├── collections_service.py  # Saved search persistence
│   │   └── analysis_service.py     # AISEO response analysis
│   ├── lib/                       # AISEO analysis library
│   │   ├── analyzer.py            # AI-powered response analysis
│   │   ├── tracker.py             # Historical tracking (SQLite)
│   │   ├── reporter.py            # Weekly report generation
│   │   ├── domain_classifier.py   # Domain classification
│   │   └── negative_detector.py   # Negative signal detection
│   └── models/
│       └── schemas.py       # Pydantic request/response models
├── frontend/                 # Next.js 14 frontend
│   └── src/
│       ├── app/             # Pages (query, results, settings, etc.)
│       ├── components/      # UI components
│       │   ├── query/       # QueryForm, FollowUpInput, SuggestedQuestions
│       │   ├── results/     # ProviderCard, ComparisonPanel, SourcesPanel
│       │   └── layout/      # Sidebar, AuthProvider
│       ├── hooks/           # useQueryExecution, useComparison, etc.
│       └── lib/             # API client, SSE, types, citations, export
└── .env.example             # Template environment config
```

### Key Design Decisions

- **Direct API calls**: Frontend calls backend at `localhost:8000` directly (not through Next.js proxy) to avoid SSE buffering and proxy timeouts on long-running LLM calls
- **SSE streaming**: Server-Sent Events with `provider_token`, `provider_thinking`, and `provider_status` event types for real-time UI updates
- **Thread-to-async bridging**: Provider API calls run in thread executor; use `loop.call_soon_threadsafe(queue.put_nowait, ...)` to push SSE events from sync threads to the async queue
- **In-memory state**: Query results, conversations, and collections stored in-memory with TTL cleanup (no database required for the web app)
- **Conversation context**: OpenAI/Anthropic/Perplexity use native messages arrays; Google/web search paths get context prepended as text

## Configuration

### Environment Variables

See `.env.example` for all options. Key settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `PERPLEXITY_API_KEY` | Perplexity API key | - |
| `GOOGLE_API_KEY` | Google Gemini API key | - |
| `XAI_API_KEY` | xAI Grok API key | - |
| `GOOGLE_SEARCH_API_KEY` | Google Custom Search API key | - |
| `GOOGLE_SEARCH_CX` | Custom Search Engine ID | - |
| `AUTH_SECRET` | Frontend login password | `change-me` |
| `JWT_SECRET` | JWT signing secret | `change-me` |
| `MAX_TOKENS` | Max tokens per response | `4000` |
| `*_WEB_SEARCH` | Enable web search per provider | `false` |
| `*_DEEP_RESEARCH` | Enable deep research per provider | `false` |

### Provider API Key Sources

- **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Anthropic**: [console.anthropic.com](https://console.anthropic.com)
- **Perplexity**: [perplexity.ai/settings/api](https://perplexity.ai/settings/api)
- **Google Gemini**: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- **xAI Grok**: [console.x.ai](https://console.x.ai)
- **Google Search**: [Google Cloud Console](https://console.cloud.google.com/apis/credentials) + [Programmable Search Engine](https://programmablesearchengine.google.com)

## License

MIT
