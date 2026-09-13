from pydantic import BaseModel


class MovieCreate(BaseModel):
    title: str
    description: str | None = None
    duration_minutes: int


class MovieUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    duration_minutes: int | None = None


class MovieResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    duration_minutes: int
