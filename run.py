#!/usr/bin/env python3
"""
Fixed Multi-LLM Query Script
Corrected API implementations for all providers
"""

import os
import sys
import json
import time
import argparse
import re
from datetime import datetime
from analyzer import ResponseAnalyzer

# Import tracker for weekly report generation (optional)
try:
    from tracker import HistoricalTracker
    TRACKER_AVAILABLE = True
except ImportError:
    TRACKER_AVAILABLE = False

print("=" * 60)
print("LLM Multi-Query Script - Fixed Version")
print("=" * 60)
print()

# Check Python version
print(f"Python version: {sys.version}")
print()

# Check and import required libraries
def check_import(module_name, import_name=None):
    """Check if a module can be imported"""
    if import_name is None:
        import_name = module_name
    try:
        exec(f"import {import_name}")
        print(f"[OK] {module_name} is installed")
        return True
    except ImportError as e:
        print(f"[ERROR] {module_name} is NOT installed - Error: {e}")
        return False

# Check all dependencies
print("Checking dependencies...")
print("-" * 40)
has_openai = check_import("openai")
has_anthropic = check_import("anthropic")
# Check for Google libraries (try new one first, then old)
has_google = check_import("google.genai", "google.genai") or check_import("google.generativeai", "google.generativeai as genai")
has_requests = check_import("requests")
has_dotenv = check_import("python-dotenv", "dotenv")
print()

# Check for .env file
print("Checking configuration...")
print("-" * 40)
if os.path.exists(".env"):
    print("[OK] .env file found")
    
    # Try to load it
    if has_dotenv:
        from dotenv import load_dotenv
        # Force override system environment variables with .env values
        load_dotenv(override=True)
        print("[OK] .env file loaded (overriding system env)")
    else:
        print("[WARNING] Cannot load .env - python-dotenv not installed")
else:
    print("[ERROR] .env file NOT found")
    print("\nCreating template .env file...")
    
    template = """# LLM API Keys - Replace with your actual keys
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
PERPLEXITY_API_KEY=pplx-your-perplexity-key-here
GOOGLE_API_KEY=your-google-key-here

# Optional: Model configurations
OPENAI_MODEL=gpt-5.2
ANTHROPIC_MODEL=claude-sonnet-4-6
PERPLEXITY_MODEL=sonar-pro
GOOGLE_MODEL=gemini-2.5-flash
"""
    
    with open(".env", "w") as f:
        f.write(template)
    print("[OK] Created .env template file")
    print("\n[WARNING] Please edit .env with your actual API keys and run again!")
    sys.exit(1)

print()

# Check API keys
print("Checking API keys...")
print("-" * 40)
api_keys = {
    'openai': os.getenv('OPENAI_API_KEY'),
    'anthropic': os.getenv('ANTHROPIC_API_KEY'),
    'perplexity': os.getenv('PERPLEXITY_API_KEY'),
    'google': os.getenv('GOOGLE_API_KEY'),
    'google_search': os.getenv('GOOGLE_SEARCH_API_KEY'),
    'google_cx': os.getenv('GOOGLE_SEARCH_CX'),
}

configured_providers = []
for provider, key in api_keys.items():
    if provider == 'google_cx':
        # Special handling for Google CX ID
        if key and not key.startswith('your-'):
            print(f"[OK] GOOGLE_SEARCH_CX is configured (length: {len(key)})")
        else:
            print(f"[ERROR] GOOGLE_SEARCH_CX is NOT configured or is still template")
    elif key and not key.startswith('your-') and not key.startswith('sk-your') and not key.startswith('pplx-your'):
        print(f"[OK] {provider.upper().replace('_', '_')}_API_KEY is configured (length: {len(key)})")
        if provider != 'google_search':  # Don't add google_search to main providers list
            configured_providers.append(provider)
    else:
        print(f"[ERROR] {provider.upper().replace('_', '_')}_API_KEY is NOT configured or is still template")

# Check if Google Search is configured
if api_keys.get('google_search') and api_keys.get('google_cx'):
    configured_providers.append('google_search')

print()

if not configured_providers:
    print("[ERROR] No API keys configured!")
    print("\nTo fix this:")
    print("1. Edit the .env file")
    print("2. Replace the template keys with your actual API keys")
    print("3. Save the file and run this script again")
    sys.exit(1)

