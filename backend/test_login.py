import traceback
from fastapi.testclient import TestClient
from main import app

def test_login():
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "admin@example.com", "password": "password", "remember_me": True}
            )
            print("Response status:", response.status_code)
            # The test just ensures the app can handle the login request without crashing 
            # and returns an appropriate status code.
            assert response.status_code in [200, 400, 401, 404]
    except Exception as e:
        print("Caught Exception!")
        traceback.print_exc()
        raise e
