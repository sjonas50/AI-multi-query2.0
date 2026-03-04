# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-LLM query testing project that provides a unified interface to test and compare responses from multiple Large Language Model providers (OpenAI, Anthropic, Perplexity, Google Gemini) and Google Web Search.

The project includes two main scripts:
- **query.py**: Original testing script for querying multiple LLMs
- **run.py**: Enhanced version with AI-powered response analysis for AISEO insights

## Key Commands

### Running Tests
```bash
python3 query.py  # Basic multi-LLM testing
python3 run.py    # Testing with AI-powered analysis
```

### Installing Dependencies
```bash
# Core dependencies required (use pip3 for Python 3)
pip3 install openai anthropic google-genai requests python-dotenv
```

## Architecture

### Core Components

1. **query.py** - Basic testing framework that:
   - Validates environment setup and dependencies
   - Checks API key configuration from `.env` file
   - Tests each configured LLM provider sequentially
   - Generates timestamped JSON result files
   - Provides detailed debugging output

2. **run.py** - Enhanced testing with analysis:
   - All features of query.py PLUS
   - AI-powered response analysis using GPT-4
   - Extracts companies, authority signals, and key features
   - Provides AISEO optimization insights
   - Saves analysis to CSV for pattern tracking

3. **analyzer.py** - Response analysis module:
   - Uses OpenAI API to analyze LLM responses
   - Extracts structured insights for AISEO optimization
   - Handles JSON parsing and error recovery
   - Saves results to CSV for historical tracking

### Configuration

API keys are managed through a `.env` file with the following structure:
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic Claude API key  
- `PERPLEXITY_API_KEY` - Perplexity API key
- `GOOGLE_API_KEY` - Google Gemini API key
- `GOOGLE_SEARCH_API_KEY` - Google Custom Search API key
- `GOOGLE_SEARCH_CX` - Google Custom Search Engine ID

Optional model configurations:
- `OPENAI_MODEL` (default: gpt-5.2)
- `ANTHROPIC_MODEL` (default: claude-sonnet-4-6)
- `PERPLEXITY_MODEL` (default: sonar-pro)
- `GOOGLE_MODEL` (default: gemini-2.5-flash)

Settings:
- `MAX_TOKENS` (default: 4000) - Maximum tokens for LLM responses
- `TEMPERATURE` (default: 0.7) - Sampling temperature
- `REQUEST_TIMEOUT` (default: 30) - Request timeout in seconds

AI Analysis Settings (run.py only):
- `ANALYZE_RESPONSES` (default: false) - Enable AI-powered analysis
- `ANALYSIS_MODEL` (default: gpt-5.2) - Model for analysis (uses OpenAI API)
- `ANALYSIS_CSV_PATH` (default: analysis_results.csv) - CSV output path

### Testing Flow

The `FixedLLMTester` class orchestrates testing:
1. Validates provider configuration and library availability
2. Sends test prompts to each configured provider
3. Handles API-specific request formats and error handling
4. Collects and formats responses (full text for LLMs, top 10 results for web search)
5. Saves results to timestamped JSON files

### Output

**JSON Results** (`llm_test_results_YYYYMMDD_HHMMSS.json`):
- Query text and timestamp
- Provider name
- Response text (if successful) - full response up to MAX_TOKENS limit
- For Google Search: array of search results with title, link, and snippet
- Model information (for LLM providers)
- Error details (if failed)
- Success status
- Analysis data (run.py only)

**CSV Analysis** (`analysis_results.csv` - run.py only):
- Timestamp, query, and provider
- Companies/brands mentioned
- Reasons for mentions
- Authority signals used
- Key features highlighted
- Sources cited
- Ranking factors
- Sentiment analysis
- Optimization insights for AISEO

### Key Features

1. **No Response Truncation**: Uses MAX_TOKENS environment variable (default 4000) instead of hardcoded 100 token limit
2. **Google Web Search**: Queries Google Custom Search API and returns top 10 results with website and description
3. **Version Detection**: Automatically detects and handles different OpenAI library versions (v0.x vs v1.x)
4. **Environment Override**: Uses `load_dotenv(override=True)` to prioritize .env values over system variables
5. **Multiple Google Libraries**: Supports both new `google.genai` and legacy `google.generativeai` libraries
6. **AI Response Analysis** (run.py only): Analyzes LLM responses (OpenAI, Anthropic, Google Gemini) for AISEO insights
   - NOTE: Google Search results are NOT analyzed - only LLM-generated responses
   - Extracts companies mentioned, authority signals, and optimization insights
   - Saves analysis to CSV for pattern tracking over time
   - Uses GPT-4 to analyze responses and extract structured insights
   - Provides actionable recommendations for AI search optimization