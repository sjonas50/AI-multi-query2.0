# Multi-LLM Query Tool with AI-Powered AISEO Analysis

A unified interface for testing and comparing responses from multiple Large Language Model providers (OpenAI, Anthropic, Perplexity, and Google Gemini) with optional enterprise-grade AI optimization intelligence.

## 🚀 Enhanced with Fisher Investments-Level AI Intelligence

This tool now includes **sophisticated AI optimization tracking** matching enterprise-level AISEO strategies. All enhanced features are **100% backward compatible** and **opt-in**.

## Quick Start

### Standard Usage (Original Functionality)
```bash
# Clone the repository
git clone <repository-url>
cd AI-multi-query

# Install dependencies
pip3 install -r requirements.txt

# Run with interactive mode
python3 run.py

# Or run all standard questions
python3 run.py --batch

# Or run a specific query
python3 run.py --query "What are the best ETFs?"
```

### Enhanced Analysis Mode (New!)
```bash

# Run batch with enhanced analysis AND request sources from LLMs - Add additional queries to questions.txt
python3 run.py --batch --enhanced-analysis --track-history --request-sources

# Run batch from a specific file with enhanced analysis
python3 run.py --batch --enhanced-analysis --track-history --file custom_questions.txt

# Interactive selection with enhanced analysis
python3 run.py --select --enhanced-analysis --track-history --request-sources

# Generate weekly Fisher-style report after collecting data
python3 run.py --enhanced-analysis --weekly-report

# View historical trends
python3 run.py --show-trends
```

### Enhanced Features Include:
- **URL Extraction**: Comprehensive extraction of all URLs and domains from AI responses
- **Source Citation Requests**: Option to ask LLMs to cite their sources (`--request-sources`)
- **Domain Classification**: Categorizes sources (UGC, owned, authority, competitor)
- **Negative Signal Detection**: Identifies criticism patterns and sentiment
- **Accuracy Verification**: Flags factual errors and misattributions
- **Historical Tracking**: SQLite database for trend analysis
- **Weekly Reports**: Fisher Investments-style reports with WoW changes
- **UGC Monitoring**: Tracks Reddit, Yelp, and platform-specific growth

📖 See [ENHANCED_FEATURES.md](ENHANCED_FEATURES.md) for complete documentation of enhanced capabilities.

## Features

- Test multiple LLM providers with a single prompt
- Compare responses side-by-side
- Automatic dependency checking
- Detailed error reporting
- JSON output for further analysis
- Support for custom model configurations
- **Multiple Query Modes** (run.py):
  - Interactive single query mode
  - Command-line query mode
  - Batch processing for multiple questions
  - Interactive selection from question list
  - Custom questions file support
- **Organized Results**:
  - Results saved in dedicated `results/` directory
  - Descriptive filenames based on query content
  - Batch summaries for multi-query runs
- **AI-Powered Response Analysis** (run.py only):
  - Analyzes LLM responses for AISEO optimization insights
  - Extracts companies mentioned and reasons why
  - Identifies authority signals and key features
  - Enhanced source citation extraction
  - Provides actionable optimization recommendations
  - Saves analysis to CSV for pattern tracking over time

## Supported Providers

- **OpenAI** (GPT-4, GPT-4 Turbo, GPT-3.5, etc.)
- **Anthropic** (Claude 3.5 Sonnet, Claude 3 Opus, etc.)
- **Google** (Gemini 2.5 Flash, Gemini Pro, etc.)
- **Perplexity** (Sonar models with online search)
- **Google Search** (Web search API returning top 10 results)

## Script Options

### query.py - Basic Testing
- Original multi-LLM testing script
- Tests all configured providers
- Saves results to JSON
- No analysis features

### run.py - Testing with AI Analysis
- Identical to query.py PLUS:
- AI-powered response analysis
- AISEO optimization insights
- CSV export for pattern tracking
- Requires OpenAI API key for analysis

## Prerequisites

- Python 3.7 or higher (use `python3` command)
- pip3 (Python 3 package installer)
- API keys for the providers you want to use

## Installation

1. Clone this repository or download the script:
```bash
git clone <repository-url>
cd AI-multi-query
```

2. Install required dependencies using pip3:
```bash
pip3 install -r requirements.txt
```

Or install manually:
```bash
# Core dependencies (with minimum versions to avoid compatibility issues)
pip3 install "openai>=1.0.0" "anthropic>=0.64.0" "python-dotenv>=1.0.0" "requests>=2.31.0"

# Google client (required for Gemini models):
pip3 install "google-genai>=1.0.0"
```

**Important Version Notes:**
- `anthropic` must be version 0.64.0 or higher to avoid httpx compatibility issues
- `openai` must be version 1.0.0 or higher for the new client API
- The script automatically detects which Google library is installed and uses the appropriate one

