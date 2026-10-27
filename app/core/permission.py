from fastapi import HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials

from app.domain.roles import Role
from app.models.user import User
from app.core.openapi_security import bearer_scheme


class RoleChecker:
    def __init__(self, allowed_role: Role | str = Role.USER):
        self.allowed_role = (
            allowed_role.value if isinstance(allowed_role, Role) else allowed_role
        )

    async def __call__(
        self,
        request: Request,
        _credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    ) -> User:
        user = getattr(request.state, "current_user", None)
        if not isinstance(user, User):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Role checks do not replace ownership checks in services.
        if user.role != self.allowed_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Do not have permission",
            )

        return user
