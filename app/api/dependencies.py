from fastapi import HTTPException, Request, status
from pydantic import BaseModel


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


def get_current_user(request: Request) -> UserIdentity:
    """Return the authenticated identity in the shape expected by bookings."""
    user = _authenticated_user(request)
    return UserIdentity(id=user.user_id, role=user.role)


def get_current_user_account(request: Request) -> dict:
    """Return the current user's public account details, including role."""
    user = _authenticated_user(request)
    return {"user_id": user.user_id, "email": user.email, "role": user.role}