## Configuration

1. The script will automatically create a `.env` template file on first run, or you can create it manually:

```bash
# .env file
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
PERPLEXITY_API_KEY=pplx-your-perplexity-key-here
GOOGLE_API_KEY=your-google-key-here

# Optional: Model configurations (defaults shown)
OPENAI_MODEL=gpt-4.1
ANTHROPIC_MODEL=claude-sonnet-4-20250514
PERPLEXITY_MODEL=llama-3.1-sonar-small-128k-online
GOOGLE_MODEL=gemini-2.5-flash  # Latest Gemini model

# Optional: Settings
MAX_TOKENS=4000  # Maximum tokens for LLM responses
TEMPERATURE=0.7
REQUEST_TIMEOUT=30

# Google Custom Search API (for web search)
GOOGLE_SEARCH_API_KEY=your-google-search-api-key-here
GOOGLE_SEARCH_CX=your-custom-search-engine-id-here

# AI Analysis Settings (for run.py only)
ANALYZE_RESPONSES=true  # Enable AI-powered analysis
ANALYSIS_MODEL=gpt-4.1  # Uses your OpenAI API key
ANALYSIS_CSV_PATH=analysis_results.csv  # Where to save insights
```

2. Replace the placeholder keys with your actual API keys:
   - **OpenAI**: Get your key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - **Anthropic**: Get your key from [console.anthropic.com](https://console.anthropic.com)
   - **Perplexity**: Get your key from [perplexity.ai/settings/api](https://perplexity.ai/settings/api)
   - **Google Gemini**: Get your key from [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
   - **Google Search**: 
     - Get API key from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
     - Create Custom Search Engine at [programmablesearchengine.google.com](https://programmablesearchengine.google.com)
     - Enable "Search the entire web" option in your search engine settings
     - Copy your Search Engine ID (cx parameter)

## Usage

### Basic Testing (query.py)
Run the script using python3:
```bash
python3 query.py
```

### Enhanced Testing with Multiple Query Modes (run.py)

The `run.py` script supports multiple ways to run queries:

#### 1. Interactive Mode (Default)
```bash
python3 run.py
# You'll be prompted to enter a query
```

#### 2. Single Query via Command Line
```bash
python3 run.py --query "What are the best ETFs for retirement?"
# Or short form:
python3 run.py -q "What are the best ETFs for retirement?"
```

#### 3. Batch Mode - Run All Questions from File
```bash
python3 run.py --batch
# Or short form:
python3 run.py -b

# Use a custom questions file:
python3 run.py --batch --file my_questions.txt
```

#### 4. Select Mode - Choose from Question List
```bash
python3 run.py --select
# Or short form:
python3 run.py -s

# Shows numbered list of questions to choose from
```

#### View Available Options
```bash
python3 run.py --help
```

**Note:** Always use `python3` to ensure you're using Python 3.x, as some systems may have Python 2.x as the default `python` command.

### Questions File Format

Create a `questions.txt` file with one question per line:
```
How to find a financial advisor?
Do I need a financial advisor?
How to choose a financial advisor?
what are the top investment advisory companies?
```

The script will automatically load questions from this file when using `--batch` or `--select` modes.

### Example Usage Scenarios

#### Running Standard Financial Advisor Questions
```bash
# Run all 6 standard questions automatically
python3 run.py --batch

# Output:
# Batch mode: Running 6 questions from questions.txt
# [1/6] Processing query...
# Query: How to find a financial advisor?
# ...results...
# [2/6] Processing query...
# Query: Do I need a financial advisor?
# ...results...
```

#### Selecting Specific Questions
```bash
python3 run.py --select

# Shows:
# Available questions:
# 1. How to find a financial advisor?
# 2. Do I need a financial advisor?
# 3. How to choose a financial advisor?
# 4. How to find a good financial advisor?
# 5. who are the top investment advisory companies?
# 6. what are the top financial advisory firms?
# 7. Run all questions
# 8. Enter custom question
# 
# Select question number (or 'q' to quit): 5
```

#### Custom Query
```bash
python3 run.py --query "What are the advantages of index funds over mutual funds?"
```

### Example Output

```
============================================================
LLM Multi-Query Script - Fixed Version
============================================================

Testing LLM APIs...

[OpenAI]
----------------------------------------
SUCCESS: Response received
Model: gpt-4o-mini
Response preview: Index funds offer several advantages...

[Anthropic]
----------------------------------------
SUCCESS: Response received
Model: claude-3-5-sonnet-20241022
Response preview: Index funds have multiple benefits...

============================================================
SUMMARY
============================================================
[OK] Successful: 4 providers
[ERROR] Failed: 0 providers

Results saved to: results/llm_results_what_are_the_advantages_of_index_funds_20250824_154732.json
```

## Output

### File Organization (run.py)

When using `run.py`, results are organized in the `results/` directory:

- **Individual Query Results**: `results/llm_results_[question_slug]_[timestamp].json`
  - Example: `results/llm_results_how_to_find_a_financial_advisor_20250824_143022.json`
  
- **Batch Summary** (when using `--batch`): `results/batch_summary_[timestamp].json`
  - Contains all queries and their results in a single file
  
- **Analysis CSV**: `analysis_results.csv` (when `ANALYZE_RESPONSES=true`)
  - Cumulative file tracking all AISEO insights over time

### Legacy Output (query.py)

The original `query.py` script saves results in the root directory:
- Format: `llm_test_results_[timestamp].json`

### JSON File Contents

Each result file contains:
- Query text
- Timestamp information
- Provider name
- Response text (if successful)
- Model used
- Error details (if failed)
- Success status
- Analysis data (run.py with ANALYZE_RESPONSES=true)

## Output Features

### LLM Responses
- Full responses up to MAX_TOKENS limit (default 4000)
- No truncation of responses
- Model information for each provider

### Google Search Results
- Returns top 10 web search results
- Each result includes:
  - Title
  - URL/Link
  - Description snippet
- Total number of search results available
- Results saved in JSON format for analysis

### AI Analysis (run.py only)
When `ANALYZE_RESPONSES=true`, the system provides:
- **Companies/Brands Mentioned**: Which entities appear in responses
- **Mention Reasons**: Why each company was referenced
- **Authority Signals**: Words like "leading", "popular", "trusted"
- **Key Features**: Important capabilities highlighted
- **AISEO Optimization Tips**: Actionable insights for improving AI visibility
- **CSV Export**: All insights saved to `analysis_results.csv` for tracking patterns

Example analysis output:
```
[OpenAI] Analysis Insights:
----------------------------------------
Companies mentioned: Jasper, Writesonic, Copy.ai, Notion AI, Rytr
Authority signals: best, top options, strengths, best for
Optimization tips: Include specific use cases, mention pricing tiers...
```

## Troubleshooting

### Common Issues

1. **"Client.__init__() got an unexpected keyword argument 'proxies'" error for Anthropic**
   - This indicates an outdated anthropic library version
   - Solution: `pip3 install --upgrade "anthropic>=0.64.0"`

2. **"cannot import name 'OpenAI' from 'openai'" error**
   - This indicates an outdated OpenAI library version
   - Solution: `pip3 install --upgrade "openai>=1.0.0"`

3. **"Project key not allowed" error for OpenAI**
   - OpenAI project keys (`sk-proj-`) may have restrictions
   - The script will use `.env` values over system environment variables
   - Check that your API key has the necessary permissions

4. **401 Authorization errors**
   - Verify your API key is correct and active
   - Check that your account has credits/active subscription
   - For Perplexity, ensure the key starts with `pplx-`

5. **Model not found errors**
   - Check that the model name in `.env` is valid
   - Default models: GPT-4.1, Claude Sonnet 4, Gemini 2.5 Flash

6. **Environment variable conflicts**
   - The script uses `load_dotenv(override=True)` to prioritize `.env` values
   - If you have system environment variables set, they will be overridden by `.env`

7. **Google Search API errors**
   - Verify Custom Search JSON API is enabled in Google Cloud Console
   - Check that your Custom Search Engine ID (cx) is correct
   - Ensure "Search the entire web" is enabled in search engine settings
   - Daily quota limit is typically 100 searches for free tier

8. **Truncated LLM responses**
   - Adjust MAX_TOKENS in .env file (default 4000)
   - Some models have maximum limits (e.g., GPT-3.5 is 4096 tokens total)

## Advanced Configuration

### Custom Models

Edit the `.env` file to use different models:

```bash
# High-performance models
OPENAI_MODEL=gpt-4-turbo
ANTHROPIC_MODEL=claude-3-opus-20240229
GOOGLE_MODEL=gemini-1.5-pro

# Cost-effective models
OPENAI_MODEL=gpt-3.5-turbo
ANTHROPIC_MODEL=claude-3-haiku-20240307
GOOGLE_MODEL=gemini-2.5-flash

# Latest models (with new google-genai library)
GOOGLE_MODEL=gemini-2.5-flash  # Latest and most capable
```

### Selective Provider Testing

You can disable providers by not including their API keys in the `.env` file. The script will only test providers with valid API keys configured.

## License

MIT

## Contributing

Feel free to submit issues and enhancement requests!