from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from app.api.auth import router as auth_router
from app.api.booking import router as booking_router
from app.api.movie import router as movie_router
from app.api.payment import router as payment_router
from app.api.seat_hold import router as seat_hold_router
from app.api.showtime import router as showtime_router
from app.core.auth_middleware import AuthMiddleware
from app.core.exceptions import (
    BookingStateError,
    CinemaException,
    DuplicateSeatError,
    EmailAlreadyExistsError,
    HoldExpiredError,
    HoldOwnershipError,
    HoldStateError,
    InvalidCredentialsError,
    InvalidTokenError,
    NotFoundException,
    OwnershipError,
    PasswordMismatchError,
)

app = FastAPI(title="Cinema Booking System")
app.add_middleware(AuthMiddleware)

EXCEPTION_STATUS_MAP = {
    NotFoundException: 404,
    DuplicateSeatError: 400,
    BookingStateError: 400,
    PasswordMismatchError: 400,
    InvalidCredentialsError: 401,
    InvalidTokenError: 401,
    OwnershipError: 403,
    HoldOwnershipError: 403,
    HoldExpiredError: 409,
    HoldStateError: 409,
    EmailAlreadyExistsError: 409,
}


@app.exception_handler(CinemaException)
async def domain_exception_handler(request: Request, exc: CinemaException) -> JSONResponse:
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 500)
    headers = {"WWW-Authenticate": "Bearer"} if status_code == 401 else None
    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
        headers=headers,
    )


app.include_router(auth_router)
app.include_router(movie_router)
app.include_router(showtime_router)
app.include_router(booking_router)
app.include_router(payment_router)
app.include_router(seat_hold_router)


def custom_openapi():
    """Expose the middleware's Bearer JWT authentication in Swagger UI."""
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    schema.setdefault("components", {}).setdefault("securitySchemes", {})[
        "BearerAuth"
    ] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    protected_operations = {
        ("/api/v1/auth/me", "get"),
        ("/api/v1/bookings/", "post"),
        ("/api/v1/bookings/me", "get"),
        ("/api/v1/bookings/{booking_id}", "delete"),
        ("/api/v1/holds", "post"),
        ("/api/v1/holds/{hold_id}", "get"),
        ("/api/v1/holds/{hold_id}", "delete"),
        ("/api/v1/payments", "post"),
        ("/api/v1/payments/me", "get"),
        ("/api/v1/movies", "post"),
        ("/api/v1/movies/{movie_id}", "put"),
        ("/api/v1/movies/{movie_id}", "delete"),
        ("/api/v1/showtimes", "post"),
    }
    for path, path_item in schema["paths"].items():
        for method, operation in path_item.items():
            if (path, method.lower()) in protected_operations:
                operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )
