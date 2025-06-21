#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar que todas las APIs de IA funcionen correctamente
con todos los tipos de análisis disponibles.
"""

import os
import sys
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Agregar el directorio actual al path para importar las funciones
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar las funciones de análisis
from app import (
    analyze_cv_with_openai,
    analyze_cv_with_anthropic, 
    analyze_cv_with_gemini,
    get_analysis_prompt
)

# CV de ejemplo para pruebas
SAMPLE_CV = """
Juan Pérez
Desarrollador Full Stack
Email: juan.perez@email.com
Teléfono: +1234567890

EXPERIENCIA PROFESIONAL:

Desarrollador Senior Full Stack | TechCorp (2020-2023)
• Desarrollé aplicaciones web usando React, Node.js y PostgreSQL
• Lideré un equipo de 5 desarrolladores en proyectos ágiles
• Implementé arquitecturas de microservicios que mejoraron el rendimiento en 40%
• Reduje el tiempo de carga de aplicaciones en 60% mediante optimizaciones

Desarrollador Junior | StartupXYZ (2018-2020)
• Creé interfaces de usuario responsivas con HTML, CSS y JavaScript
• Colaboré en el desarrollo de APIs RESTful
• Participé en revisiones de código y testing automatizado

EDUCACIÓN:
Ingeniería en Sistemas | Universidad Nacional (2014-2018)

HABILIDADES TÉCNICAS:
• Lenguajes: JavaScript, Python, Java, SQL
• Frameworks: React, Node.js, Express, Django
• Bases de datos: PostgreSQL, MongoDB, MySQL
• Herramientas: Git, Docker, AWS, Jenkins

IDIOMAS:
• Español (Nativo)
• Inglés (Avanzado)
"""

# Tipos de análisis disponibles
ANALYSIS_TYPES = [
    'general_health_check',
    'content_quality_analysis', 
    'job_tailoring_optimization',
    'ats_compatibility_verification',
    'tone_style_evaluation',
    'industry_role_feedback',
    'benchmarking_comparison',
    'ai_improvement_suggestions',
    'visual_design_assessment',
    'comprehensive_score'
]

# Proveedores de IA
AI_PROVIDERS = {
    'OpenAI': analyze_cv_with_openai,
    'Anthropic': analyze_cv_with_anthropic,
    'Gemini': analyze_cv_with_gemini
}

def test_api_key_configuration():
    """Verificar que las API keys estén configuradas"""
    print("🔑 Verificando configuración de API Keys...")
    
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    print(f"OpenAI API Key: {'✅ Configurada' if openai_key and openai_key != 'your_openai_api_key_here' else '❌ No configurada'}")
    print(f"Anthropic API Key: {'✅ Configurada' if anthropic_key and anthropic_key != 'your_anthropic_api_key_here' else '❌ No configurada'}")
    print(f"Gemini API Key: {'✅ Configurada' if gemini_key and gemini_key != 'your_gemini_api_key_here' else '❌ No configurada'}")
    print()

def test_single_analysis(provider_name, analyze_function, analysis_type):
    """Probar un análisis específico con un proveedor"""
    try:
        print(f"  📊 Probando {analysis_type}...")
        result = analyze_function(SAMPLE_CV, analysis_type)
        
        # Verificar que el resultado tenga la estructura esperada
        required_fields = ['score', 'strengths', 'weaknesses', 'recommendations', 'keywords', 'analysis_type']
        missing_fields = [field for field in required_fields if field not in result]
        
        if missing_fields:
            print(f"    ❌ Campos faltantes: {missing_fields}")
            return False
        
        # Solo considerar error si el resultado indica explícitamente un error
        if result.get('error') and ('Error' in str(result.get('detailed_feedback', '')) or result.get('score', 0) == 0):
            print(f"    ❌ Error: {result.get('detailed_feedback', 'Error desconocido')}")
            return False
        
        # Verificar tipos de datos
        if not isinstance(result['score'], (int, float)) or not (0 <= result['score'] <= 100):
            print(f"    ❌ Score inválido: {result['score']}")
            return False
        
        if not isinstance(result['strengths'], list) or len(result['strengths']) == 0:
            print(f"    ❌ Strengths inválidas: {result['strengths']}")
            return False
        
        print(f"    ✅ Exitoso - Score: {result['score']}/100")
        return True
        
    except Exception as e:
        print(f"    ❌ Error de excepción: {str(e)}")
        return False

def test_provider(provider_name, analyze_function):
    """Probar todos los tipos de análisis para un proveedor específico"""
    print(f"🤖 Probando {provider_name}...")
    
    success_count = 0
    total_count = len(ANALYSIS_TYPES)
    
    for analysis_type in ANALYSIS_TYPES:
        if test_single_analysis(provider_name, analyze_function, analysis_type):
            success_count += 1
    
    success_rate = (success_count / total_count) * 100
    print(f"  📈 Resultado: {success_count}/{total_count} exitosos ({success_rate:.1f}%)")
    print()
    
    return success_count, total_count

def main():
    """Función principal de pruebas"""
    print("🚀 Iniciando pruebas de proveedores de IA para análisis de CV")
    print("=" * 60)
    print()
    
    # Verificar configuración
    test_api_key_configuration()
    
    # Probar cada proveedor
    total_success = 0
    total_tests = 0
    
    for provider_name, analyze_function in AI_PROVIDERS.items():
        success, tests = test_provider(provider_name, analyze_function)
        total_success += success
        total_tests += tests
    
    # Resumen final
    print("📊 RESUMEN FINAL")
    print("=" * 30)
    overall_success_rate = (total_success / total_tests) * 100 if total_tests > 0 else 0
    print(f"Total de pruebas exitosas: {total_success}/{total_tests} ({overall_success_rate:.1f}%)")
    
    if overall_success_rate >= 90:
        print("🎉 ¡Excelente! Todos los proveedores funcionan correctamente.")
    elif overall_success_rate >= 70:
        print("⚠️  La mayoría de los proveedores funcionan, pero hay algunos problemas.")
    else:
        print("❌ Hay problemas significativos que necesitan ser resueltos.")
    
    print("\n💡 Notas importantes:")
    print("- Si algún proveedor falla, verifica que la API Key esté configurada correctamente")
    print("- Los errores de 'Librería no instalada' indican que faltan dependencias")
    print("- Los errores de JSON indican problemas en el formato de respuesta de la IA")

if __name__ == "__main__":
    main()