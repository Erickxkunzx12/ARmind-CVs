#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import importlib.util
import os

print("=== DIAGNÓSTICO DE GOOGLE GENERATIVE AI ===")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Verificar si el módulo está instalado
spec = importlib.util.find_spec("google.generativeai")
if spec is None:
    print("❌ google.generativeai no encontrado en el sistema")
    
    # Buscar manualmente
    for path in sys.path:
        google_path = os.path.join(path, 'google')
        if os.path.exists(google_path) and os.path.isdir(google_path):
            print(f"📁 Directorio google encontrado en: {google_path}")
            contents = os.listdir(google_path)
            print(f"   Contenido: {contents}")
            
            genai_path = os.path.join(google_path, 'generativeai')
            if os.path.exists(genai_path):
                print(f"✅ generativeai encontrado en: {genai_path}")
                if os.path.isdir(genai_path):
                    genai_contents = os.listdir(genai_path)
                    print(f"   Contenido de generativeai: {genai_contents[:10]}...")  # Primeros 10
else:
    print(f"✅ google.generativeai encontrado en: {spec.origin}")

# Intentar diferentes formas de importar
print("\n=== INTENTOS DE IMPORTACIÓN ===")

# Método 1: Importación directa
try:
    import google.generativeai as genai
    print("✅ Método 1: import google.generativeai as genai - ÉXITO")
    print(f"   Ubicación: {genai.__file__}")
    print(f"   Versión: {getattr(genai, '__version__', 'No disponible')}")
except ImportError as e:
    print(f"❌ Método 1: import google.generativeai as genai - FALLO: {e}")

# Método 2: Importación desde google
try:
    from google import generativeai as genai2
    print("✅ Método 2: from google import generativeai - ÉXITO")
    print(f"   Ubicación: {genai2.__file__}")
except ImportError as e:
    print(f"❌ Método 2: from google import generativeai - FALLO: {e}")

# Método 3: Importación del módulo google primero
try:
    import google
    print(f"✅ Módulo google importado desde: {google.__file__}")
    print(f"   Contenido del módulo google: {dir(google)}")
    
    # Ahora intentar generativeai
    import google.generativeai as genai3
    print("✅ Método 3: google.generativeai después de importar google - ÉXITO")
except ImportError as e:
    print(f"❌ Método 3: FALLO: {e}")

# Método 4: Verificar namespace packages
try:
    import google
    print(f"\nNamespace info para google: {google.__path__}")
except:
    pass

print("\n=== FIN DEL DIAGNÓSTICO ===")