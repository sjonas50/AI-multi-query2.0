#!/usr/bin/env python3
"""
Fixed Multi-LLM Query Script - Compatible with older OpenAI library versions
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment variables.")

class LLMQuerier:
    """Query multiple LLM providers with compatibility handling"""
    
    def __init__(self):
        self.api_keys = {
            'openai': os.getenv('OPENAI_API_KEY'),
            'anthropic': os.getenv('ANTHROPIC_API_KEY'),
            'perplexity': os.getenv('PERPLEXITY_API_KEY'),
            'google': os.getenv('GOOGLE_API_KEY'),
        }
        
        # Check which libraries are available
        self.check_libraries()
        
    def check_libraries(self):
        """Check which libraries are installed and their versions"""
        self.available = {}
        
        # Check OpenAI
        try:
            import openai
            self.available['openai'] = True
            # Check OpenAI version
            try:
                # Try new API (1.0+)
                test = openai.OpenAI
                self.openai_version = 'new'
                print("✅ OpenAI library detected (v1.0+)")
            except AttributeError:
                # Old API (0.x)
                self.openai_version = 'old'
                print("✅ OpenAI library detected (v0.x - please upgrade: pip install openai --upgrade)")
        except ImportError:
            self.available['openai'] = False
            print("❌ OpenAI library not installed")
        
        # Check Anthropic
        try:
            import anthropic
            self.available['anthropic'] = True
            print("✅ Anthropic library detected")
        except ImportError:
            self.available['anthropic'] = False
            print("❌ Anthropic library not installed")
        
        # Check Google
        try:
            import google.generativeai as genai
            self.available['google'] = True
            print("✅ Google Generative AI library detected")
        except ImportError:
            self.available['google'] = False
            print("❌ Google Generative AI library not installed")
        
        # Requests is always needed for Perplexity
        try:
            import requests
            self.available['perplexity'] = True
            print("✅ Requests library detected (for Perplexity)")
        except ImportError:
            self.available['perplexity'] = False
            print("❌ Requests library not installed")
        
        print()
    
    def query_openai(self, prompt: str, model: str = None) -> Dict:
        """Query OpenAI API with version compatibility"""
        if not self.available.get('openai') or not self.api_keys.get('openai'):
            return {'provider': 'OpenAI', 'error': 'Not configured or library not installed'}
        
        if model is None:
            model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')  # Use gpt-3.5-turbo as fallback
        
        try:
            import openai
            start_time = time.time()
            
            if self.openai_version == 'new':
                # New API (1.0+)
                client = openai.OpenAI(api_key=self.api_keys['openai'])
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                result = {
                    'provider': 'OpenAI',
                    'model': model,
                    'response': response.choices[0].message.content,
                    'time': time.time() - start_time,
                    'tokens': response.usage.total_tokens if response.usage else None
                }
            else:
                # Old API (0.x)
                openai.api_key = self.api_keys['openai']
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                result = {
                    'provider': 'OpenAI',
                    'model': model,
                    'response': response.choices[0].message.content,
                    'time': time.time() - start_time,
                    'tokens': response.usage.total_tokens if response.usage else None
                }
            
            return result
            
        except Exception as e:
            return {'provider': 'OpenAI', 'error': str(e)}
    
    def query_anthropic(self, prompt: str, model: str = None) -> Dict:
        """Query Anthropic API"""
        if not self.available.get('anthropic') or not self.api_keys.get('anthropic'):
            return {'provider': 'Anthropic', 'error': 'Not configured or library not installed'}
        
        if model is None:
            model = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')
        
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_keys['anthropic'])
            start_time = time.time()
            
            response = client.messages.create(
                model=model,
                max_tokens=1000,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                'provider': 'Anthropic',
                'model': model,
                'response': response.content[0].text,
                'time': time.time() - start_time,
                'tokens': response.usage.input_tokens + response.usage.output_tokens if response.usage else None
            }
            
        except Exception as e:
            return {'provider': 'Anthropic', 'error': str(e)}
    
    def query_perplexity(self, prompt: str, model: str = None) -> Dict:
        """Query Perplexity API"""
        if not self.available.get('perplexity') or not self.api_keys.get('perplexity'):
            return {'provider': 'Perplexity', 'error': 'Not configured or requests library not installed'}
        
        # Check if the API key looks valid
        if self.api_keys['perplexity'].startswith('pplx-'):
            print("✅ Perplexity API key format looks correct")
        else:
            print("⚠️  Perplexity API key should start with 'pplx-'")
        
        if model is None:
            model = os.getenv('PERPLEXITY_MODEL', 'llama-3.1-sonar-small-128k-online')
        
        try:
            import requests
            start_time = time.time()
            
            headers = {
                'Authorization': f"Bearer {self.api_keys['perplexity']}",
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': model,
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.7,
                'max_tokens': 1000
            }
            
            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'provider': 'Perplexity',
                    'model': model,
                    'response': result['choices'][0]['message']['content'],
                    'time': time.time() - start_time,
                    'tokens': result.get('usage', {}).get('total_tokens')
                }
            elif response.status_code == 401:
                return {'provider': 'Perplexity', 'error': 'Invalid API key. Please check your Perplexity API key.'}
            else:
                return {'provider': 'Perplexity', 'error': f"API error {response.status_code}: {response.text[:200]}"}
                
        except Exception as e:
            return {'provider': 'Perplexity', 'error': str(e)}
    
    def query_google(self, prompt: str, model: str = None) -> Dict:
        """Query Google Gemini API"""
        if not self.available.get('google') or not self.api_keys.get('google'):
            return {'provider': 'Google', 'error': 'Not configured or library not installed'}
        
        if model is None:
            model = os.getenv('GOOGLE_MODEL', 'gemini-1.5-flash')
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_keys['google'])
            model_obj = genai.GenerativeModel(model)
            start_time = time.time()
            
            response = model_obj.generate_content(prompt)
            
            return {
                'provider': 'Google',
                'model': model,
                'response': response.text,
                'time': time.time() - start_time,
                'tokens': None  # Gemini doesn't easily provide token count
            }
            
        except Exception as e:
            return {'provider': 'Google', 'error': str(e)}
    
    def query_all(self, prompt: str, providers: List[str] = None) -> List[Dict]:
        """Query all configured providers"""
        if providers is None:
            # Use all available and configured providers
            providers = []
            if self.available.get('openai') and self.api_keys.get('openai'):
                providers.append('openai')
            if self.available.get('anthropic') and self.api_keys.get('anthropic'):
                providers.append('anthropic')
            if self.available.get('perplexity') and self.api_keys.get('perplexity'):
                providers.append('perplexity')
            if self.available.get('google') and self.api_keys.get('google'):
                providers.append('google')
        
        results = []
        
        print(f"\nQuerying {len(providers)} providers: {', '.join(providers)}\n")
        
        for provider in providers:
            print(f"Querying {provider}...")
            
            if provider == 'openai':
                result = self.query_openai(prompt)
            elif provider == 'anthropic':
                result = self.query_anthropic(prompt)
            elif provider == 'perplexity':
                result = self.query_perplexity(prompt)
            elif provider == 'google':
                result = self.query_google(prompt)
            else:
                result = {'provider': provider, 'error': 'Unknown provider'}
            
            results.append(result)
            
            if 'error' in result:
                print(f"  ❌ {provider}: {result['error']}")
            else:
                print(f"  ✅ {provider}: Response received ({result.get('time', 0):.2f}s)")
        
        return results
    
    def format_results(self, results: List[Dict], format_type: str = 'text') -> str:
        """Format results for display"""
        if format_type == 'json':
            return json.dumps(results, indent=2)
        
        elif format_type == 'markdown':
            output = "# LLM Response Comparison\n\n"
            output += f"**Query Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for result in results:
                provider = result.get('provider', 'Unknown')
                output += f"## {provider}\n\n"
                
                if 'error' in result:
                    output += f"**Error:** {result['error']}\n\n"
                else:
                    output += f"**Model:** {result.get('model', 'N/A')}\n"
                    output += f"**Response Time:** {result.get('time', 0):.2f}s\n"
                    output += f"**Tokens:** {result.get('tokens', 'N/A')}\n\n"
                    output += f"**Response:**\n{result.get('response', 'No response')}\n\n"
                    output += "---\n\n"
            
            return output
        
        else:  # text format
            output = "=" * 80 + "\n"
            output += "LLM RESPONSE COMPARISON\n"
            output += f"Query Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += "=" * 80 + "\n\n"
            
            for result in results:
                provider = result.get('provider', 'Unknown')
                output += f"[{provider}]\n"
                output += "-" * 40 + "\n"
                
                if 'error' in result:
                    output += f"ERROR: {result['error']}\n\n"
                else:
                    output += f"Model: {result.get('model', 'N/A')}\n"
                    output += f"Response Time: {result.get('time', 0):.2f}s\n"
                    output += f"Tokens: {result.get('tokens', 'N/A')}\n\n"
                    output += f"Response:\n{result.get('response', 'No response')}\n\n"
                
                output += "=" * 80 + "\n\n"
            
            return output


def setup_instructions():
    """Print setup instructions"""
    print("\n" + "=" * 80)
    print("SETUP INSTRUCTIONS")
    print("=" * 80 + "\n")
    
    print("1. FIX OPENAI (optional):")
    print("   pip install openai --upgrade")
    print("   (You have an old version - upgrade for better compatibility)\n")
    
    print("2. FIX PERPLEXITY:")
    print("   - Get your API key from: https://www.perplexity.ai/settings/api")
    print("   - Make sure it starts with 'pplx-'")
    print("   - Update your .env file with the correct key\n")
    
    print("3. ADD GOOGLE (optional):")
    print("   pip install google-generativeai")
    print("   - Get API key from: https://makersuite.google.com/app/apikey")
    print("   - Add to .env: GOOGLE_API_KEY=your-key-here\n")
    
    print("4. ANTHROPIC is working! ✅\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Query multiple LLMs with the same prompt')
    parser.add_argument('prompt', nargs='?', help='The prompt to send to all LLMs')
    parser.add_argument('--providers', nargs='+', help='Specific providers to query')
    parser.add_argument('--format', choices=['text', 'json', 'markdown'], default='text',
                       help='Output format')
    parser.add_argument('--save', help='Save results to file')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--setup', action='store_true', help='Show setup instructions')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_instructions()
        return
    
    print("\n" + "=" * 80)
    print("Multi-LLM Query Script")
    print("=" * 80 + "\n")
    
    querier = LLMQuerier()
    
    # Check if we have any working providers
    working_providers = []
    if querier.available.get('openai') and querier.api_keys.get('openai'):
        working_providers.append('openai')
    if querier.available.get('anthropic') and querier.api_keys.get('anthropic'):
        working_providers.append('anthropic')
    if querier.available.get('perplexity') and querier.api_keys.get('perplexity'):
        working_providers.append('perplexity')
    if querier.available.get('google') and querier.api_keys.get('google'):
        working_providers.append('google')
    
    if not working_providers:
        print("❌ No LLM providers are properly configured!")
        setup_instructions()
        return
    
    print(f"Available providers: {', '.join(working_providers)}")
    
    if args.interactive:
        print("\nInteractive mode. Type 'quit' to exit.\n")
        while True:
            prompt = input("\nEnter prompt: ").strip()
            if prompt.lower() in ['quit', 'exit', 'q']:
                break
            
            if prompt:
                results = querier.query_all(prompt, args.providers)
                output = querier.format_results(results, args.format)
                print(output)
                
                if args.save:
                    with open(args.save, 'w') as f:
                        f.write(output)
                    print(f"Saved to {args.save}")
    else:
        if not args.prompt:
            prompt = input("Enter your prompt: ").strip()
        else:
            prompt = args.prompt
        
        if prompt:
            results = querier.query_all(prompt, args.providers)
            output = querier.format_results(results, args.format)
            print(output)
            
            if args.save:
                with open(args.save, 'w') as f:
                    f.write(output)
                print(f"Saved to {args.save}")


if __name__ == "__main__":
    main()