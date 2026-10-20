from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.booking import router as booking_router
from app.api.movie import router as movie_router
from app.api.payment import router as payment_router
from app.api.seat_hold import router as seat_hold_router
from app.api.showtime import router as showtime_router
from app.core.auth_middleware import AuthMiddleware
from app.core.exceptions import (
    AuthenticationError,
    BookingStateError,
    CinemaException,
    DuplicateSeatError,
    EmailAlreadyExistsError,
    ForbiddenException,
    HoldExpiredError,
    HoldOwnershipError,
    HoldStateError,
    InvalidCredentialsError,
    InvalidTokenError,
    NotFoundException,
    OwnershipError,
    PaymentOwnershipError,
    PasswordMismatchError,
    UnauthorizedException,
)

app = FastAPI(title="Cinema Booking System")
app.add_middleware(AuthMiddleware)

EXCEPTION_STATUS_MAP = {
    NotFoundException: 404,
    DuplicateSeatError: 400,
    BookingStateError: 400,
    PasswordMismatchError: 400,
    InvalidCredentialsError: 401,
    AuthenticationError: 401,
    InvalidTokenError: 401,
    UnauthorizedException: 401,
    OwnershipError: 403,
    PaymentOwnershipError: 403,
    HoldOwnershipError: 403,
    HoldExpiredError: 409,
    HoldStateError: 409,
    ForbiddenException: 403,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )
