#!/usr/bin/env python3
"""
Simple Direct LLM Test Script - Guaranteed Output
"""

import os
import json
import time
from datetime import datetime

print("\n" + "="*60)
print("SIMPLE LLM TEST SCRIPT - STARTING")
print("="*60)

# Load environment variables if dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except:
    print("⚠️  Using system environment variables")

# Get API keys
api_keys = {
    'openai': os.getenv('OPENAI_API_KEY'),
    'anthropic': os.getenv('ANTHROPIC_API_KEY'),
    'perplexity': os.getenv('PERPLEXITY_API_KEY'),
    'google': os.getenv('GOOGLE_API_KEY'),
}

print("\n📋 API Keys Status:")
for name, key in api_keys.items():
    if key and not key.startswith('your-'):
        print(f"  ✅ {name}: configured (length: {len(key)})")
    else:
        print(f"  ❌ {name}: not configured")

# Test prompt
test_prompt = "What is 2+2? Answer in one short sentence."
print(f"\n📝 Test prompt: '{test_prompt}'")
print("\n" + "="*60)

results = []

# Test Anthropic (we know this works)
print("\n🔍 Testing Anthropic...")
if api_keys['anthropic']:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_keys['anthropic'])
        
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=100,
            messages=[{"role": "user", "content": test_prompt}]
        )
        
        result = {
            'provider': 'Anthropic',
            'status': 'SUCCESS',
            'response': response.content[0].text
        }
        print(f"✅ Anthropic responded: {response.content[0].text[:100]}")
        results.append(result)
    except Exception as e:
        print(f"❌ Anthropic error: {e}")
        results.append({'provider': 'Anthropic', 'status': 'ERROR', 'error': str(e)})
else:
    print("⏭️  Skipping Anthropic - no API key")

# Test OpenAI (handle both old and new versions)
print("\n🔍 Testing OpenAI...")
if api_keys['openai']:
    try:
        import openai
        
        # Try to detect version
        try:
            # New version (1.0+)
            client = openai.OpenAI(api_key=api_keys['openai'])
            response = client.chat.completions.create(
                model="gpt-5.2",
                messages=[{"role": "user", "content": test_prompt}],
                max_tokens=100
            )
            result = {
                'provider': 'OpenAI',
                'status': 'SUCCESS',
                'response': response.choices[0].message.content
            }
            print(f"✅ OpenAI responded: {response.choices[0].message.content[:100]}")
            results.append(result)
        except AttributeError:
            # Old version (0.x)
            print("  Using old OpenAI API...")
            openai.api_key = api_keys['openai']
            response = openai.ChatCompletion.create(
                model="gpt-5.2",
                messages=[{"role": "user", "content": test_prompt}],
                max_tokens=100
            )
            result = {
                'provider': 'OpenAI',
                'status': 'SUCCESS',
                'response': response.choices[0].message.content
            }
            print(f"✅ OpenAI responded: {response.choices[0].message.content[:100]}")
            results.append(result)
    except Exception as e:
        print(f"❌ OpenAI error: {e}")
        results.append({'provider': 'OpenAI', 'status': 'ERROR', 'error': str(e)})
else:
    print("⏭️  Skipping OpenAI - no API key")

# Test Perplexity
print("\n🔍 Testing Perplexity...")
if api_keys['perplexity']:
    try:
        import requests
        
        response = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={
                'Authorization': f"Bearer {api_keys['perplexity']}",
                'Content-Type': 'application/json'
            },
            json={
                'model': 'sonar-pro',
                'messages': [{'role': 'user', 'content': test_prompt}],
                'max_tokens': 100
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            result = {
                'provider': 'Perplexity',
                'status': 'SUCCESS',
                'response': data['choices'][0]['message']['content']
            }
            print(f"✅ Perplexity responded: {data['choices'][0]['message']['content'][:100]}")
            results.append(result)
        else:
            print(f"❌ Perplexity API error: {response.status_code}")
            results.append({'provider': 'Perplexity', 'status': 'ERROR', 'error': f"HTTP {response.status_code}"})
    except Exception as e:
        print(f"❌ Perplexity error: {e}")
        results.append({'provider': 'Perplexity', 'status': 'ERROR', 'error': str(e)})
else:
    print("⏭️  Skipping Perplexity - no API key")

# Test Google
print("\n🔍 Testing Google...")
if api_keys['google']:
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_keys['google'])
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        response = model.generate_content(test_prompt)
        
        result = {
            'provider': 'Google',
            'status': 'SUCCESS',
            'response': response.text
        }
        print(f"✅ Google responded: {response.text[:100]}")
        results.append(result)
    except Exception as e:
        print(f"❌ Google error: {e}")
        results.append({'provider': 'Google', 'status': 'ERROR', 'error': str(e)})
else:
    print("⏭️  Skipping Google - no API key")

# Display final results
print("\n" + "="*60)
print("FINAL RESULTS")
print("="*60)

success_count = sum(1 for r in results if r['status'] == 'SUCCESS')
error_count = sum(1 for r in results if r['status'] == 'ERROR')

print(f"\n📊 Summary: {success_count} successful, {error_count} errors")

print("\n📝 Detailed Results:")
for result in results:
    print(f"\n[{result['provider']}]")
    print("-" * 40)
    if result['status'] == 'SUCCESS':
        print(f"✅ Status: SUCCESS")
        print(f"Response: {result['response']}")
    else:
        print(f"❌ Status: ERROR")
        if 'error' in result:
            print(f"Error: {result['error']}")

# Save results
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
filename = f"llm_test_{timestamp}.json"

with open(filename, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Results saved to: {filename}")

# Interactive prompt option
print("\n" + "="*60)
user_input = input("\n🤔 Want to try another prompt? Enter it here (or press Enter to skip): ").strip()

if user_input:
    print(f"\n📝 Testing with: '{user_input}'")
    print("-" * 40)
    
    # Just test with working providers
    for result in results:
        if result['status'] == 'SUCCESS':
            provider = result['provider']
            print(f"\n[{provider}]")
            
            try:
                if provider == 'Anthropic' and api_keys['anthropic']:
                    import anthropic
                    client = anthropic.Anthropic(api_key=api_keys['anthropic'])
                    response = client.messages.create(
                        model="claude-sonnet-4-6",
                        max_tokens=500,
                        messages=[{"role": "user", "content": user_input}]
                    )
                    print(f"Response: {response.content[0].text}")
                    
                elif provider == 'OpenAI' and api_keys['openai']:
                    import openai
                    try:
                        # Try new API
                        client = openai.OpenAI(api_key=api_keys['openai'])
                        response = client.chat.completions.create(
                            model="gpt-5.2",
                            messages=[{"role": "user", "content": user_input}],
                            max_tokens=500
                        )
                        print(f"Response: {response.choices[0].message.content}")
                    except AttributeError:
                        # Old API
                        openai.api_key = api_keys['openai']
                        response = openai.ChatCompletion.create(
                            model="gpt-5.2",
                            messages=[{"role": "user", "content": user_input}],
                            max_tokens=500
                        )
                        print(f"Response: {response.choices[0].message.content}")
                        
            except Exception as e:
                print(f"Error: {e}")

print("\n✅ Script complete!")
print("="*60)