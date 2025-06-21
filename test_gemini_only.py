#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import analyze_cv_with_gemini

print("🧪 Probando Gemini específicamente...")

cv_text = "Ingeniero de Software con 5 años de experiencia en Python y JavaScript. Especializado en desarrollo web y APIs REST."
analysis_type = "general_health_check"

try:
    result = analyze_cv_with_gemini(cv_text, analysis_type)
    print(f"✅ Resultado Gemini: {result}")
    
    if 'error' in str(result).lower():
        print("❌ Gemini devolvió un error")
    else:
        print("✅ Gemini funcionó correctamente")
        
except Exception as e:
    print(f"❌ Error ejecutando Gemini: {e}")
    import traceback
    traceback.print_exc()