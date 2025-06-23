#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🧪 Testing minimal Anthropic setup...\n")

try:
    # Try importing without any initialization
    import anthropic
    print(f"✅ Anthropic imported, version: {anthropic.__version__}")
    
    # Get API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key or api_key == 'your_anthropic_api_key_here':
        print("❌ API key not configured properly")
        exit(1)
    
    print(f"✅ API key found: {api_key[:10]}...")
    
    # Try creating client with minimal parameters
    print("\n🔧 Attempting client creation with minimal parameters...")
    
    try:
        # Method 1: Only api_key
        client = anthropic.Anthropic(api_key=api_key)
        print("✅ Method 1: Client created successfully with only api_key")
        
        # Test a simple message
        print("\n📤 Testing message creation...")
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=50,
            messages=[
                {"role": "user", "content": "Say hello in one word."}
            ]
        )
        print(f"✅ Response received: {response.content[0].text}")
        
    except TypeError as e:
        if "proxies" in str(e):
            print(f"❌ Still getting proxies error: {e}")
            
            # Try with explicit None for proxies
            print("\n🔧 Trying with explicit proxies=None...")
            try:
                client = anthropic.Anthropic(api_key=api_key, proxies=None)
                print("✅ Method 2: Client created with proxies=None")
            except Exception as e2:
                print(f"❌ Method 2 failed: {e2}")
                
                # Try without any optional parameters
                print("\n🔧 Trying to bypass the issue...")
                try:
                    # Create a custom client class that ignores proxies
                    class CustomAnthropicClient(anthropic.Anthropic):
                        def __init__(self, api_key, **kwargs):
                            # Remove problematic parameters
                            kwargs.pop('proxies', None)
                            super().__init__(api_key=api_key, **kwargs)
                    
                    client = CustomAnthropicClient(api_key=api_key)
                    print("✅ Method 3: Custom client created successfully")
                    
                except Exception as e3:
                    print(f"❌ Method 3 failed: {e3}")
        else:
            print(f"❌ Different TypeError: {e}")
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ General error: {e}")
    import traceback
    traceback.print_exc()