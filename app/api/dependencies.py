from fastapi import HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.core.openapi_security import bearer_scheme


class UserIdentity(BaseModel):
    id: int
    role: str


def _authenticated_user(request: Request):
    user = getattr(request.state, "current_user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_user(
    request: Request,
    _credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> UserIdentity:
    """Return the authenticated identity in the shape expected by bookings."""
    user = _authenticated_user(request)
    return UserIdentity(id=user.user_id, role=user.role)


def get_current_user_account(
    request: Request,
    _credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> dict:
    """Return the current user's public account details, including role."""
    user = _authenticated_user(request)
    return {"user_id": user.user_id, "email": user.email, "role": user.role}
