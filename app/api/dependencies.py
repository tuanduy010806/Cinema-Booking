from fastapi import HTTPException, Request, status


def get_current_user(request: Request) -> dict:
    """Return the authenticated user in the shape expected by booking services."""
    user = getattr(request.state, "current_user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"id": user.user_id, "role": user.role}
