import requests
import time

def test_sales_routes():
    """Probar las rutas de ventas directamente"""
    base_url = "http://127.0.0.1:5000"
    
    # Crear una sesión para mantener cookies
    session = requests.Session()
    
    print("=== TESTING SALES ROUTES DIRECTLY ===")
    
    # Test 1: Probar ruta de reportes
    print("\n1. Testing /admin/sales/reports")
    try:
        response = session.get(f"{base_url}/admin/sales/reports", allow_redirects=False)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 302:
            print(f"Redirect Location: {response.headers.get('Location', 'No location header')}")
        elif response.status_code == 200:
            print("✅ Route working correctly")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing route: {e}")
    
    # Test 2: Probar ruta de vendedores
    print("\n2. Testing /admin/sellers")
    try:
        response = session.get(f"{base_url}/admin/sellers", allow_redirects=False)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 302:
            print(f"Redirect Location: {response.headers.get('Location', 'No location header')}")
        elif response.status_code == 200:
            print("✅ Route working correctly")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing route: {e}")
    
    # Test 3: Probar dashboard de ventas (que funciona)
    print("\n3. Testing /admin/sales (working route for comparison)")
    try:
        response = session.get(f"{base_url}/admin/sales", allow_redirects=False)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 302:
            print(f"Redirect Location: {response.headers.get('Location', 'No location header')}")
        elif response.status_code == 200:
            print("✅ Route working correctly")
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing route: {e}")
    
    # Test 4: Verificar si el servidor está corriendo
    print("\n4. Testing server availability")
    try:
        response = session.get(f"{base_url}/", allow_redirects=False)
        print(f"Server Status Code: {response.status_code}")
        print("✅ Server is running")
    except Exception as e:
        print(f"❌ Server not accessible: {e}")

if __name__ == "__main__":
    print("Waiting 2 seconds for server to be ready...")
    time.sleep(2)
    test_sales_routes()