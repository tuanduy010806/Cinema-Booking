from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    PasswordMismatchError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.domain.roles import Role
from app.domain.unit_of_work import UnitOfWork
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    """Business logic for authentication."""

    def __init__(
        self, user_repository, unit_of_work: UnitOfWork | None = None
    ):
        self.user_repository = user_repository
        self.unit_of_work = unit_of_work

    async def register(self, payload: RegisterRequest) -> TokenResponse:
        if payload.password != payload.repassword:
            raise PasswordMismatchError("Passwords do not match")

        if await self.user_repository.get_by_email(payload.email) is not None:
            raise EmailAlreadyExistsError("Email is already registered")

        try:
            user = await self.user_repository.create(
                {
                    "email": payload.email,
                    "username": payload.email.partition("@")[0],
                    "password_hash": hash_password(payload.password),
                    "role": Role.USER.value,
                }
            )
            if self.unit_of_work is not None:
                await self.unit_of_work.commit()
        except Exception:
            if self.unit_of_work is not None:
                await self.unit_of_work.rollback()
            raise
        # Issue a token only after user creation succeeds.
        access_token = create_access_token({"sub": str(user.user_id)})
        return TokenResponse(access_token=access_token)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        user = await self.user_repository.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        access_token = create_access_token({"sub": str(user.user_id)})
        return TokenResponse(access_token=access_token)
