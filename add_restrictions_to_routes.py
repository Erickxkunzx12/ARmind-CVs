#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para agregar restricciones de suscripción a las rutas principales
"""

import re

def add_restrictions_to_app():
    """Agregar restricciones a las rutas principales en app.py"""
    
    # Leer el archivo app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar si ya se importaron las funciones de restricción
    if 'from subscription_system import check_user_limits, increment_usage' not in content:
        # Agregar import después de las otras importaciones
        import_pattern = r'(from flask import.*?\n)'
        replacement = r'\1from subscription_system import check_user_limits, increment_usage\n'
        content = re.sub(import_pattern, replacement, content, count=1)
        print("✅ Importaciones de restricciones agregadas")
    else:
        print("✅ Importaciones ya presentes")
    
    # Agregar restricciones a la ruta analyze_cv
    analyze_cv_pattern = r'(@app\.route\("/analyze_cv".*?\n@login_required\ndef analyze_cv\(\):.*?\n)(.*?)(if request\.method == "POST":)'
    
    restriction_code_analyze = '''    # Verificar restricciones de suscripción
    user_id = session.get('user_id')
    can_analyze, message = check_user_limits(user_id, 'cv_analysis')
    
    if not can_analyze:
        flash(f'Restricción de plan: {message}', 'error')
        return redirect(url_for('dashboard'))
    
    '''
    
    if 'check_user_limits(user_id, \'cv_analysis\')' not in content:
        content = re.sub(
            analyze_cv_pattern,
            r'\1' + restriction_code_analyze + r'\3',
            content,
            flags=re.DOTALL
        )
        print("✅ Restricciones agregadas a analyze_cv")
    else:
        print("✅ Restricciones ya presentes en analyze_cv")
    
    # Agregar restricciones a la ruta create_cv
    create_cv_pattern = r'(@app\.route\("/create_cv".*?\n@login_required\ndef create_cv\(\):.*?\n)(.*?)(return render_template)'
    
    restriction_code_create = '''    # Verificar restricciones de suscripción
    user_id = session.get('user_id')
    can_create, message = check_user_limits(user_id, 'cv_creation')
    
    if not can_create:
        flash(f'Restricción de plan: {message}', 'error')
        return redirect(url_for('dashboard'))
    
    '''
    
    if 'check_user_limits(user_id, \'cv_creation\')' not in content:
        content = re.sub(
            create_cv_pattern,
            r'\1' + restriction_code_create + r'\3',
            content,
            flags=re.DOTALL
        )
        print("✅ Restricciones agregadas a create_cv")
    else:
        print("✅ Restricciones ya presentes en create_cv")
    
    # Agregar incremento de uso después del análisis exitoso
    # Buscar donde se procesa el CV exitosamente
    success_pattern = r'(session\["cv_text"\] = extracted_text.*?\n)(.*?)(return redirect\(url_for\("select_ai_provider"\)\))'
    
    increment_code = '''        # Incrementar contador de uso
        increment_usage(session.get('user_id'), 'cv_analysis')
        
        '''
    
    if 'increment_usage(session.get(\'user_id\'), \'cv_analysis\')' not in content:
        content = re.sub(
            success_pattern,
            r'\1' + increment_code + r'\3',
            content,
            flags=re.DOTALL
        )
        print("✅ Incremento de uso agregado al análisis")
    else:
        print("✅ Incremento de uso ya presente en análisis")
    
    # Escribir el archivo modificado
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n✅ Restricciones implementadas en app.py")
    return True

def create_middleware_decorator():
    """Crear un decorador para verificar restricciones"""
    
    decorator_code = '''
# Decorador para verificar restricciones de suscripción
from functools import wraps
from flask import session, flash, redirect, url_for
from subscription_system import check_user_limits, increment_usage

def require_subscription_limit(action_type, increment_on_success=False):
    """Decorador para verificar límites de suscripción"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                flash('Debes iniciar sesión', 'error')
                return redirect(url_for('login'))
            
            # Verificar límites
            can_perform, message = check_user_limits(user_id, action_type)
            if not can_perform:
                flash(f'Restricción de plan: {message}', 'error')
                return redirect(url_for('dashboard'))
            
            # Ejecutar la función original
            result = f(*args, **kwargs)
            
            # Incrementar uso si es exitoso
            if increment_on_success and result:
                increment_usage(user_id, action_type)
            
            return result
        return decorated_function
    return decorator
'''
    
    with open('subscription_decorators.py', 'w', encoding='utf-8') as f:
        f.write(decorator_code)
    
    print("✅ Decorador de restricciones creado en subscription_decorators.py")
    return True

def verify_implementation():
    """Verificar que las restricciones estén implementadas"""
    print("\n🔍 Verificando implementación de restricciones...")
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('Importación de funciones', 'from subscription_system import check_user_limits, increment_usage'),
        ('Restricción en analyze_cv', 'check_user_limits(user_id, \'cv_analysis\')'),
        ('Restricción en create_cv', 'check_user_limits(user_id, \'cv_creation\')'),
        ('Incremento de uso', 'increment_usage(session.get(\'user_id\'), \'cv_analysis\')'),
    ]
    
    all_present = True
    for check_name, pattern in checks:
        if pattern in content:
            print(f"  ✅ {check_name}: Implementado")
        else:
            print(f"  ❌ {check_name}: NO implementado")
            all_present = False
    
    return all_present

if __name__ == "__main__":
    print("🔧 IMPLEMENTANDO RESTRICCIONES EN RUTAS PRINCIPALES")
    print("=" * 60)
    
    try:
        # Agregar restricciones a app.py
        add_restrictions_to_app()
        
        # Crear decorador auxiliar
        create_middleware_decorator()
        
        # Verificar implementación
        success = verify_implementation()
        
        if success:
            print("\n🎉 RESTRICCIONES IMPLEMENTADAS CORRECTAMENTE")
            print("\n📋 Próximos pasos:")
            print("   1. Reinicia la aplicación Flask")
            print("   2. Prueba con diferentes usuarios")
            print("   3. Verifica que las restricciones funcionen")
        else:
            print("\n⚠️  IMPLEMENTACIÓN INCOMPLETA")
            print("   Revisa manualmente las rutas en app.py")
            
    except Exception as e:
        print(f"\n💥 Error durante la implementación: {e}")
        import traceback
        traceback.print_exc()