from typing import Protocol


class UnitOfWork(Protocol):
    """Transaction boundary used by business services.

    The interface deliberately exposes no database session or ORM types.
    """

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
