"""
Quick test script to verify backend is running
"""

import requests
import sys

def test_backend():
    try:
        # Test root endpoint
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✓ Backend is running!")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"✗ Backend returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to backend at http://localhost:8000")
        print("  Make sure the backend is running: python start_backend.py")
        return False
    except Exception as e:
        print(f"✗ Error testing backend: {e}")
        return False

if __name__ == "__main__":
    print("Testing backend connection...")
    success = test_backend()
    sys.exit(0 if success else 1)
