from app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    """Business logic for authentication."""

    def __init__(self, user_repository):
        self.user_repository = user_repository

    def register(self, payload: RegisterRequest):
        # TODO: implement
        pass

    def login(self, payload: LoginRequest):
        # TODO: implement
        pass