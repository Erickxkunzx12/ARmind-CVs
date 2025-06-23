#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio actual al path para importar desde app.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("🧪 Prueba de análisis de CV con Anthropic\n")

try:
    from app import analyze_cv_with_anthropic
    
    # Texto de CV de prueba
    cv_text = """
    Juan Pérez
    Ingeniero de Software
    
    Experiencia:
    - 3 años como desarrollador Python
    - Experiencia con Flask, Django
    - Conocimientos en bases de datos PostgreSQL
    - Trabajo en equipo y metodologías ágiles
    
    Educación:
    - Ingeniería en Informática, Universidad XYZ
    
    Habilidades:
    - Python, JavaScript, SQL
    - Git, Docker
    - Inglés intermedio
    """
    
    print("📄 Texto de CV de prueba preparado")
    print("🔍 Iniciando análisis con Anthropic...\n")
    
    # Probar análisis general
    result = analyze_cv_with_anthropic("general", cv_text)
    
    print("📊 Resultado del análisis:")
    print(f"Tipo: {type(result)}")
    
    if isinstance(result, dict):
        print("✅ Análisis completado exitosamente")
        print(f"Proveedor: {result.get('ai_provider', 'No especificado')}")
        print(f"Tipo de análisis: {result.get('analysis_type', 'No especificado')}")
        print(f"Puntuación: {result.get('score', 'No disponible')}")
        
        if 'strengths' in result:
            print(f"Fortalezas encontradas: {len(result['strengths'])}")
        if 'weaknesses' in result:
            print(f"Debilidades encontradas: {len(result['weaknesses'])}")
        if 'recommendations' in result:
            print(f"Recomendaciones: {len(result['recommendations'])}")
        if 'keywords' in result:
            print(f"Palabras clave: {len(result['keywords'])}")
            
        print("\n🎉 ¡Anthropic está funcionando correctamente para análisis de CV!")
    else:
        print(f"❌ Resultado inesperado: {result}")
        
except ImportError as e:
    print(f"❌ Error de importación: {e}")
except Exception as e:
    print(f"❌ Error durante el análisis: {e}")
    import traceback
    traceback.print_exc()