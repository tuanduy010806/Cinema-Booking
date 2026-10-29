from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    PasswordMismatchError,
)
from app.domain.commands import RegisterCommand, LoginCommand, CreateUserCommand
from app.domain.entities import TokenResult
from app.domain.ports import UserRepository, PasswordSecurity, TokenIssuer
from app.domain.roles import Role
from app.domain.unit_of_work import UnitOfWork


class AuthService:
    def __init__(
        self, user_repository: UserRepository, password_security: PasswordSecurity,
        token_issuer: TokenIssuer, unit_of_work: UnitOfWork | None = None
    ):
        self.user_repository = user_repository
        self.password_security = password_security
        self.token_issuer = token_issuer
        self.unit_of_work = unit_of_work

    async def register(self, payload: RegisterCommand) -> TokenResult:
        if payload.password != payload.repassword:
            raise PasswordMismatchError("Passwords do not match")

        if await self.user_repository.get_by_email(payload.email) is not None:
            raise EmailAlreadyExistsError("Email is already registered")

        try:
            user = await self.user_repository.create(
                CreateUserCommand(
                    email=payload.email, username=payload.email.partition("@")[0],
                    password_hash=self.password_security.hash(payload.password),
                    role=Role.USER.value,
                )
            )
            if self.unit_of_work is not None:
                await self.unit_of_work.commit()
        except Exception:
            if self.unit_of_work is not None:
                await self.unit_of_work.rollback()
            raise
        # Issue a token only after user creation succeeds.
        access_token = self.token_issuer.issue(user.user_id)
        return TokenResult(access_token=access_token)

    async def login(self, payload: LoginCommand) -> TokenResult:
        user = await self.user_repository.get_credentials_by_email(payload.email)
        if user is None or not self.password_security.verify(payload.password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        access_token = self.token_issuer.issue(user.user_id)
        return TokenResult(access_token=access_token)
