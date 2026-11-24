from uuid import uuid4

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def register_and_login(prefix):
    unique = uuid4().hex[:8]
    email = f"{prefix}_{unique}@example.com"
    username = f"{prefix}_{unique}"
    password = "StrongPass123!"

    register = client.post(
        "/v1/auth/register",
        json={
            "email": email,
            "username": username,
            "password": password
        }
    )

    assert register.status_code == 201, register.text
    user_id = register.json()["id"]

    login = client.post(
        "/v1/auth/login",
        json={
            "email": email,
            "password": password
        }
    )

    assert login.status_code == 200, login.text

    return user_id, login.json()["access_token"]


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_conversation_membership_authorization():
    member_id, member_token = register_and_login("conversation_member")
    _, nonmember_token = register_and_login("conversation_nonmember")

    # Create conversation
    create_response = client.post(
        "/v1/conversations",
        json={
            "title": "Automated Security Test",
            "member_ids": [member_id]
        },
        headers=auth_header(member_token)
    )

    assert create_response.status_code == 201, create_response.text

    conversation_id = create_response.json()["id"]

    # Member can list conversation
    list_response = client.get(
        "/v1/conversations",
        headers=auth_header(member_token)
    )

    assert list_response.status_code == 200
    assert any(
        item["id"] == conversation_id
        for item in list_response.json()
    )

    # Member can access detail
    member_detail = client.get(
        f"/v1/conversations/{conversation_id}",
        headers=auth_header(member_token)
    )

    assert member_detail.status_code == 200
    assert member_detail.json()["id"] == conversation_id

    # Non-member cannot see conversation in list
    nonmember_list = client.get(
        "/v1/conversations",
        headers=auth_header(nonmember_token)
    )

    assert nonmember_list.status_code == 200
    assert all(
        item["id"] != conversation_id
        for item in nonmember_list.json()
    )

    # Non-member detail access forbidden
    nonmember_detail = client.get(
        f"/v1/conversations/{conversation_id}",
        headers=auth_header(nonmember_token)
    )

    assert nonmember_detail.status_code == 403

    # Unknown conversation returns 404
    missing_detail = client.get(
        "/v1/conversations/999999",
        headers=auth_header(member_token)
    )

    assert missing_detail.status_code == 404
