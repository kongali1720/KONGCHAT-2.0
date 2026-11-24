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
            "password": password,
        },
    )
    assert register.status_code == 201, register.text

    user_id = register.json()["id"]

    login = client.post(
        "/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login.status_code == 200, login.text

    return user_id, login.json()["access_token"]


def create_conversation(token, member_ids):
    response = client.post(
        "/v1/conversations",
        json={
            "title": "Realtime Test Conversation",
            "member_ids": member_ids,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def websocket_auth(ws, token):
    ws.send_json({
        "type": "auth",
        "token": token,
    })
    response = ws.receive_json()
    assert response["type"] == "authenticated"
    return response


def test_realtime_message_broadcast_and_persistence():
    user1_id, token1 = register_and_login("rt_sender")
    user2_id, token2 = register_and_login("rt_receiver")

    conversation_id = create_conversation(
        token1,
        [user1_id, user2_id],
    )

    message_content = "Hello KONGCHAT Realtime Engine!"

    with client.websocket_connect(
        f"/ws/conversations/{conversation_id}"
    ) as ws1:
        with client.websocket_connect(
            f"/ws/conversations/{conversation_id}"
        ) as ws2:
            websocket_auth(ws1, token1)
            websocket_auth(ws2, token2)

            ws1.send_json({
                "type": "message",
                "content": message_content,
            })

            received1 = ws1.receive_json()
            received2 = ws2.receive_json()

            assert received1["type"] == "message"
            assert received2["type"] == "message"

            message1 = received1["message"]
            message2 = received2["message"]

            assert message1["content"] == message_content
            assert message2["content"] == message_content
            assert message1["id"] == message2["id"]
            assert message1["sender_id"] == user1_id
            assert message1["conversation_id"] == conversation_id

    # Verify persistence through existing REST history endpoint.
    history = client.get(
        f"/v1/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {token1}"},
    )

    assert history.status_code == 200, history.text

    saved_messages = history.json()["items"]
    assert any(
        item["content"] == message_content
        and item["sender_id"] == user1_id
        for item in saved_messages
    )

    print("PASS: authenticated WebSocket connection")
    print("PASS: realtime message broadcast")
    print("PASS: message persistence verified")


def test_realtime_invalid_token_rejected():
    user_id, token = register_and_login("rt_invalid")

    conversation_id = create_conversation(
        token,
        [user_id],
    )

    with client.websocket_connect(
        f"/ws/conversations/{conversation_id}"
    ) as ws:
        ws.send_json({
            "type": "auth",
            "token": "invalid.jwt.token",
        })

        response = ws.receive_json()

        assert response["type"] == "error"
        assert "authentication" in response["detail"].lower()

    print("PASS: invalid JWT rejected")


def test_realtime_non_member_rejected():
    owner_id, owner_token = register_and_login("rt_owner")
    _, outsider_token = register_and_login("rt_outsider")

    conversation_id = create_conversation(
        owner_token,
        [owner_id],
    )

    with client.websocket_connect(
        f"/ws/conversations/{conversation_id}"
    ) as ws:
        ws.send_json({
            "type": "auth",
            "token": outsider_token,
        })

        response = ws.receive_json()

        assert response["type"] == "error"
        assert "not a member" in response["detail"].lower()

    print("PASS: non-member access rejected")


def test_realtime_typing_indicator_broadcast():
    user1_id, token1 = register_and_login("rt_typing_sender")
    user2_id, token2 = register_and_login("rt_typing_receiver")

    conversation_id = create_conversation(
        token1,
        [user1_id, user2_id],
    )

    profile = client.get(
        "/v1/users/me",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert profile.status_code == 200, profile.text
    username = profile.json()["username"]

    with client.websocket_connect(
        f"/ws/conversations/{conversation_id}"
    ) as ws1:
        with client.websocket_connect(
            f"/ws/conversations/{conversation_id}"
        ) as ws2:
            websocket_auth(ws1, token1)
            websocket_auth(ws2, token2)

            # Typing START broadcast.
            ws1.send_json({"type": "typing.start"})

            received_start1 = ws1.receive_json()
            received_start2 = ws2.receive_json()

            for event in (received_start1, received_start2):
                assert event["type"] == "typing"
                assert event["conversation_id"] == conversation_id
                assert event["user_id"] == user1_id
                assert event["username"] == username
                assert event["status"] == "start"

            # Typing STOP broadcast.
            ws1.send_json({"type": "typing.stop"})

            received_stop1 = ws1.receive_json()
            received_stop2 = ws2.receive_json()

            for event in (received_stop1, received_stop2):
                assert event["type"] == "typing"
                assert event["conversation_id"] == conversation_id
                assert event["user_id"] == user1_id
                assert event["username"] == username
                assert event["status"] == "stop"

    # Typing events must not be persisted as chat messages.
    history = client.get(
        f"/v1/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {token1}"},
    )

    assert history.status_code == 200, history.text
    assert history.json()["items"] == []

    print("PASS: typing.start broadcast to both clients")
    print("PASS: typing.stop broadcast to both clients")
    print("PASS: typing events are not persisted")
