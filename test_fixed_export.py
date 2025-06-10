import requests
import json

def test_fixed_export_error_handling():
    """Test the improved error handling in export_cv"""
    
    print("=== PROBANDO MANEJO DE ERRORES MEJORADO ===")
    
    session = requests.Session()
    
    # Test 1: Sin sesión (debería redirigir)
    print("\n1. Probando sin sesión...")
    try:
        response = session.get("http://127.0.0.1:5000/export_cv/80", allow_redirects=False)
        print(f"   Status: {response.status_code}")
        if response.status_code == 302:
            print("   ✅ Redirige correctamente a login")
        else:
            print(f"   ❌ Status inesperado: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Con sesión falsa (podría causar error 500)
    print("\n2. Probando con sesión falsa...")
    try:
        session.cookies.set('session', 'invalid_session_data')
        response = session.get("http://127.0.0.1:5000/export_cv/80")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 500:
            try:
                error_data = response.json()
                print(f"   Error JSON: {error_data}")
                
                # Verificar que ya no devuelve "Error al obtener CV: 0"
                if 'error' in error_data:
                    error_msg = error_data['error']
                    if error_msg == "Error al obtener CV: 0":
                        print("   ❌ Todavía devuelve el error '0'")
                    elif "Error al obtener CV: Error desconocido" in error_msg:
                        print("   ✅ Error mejorado - ya no muestra '0'")
                    else:
                        print(f"   ✅ Error descriptivo: {error_msg}")
                        
            except:
                print(f"   Response no es JSON: {response.text[:200]}")
        else:
            print(f"   Status inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error en test: {e}")
    
    # Test 3: Con CV inexistente
    print("\n3. Probando con CV inexistente...")
    try:
        response = session.get("http://127.0.0.1:5000/export_cv/999999")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 404 or response.status_code == 500:
            try:
                error_data = response.json()
                print(f"   Error JSON: {error_data}")
                
                if 'error' in error_data:
                    error_msg = error_data['error']
                    if "Error al obtener CV: 0" in error_msg:
                        print("   ❌ Todavía devuelve el error '0'")
                    else:
                        print(f"   ✅ Error descriptivo: {error_msg}")
                        
            except:
                print(f"   Response no es JSON: {response.text[:200]}")
        else:
            print(f"   Status inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error en test: {e}")

def test_normal_export_still_works():
    """Verificar que la exportación normal sigue funcionando"""
    
    print("\n=== VERIFICANDO QUE LA EXPORTACIÓN NORMAL FUNCIONA ===")
    
    try:
        # Test con acceso directo (sin autenticación)
        response = requests.get("http://127.0.0.1:5000/export_cv/80", allow_redirects=True)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'No Content-Type')}")
        print(f"Content Length: {len(response.text)}")
        
        if response.status_code == 200:
            if 'text/html' in response.headers.get('Content-Type', ''):
                if 'CV' in response.text or 'Curriculum' in response.text:
                    print("✅ Exportación funciona correctamente")
                elif 'login' in response.text.lower():
                    print("✅ Redirige a login correctamente")
                else:
                    print("❓ Contenido inesperado")
                    print(f"Primeros 200 caracteres: {response.text[:200]}")
            else:
                print(f"❓ Content-Type inesperado: {response.headers.get('Content-Type')}")
        else:
            print(f"❌ Status inesperado: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error en test normal: {e}")

if __name__ == "__main__":
    test_fixed_export_error_handling()
    test_normal_export_still_works()