from app.domain.commands import RegisterCommand, LoginCommand
from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user_account
from app.api.providers import get_auth_service
from app.schemas.auth import CurrentUserResponse, LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    result = await service.register(RegisterCommand(**payload.model_dump()))
    return TokenResponse(access_token=result.access_token, token_type=result.token_type)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    result = await service.login(LoginCommand(**payload.model_dump()))
    return TokenResponse(access_token=result.access_token, token_type=result.token_type)


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(current_user: dict = Depends(get_current_user_account)):
    """Return the identity and role associated with the current access token."""
    return current_user
