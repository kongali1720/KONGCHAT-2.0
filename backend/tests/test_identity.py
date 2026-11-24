from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_login_and_profile():
    email = "identity-test@example.com"
    username = "identity_test_user"

    register = client.post(
        "/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": "StrongPass123!"
        }
    )

    if register.status_code == 409:
        login = client.post(
            "/v1/auth/login",
            json={"email": email, "password": "StrongPass123!"}
        )
    else:
        assert register.status_code == 201
        login = client.post(
            "/v1/auth/login",
            json={"email": email, "password": "StrongPass123!"}
        )

    assert login.status_code == 200
    token = login.json()["access_token"]

    profile = client.get(
        "/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert profile.status_code == 200
    assert profile.json()["username"] == username


def test_invalid_login():
    response = client.post(
        "/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "WrongPassword123!"
        }
    )
    assert response.status_code == 401


def test_protected_route():
    response = client.get("/v1/users/me")
    assert response.status_code == 401
