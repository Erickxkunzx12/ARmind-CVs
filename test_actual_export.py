import requests
import json

def test_actual_export_endpoint():
    """Test the actual export_cv endpoint to reproduce the error"""
    
    # URL del endpoint
    url = "http://127.0.0.1:5000/export_cv/80"
    
    print(f"=== PROBANDO ENDPOINT REAL: {url} ===")
    
    try:
        # Hacer la petición sin sesión (esto debería causar el error)
        response = requests.get(url)
        
        print(f"Status Code: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'No Content-Type')}")
        print(f"Response Length: {len(response.text)}")
        
        if response.status_code != 200:
            print(f"Error Response: {response.text}")
            
            # Intentar parsear como JSON
            try:
                error_data = response.json()
                print(f"Error JSON: {error_data}")
            except:
                print("No se pudo parsear como JSON")
        else:
            print("✅ Respuesta exitosa")
            print(f"Primeros 200 caracteres: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error en la petición: {e}")

def test_with_session():
    """Test with a session to see if that's the issue"""
    
    print("\n=== PROBANDO CON SESIÓN ===")
    
    session = requests.Session()
    
    # Primero hacer login (esto es solo una simulación)
    login_url = "http://127.0.0.1:5000/login"
    
    try:
        # Intentar obtener la página de login para establecer cookies
        login_page = session.get(login_url)
        print(f"Login page status: {login_page.status_code}")
        
        # Ahora intentar el export
        export_url = "http://127.0.0.1:5000/export_cv/80"
        response = session.get(export_url)
        
        print(f"Export Status Code: {response.status_code}")
        print(f"Export Response Length: {len(response.text)}")
        
        if response.status_code != 200:
            print(f"Export Error Response: {response.text}")
            
            try:
                error_data = response.json()
                print(f"Export Error JSON: {error_data}")
            except:
                print("No se pudo parsear como JSON")
        else:
            print("✅ Export exitoso con sesión")
            
    except Exception as e:
        print(f"❌ Error con sesión: {e}")

if __name__ == "__main__":
    test_actual_export_endpoint()
    test_with_session()