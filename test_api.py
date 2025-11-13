import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_api():
    print("Testing Football Fields Booking API")
    print("=" * 40)
    
    # Test 1: Register a new user
    print("\n1. Testing user registration...")
    user_data = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpass123",
        "phone": "0123456789",
        "role": "user"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=user_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test 2: Login
    print("\n2. Testing user login...")
    login_data = {
        "email": "test@example.com",
        "password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/login", json=login_data)
    print(f"Status Code: {response.status_code}")
    login_response = response.json()
    print(f"Response: {login_response}")
    
    # Save access token for later use
    access_token = login_response.get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"} if access_token else {}
    
    # Test 3: Get fields in Giza
    print("\n3. Testing get fields in Giza...")
    response = requests.get(f"{BASE_URL}/fields?governorate=giza")
    print(f"Status Code: {response.status_code}")
    fields_response = response.json()
    print(f"Number of fields found: {len(fields_response.get('fields', []))}")
    
    # Test 4: Get field details
    print("\n4. Testing get field details...")
    if fields_response.get("fields"):
        field_id = fields_response["fields"][0]["id"]
        response = requests.get(f"{BASE_URL}/fields/{field_id}")
        print(f"Status Code: {response.status_code}")
        print(f"Field name: {response.json().get('field', {}).get('name', 'N/A')}")
    
    print("\n" + "=" * 40)
    print("API testing completed!")

if __name__ == "__main__":
    test_api()