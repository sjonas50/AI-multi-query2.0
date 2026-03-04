#!/usr/bin/env python3
"""
Fixed Multi-LLM Query Script
Corrected API implementations for all providers
"""

import os
import sys
import json
import time
from datetime import datetime

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
    
    def test_openai(self, prompt):
        """Test OpenAI API with version detection"""
        if 'openai' not in self.configured_providers or not self.has_openai:
            return {'provider': 'OpenAI', 'error': 'Not configured or library not installed'}
        
        try:
            import openai
            print("Testing OpenAI...")
            
            # Check OpenAI library version
            openai_version = getattr(openai, '__version__', '0.0.0')
            major_version = int(openai_version.split('.')[0])
            
            if major_version >= 1:
                # New OpenAI client (v1.x)
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=self.api_keys['openai'])
                    
                    response = client.chat.completions.create(
                        model=os.getenv('OPENAI_MODEL', 'gpt-5.2'),
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=int(os.getenv('MAX_TOKENS', 1000)),
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
                        model=os.getenv('OPENAI_MODEL', 'gpt-5.2'),
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=int(os.getenv('MAX_TOKENS', 1000)),
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
                    model=os.getenv('OPENAI_MODEL', 'gpt-5.2'),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=int(os.getenv('MAX_TOKENS', 1000)),
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
            
            client = anthropic.Anthropic(api_key=self.api_keys['anthropic'])
            
            response = client.messages.create(
                model=os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-6'),
                max_tokens=int(os.getenv('MAX_TOKENS', 1000)),
                messages=[{"role": "user", "content": prompt}]
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
                        messages=[{"role": "user", "content": prompt}],
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


# Main execution
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("STARTING TESTS")
    print("=" * 60 + "\n")
    
    # Get test prompt
    test_prompt = input("Enter a test prompt (or press Enter for default): ").strip()
    if not test_prompt:
        test_prompt = "What is 2+2? Answer in one sentence."
        print(f"Using default prompt: '{test_prompt}'")
    
    # Run tests
    tester = FixedLLMTester()
    results = tester.test_all(test_prompt)
    
    # Display results
    tester.display_results(results)
    
    # Save results to file
    print("\n" + "=" * 60)
    print("SAVING RESULTS")
    print("=" * 60 + "\n")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"llm_test_results_{timestamp}.json"
    
    # Create enhanced output with metadata
    output_data = {
        'query': test_prompt,
        'timestamp': datetime.now().isoformat(),
        'date': datetime.now().strftime('%Y-%m-%d'),
        'time': datetime.now().strftime('%H:%M:%S'),
        'results': results
    }
    
    with open(filename, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)
    
    print(f"Results saved to: {filename}")
    print("\n[OK] Testing complete!")