"""Snapshot loaded ORM scalar values without exposing session-bound objects."""
from dataclasses import fields
from typing import TypeVar

from app.domain.entities import SeatHoldEntity, SeatHoldSeatEntity

T = TypeVar("T")


def to_entity(entity_type: type[T], model) -> T | None:
    if model is None:
        return None
    return entity_type(**{field.name: getattr(model, field.name) for field in fields(entity_type)})


def to_hold(model) -> SeatHoldEntity | None:
    if model is None:
        return None
    return SeatHoldEntity(
        id=model.id, user_id=model.user_id, showtime_id=model.showtime_id,
        status=model.status, created_at=model.created_at, expires_at=model.expires_at,
        seats=tuple(to_entity(SeatHoldSeatEntity, seat) for seat in model.seats),
    )
