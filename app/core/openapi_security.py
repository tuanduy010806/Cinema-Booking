"""OpenAPI security metadata for bearer-authenticated endpoints.

JWT validation remains the responsibility of ``AuthMiddleware``. This scheme
is declared so FastAPI can describe bearer authentication in Swagger/OpenAPI.
"""

from fastapi.security import HTTPBearer


bearer_scheme = HTTPBearer(auto_error=False)
