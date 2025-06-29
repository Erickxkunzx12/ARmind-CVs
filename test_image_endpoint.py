import requests

try:
    print("🧪 Testing image endpoint...")
    response = requests.get('http://127.0.0.1:5000/image/8')
    print(f"✅ Status: {response.status_code}")
    print(f"✅ Content-Type: {response.headers.get('content-type')}")
    print(f"✅ Content-Length: {len(response.content)} bytes")
    
    if response.status_code == 200:
        print("✅ Image served successfully!")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")