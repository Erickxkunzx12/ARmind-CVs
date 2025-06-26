import requests
import time

def test_route(url):
    try:
        print(f"Testing {url}...")
        response = requests.get(url, allow_redirects=False)
        print(f"Status: {response.status_code}")
        if response.status_code == 302:
            print(f"Redirect to: {response.headers.get('Location', 'Unknown')}")
        time.sleep(2)  # Wait to see server logs
        return response.status_code
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    base_url = "http://127.0.0.1:5000"
    
    # Test sales reports
    print("=== Testing Sales Reports ===")
    test_route(f"{base_url}/admin/sales/reports")
    
    print("\n=== Testing Sellers ===")
    test_route(f"{base_url}/admin/sellers")
    
    print("\nDone. Check server console for error details.")