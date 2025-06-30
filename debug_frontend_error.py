#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de diagnóstico para errores de frontend en comparación CV-Trabajo
Este script ayuda a identificar problemas específicos en el frontend
"""

import json
import os
from datetime import datetime

def create_test_result():
    """Crear un resultado de prueba para verificar el template"""
    test_result = {
        "match_percentage": 75,
        "strengths": [
            "Experiencia relevante en el área",
            "Habilidades técnicas alineadas",
            "Formación académica adecuada"
        ],
        "keywords_found": [
            "Python",
            "JavaScript",
            "React",
            "SQL"
        ],
        "improvements": [
            "Agregar más detalles sobre proyectos específicos",
            "Incluir certificaciones relevantes",
            "Mejorar la descripción de logros cuantificables"
        ],
        "summary": "El candidato muestra una buena compatibilidad con la oferta laboral, especialmente en habilidades técnicas. Se recomienda optimizar algunas secciones para aumentar la relevancia."
    }
    return test_result

def check_template_syntax():
    """Verificar sintaxis del template"""
    template_path = "templates/cv_job_comparison_result.html"
    
    if not os.path.exists(template_path):
        print(f"❌ Template no encontrado: {template_path}")
        return False
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Verificar elementos críticos
        critical_elements = [
            "{{ result.match_percentage|default(0) }}",
            "{% if result and result.strengths",
            "{% if result and result.keywords_found",
            "{% if result and result.improvements",
            "{{ result.summary|default("
        ]
        
        missing_elements = []
        for element in critical_elements:
            if element not in content:
                missing_elements.append(element)
        
        if missing_elements:
            print("❌ Elementos críticos faltantes en el template:")
            for element in missing_elements:
                print(f"   - {element}")
            return False
        else:
            print("✅ Template contiene todos los elementos críticos")
            return True
            
    except Exception as e:
        print(f"❌ Error leyendo template: {e}")
        return False

def generate_debug_report():
    """Generar reporte de diagnóstico"""
    print("🔍 DIAGNÓSTICO DE ERROR FRONTEND - COMPARACIÓN CV-TRABAJO")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Verificar template
    print("1. VERIFICACIÓN DE TEMPLATE:")
    template_ok = check_template_syntax()
    print()
    
    # 2. Crear resultado de prueba
    print("2. RESULTADO DE PRUEBA:")
    test_result = create_test_result()
    print(f"✅ Resultado de prueba generado: {json.dumps(test_result, indent=2, ensure_ascii=False)}")
    print()
    
    # 3. Recomendaciones
    print("3. RECOMENDACIONES PARA DEBUGGING:")
    print("   a) Abrir las herramientas de desarrollador del navegador (F12)")
    print("   b) Ir a la pestaña 'Console' para ver errores JavaScript")
    print("   c) Ir a la pestaña 'Network' para ver errores de red")
    print("   d) Verificar si hay errores 404 o 500 en las peticiones")
    print("   e) Limpiar cache del navegador (Ctrl+Shift+R)")
    print()
    
    # 4. Posibles causas
    print("4. POSIBLES CAUSAS DEL ERROR:")
    print("   ❓ Cache del navegador desactualizado")
    print("   ❓ Error JavaScript en el template")
    print("   ❓ Problema con la librería Chart.js")
    print("   ❓ Conflicto con otros scripts")
    print("   ❓ Problema de codificación de caracteres")
    print()
    
    # 5. Soluciones sugeridas
    print("5. SOLUCIONES SUGERIDAS:")
    print("   🔧 Limpiar cache del navegador completamente")
    print("   🔧 Probar en modo incógnito/privado")
    print("   🔧 Probar en otro navegador")
    print("   🔧 Verificar la consola del navegador para errores específicos")
    print("   🔧 Reiniciar el servidor Flask")
    print()
    
    return template_ok

if __name__ == "__main__":
    success = generate_debug_report()
    
    if success:
        print("✅ DIAGNÓSTICO COMPLETADO - Template parece estar correcto")
        print("💡 El problema probablemente está en el frontend/navegador")
    else:
        print("❌ DIAGNÓSTICO COMPLETADO - Se encontraron problemas en el template")
        print("💡 Revisar y corregir los elementos faltantes")
    
    print("\n📋 PRÓXIMOS PASOS:")
    print("1. Ejecutar este diagnóstico")
    print("2. Revisar la consola del navegador")
    print("3. Limpiar cache y probar nuevamente")
    print("4. Reportar errores específicos de la consola del navegador")