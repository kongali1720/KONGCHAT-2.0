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
            "title": "Message History Test",
            "member_ids": member_ids
        },
        headers=auth_header(token)
    )

    assert response.status_code == 201, response.text
    return response.json()["id"]


def send_message(token, conversation_id, content):
    response = client.post(
        f"/v1/conversations/{conversation_id}/messages",
        json={"content": content},
        headers=auth_header(token)
    )

    assert response.status_code == 201, response.text
    return response.json()


def test_member_can_retrieve_message_history():
    user_id, token = register_and_login("hist_member")

    conversation_id = create_conversation(
        token,
        [user_id]
    )

    send_message(token, conversation_id, "Message one")
    send_message(token, conversation_id, "Message two")
    send_message(token, conversation_id, "Message three")

    response = client.get(
        f"/v1/conversations/{conversation_id}/messages",
        headers=auth_header(token)
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data["items"]) == 3
    assert [m["content"] for m in data["items"]] == [
        "Message one",
        "Message two",
        "Message three"
    ]
    assert all(m["sender_id"] == user_id for m in data["items"])
    assert data["limit"] == 50
    assert data["offset"] == 0
    assert data["has_more"] is False

    print("PASS: member retrieved chronological history")


def test_message_history_pagination():
    user_id, token = register_and_login("hist_page")

    conversation_id = create_conversation(
        token,
        [user_id]
    )

    send_message(token, conversation_id, "Page message 1")
    send_message(token, conversation_id, "Page message 2")
    send_message(token, conversation_id, "Page message 3")
    send_message(token, conversation_id, "Page message 4")
    send_message(token, conversation_id, "Page message 5")

    page_one = client.get(
        f"/v1/conversations/{conversation_id}/messages?limit=2&offset=0",
        headers=auth_header(token)
    )

    assert page_one.status_code == 200, page_one.text

    data_one = page_one.json()

    assert len(data_one["items"]) == 2
    assert [m["content"] for m in data_one["items"]] == [
        "Page message 1",
        "Page message 2"
    ]
    assert data_one["has_more"] is True

    page_two = client.get(
        f"/v1/conversations/{conversation_id}/messages?limit=2&offset=2",
        headers=auth_header(token)
    )

    assert page_two.status_code == 200, page_two.text

    data_two = page_two.json()

    assert len(data_two["items"]) == 2
    assert [m["content"] for m in data_two["items"]] == [
        "Page message 3",
        "Page message 4"
    ]
    assert data_two["has_more"] is True

    page_three = client.get(
        f"/v1/conversations/{conversation_id}/messages?limit=2&offset=4",
        headers=auth_header(token)
    )

    assert page_three.status_code == 200, page_three.text

    data_three = page_three.json()

    assert len(data_three["items"]) == 1
    assert data_three["items"][0]["content"] == "Page message 5"
    assert data_three["has_more"] is False

    print("PASS: message history pagination")


def test_non_member_cannot_read_message_history():
    owner_id, owner_token = register_and_login("hist_owner")
    _, nonmember_token = register_and_login("hist_nonmember")

    conversation_id = create_conversation(
        owner_token,
        [owner_id]
    )

    send_message(owner_token, conversation_id, "Private history")

    response = client.get(
        f"/v1/conversations/{conversation_id}/messages",
        headers=auth_header(nonmember_token)
    )

    assert response.status_code == 403

    print("PASS: non-member blocked from message history")


def test_unknown_conversation_history_returns_404():
    _, token = register_and_login("hist_missing")

    response = client.get(
        "/v1/conversations/999999/messages",
        headers=auth_header(token)
    )

    assert response.status_code == 404

    print("PASS: unknown conversation returns 404")


def test_empty_conversation_history():
    user_id, token = register_and_login("hist_empty")

    conversation_id = create_conversation(
        token,
        [user_id]
    )

    response = client.get(
        f"/v1/conversations/{conversation_id}/messages",
        headers=auth_header(token)
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["items"] == []
    assert data["has_more"] is False
    assert data["limit"] == 50
    assert data["offset"] == 0

    print("PASS: empty history")


def test_invalid_history_pagination_parameters():
    user_id, token = register_and_login("hist_invalid")

    conversation_id = create_conversation(
        token,
        [user_id]
    )

    invalid_limit_zero = client.get(
        f"/v1/conversations/{conversation_id}/messages?limit=0",
        headers=auth_header(token)
    )

    invalid_limit_over_max = client.get(
        f"/v1/conversations/{conversation_id}/messages?limit=101",
        headers=auth_header(token)
    )

    invalid_offset = client.get(
        f"/v1/conversations/{conversation_id}/messages?offset=-1",
        headers=auth_header(token)
    )

    assert invalid_limit_zero.status_code == 422
    assert invalid_limit_over_max.status_code == 422
    assert invalid_offset.status_code == 422

    print("PASS: invalid pagination parameters rejected")
