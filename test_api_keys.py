#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_openai():
    """Probar configuración de OpenAI"""
    try:
        import openai
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            print("❌ OpenAI API Key no encontrada")
            return False
            
        if api_key == 'your_openai_api_key_here':
            print("❌ OpenAI API Key no configurada (valor por defecto)")
            return False
            
        print(f"✅ OpenAI API Key configurada: {api_key[:10]}...")
        
        # Probar conexión simple
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Responde solo con 'OK' si puedes leer este mensaje"}
            ],
            max_tokens=10
        )
        
        print("✅ OpenAI conectado correctamente")
        print(f"Respuesta: {response.choices[0].message.content}")
        return True
        
    except ImportError:
        print("❌ Librería openai no instalada")
        return False
    except Exception as e:
        print(f"❌ Error con OpenAI: {e}")
        return False

def test_anthropic():
    """Probar configuración de Anthropic"""
    try:
        import anthropic
        api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not api_key:
            print("❌ Anthropic API Key no encontrada")
            return False
            
        if api_key == 'your_anthropic_api_key_here':
            print("❌ Anthropic API Key no configurada (valor por defecto)")
            return False
            
        print(f"✅ Anthropic API Key configurada: {api_key[:10]}...")
        
        # Probar conexión simple
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[
                {"role": "user", "content": "Responde solo con 'OK'"}
            ]
        )
        
        print("✅ Anthropic conectado correctamente")
        print(f"Respuesta: {response.content[0].text}")
        return True
        
    except ImportError:
        print("❌ Librería anthropic no instalada")
        return False
    except Exception as e:
        print(f"❌ Error con Anthropic: {e}")
        return False

def test_gemini():
    """Probar configuración de Gemini"""
    try:
        import google.generativeai as genai
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            print("❌ Gemini API Key no encontrada")
            return False
            
        if api_key == 'your_gemini_api_key_here':
            print("❌ Gemini API Key no configurada (valor por defecto)")
            return False
            
        print(f"✅ Gemini API Key configurada: {api_key[:10]}...")
        
        # Probar conexión simple
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Responde solo con 'OK'")
        
        print("✅ Gemini conectado correctamente")
        print(f"Respuesta: {response.text}")
        return True
        
    except ImportError:
        print("❌ Librería google-generativeai no instalada")
        return False
    except Exception as e:
        print(f"❌ Error con Gemini: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Probando configuración de APIs de IA...\n")
    
    results = {
        "OpenAI": test_openai(),
        "Anthropic": test_anthropic(), 
        "Gemini": test_gemini()
    }
    
    print("\n📊 Resumen:")
    working_apis = []
    for api, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {api}: {'Funcionando' if status else 'Con problemas'}")
        if status:
            working_apis.append(api)
    
    if working_apis:
        print(f"\n🎉 APIs funcionando: {', '.join(working_apis)}")
        print("La aplicación debería poder realizar análisis.")
    else:
        print("\n⚠️ Ninguna API está funcionando correctamente.")
        print("Revisa las configuraciones y conexión a internet.")