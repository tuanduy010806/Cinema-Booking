from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.booking import router as booking_router
from app.api.movie import router as movie_router
from app.api.showtime import router as showtime_router

app = FastAPI(title="Cinema Booking System")

app.include_router(auth_router)
app.include_router(movie_router)
app.include_router(showtime_router)
app.include_router(booking_router)
