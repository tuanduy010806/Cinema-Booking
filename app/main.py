from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.booking import router as booking_router
from app.api.movie import router as movie_router
from app.api.showtime import router as showtime_router
from app.core.auth_middleware import AuthMiddleware
from app.core.exceptions import ForbiddenException, NotFoundException, UnauthorizedException

app = FastAPI(title="Cinema Booking System")
app.add_middleware(AuthMiddleware)


# ---------------------------------------------------------------------------
# Global domain exception handlers
# Map service-layer exceptions → correct HTTP status codes
# ---------------------------------------------------------------------------


@app.exception_handler(NotFoundException)
async def not_found_handler(request: Request, exc: NotFoundException) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(UnauthorizedException)
async def unauthorized_handler(request: Request, exc: UnauthorizedException) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(ForbiddenException)
async def forbidden_handler(request: Request, exc: ForbiddenException) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth_router)
app.include_router(movie_router)
app.include_router(showtime_router)
app.include_router(booking_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )
