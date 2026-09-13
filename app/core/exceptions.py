class CinemaException(Exception):
    """Base exception for cinema booking system."""


class NotFoundException(CinemaException):
    """Resource not found."""


class UnauthorizedException(CinemaException):
    """Unauthorized access."""


class ForbiddenException(CinemaException):
    """Forbidden access."""
