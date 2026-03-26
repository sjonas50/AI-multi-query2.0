# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A full-stack multi-LLM comparison platform (FastAPI backend + Next.js frontend) deployed on Railway. Queries multiple LLM providers (OpenAI, Anthropic, Perplexity, Google Gemini, Grok/xAI) and Google Web Search, with real-time streaming, cross-provider comparison, and optional AISEO analysis.

## Key Commands

### Running Locally
```bash
# Backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend && npm run dev
```

### Installing Dependencies
```bash
pip3 install -r requirements.txt
cd frontend && npm install
```

## Architecture

### Backend (`backend/`)

- **main.py** — FastAPI app entry point, CORS, router registration
- **config.py** — Loads `.env`, API keys, model defaults, database paths
- **auth.py** — JWT authentication, rate limiting, admin/user roles
- **routers/** — API endpoints (queries, providers, results, analysis, collections, comparisons, reports, admin, aiseo)
- **services/** — Business logic
  - `query_service.py` — LLM provider querying with SSE streaming (supports OpenAI, Anthropic, Perplexity, Google, xAI, Google Search)
  - `analysis_service.py` — Wraps library modules for AISEO analysis
  - `company_config_service.py` — AISEO company/competitor config (SQLite)
  - `comparison_service.py` — Cross-provider comparison via Claude Opus
  - `conversation_service.py` — Multi-turn conversation state
  - `suggestions_service.py` — Follow-up question generation
  - `user_service.py` — User management and auth
  - `collections_service.py` — Saved searches and collections
  - `results_service.py` — Query result retrieval
- **lib/** — AISEO analysis library modules
  - `analyzer.py` — ResponseAnalyzer: AI-powered response analysis using OpenAI
  - `tracker.py` — HistoricalTracker: SQLite-based historical trend tracking
  - `reporter.py` — WeeklyReporter: generates weekly AISEO reports
  - `domain_classifier.py` — Classifies cited domains (owned, competitor, UGC, authority)
  - `negative_detector.py` — Detects negative signals and sentiment

### Frontend (`frontend/`)

Next.js app with React, TypeScript, Tailwind, and shadcn/ui components. Key pages: query, results, analysis, settings, admin.

### Configuration

API keys are managed through `.env` (see `.env.example`):
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `PERPLEXITY_API_KEY`, `GOOGLE_API_KEY`, `XAI_API_KEY`
- `GOOGLE_SEARCH_API_KEY` + `GOOGLE_SEARCH_CX`
- Model overrides: `OPENAI_MODEL` (gpt-5.2), `ANTHROPIC_MODEL` (claude-sonnet-4-6), etc.
- `MAX_TOKENS` (8000), `TEMPERATURE` (0.7), `REQUEST_TIMEOUT` (30)
- `JWT_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`
- `DATA_DIR` — persistent storage directory (SQLite databases)

### Deployment

Deployed on Railway with two services:
- **Backend** — `Dockerfile.backend`, uses `$PORT` env var, persistent volume at `/app/data`
- **Frontend** — `Dockerfile.frontend`, `NEXT_PUBLIC_API_URL` set to backend URL
- `docker-compose.yml` + `nginx.conf` available for local Docker deployment

### Data Storage

All persistent data in `DATA_DIR` (default: `data/`):
- `users.db` — accounts, invite codes
- `company_config.db` — AISEO settings, competitors, accuracy facts
- `tracking.db` — query history, analysis results, competitor mentions
- `collections.db` — saved searches
- `results/` — JSON query result files
- `reports/` — generated weekly reports
