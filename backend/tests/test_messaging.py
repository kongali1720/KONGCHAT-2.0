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


def create_conversation(token, member_ids):
    response = client.post(
        "/v1/conversations",
        json={
            "title": "Messaging Test Conversation",
            "member_ids": member_ids
        },
        headers=auth_header(token)
    )

    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_member_can_send_message_and_sender_cannot_be_spoofed():
    member_id, token = register_and_login("msg_member")

    conversation_id = create_conversation(
        token,
        [member_id]
    )

    response = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={
            "content": "  Hello KONGCHAT Messaging Engine!  ",
            "sender_id": 999999
        },
        headers=auth_header(token)
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["id"] > 0
    assert data["conversation_id"] == conversation_id
    assert data["sender_id"] == member_id
    assert data["content"] == "Hello KONGCHAT Messaging Engine!"
    assert data["created_at"] is not None

    print("PASS: member sent message")
    print("PASS: sender_id spoofing prevented")


def test_non_member_cannot_send_message():
    owner_id, owner_token = register_and_login("msg_owner")
    _, nonmember_token = register_and_login("msg_nonmember")

    conversation_id = create_conversation(
        owner_token,
        [owner_id]
    )

    response = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "Unauthorized message"},
        headers=auth_header(nonmember_token)
    )

    assert response.status_code == 403


def test_unknown_conversation_returns_404():
    user_id, token = register_and_login("msg_missing")

    response = client.post(
        "/v1/conversations/999999/messages",
        json={"content": "Hello"},
        headers=auth_header(token)
    )

    assert response.status_code == 404


def test_whitespace_message_rejected():
    user_id, token = register_and_login("msg_empty")

    conversation_id = create_conversation(
        token,
        [user_id]
    )

    response = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "     "},
        headers=auth_header(token)
    )

    assert response.status_code == 422


def test_message_over_10000_characters_rejected():
    user_id, token = register_and_login("msg_long")

    conversation_id = create_conversation(
        token,
        [user_id]
    )

    response = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": "x" * 10001},
        headers=auth_header(token)
    )

    assert response.status_code == 422
