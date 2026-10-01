from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import decode_access_token
from app.db.database import AsyncSessionLocal
from app.repositories.user_repository import UserRepository


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication."""

    async def dispatch(self, request: Request, call_next):
        authorization = request.headers.get("Authorization")
        request.state.current_user = None

        if authorization is None:
            return await call_next(request)

        scheme, separator, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not separator or not token.strip():
            return self._unauthorized()

        try:
            payload = decode_access_token(token.strip())
            user_id = int(payload["sub"])
        except (HTTPException, KeyError, TypeError, ValueError):
            return self._unauthorized()

        async with AsyncSessionLocal() as session:
            user = await UserRepository(session).get_by_id(user_id)

        if user is None:
            return self._unauthorized()

        request.state.current_user = user
        return await call_next(request)

    @staticmethod
    def _unauthorized() -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Could not validate credentials"},
            headers={"WWW-Authenticate": "Bearer"},
        )