print(f"Configured providers: {', '.join(configured_providers)}")
print()

# Fixed LLM tester class
class FixedLLMTester:
    def __init__(self):
        self.results = []
        # Store global variables as instance variables
        self.configured_providers = configured_providers
        self.api_keys = api_keys
        self.has_openai = has_openai
        self.has_anthropic = has_anthropic
        self.has_google = has_google
        
        # Source citation settings
        self.request_sources = os.getenv('REQUEST_SOURCES', 'false').lower() == 'true'
        self.source_instruction = os.getenv('SOURCE_INSTRUCTION', 
            'Please cite your sources with specific URLs or domain names where this information can be verified.')
    
    def _enhance_prompt_with_sources(self, prompt):
        """Add source citation request to prompt if enabled"""
        if self.request_sources:
            return f"{prompt}\n\n{self.source_instruction}"
        return prompt
    
    def test_openai(self, prompt):
        """Test OpenAI API with version detection"""
        if 'openai' not in self.configured_providers or not self.has_openai:
            return {'provider': 'OpenAI', 'error': 'Not configured or library not installed'}
        
        try:
            import openai
            print("Testing OpenAI...")
            
            # Enhance prompt with source request if enabled
            enhanced_prompt = self._enhance_prompt_with_sources(prompt)
            
            # Check OpenAI library version
            openai_version = getattr(openai, '__version__', '0.0.0')
            major_version = int(openai_version.split('.')[0])
            
            if major_version >= 1:
                # New OpenAI client (v1.x)
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=self.api_keys['openai'])
                    
                    response = client.chat.completions.create(
                        model=os.getenv('OPENAI_MODEL', 'gpt-4.1'),
                        messages=[{"role": "user", "content": enhanced_prompt}],
                        max_tokens=int(os.getenv('MAX_TOKENS', 4000)),
                        temperature=0.7
                    )
                    
                    result = {
                        'provider': 'OpenAI',
                        'response': response.choices[0].message.content,
                        'model': response.model,
                        'success': True
                    }
                except ImportError:
                    # Fallback to old style if import fails
                    openai.api_key = self.api_keys['openai']
                    response = openai.ChatCompletion.create(
                        model=os.getenv('OPENAI_MODEL', 'gpt-4.1'),
                        messages=[{"role": "user", "content": enhanced_prompt}],
                        max_tokens=int(os.getenv('MAX_TOKENS', 4000)),
                        temperature=0.7
                    )
                    
                    result = {
                        'provider': 'OpenAI',
                        'response': response.choices[0].message.content,
                        'model': response.model,
                        'success': True
                    }
            else:
                # Old OpenAI library (v0.x)
                openai.api_key = self.api_keys['openai']
                response = openai.ChatCompletion.create(
                    model=os.getenv('OPENAI_MODEL', 'gpt-4.1'),
                    messages=[{"role": "user", "content": enhanced_prompt}],
                    max_tokens=int(os.getenv('MAX_TOKENS', 4000)),
                    temperature=0.7
                )
                
                result = {
                    'provider': 'OpenAI',
                    'response': response.choices[0].message.content,
                    'model': response.model,
                    'success': True
                }
            
            print(f"[OK] OpenAI responded successfully")
            return result
            
        except Exception as e:
            print(f"[ERROR] OpenAI error: {e}")
            return {'provider': 'OpenAI', 'error': str(e)}
    
    def test_anthropic(self, prompt):
        """Test Anthropic API"""
        if 'anthropic' not in self.configured_providers or not self.has_anthropic:
            return {'provider': 'Anthropic', 'error': 'Not configured or library not installed'}
        
        try:
            import anthropic
            print("Testing Anthropic...")
            
            # Enhance prompt with source request if enabled
            enhanced_prompt = self._enhance_prompt_with_sources(prompt)
            
            client = anthropic.Anthropic(api_key=self.api_keys['anthropic'])
            
            response = client.messages.create(
                model=os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514'),
                max_tokens=int(os.getenv('MAX_TOKENS', 4000)),
                messages=[{"role": "user", "content": enhanced_prompt}]
            )
            
            result = {
                'provider': 'Anthropic',
                'response': response.content[0].text,
                'model': response.model,
                'success': True
            }
            print(f"[OK] Anthropic responded successfully")
            return result
            
        except Exception as e:
            print(f"[ERROR] Anthropic error: {e}")
            return {'provider': 'Anthropic', 'error': str(e)}
    
    def test_perplexity(self, prompt):
        """Test Perplexity API with version detection"""
        if 'perplexity' not in self.configured_providers:
            return {'provider': 'Perplexity', 'error': 'Not configured'}
        
        try:
            import openai
            print("Testing Perplexity...")
            
            # Enhance prompt with source request if enabled
            enhanced_prompt = self._enhance_prompt_with_sources(prompt)
            
            # Check OpenAI library version for Perplexity (uses OpenAI-compatible API)
            openai_version = getattr(openai, '__version__', '0.0.0')
            major_version = int(openai_version.split('.')[0])
            
            if major_version >= 1:
                try:
                    # New OpenAI client (v1.x)
                    from openai import OpenAI
                    client = OpenAI(
                        api_key=self.api_keys['perplexity'],
                        base_url="https://api.perplexity.ai"
                    )
                    
                    response = client.chat.completions.create(
                        model=os.getenv('PERPLEXITY_MODEL', 'sonar-pro'),
                        messages=[{"role": "user", "content": enhanced_prompt}],
                        max_tokens=int(os.getenv('MAX_TOKENS', 1000))
                    )
                    
                    result = {
                        'provider': 'Perplexity',
                        'response': response.choices[0].message.content,
                        'model': response.model,
                        'success': True
                    }
                except ImportError:
                    # Can't use old style with Perplexity
                    return {'provider': 'Perplexity', 'error': 'OpenAI library v1.x required for Perplexity API'}
            else:
                # Old OpenAI library doesn't support Perplexity well
                return {'provider': 'Perplexity', 'error': 'OpenAI library v1.x required for Perplexity API'}
            
            print(f"[OK] Perplexity responded successfully")
            return result
                
        except Exception as e:
            print(f"[ERROR] Perplexity error: {e}")
            return {'provider': 'Perplexity', 'error': str(e)}
    
    def test_google(self, prompt):
        """Test Google Gemini API with support for both old and new client libraries"""
        if 'google' not in self.configured_providers:
            return {'provider': 'Google', 'error': 'Not configured'}
        
        if not self.has_google:
            return {'provider': 'Google', 'error': 'Google library not installed'}
        
        print("Testing Google...")
        
        # Try new google.genai library first
        try:
            from google import genai
            print("Using new google.genai library...")
            
            client = genai.Client(api_key=self.api_keys['google'])
            
            # Use gemini-2.5-flash by default for new client, fallback to env setting
            model_name = os.getenv('GOOGLE_MODEL', 'gemini-2.5-flash')
            
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            
            result = {
                'provider': 'Google',
                'response': response.text,
                'model': model_name,
                'success': True
            }
            print(f"[OK] Google responded successfully (new client)")
            return result
            
        except ImportError:
            # Fallback to old google.generativeai library
            try:
                import google.generativeai as genai
                print("Using legacy google.generativeai library...")
                
                genai.configure(api_key=self.api_keys['google'])
                model = genai.GenerativeModel(os.getenv('GOOGLE_MODEL', 'gemini-2.5-flash'))
                
                response = model.generate_content(prompt)
                
                result = {
                    'provider': 'Google',
                    'response': response.text,
                    'model': os.getenv('GOOGLE_MODEL', 'gemini-2.5-flash'),
                    'success': True
                }
                print(f"[OK] Google responded successfully (legacy client)")
                return result
                
            except ImportError:
                return {'provider': 'Google', 'error': 'Google library not installed. Install with: pip install google-genai'}
            except Exception as e:
                print(f"[ERROR] Google error (legacy): {e}")
                return {'provider': 'Google', 'error': str(e)}
                
        except Exception as e:
            print(f"[ERROR] Google error: {e}")
            return {'provider': 'Google', 'error': str(e)}
    
    def test_google_search(self, prompt):
        """Test Google Custom Search API"""
        if 'google_search' not in self.configured_providers:
            return {'provider': 'Google Search', 'error': 'Not configured'}
        
        try:
            import requests
            print("Testing Google Search...")
            
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.api_keys['google_search'],
                'cx': self.api_keys['google_cx'],
                'q': prompt,
                'num': 10  # Get top 10 results
            }
            
            response = requests.get(url, params=params, timeout=int(os.getenv('REQUEST_TIMEOUT', 30)))
            
            if response.status_code != 200:
                return {
                    'provider': 'Google Search',
                    'error': f"API returned status {response.status_code}: {response.text}"
                }
            
            data = response.json()
            
            # Format search results
            search_results = []
            if 'items' in data:
                for item in data['items']:
                    search_results.append({
                        'title': item.get('title', 'No title'),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', 'No description available')
                    })
            
            result = {
                'provider': 'Google Search',
                'response': search_results,
                'query': prompt,
                'total_results': data.get('searchInformation', {}).get('totalResults', '0'),
                'success': True
            }
            print(f"[OK] Google Search responded successfully ({len(search_results)} results)")
            return result
            
        except Exception as e:
            print(f"[ERROR] Google Search error: {e}")
            return {'provider': 'Google Search', 'error': str(e)}
    
    def test_all(self, prompt):
        """Test all configured providers"""
        print("\n" + "=" * 60)
        print("Testing LLM APIs...")
        print("=" * 60 + "\n")
        
        results = []
        
        # Test each provider
        for provider in self.configured_providers:
            if provider == 'openai':
                results.append(self.test_openai(prompt))
            elif provider == 'anthropic':
                results.append(self.test_anthropic(prompt))
            elif provider == 'perplexity':
                results.append(self.test_perplexity(prompt))
            elif provider == 'google':
                results.append(self.test_google(prompt))
            elif provider == 'google_search':
                results.append(self.test_google_search(prompt))
            
            print()  # Space between tests
        
        return results
    
    def display_results(self, results):
        """Display test results"""
        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60 + "\n")
        
        for result in results:
            print(f"[{result['provider']}]")
            print("-" * 40)
            
            if 'error' in result:
                print(f"ERROR: {result['error']}")
            else:
                print(f"SUCCESS: Response received")
                if 'model' in result:
                    print(f"Model: {result['model']}")
                
                # Handle Google Search results differently
                if result['provider'] == 'Google Search':
                    print(f"Total results: {result.get('total_results', '0')}")
                    print(f"Top {len(result['response'])} results:")
                    for i, item in enumerate(result['response'][:3], 1):  # Show first 3 results
                        print(f"  {i}. {item['title']}")
                        print(f"     {item['link']}")
                        print(f"     {item['snippet'][:100]}...")
                    if len(result['response']) > 3:
                        print(f"  ... and {len(result['response']) - 3} more results")
                else:
                    # Regular LLM response
                    response_text = str(result['response'])
                    if len(response_text) > 100:
                        print(f"Response preview: {response_text[:100]}...")
                    else:
                        print(f"Response: {response_text}")
            
            print()
        
        # Summary
        successful = [r for r in results if 'error' not in r]
        failed = [r for r in results if 'error' in r]
        
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"[OK] Successful: {len(successful)} providers")
        print(f"[ERROR] Failed: {len(failed)} providers")
        
        if successful:
            print(f"\nWorking providers: {', '.join([r['provider'] for r in successful])}")
        
        if failed:
            print(f"\nFailed providers: {', '.join([r['provider'] for r in failed])}")
            print("\nTo fix failed providers:")
            print("1. Check that the API key is correct in .env file")
            print("2. Verify the API key format (some providers have specific prefixes)")
            print("3. Check your API account has credits/is active")
            print("4. For Perplexity: Ensure key starts with 'pplx-'")
            print("5. For Google: Enable Generative AI API in Google Cloud Console")


