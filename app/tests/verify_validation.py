from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_project_validation():
    print("Testing Project ID Validation...")
    
    # Test valid ID (should be 404 or 200, but NOT 422)
    response = client.get("/api/v1/projects/1")
    assert response.status_code in [200, 401, 403, 404]
    if response.status_code == 422:
        print("FAIL: Valid ID 1 returned 422")
    else:
        print(f"PASS: Valid ID 1 returned {response.status_code}")

    # Test invalid ID 0
    response = client.get("/api/v1/projects/0")
    if response.status_code == 422:
        print("PASS: ID 0 correctly returned 422 Validation Error")
    else:
        print(f"FAIL: ID 0 returned {response.status_code}")
        
    # Test invalid ID -1
    response = client.get("/api/v1/projects/-1")
    if response.status_code == 422:
        print("PASS: ID -1 correctly returned 422 Validation Error")
    else:
        print(f"FAIL: ID -1 returned {response.status_code}")

def test_issue_validation():
    print("\nTesting Issue ID Validation...")
    response = client.get("/api/v1/issues/0")
    if response.status_code == 422:
        print("PASS: Issue ID 0 correctly returned 422")
    else:
        print(f"FAIL: Issue ID 0 returned {response.status_code}")

if __name__ == "__main__":
    test_project_validation()
    test_issue_validation()
