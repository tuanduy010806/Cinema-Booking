from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.exceptions import InvalidTokenError

password_hasher = PasswordHash.recommended()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify(plain_password, hashed_password)


def create_access_token(data: dict, exprie_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if exprie_delta is None:
        exprie_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": datetime.now(timezone.utc) + exprie_delta})
    access_token = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return access_token


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        raise InvalidTokenError("could not validate") from None
    return payload
