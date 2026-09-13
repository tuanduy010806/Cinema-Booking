from fastapi import APIRouter

from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest):
    """Register a new user."""
    return AuthService().register(payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    """Authenticate user."""
    return AuthService().login(payload)
