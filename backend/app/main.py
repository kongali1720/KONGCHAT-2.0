from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .config import APP_NAME
from .database import Base, engine, get_db
from .models import User, Conversation, ConversationMember, Message
from .schemas import RegisterRequest, LoginRequest, TokenResponse, UserResponse, ConversationCreate, ConversationResponse, MessageCreate, MessageResponse, MessageHistoryResponse
from .security import hash_password, verify_password, create_access_token
from .auth import get_current_user

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=APP_NAME,
    version="0.1.0",
    description="KONGCHAT Identity Engine — authentication and identity foundation"
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "kongchat-identity-engine"}


@app.post(
    "/v1/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    username = payload.username.strip()

    existing = db.query(User).filter(
        or_(User.email == email, User.username == username)
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Email or username already registered"
        )

    user = User(
        email=email,
        username=username,
        password_hash=hash_password(payload.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/v1/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token, expires_in = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": user
    }


@app.get("/v1/users/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post(
    "/v1/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Creator is always included as a member.
    member_ids = list(set(payload.member_ids + [current_user.id]))

    # Validate that every requested user exists.
    users = db.query(User).filter(User.id.in_(member_ids)).all()

    if len(users) != len(member_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more member IDs do not exist"
        )

    conversation = Conversation(
        title=payload.title.strip() if payload.title and payload.title.strip() else None
    )

    db.add(conversation)
    db.flush()

    memberships = [
        ConversationMember(
            conversation_id=conversation.id,
            user_id=user_id
        )
        for user_id in member_ids
    ]

    db.add_all(memberships)
    db.commit()
    db.refresh(conversation)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "member_ids": member_ids
    }


@app.get(
    "/v1/conversations",
    response_model=list[ConversationResponse]
)
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversations = (
        db.query(Conversation)
        .join(ConversationMember)
        .filter(ConversationMember.user_id == current_user.id)
        .order_by(Conversation.id.desc())
        .all()
    )

    result = []

    for conversation in conversations:
        member_ids = [
            member.user_id for member in conversation.members
        ]

        result.append({
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at,
            "member_ids": member_ids
        })

    return result


@app.get(
    "/v1/conversations/{conversation_id}",
    response_model=ConversationResponse
)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Find conversation first.
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Verify membership before exposing conversation details.
    membership = (
        db.query(ConversationMember)
        .filter(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == current_user.id
        )
        .first()
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this conversation"
        )

    member_ids = [
        member.user_id for member in conversation.members
    ]

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "member_ids": member_ids
    }

# Messaging Engine — Send Message

@app.post(
    "/v1/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED
)
def send_message(
    conversation_id: int,
    payload: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    membership = (
        db.query(ConversationMember)
        .filter(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == current_user.id
        )
        .first()
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this conversation"
        )

    message = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        content=payload.content
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message



# Message History Engine — Retrieve Messages

@app.get(
    "/v1/conversations/{conversation_id}/messages",
    response_model=MessageHistoryResponse
)
def get_messages(
    conversation_id: int,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    membership = (
        db.query(ConversationMember)
        .filter(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == current_user.id
        )
        .first()
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this conversation"
        )

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.id.asc())
        .offset(offset)
        .limit(limit + 1)
        .all()
    )

    has_more = len(messages) > limit
    messages = messages[:limit]

    return {
        "items": messages,
        "limit": limit,
        "offset": offset,
        "has_more": has_more
    }
