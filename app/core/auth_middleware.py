from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication."""

    async def dispatch(self, request: Request, call_next):
        # TODO: implement authentication
        return await call_next(request)
