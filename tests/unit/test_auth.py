from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.security import decode_access_token
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService


class FakeUserRepository:
    def __init__(self):
        self.users_by_email = {}

    async def get_by_email(self, email: str):
        return self.users_by_email.get(email)

    async def create(self, user_data: dict):
        user = SimpleNamespace(user_id=len(self.users_by_email) + 1, **user_data)
        self.users_by_email[user.email] = user
        return user


@pytest.fixture
def auth_service():
    repository = FakeUserRepository()
    return AuthService(repository), repository


@pytest.mark.asyncio
async def test_register_always_creates_user_and_returns_jwt(auth_service):
    service, repository = auth_service

    response = await service.register(
        RegisterRequest(
            email="user@example.test",
            password="strong-password",
            repassword="strong-password",
        )
    )

    user = repository.users_by_email["user@example.test"]
    assert user.role == "USER"
    assert user.password_hash != "strong-password"
    assert decode_access_token(response.access_token)["sub"] == str(user.user_id)


@pytest.mark.asyncio
async def test_login_accepts_valid_password_and_returns_jwt(auth_service):
    service, _ = auth_service
    await service.register(
        RegisterRequest(
            email="login@example.test",
            password="strong-password",
            repassword="strong-password",
        )
    )

    response = await service.login(
        LoginRequest(email="login@example.test", password="strong-password")
    )

    assert decode_access_token(response.access_token)["sub"] == "1"


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(auth_service):
    service, _ = auth_service
    await service.register(
        RegisterRequest(
            email="login@example.test",
            password="strong-password",
            repassword="strong-password",
        )
    )

    with pytest.raises(HTTPException) as error:
        await service.login(
            LoginRequest(email="login@example.test", password="incorrect")
        )

    assert error.value.status_code == 401
