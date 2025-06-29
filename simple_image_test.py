import requests

def test_image_access():
    """Test if images are accessible via the /image/ route"""
    try:
        # Test image with ID 8
        response = requests.get('http://127.0.0.1:5000/image/8', timeout=5)
        print(f"Image ID 8:")
        print(f"  Status: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"  Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print("  ✅ Image served successfully")
        else:
            print(f"  ❌ Error: {response.text[:200]}")
            
        # Test image with ID 9
        response2 = requests.get('http://127.0.0.1:5000/image/9', timeout=5)
        print(f"\nImage ID 9:")
        print(f"  Status: {response2.status_code}")
        print(f"  Content-Type: {response2.headers.get('content-type', 'unknown')}")
        print(f"  Content-Length: {len(response2.content)} bytes")
        
        if response2.status_code == 200:
            print("  ✅ Image served successfully")
        else:
            print(f"  ❌ Error: {response2.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error testing images: {e}")

if __name__ == "__main__":
    print("🧪 Testing image serving...\n")
    test_image_access()
    print("\n✅ Test completed")