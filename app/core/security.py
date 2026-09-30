from pwdlib import PasswordHash
from typing import Optional
from app.schemas.token import Token
import jwt
from datetime import timedelta, datetime, timezone
from fastapi import HTTPException, status
from app.core.exceptions import InvalidTokenError
import os
from dotenv import load_dotenv
load_dotenv()

password_hasher = PasswordHash.recommended()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hasher.verify(hashed_password, plain_password)


def create_access_token(data: dict , exprie_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if exprie_delta is None:
        exprie_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": datetime.now(timezone.utc) + exprie_delta})
    access_token = jwt.encode(to_encode, SECRET_KEY, ALGORITHM)
    return Token(access_token=access_token, token_type="bearer")


def decode_access_token(token: str) -> dict:
    credentials_exception = HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="could not validate"
    )
    try :
        payload = jwt.decode(token,key=SECRET_KEY,algorithms=[ALGORITHM])
    except InvalidTokenError:
        raise credentials_exception
    return payload