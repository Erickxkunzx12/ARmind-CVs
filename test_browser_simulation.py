import requests
import json
from requests.cookies import RequestsCookieJar

def test_browser_export_simulation():
    """Simulate exactly how the browser calls the export endpoint"""
    
    print("=== SIMULANDO COMPORTAMIENTO DEL NAVEGADOR ===")
    
    session = requests.Session()
    
    # Simular que el usuario ya está logueado
    # Primero obtener la página principal para establecer cookies
    try:
        print("1. Obteniendo página principal...")
        main_page = session.get("http://127.0.0.1:5000/")
        print(f"   Status: {main_page.status_code}")
        
        # Intentar hacer login (simulado)
        print("2. Intentando acceso directo al export...")
        export_url = "http://127.0.0.1:5000/export_cv/80"
        
        # Agregar headers que normalmente envía el navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = session.get(export_url, headers=headers, allow_redirects=False)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 302:
            print(f"   Redirect Location: {response.headers.get('Location', 'No location')}")
            print("   ✅ Redirigiendo a login (comportamiento esperado sin sesión)")
        elif response.status_code == 200:
            print(f"   Content-Type: {response.headers.get('Content-Type')}")
            print(f"   Content Length: {len(response.text)}")
            
            # Verificar si es HTML de login o el CV
            if 'Iniciar Sesión' in response.text:
                print("   ✅ Página de login devuelta")
            elif 'CV' in response.text and 'html' in response.headers.get('Content-Type', ''):
                print("   ✅ CV HTML devuelto")
            else:
                print("   ❓ Contenido inesperado")
                print(f"   Primeros 200 caracteres: {response.text[:200]}")
        else:
            print(f"   ❌ Status inesperado: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error en simulación: {e}")
        import traceback
        traceback.print_exc()

def test_ajax_call_simulation():
    """Simulate AJAX call to export endpoint"""
    
    print("\n=== SIMULANDO LLAMADA AJAX ===")
    
    session = requests.Session()
    
    try:
        # Headers típicos de una llamada AJAX
        ajax_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Referer': 'http://127.0.0.1:5000/dashboard'
        }
        
        export_url = "http://127.0.0.1:5000/export_cv/80"
        response = session.get(export_url, headers=ajax_headers, allow_redirects=False)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 302:
            print(f"Redirect Location: {response.headers.get('Location')}")
            print("✅ AJAX redirect (puede causar problemas en el frontend)")
        elif response.status_code == 200:
            print(f"Content Length: {len(response.text)}")
            
            # Intentar parsear como JSON
            try:
                json_data = response.json()
                print(f"JSON Response: {json_data}")
            except:
                print("No es JSON válido")
                if len(response.text) < 1000:
                    print(f"Response completa: {response.text}")
                else:
                    print(f"Primeros 500 caracteres: {response.text[:500]}")
        else:
            print(f"❌ Status inesperado: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error en AJAX: {e}")
        import traceback
        traceback.print_exc()

def test_with_fake_session():
    """Test with manually crafted session cookie"""
    
    print("\n=== PROBANDO CON SESIÓN FALSA ===")
    
    session = requests.Session()
    
    # Intentar con una cookie de sesión falsa
    session.cookies.set('session', 'fake_session_value')
    
    try:
        export_url = "http://127.0.0.1:5000/export_cv/80"
        response = session.get(export_url, allow_redirects=False)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 500:
            print("✅ Error 500 - esto podría ser nuestro problema")
            try:
                error_data = response.json()
                print(f"Error JSON: {error_data}")
                
                # Verificar si el error es "Error al obtener CV: 0"
                if 'error' in error_data and 'Error al obtener CV' in error_data['error']:
                    print(f"🎯 ENCONTRADO EL ERROR: {error_data['error']}")
                    
            except:
                print(f"Response text: {response.text}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_browser_export_simulation()
    test_ajax_call_simulation()
    test_with_fake_session()