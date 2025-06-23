#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import inspect

try:
    import anthropic
    print(f"✅ Versión Anthropic: {anthropic.__version__}")
    
    # Inspeccionar la función __init__
    print("\n🔍 Parámetros de anthropic.Anthropic.__init__:")
    sig = inspect.signature(anthropic.Anthropic.__init__)
    for param_name, param in sig.parameters.items():
        if param_name != 'self':
            print(f"  {param_name}: {param}")
    
    print("\n🔍 Documentación de __init__:")
    print(anthropic.Anthropic.__init__.__doc__)
    
    print("\n🧪 Intentando crear cliente con diferentes configuraciones...")
    
    # Intentar con solo api_key
    try:
        client = anthropic.Anthropic(api_key="test")
        print("✅ Cliente creado con solo api_key")
    except Exception as e:
        print(f"❌ Error con solo api_key: {e}")
    
except ImportError as e:
    print(f"❌ Error importando Anthropic: {e}")
except Exception as e:
    print(f"❌ Error general: {e}")