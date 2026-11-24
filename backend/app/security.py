from datetime import datetime, timedelta, timezone
from jose import jwt
from pwdlib import PasswordHash
from .config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def create_access_token(user_id: int) -> tuple[str, int]:
    expires_in = JWT_EXPIRE_MINUTES * 60
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": expires_at,
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expires_in
