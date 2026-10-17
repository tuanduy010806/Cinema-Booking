import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, status
from starlette.requests import Request

from app.core.permission import RoleChecker
from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
    PasswordMismatchError,
)
from app.core.security import decode_access_token, verify_password
from app.models.user import Role, User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService


class FakeUserRepository:
    def __init__(self):
        self.users = {}

    async def get_by_email(self, email: str):
        return self.users.get(email)

    async def create(self, user_data: dict):
        user = SimpleNamespace(user_id=len(self.users) + 1, **user_data)
        self.users[user.email] = user
        return user


def test_register_creates_user_and_returns_jwt():
    repository = FakeUserRepository()
    service = AuthService(repository)

    result = asyncio.run(
        service.register(
            RegisterRequest(
                email="user@example.com",
                password="correct-password",
                repassword="correct-password",
            )
        )
    )

    user = repository.users["user@example.com"]
    assert user.role == Role.USER.value
    assert verify_password("correct-password", user.password_hash)
    assert decode_access_token(result.access_token)["sub"] == str(user.user_id)


def test_register_rejects_mismatched_passwords():
    service = AuthService(FakeUserRepository())

    with pytest.raises(PasswordMismatchError) as error:
        asyncio.run(
            service.register(
                RegisterRequest(
                    email="user@example.com",
                    password="first-password",
                    repassword="different-password",
                )
            )
        )

    assert str(error.value) == "Passwords do not match"


def test_register_rejects_existing_email():
    repository = FakeUserRepository()
    service = AuthService(repository)
    payload = RegisterRequest(
        email="user@example.com",
        password="correct-password",
        repassword="correct-password",
    )
    asyncio.run(service.register(payload))

    with pytest.raises(EmailAlreadyExistsError) as error:
        asyncio.run(service.register(payload))

    assert str(error.value) == "Email is already registered"


def test_login_verifies_plaintext_password_against_stored_hash():
    repository = FakeUserRepository()
    service = AuthService(repository)
    asyncio.run(
        service.register(
            RegisterRequest(
                email="user@example.com",
                password="correct-password",
                repassword="correct-password",
            )
        )
    )

    result = asyncio.run(
        service.login(
            LoginRequest(email="user@example.com", password="correct-password")
        )
    )

    user = repository.users["user@example.com"]
    assert decode_access_token(result.access_token)["sub"] == str(user.user_id)


def test_login_rejects_unknown_email_or_wrong_password():
    repository = FakeUserRepository()
    service = AuthService(repository)
    asyncio.run(
        service.register(
            RegisterRequest(
                email="user@example.com",
                password="correct-password",
                repassword="correct-password",
            )
        )
    )

    with pytest.raises(InvalidCredentialsError) as wrong_password_error:
        asyncio.run(
            service.login(
                LoginRequest(email="user@example.com", password="wrong-password")
            )
        )

    assert str(wrong_password_error.value) == "Invalid email or password"

    with pytest.raises(InvalidCredentialsError) as missing_email_error:
        asyncio.run(
            service.login(
                LoginRequest(email="missing@example.com", password="correct-password")
            )
        )

    assert str(missing_email_error.value) == "Invalid email or password"


def test_decode_access_token_rejects_invalid_jwt_with_domain_exception():
    with pytest.raises(InvalidTokenError) as error:
        decode_access_token("not-a-valid-jwt")
    assert str(error.value) == "could not validate"


def _request_with_user(user: User | None) -> Request:
    request = Request({"type": "http", "headers": []})
    request.state.current_user = user
    return request


def test_admin_permission_checker_allows_admin_and_rejects_user():
    checker = RoleChecker(Role.ADMIN)
    admin = User(user_id=1, email="admin@example.com", password_hash="hash", role="ADMIN")
    regular_user = User(
        user_id=2,
        email="user@example.com",
        password_hash="hash",
        role="USER",
    )

    assert asyncio.run(checker(_request_with_user(admin))) is admin
    with pytest.raises(HTTPException) as error:
        asyncio.run(checker(_request_with_user(regular_user)))
    assert error.value.status_code == status.HTTP_403_FORBIDDEN


def test_permission_checker_rejects_missing_user():
    with pytest.raises(HTTPException) as error:
        asyncio.run(RoleChecker(Role.ADMIN)(_request_with_user(None)))

    assert error.value.status_code == status.HTTP_401_UNAUTHORIZED
