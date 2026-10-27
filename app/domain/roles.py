from enum import Enum


class Role(str, Enum):
    """Application roles, independent of the persistence implementation."""

    USER = "USER"
    ADMIN = "ADMIN"
