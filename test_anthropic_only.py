#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_anthropic_detailed():
    """Probar Anthropic con detalles específicos"""
    try:
        print("🔍 Importando Anthropic...")
        import anthropic
        print("✅ Anthropic importado correctamente")
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        print(f"🔑 API Key: {api_key[:10]}..." if api_key else "❌ No API Key")
        
        if not api_key:
            print("❌ Anthropic API Key no encontrada")
            return False
            
        print("🔧 Creando cliente Anthropic...")
        
        # Intentar crear cliente sin argumentos adicionales
        try:
            client = anthropic.Anthropic(api_key=api_key)
            print("✅ Cliente Anthropic creado correctamente")
        except Exception as e:
            print(f"❌ Error creando cliente: {e}")
            print(f"Tipo de error: {type(e).__name__}")
            
            # Intentar con diferentes configuraciones
            print("🔄 Intentando configuraciones alternativas...")
            
            try:
                # Intentar sin argumentos de configuración adicionales
                client = anthropic.Anthropic(
                    api_key=api_key,
                    # Remover cualquier configuración de proxy
                )
                print("✅ Cliente creado con configuración mínima")
            except Exception as e2:
                print(f"❌ Error con configuración mínima: {e2}")
                return False
        
        print("📡 Probando conexión...")
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=[
                    {"role": "user", "content": "Responde solo con 'OK'"}
                ]
            )
            
            print("✅ Anthropic conectado correctamente")
            print(f"Respuesta: {message.content[0].text}")
            return True
            
        except Exception as e:
            print(f"❌ Error en la conexión: {e}")
            print(f"Tipo de error: {type(e).__name__}")
            return False
        
    except ImportError as e:
        print(f"❌ Error importando Anthropic: {e}")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        print(f"Tipo de error: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("🧪 Prueba detallada de Anthropic\n")
    result = test_anthropic_detailed()
    
    print(f"\n📊 Resultado: {'✅ Éxito' if result else '❌ Fallo'}")