from collections.abc import Generator

from sqlalchemy.orm import DeclarativeBase, Session


class Base(DeclarativeBase):
    pass


# TODO: configure database engine and session factory
engine = None
SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """Provide a database session."""
    # TODO: implement
    pass
