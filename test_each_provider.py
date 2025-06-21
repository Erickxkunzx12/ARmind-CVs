#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import analyze_cv_with_openai, analyze_cv_with_anthropic, analyze_cv_with_gemini

print("🧪 Probando cada proveedor individualmente...")

cv_text = "Ingeniero de Software con 5 años de experiencia en Python y JavaScript."
analysis_type = "general_health_check"

providers = {
    'OpenAI': analyze_cv_with_openai,
    'Anthropic': analyze_cv_with_anthropic,
    'Gemini': analyze_cv_with_gemini
}

for name, func in providers.items():
    print(f"\n🤖 Probando {name}...")
    try:
        result = func(cv_text, analysis_type)
        
        # Verificar campos requeridos
        required_fields = ['score', 'strengths', 'weaknesses', 'recommendations', 'keywords', 'analysis_type']
        missing_fields = [field for field in required_fields if field not in result]
        
        if missing_fields:
            print(f"    ❌ Campos faltantes: {missing_fields}")
        elif result.get('error') and ('Error' in str(result.get('detailed_feedback', '')) or result.get('score', 0) == 0):
            print(f"    ❌ Error: {result.get('detailed_feedback', 'Error desconocido')}")
        elif not isinstance(result['score'], (int, float)) or not (0 <= result['score'] <= 100):
            print(f"    ❌ Score inválido: {result['score']}")
        elif not isinstance(result['strengths'], list) or len(result['strengths']) == 0:
            print(f"    ❌ Strengths inválidas: {result['strengths']}")
        else:
            print(f"    ✅ Exitoso - Score: {result['score']}/100")
            
    except Exception as e:
        print(f"    ❌ Error de excepción: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n🏁 Test completado")