def load_questions(filename='questions.txt'):
    """Load questions from a file"""
    if not os.path.exists(filename):
        return []
    
    with open(filename, 'r') as f:
        questions = [line.strip() for line in f if line.strip()]
    
    return questions

def create_slug(text, max_length=50):
    """Create a filesystem-safe slug from text"""
    # Remove special characters and replace spaces with underscores
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '_', slug)
    # Truncate to max length
    return slug[:max_length]

def select_questions_interactive(questions):
    """Show numbered list and let user select"""
    print("\nAvailable questions:")
    print("-" * 40)
    for i, q in enumerate(questions, 1):
        print(f"{i}. {q}")
    print(f"{len(questions) + 1}. Run all questions")
    print(f"{len(questions) + 2}. Enter custom question")
    print()
    
    while True:
        try:
            choice = input("Select question number (or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                return None
            
            choice_num = int(choice)
            if choice_num == len(questions) + 1:
                return questions  # Run all
            elif choice_num == len(questions) + 2:
                custom = input("Enter your question: ").strip()
                return [custom] if custom else None
            elif 1 <= choice_num <= len(questions):
                return [questions[choice_num - 1]]
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

def run_single_query(tester, query, analyzer=None, save_individual=True):
    """Run a single query and return results"""
    print(f"\nQuery: {query}")
    print("-" * 60)
    
    # Run tests
    results = tester.test_all(query)
    
    # Display results
    tester.display_results(results)
    
    # Analyze if enabled
    if analyzer and os.getenv('ANALYZE_RESPONSES', 'false').lower() == 'true':
        print("\n" + "=" * 60)
        print("ANALYZING RESPONSES FOR AISEO INSIGHTS")
        print("=" * 60)
        
        for result in results:
            # Skip Google Search results - only analyze LLM responses
            if result.get('provider') == 'Google Search':
                continue
                
            if 'error' not in result and result.get('response'):
                # Analyze the response
                analysis = analyzer.analyze_with_ai(
                    result['response'],
                    query,
                    result['provider']
                )
                
                if analysis:
                    # Add analysis to result
                    result['analysis'] = analysis
                    
                    # Save to CSV
                    analyzer.save_to_csv(analysis)
                    
                    # Display insights
                    analyzer.display_insights(analysis)
    
    # Save results if requested
    if save_individual:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        slug = create_slug(query)
        
        # Create results directory if it doesn't exist
        os.makedirs('results', exist_ok=True)
        
        filename = f"results/llm_results_{slug}_{timestamp}.json"
        
        output_data = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'time': datetime.now().strftime('%H:%M:%S'),
            'results': results
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        print(f"\nResults saved to: {filename}")
    
    return results

# Main execution
if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Multi-LLM Query Testing Tool with Enhanced AI Analysis')
    parser.add_argument('--query', '-q', type=str, help='Single query to test')
    parser.add_argument('--batch', '-b', action='store_true', help='Run all questions from questions.txt')
    parser.add_argument('--select', '-s', action='store_true', help='Select questions interactively')
    parser.add_argument('--file', '-f', type=str, default='questions.txt', help='Questions file to use (default: questions.txt)')
    
    # Enhanced analysis flags
    parser.add_argument('--enhanced-analysis', action='store_true', 
                       help='Enable enhanced analysis features (domain classification, negative signals, etc.)')
    parser.add_argument('--weekly-report', action='store_true',
                       help='Generate weekly report from tracked data')
    parser.add_argument('--track-history', action='store_true',
                       help='Enable historical tracking in database')
    parser.add_argument('--show-trends', action='store_true',
                       help='Show historical trends from tracking database')
    parser.add_argument('--request-sources', action='store_true',
                       help='Ask LLMs to cite their sources with URLs and domain names')
    
    args = parser.parse_args()
    
    # Set enhanced analysis environment variables based on flags
    if args.enhanced_analysis:
        os.environ['ENABLE_ENHANCED_ANALYSIS'] = 'true'
        os.environ['DOMAIN_CLASSIFICATION'] = 'true'
        os.environ['NEGATIVE_SIGNAL_DETECTION'] = 'true'
        os.environ['ACCURACY_VERIFICATION'] = 'true'
        print("[OK] Enhanced analysis features enabled")
    
    if args.track_history:
        os.environ['TRACK_HISTORY'] = 'true'
        print("[OK] Historical tracking enabled")
    
    if args.request_sources:
        os.environ['REQUEST_SOURCES'] = 'true'
        print("[OK] Source citation requests enabled")
    
    # Handle weekly report generation
    if args.weekly_report:
        os.environ['WEEKLY_REPORTING'] = 'true'
        os.environ['TRACK_HISTORY'] = 'true'  # Required for reports
        analyzer = ResponseAnalyzer()
        
        if analyzer.tracker and analyzer.reporter:
            print("\nGenerating weekly report...")
            report_path = analyzer.generate_weekly_report()
            if report_path:
                print(f"[OK] Report saved to: {report_path}")
        else:
            print("[ERROR] Weekly reporting requires enhanced analysis to be enabled")
            print("       Use: python3 run.py --enhanced-analysis --weekly-report")
        sys.exit(0)
    
    # Handle trends display
    if args.show_trends:
        if TRACKER_AVAILABLE:
            tracker = HistoricalTracker()
            trends = tracker.get_historical_trends(4)
            
            print("\nHistorical Trends (Last 4 Weeks):")
            print("-" * 60)
            for week_data in trends:
                week = week_data['week_start']
                summary = week_data['summary']
                print(f"\nWeek of {week}:")
                print(f"  UGC: {summary.get('avg_ugc_percentage', 0):.1f}%")
                print(f"  Owned: {summary.get('avg_owned_percentage', 0):.1f}%")
                print(f"  Authority: {summary.get('avg_authority_percentage', 0):.1f}%")
                print(f"  Negative content: {summary.get('negative_content_count', 0)}")
        else:
            print("[ERROR] Historical tracking module not available")
        sys.exit(0)
    
    print("\n" + "=" * 60)
    print("STARTING TESTS")
    print("=" * 60 + "\n")
    
    # Initialize tester and analyzer
    tester = FixedLLMTester()
    analyzer = ResponseAnalyzer() if os.getenv('ANALYZE_RESPONSES', 'false').lower() == 'true' else None
    
    queries_to_run = []
    
    # Determine which mode to run
    if args.query:
        # Single query from command line
        queries_to_run = [args.query]
        print(f"Running single query: {args.query}")
        
    elif args.batch:
        # Batch mode - run all questions from file
        questions = load_questions(args.file)
        if not questions:
            print(f"[ERROR] No questions found in {args.file}")
            print("\nPlease create a questions file with one question per line.")
            sys.exit(1)
        
        queries_to_run = questions
        print(f"Batch mode: Running {len(questions)} questions from {args.file}")
        
    elif args.select:
        # Select mode - interactive selection
        questions = load_questions(args.file)
        if not questions:
            print(f"[WARNING] No questions found in {args.file}")
            custom = input("Enter your question: ").strip()
            queries_to_run = [custom] if custom else []
        else:
            selected = select_questions_interactive(questions)
            if selected is None:
                print("Exiting...")
                sys.exit(0)
            queries_to_run = selected
            
    else:
        # Default interactive mode (backward compatible)
        test_prompt = input("Enter a test prompt (or press Enter for default): ").strip()
        if not test_prompt:
            test_prompt = "What is 2+2? Answer in one sentence."
            print(f"Using default prompt: '{test_prompt}'")
        queries_to_run = [test_prompt]
    
    # Check if we have queries to run
    if not queries_to_run:
        print("[ERROR] No queries to run.")
        sys.exit(1)
    
    # Run queries
    all_results = []
    
    if len(queries_to_run) == 1:
        # Single query
        results = run_single_query(tester, queries_to_run[0], analyzer, save_individual=True)
        all_results.append({'query': queries_to_run[0], 'results': results})
        
    else:
        # Multiple queries
        print(f"\n[INFO] Running {len(queries_to_run)} queries...")
        print("=" * 60)
        
        for i, query in enumerate(queries_to_run, 1):
            print(f"\n[{i}/{len(queries_to_run)}] Processing query...")
            results = run_single_query(tester, query, analyzer, save_individual=True)
            all_results.append({'query': query, 'results': results})
            
            # Add a small delay between queries to avoid rate limiting
            if i < len(queries_to_run):
                time.sleep(2)
        
        # Save batch summary
        print("\n" + "=" * 60)
        print("SAVING BATCH SUMMARY")
        print("=" * 60 + "\n")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        os.makedirs('results', exist_ok=True)
        summary_filename = f"results/batch_summary_{timestamp}.json"
        
        summary_data = {
            'batch_timestamp': datetime.now().isoformat(),
            'total_queries': len(queries_to_run),
            'queries_run': queries_to_run,
            'all_results': all_results
        }
        
        with open(summary_filename, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        
        print(f"Batch summary saved to: {summary_filename}")
    
    if analyzer:
        print(f"\n[OK] Analysis results saved to: {analyzer.csv_path}")
    
    print("\n[OK] Testing complete!")