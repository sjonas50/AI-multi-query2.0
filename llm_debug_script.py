#!/usr/bin/env python3
"""
Debug Version - Multi-LLM Query Script
Enhanced with verbose logging and error detection
"""

import os
import sys
import json
import time
from datetime import datetime

print("=" * 60)
print("LLM Multi-Query Script - Debug Mode")
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
        print(f"✅ {module_name} is installed")
        return True
    except ImportError as e:
        print(f"❌ {module_name} is NOT installed - Error: {e}")
        return False

# Check all dependencies
print("Checking dependencies...")
print("-" * 40)
has_openai = check_import("openai")
has_anthropic = check_import("anthropic")
has_google = check_import("google.generativeai", "google.generativeai as genai")
has_requests = check_import("requests")
has_dotenv = check_import("python-dotenv", "dotenv")
print()

# Check for .env file
print("Checking configuration...")
print("-" * 40)
if os.path.exists(".env"):
    print("✅ .env file found")
    
    # Try to load it
    if has_dotenv:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env file loaded")
    else:
        print("⚠️  Cannot load .env - python-dotenv not installed")
else:
    print("❌ .env file NOT found")
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
    print("✅ Created .env template file")
    print("\n⚠️  Please edit .env with your actual API keys and run again!")
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
}

configured_providers = []
for provider, key in api_keys.items():
    if key and not key.startswith('your-') and not key.startswith('sk-your'):
        print(f"✅ {provider.upper()}_API_KEY is configured (length: {len(key)})")
        configured_providers.append(provider)
    else:
        print(f"❌ {provider.upper()}_API_KEY is NOT configured or is still template")

print()

if not configured_providers:
    print("❌ No API keys configured!")
    print("\nTo fix this:")
    print("1. Edit the .env file")
    print("2. Replace the template keys with your actual API keys")
    print("3. Save the file and run this script again")
    sys.exit(1)

print(f"Configured providers: {', '.join(configured_providers)}")
print()

# Simple test class
class SimpleLLMTester:
    def __init__(self):
        self.results = []
    
    def test_openai(self, prompt):
        """Test OpenAI API"""
        if 'openai' not in configured_providers or not has_openai:
            return {'provider': 'OpenAI', 'error': 'Not configured or library not installed'}
        
        try:
            import openai
            print("Testing OpenAI...")
            
            client = openai.OpenAI(api_key=api_keys['openai'])
            
            response = client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-4.1'),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.7
            )
            
            result = {
                'provider': 'OpenAI',
                'response': response.choices[0].message.content,
                'success': True
            }
            print(f"✅ OpenAI responded successfully")
            return result
            
        except Exception as e:
            print(f"❌ OpenAI error: {e}")
            return {'provider': 'OpenAI', 'error': str(e)}
    
    def test_anthropic(self, prompt):
        """Test Anthropic API"""
        if 'anthropic' not in configured_providers or not has_anthropic:
            return {'provider': 'Anthropic', 'error': 'Not configured or library not installed'}
        
        try:
            import anthropic
            print("Testing Anthropic...")
            
            client = anthropic.Anthropic(api_key=api_keys['anthropic'])
            
            response = client.messages.create(
                model=os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514'),
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = {
                'provider': 'Anthropic',
                'response': response.content[0].text,
                'success': True
            }
            print(f"✅ Anthropic responded successfully")
            return result
            
        except Exception as e:
            print(f"❌ Anthropic error: {e}")
            return {'provider': 'Anthropic', 'error': str(e)}
    
    def test_perplexity(self, prompt):
        """Test Perplexity API"""
        if 'perplexity' not in configured_providers or not has_requests:
            return {'provider': 'Perplexity', 'error': 'Not configured or requests not installed'}
        
        try:
            import requests
            print("Testing Perplexity...")
            
            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers={
                    'Authorization': f"Bearer {api_keys['perplexity']}",
                    'Content-Type': 'application/json'
                },
                json={
                    'model': os.getenv('PERPLEXITY_MODEL', 'sonar-pro'),
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 100
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    'provider': 'Perplexity',
                    'response': data['choices'][0]['message']['content'],
                    'success': True
                }
                print(f"✅ Perplexity responded successfully")
                return result
            else:
                print(f"❌ Perplexity API error: {response.status_code}")
                print(f"Response: {response.text}")
                return {'provider': 'Perplexity', 'error': f"API error {response.status_code}: {response.text}"}
                
        except Exception as e:
            print(f"❌ Perplexity error: {e}")
            return {'provider': 'Perplexity', 'error': str(e)}
    
    def test_google(self, prompt):
        """Test Google API"""
        if 'google' not in configured_providers or not has_google:
            return {'provider': 'Google', 'error': 'Not configured or library not installed'}
        
        try:
            import google.generativeai as genai
            print("Testing Google...")
            
            genai.configure(api_key=api_keys['google'])
            model = genai.GenerativeModel(os.getenv('GOOGLE_MODEL', 'gemini-2.5-flash'))
            
            response = model.generate_content(prompt)
            
            result = {
                'provider': 'Google',
                'response': response.text,
                'success': True
            }
            print(f"✅ Google responded successfully")
            return result
            
        except Exception as e:
            print(f"❌ Google error: {e}")
            return {'provider': 'Google', 'error': str(e)}
    
    def test_all(self, prompt):
        """Test all configured providers"""
        print("\n" + "=" * 60)
        print("Testing LLM APIs...")
        print("=" * 60 + "\n")
        
        results = []
        
        # Test each provider
        for provider in configured_providers:
            if provider == 'openai':
                results.append(self.test_openai(prompt))
            elif provider == 'anthropic':
                results.append(self.test_anthropic(prompt))
            elif provider == 'perplexity':
                results.append(self.test_perplexity(prompt))
            elif provider == 'google':
                results.append(self.test_google(prompt))
            
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
                print(f"Response preview: {result['response'][:100]}...")
            
            print()
        
        # Summary
        successful = [r for r in results if 'error' not in r]
        failed = [r for r in results if 'error' in r]
        
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"✅ Successful: {len(successful)} providers")
        print(f"❌ Failed: {len(failed)} providers")
        
        if successful:
            print(f"\nWorking providers: {', '.join([r['provider'] for r in successful])}")
        
        if failed:
            print(f"\nFailed providers: {', '.join([r['provider'] for r in failed])}")
            print("\nTo fix failed providers:")
            print("1. Check that the API key is correct")
            print("2. Verify the library is installed (pip install <library>)")
            print("3. Check your API account has credits/is active")


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
    tester = SimpleLLMTester()
    results = tester.test_all(test_prompt)
    
    # Display results
    tester.display_results(results)
    
    # Save results to file
    print("\n" + "=" * 60)
    print("SAVING RESULTS")
    print("=" * 60 + "\n")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"llm_test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Results saved to: {filename}")
    print("\n✅ Testing complete!")