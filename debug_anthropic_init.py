#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import inspect

print("🔍 Debugging Anthropic initialization issue...\n")

try:
    # Check if anthropic is already imported
    if 'anthropic' in sys.modules:
        print("⚠️ Anthropic already imported, removing from cache...")
        del sys.modules['anthropic']
    
    # Import anthropic fresh
    import anthropic
    print(f"✅ Anthropic imported successfully, version: {anthropic.__version__}")
    
    # Get the original __init__ method
    original_init = anthropic.Anthropic.__init__
    print(f"\n🔍 Original __init__ method: {original_init}")
    
    # Check if __init__ has been monkey patched
    print(f"\n🔍 __init__ source file: {inspect.getfile(original_init)}")
    
    # Try to get the signature
    try:
        sig = inspect.signature(original_init)
        print(f"\n📋 Method signature: {sig}")
        
        # Check each parameter
        for name, param in sig.parameters.items():
            if name != 'self':
                print(f"  Parameter: {name} = {param}")
                
        # Check if 'proxies' is in parameters
        if 'proxies' in sig.parameters:
            print("\n⚠️ 'proxies' parameter found in signature!")
        else:
            print("\n✅ No 'proxies' parameter in signature")
            
    except Exception as e:
        print(f"\n❌ Error getting signature: {e}")
    
    # Try to create a wrapper to see what arguments are being passed
    def debug_init(self, *args, **kwargs):
        print(f"\n🐛 __init__ called with:")
        print(f"  args: {args}")
        print(f"  kwargs: {kwargs}")
        
        # Check if proxies is in kwargs
        if 'proxies' in kwargs:
            print(f"\n⚠️ Found 'proxies' in kwargs: {kwargs['proxies']}")
            print("\n🔧 Removing 'proxies' from kwargs...")
            del kwargs['proxies']
        
        # Call original method
        return original_init(self, *args, **kwargs)
    
    # Monkey patch for debugging
    anthropic.Anthropic.__init__ = debug_init
    
    print("\n🧪 Testing client creation with debug wrapper...")
    
    try:
        client = anthropic.Anthropic(api_key="test_key")
        print("✅ Client created successfully with debug wrapper!")
    except Exception as e:
        print(f"❌ Still failed with debug wrapper: {e}")
        
except Exception as e:
    print(f"❌ Error during debugging: {e}")
    import traceback
    traceback.print_exc()