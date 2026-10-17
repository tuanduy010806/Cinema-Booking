from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_account
from app.db.database import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import CurrentUserResponse, LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


@router.post("/register", response_model=TokenResponse)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Register a new user."""
    return await service.register(payload)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Authenticate user."""
    return await service.login(payload)


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(current_user: dict = Depends(get_current_user_account)):
    """Return the identity and role associated with the current access token."""
    return current_user