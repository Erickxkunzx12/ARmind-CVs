#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
    import anthropic
    print("✅ Anthropic importado correctamente")
except ImportError as e:
    print(f"❌ Error importando Anthropic: {e}")

try:
    import google.generativeai as genai
    print("✅ Google Generative AI importado correctamente")
except ImportError as e:
    print(f"❌ Error importando Google Generative AI: {e}")

try:
    import openai
    print("✅ OpenAI importado correctamente")
except ImportError as e:
    print(f"❌ Error importando OpenAI: {e}")

print("\n🔧 Test de importaciones completado")