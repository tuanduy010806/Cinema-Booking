from fastapi import HTTPException, status

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import Role
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    """Business logic for authentication."""

    def __init__(self, user_repository):
        self.user_repository = user_repository

    async def register(self, payload: RegisterRequest) -> TokenResponse:
        if payload.password != payload.repassword:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match",
            )

        if await self.user_repository.get_by_email(payload.email) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email is already registered",
            )

        user = await self.user_repository.create(
            {
                "email": payload.email,
                "username": payload.email.partition("@")[0],
                "password_hash": hash_password(payload.password),
                "role": Role.USER.value,
            }
        )
        access_token = create_access_token({"sub": str(user.user_id)})
        return TokenResponse(access_token=access_token)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.user_repository.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token({"sub": str(user.user_id)})
        return TokenResponse(access_token=access_token)