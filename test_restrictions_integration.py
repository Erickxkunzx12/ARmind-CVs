#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para probar la integración de restricciones en las rutas principales
"""

import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración del servidor
BASE_URL = "http://localhost:5000"

# Usuarios de prueba
TEST_USERS = {
    'admin': {
        'email': 'admin@armind.test',
        'password': 'admin123',
        'expected_plan': None
    },
    'free': {
        'email': 'free@armind.test', 
        'password': 'free123',
        'expected_plan': 'free_trial'
    },
    'standard': {
        'email': 'standard@armind.test',
        'password': 'standard123',
        'expected_plan': 'standard'
    },
    'pro': {
        'email': 'pro@armind.test',
        'password': 'pro123',
        'expected_plan': 'pro'
    }
}

class RestrictionsIntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.logged_in_users = {}
    
    def login_user(self, user_type):
        """Iniciar sesión con un usuario específico"""
        if user_type in self.logged_in_users:
            return self.logged_in_users[user_type]
        
        user_data = TEST_USERS[user_type]
        
        # Intentar login
        login_data = {
            'email': user_data['email'],
            'password': user_data['password']
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
            
            if response.status_code in [200, 302]:  # Login exitoso
                print(f"  ✅ Login exitoso para {user_type}")
                self.logged_in_users[user_type] = True
                return True
            else:
                print(f"  ❌ Login fallido para {user_type}: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ Error en login para {user_type}: {e}")
            return False
    
    def test_usage_check_api(self, user_type, action_type):
        """Probar la API de verificación de uso"""
        if not self.login_user(user_type):
            return False, "Login fallido"
        
        try:
            response = self.session.post(f"{BASE_URL}/usage/check", 
                                       json={'action_type': action_type})
            
            if response.status_code == 200:
                data = response.json()
                return data.get('allowed', False), data.get('message', 'Sin mensaje')
            else:
                return False, f"Error HTTP {response.status_code}"
                
        except Exception as e:
            return False, f"Error: {e}"
    
    def test_usage_increment_api(self, user_type, resource_type):
        """Probar la API de incremento de uso"""
        if not self.login_user(user_type):
            return False, "Login fallido"
        
        try:
            response = self.session.post(f"{BASE_URL}/usage/increment",
                                       json={'resource_type': resource_type})
            
            if response.status_code == 200:
                data = response.json()
                return data.get('success', False), data.get('message', 'Sin mensaje')
            else:
                return False, f"Error HTTP {response.status_code}"
                
        except Exception as e:
            return False, f"Error: {e}"
    
    def test_cv_analysis_route(self, user_type):
        """Probar acceso a la ruta de análisis de CV"""
        if not self.login_user(user_type):
            return False, "Login fallido"
        
        try:
            # Crear un archivo de prueba simple
            test_file = {'cv_file': ('test.txt', 'Contenido de prueba CV', 'text/plain')}
            
            response = self.session.post(f"{BASE_URL}/analyze_cv", 
                                       files=test_file, 
                                       allow_redirects=False)
            
            # Verificar si la respuesta indica restricción o éxito
            if response.status_code == 403:
                return False, "Acceso denegado por restricciones"
            elif response.status_code in [200, 302]:
                return True, "Acceso permitido"
            else:
                return False, f"Respuesta inesperada: {response.status_code}"
                
        except Exception as e:
            return False, f"Error: {e}"
    
    def test_cv_creation_route(self, user_type):
        """Probar acceso a la ruta de creación de CV"""
        if not self.login_user(user_type):
            return False, "Login fallido"
        
        try:
            response = self.session.get(f"{BASE_URL}/create_cv")
            
            if response.status_code == 403:
                return False, "Acceso denegado por restricciones"
            elif response.status_code == 200:
                return True, "Acceso permitido"
            else:
                return False, f"Respuesta inesperada: {response.status_code}"
                
        except Exception as e:
            return False, f"Error: {e}"
    
    def test_subscription_info(self, user_type):
        """Obtener información de suscripción del usuario"""
        if not self.login_user(user_type):
            return None, "Login fallido"
        
        try:
            response = self.session.get(f"{BASE_URL}/my_subscription")
            
            if response.status_code == 200:
                # Buscar información del plan en el HTML
                content = response.text
                if 'Free Trial' in content:
                    return 'free_trial', "Plan detectado en página"
                elif 'Standard' in content:
                    return 'standard', "Plan detectado en página"
                elif 'Pro' in content:
                    return 'pro', "Plan detectado en página"
                elif 'admin' in user_type.lower():
                    return 'admin', "Usuario administrador"
                else:
                    return 'unknown', "Plan no detectado"
            else:
                return None, f"Error HTTP {response.status_code}"
                
        except Exception as e:
            return None, f"Error: {e}"
    
    def run_comprehensive_test(self):
        """Ejecutar pruebas completas del sistema de restricciones"""
        print("🧪 PRUEBAS DE INTEGRACIÓN DE RESTRICCIONES")
        print("=" * 50)
        
        # Verificar que el servidor esté ejecutándose
        try:
            response = requests.get(BASE_URL, timeout=5)
            print(f"✅ Servidor accesible en {BASE_URL}")
        except:
            print(f"❌ Servidor NO accesible en {BASE_URL}")
            print("   Asegúrate de que la aplicación Flask esté ejecutándose")
            return False
        
        results = {}
        
        for user_type in TEST_USERS.keys():
            print(f"\n👤 Probando usuario: {user_type.upper()}")
            
            user_results = {
                'login': False,
                'subscription_info': None,
                'cv_analysis_check': None,
                'cv_creation_check': None,
                'cv_analysis_route': None,
                'cv_creation_route': None
            }
            
            # Test 1: Login
            user_results['login'] = self.login_user(user_type)
            
            if user_results['login']:
                # Test 2: Información de suscripción
                plan, msg = self.test_subscription_info(user_type)
                user_results['subscription_info'] = (plan, msg)
                print(f"  📋 Plan detectado: {plan} - {msg}")
                
                # Test 3: API de verificación de límites
                allowed, msg = self.test_usage_check_api(user_type, 'cv_analysis')
                user_results['cv_analysis_check'] = (allowed, msg)
                print(f"  📊 Check análisis CV: {'✅' if allowed else '❌'} - {msg}")
                
                allowed, msg = self.test_usage_check_api(user_type, 'cv_creation')
                user_results['cv_creation_check'] = (allowed, msg)
                print(f"  📝 Check creación CV: {'✅' if allowed else '❌'} - {msg}")
                
                # Test 4: Rutas principales
                allowed, msg = self.test_cv_analysis_route(user_type)
                user_results['cv_analysis_route'] = (allowed, msg)
                print(f"  🔍 Ruta análisis CV: {'✅' if allowed else '❌'} - {msg}")
                
                allowed, msg = self.test_cv_creation_route(user_type)
                user_results['cv_creation_route'] = (allowed, msg)
                print(f"  ✏️  Ruta creación CV: {'✅' if allowed else '❌'} - {msg}")
            
            results[user_type] = user_results
        
        # Generar reporte final
        self.generate_final_report(results)
        
        return results
    
    def generate_final_report(self, results):
        """Generar reporte final de las pruebas"""
        print("\n📊 REPORTE FINAL DE RESTRICCIONES")
        print("=" * 50)
        
        all_passed = True
        
        for user_type, user_results in results.items():
            expected_plan = TEST_USERS[user_type]['expected_plan']
            detected_plan = user_results['subscription_info'][0] if user_results['subscription_info'] else None
            
            print(f"\n{user_type.upper()}:")
            print(f"  Plan esperado: {expected_plan}")
            print(f"  Plan detectado: {detected_plan}")
            
            if user_type == 'admin':
                # Los admins deben tener acceso a todo
                if (user_results['cv_analysis_check'] and user_results['cv_analysis_check'][0] and
                    user_results['cv_creation_check'] and user_results['cv_creation_check'][0]):
                    print(f"  ✅ Restricciones correctas para admin")
                else:
                    print(f"  ❌ Restricciones incorrectas para admin")
                    all_passed = False
            else:
                # Los usuarios normales deben tener restricciones según su plan
                analysis_allowed = user_results['cv_analysis_check'] and user_results['cv_analysis_check'][0]
                creation_allowed = user_results['cv_creation_check'] and user_results['cv_creation_check'][0]
                
                print(f"  Análisis permitido: {'✅' if analysis_allowed else '❌'}")
                print(f"  Creación permitida: {'✅' if creation_allowed else '❌'}")
        
        if all_passed:
            print("\n🎉 TODAS LAS RESTRICCIONES FUNCIONAN CORRECTAMENTE")
        else:
            print("\n⚠️  ALGUNAS RESTRICCIONES REQUIEREN ATENCIÓN")
        
        return all_passed

if __name__ == "__main__":
    tester = RestrictionsIntegrationTester()
    tester.run_comprehensive_test()