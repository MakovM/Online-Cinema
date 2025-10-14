class TokenExpiredError(Exception):
    """Raised when JWT token has expired."""
    pass


class InvalidTokenError(Exception):
    """Raised when JWT token is invalid."""
    pass
